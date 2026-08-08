"""OYO-style gaming parlor booking business logic."""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.gaming_booking.booking_ref import generate_booking_ref
from app.domains.gaming_booking.gc_points import GCPointsTransaction
from app.domains.gaming_booking.models import GamingBooking, GamingSlot
from app.domains.gaming_booking.offer_service import OfferService
from app.domains.gaming_booking.repository import GamingBookingRepository
from app.domains.gaming_booking.schemas import (
    CancelBookingRequest,
    CompletePaymentRequest,
    CreateGamingBookingRequest,
    GamingBookingResponse,
    PaymentOption,
    PaymentOptionsResponse,
    PriceBreakdown,
)
from app.domains.gaming_place.location_utils import extract_images, extract_locality, is_open_now
from app.domains.gaming_place.mappers import resolve_media_url, to_view
from app.domains.gaming_place.models import GamingPlaceExtension
from app.domains.parlor.repository import ParlorRepository

DEFAULT_TAX_RATE = Decimal("18")
GC_POINTS_PER_RUPEE = 1


def _slot_hours(start: time, end: time) -> Decimal:
    start_mins = start.hour * 60 + start.minute
    end_mins = end.hour * 60 + end.minute
    if end_mins <= start_mins:
        end_mins += 24 * 60
    hours = Decimal(end_mins - start_mins) / Decimal("60")
    return hours.quantize(Decimal("0.01"))


def _combine_slot_datetime(slot_date: date, slot_time: time) -> datetime:
    return datetime.combine(slot_date, slot_time, tzinfo=UTC)


class GamingBookingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = GamingBookingRepository(session)
        self.parlor_repo = ParlorRepository(session)
        self.offer_service = OfferService(session)

    async def calculate_price(
        self,
        parlour_id: UUID,
        slot: GamingSlot,
        *,
        num_players: int = 1,
        offer_id: UUID | None = None,
    ) -> PriceBreakdown:
        ext = await self.repo.get_extension(parlour_id)
        tax_rate = (
            Decimal(str(ext.base_tax_rate))
            if ext and ext.base_tax_rate is not None
            else DEFAULT_TAX_RATE
        )
        hours = _slot_hours(slot.start_time, slot.end_time)
        subtotal = (slot.price_per_hour * hours * num_players).quantize(Decimal("0.01"))

        offer = None
        if offer_id:
            offer = await self.offer_service.validate_offer(
                offer_id, parlour_id, hours_booked=hours
            )
        discount = self.offer_service.calculate_discount(offer, subtotal)
        taxable = subtotal - discount
        tax_amount = (taxable * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        final_price = (taxable + tax_amount).quantize(Decimal("0.01"))

        return PriceBreakdown(
            price_per_hour=slot.price_per_hour,
            hours_booked=hours,
            num_players=num_players,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            discount_amount=discount,
            final_price=final_price,
        )

    async def check_slot_availability(self, slot_id: UUID, num_players: int = 1) -> GamingSlot:
        slot = await self.repo.get_slot_by_id(slot_id)
        if slot is None:
            raise NotFoundError("Slot not found")
        if not slot.is_available:
            raise ValidationError("Slot is not available")
        remaining = slot.max_players - slot.current_bookings
        if remaining < num_players:
            raise ValidationError("Not enough capacity in this slot")
        return slot

    async def create_booking(
        self,
        user_id: UUID,
        data: CreateGamingBookingRequest,
        redis: aioredis.Redis | None = None,
    ) -> GamingBookingResponse:
        lock_key = f"lock:gaming_slot:{data.slot_id}"
        if redis is not None:
            acquired = await redis.set(lock_key, "1", nx=True, ex=5)
            if not acquired:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Try again in a moment",
                )

        try:
            result = await self.session.execute(
                select(GamingSlot)
                .where(GamingSlot.id == data.slot_id)
                .with_for_update()
            )
            slot = result.scalar_one_or_none()
            if slot is None:
                raise NotFoundError("Slot not found")
            if slot.parlour_id != data.parlour_id:
                raise ValidationError("Slot does not belong to this parlor")
            if not slot.is_available:
                raise ValidationError("Slot is not available")
            if slot.max_players - slot.current_bookings < data.num_players:
                raise ValidationError("Not enough capacity in this slot")

            price = await self.calculate_price(
                data.parlour_id,
                slot,
                num_players=data.num_players,
                offer_id=data.offer_id,
            )

            booking_ref = await generate_booking_ref(self.session)
            slot_start = _combine_slot_datetime(slot.slot_date, slot.start_time)
            free_cancel_before = slot_start - timedelta(hours=2)

            booking = GamingBooking(
                booking_ref=booking_ref,
                user_id=user_id,
                parlour_id=data.parlour_id,
                slot_id=slot.id,
                offer_id=data.offer_id,
                guest_name=data.guest_name,
                num_players=data.num_players,
                slot_date=slot.slot_date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                hours_booked=price.hours_booked,
                price_per_hour=price.price_per_hour,
                total_price=price.subtotal,
                tax_amount=price.tax_amount,
                discount_amount=price.discount_amount,
                final_price=price.final_price,
                payment_mode=data.payment_mode,
                payment_status="pending",
                booking_status="confirmed",
                free_cancellation_before=free_cancel_before,
                is_non_refundable=data.payment_mode == "non_refundable",
                contact_email=data.contact_email,
                contact_phone=data.contact_phone,
            )

            slot.current_bookings += data.num_players
            if slot.current_bookings >= slot.max_players:
                slot.is_available = False

            if data.offer_id:
                offer = await self.repo.get_offer_by_id(data.offer_id)
                if offer:
                    await self.offer_service.increment_offer_usage(offer)

            await self.repo.create_booking(booking)
            await self.session.commit()
            await self.session.refresh(booking)
            return await self._to_response(booking)
        finally:
            if redis is not None:
                await redis.delete(lock_key)

    async def get_payment_options(self, booking_id: UUID, user_id: UUID) -> PaymentOptionsResponse:
        booking = await self._get_user_booking(booking_id, user_id)
        options = [
            PaymentOption(
                mode="pay_at_parlor",
                label="Pay at Parlor",
                description="Pay when you arrive at the gaming parlor",
                is_available=True,
            ),
            PaymentOption(
                mode="online",
                label="Pay Online (Cashfree)",
                description="Pay now via UPI, card, or net banking (Cashfree)",
                is_available=booking.final_price is not None and booking.final_price > 0,
            ),
            PaymentOption(
                mode="non_refundable",
                label="Non-refundable (Instant)",
                description="Lower price, no free cancellation",
                is_available=True,
            ),
        ]
        return PaymentOptionsResponse(booking_id=booking_id, options=options)

    async def complete_payment(
        self,
        booking_id: UUID,
        user_id: UUID,
        data: CompletePaymentRequest,
    ) -> tuple[GamingBookingResponse, int]:
        booking = await self._get_user_booking(booking_id, user_id)
        if booking.payment_status == "paid":
            raise ValidationError("Already paid")

        if booking.payment_mode == "online":
            if not data.order_id or not data.payment_id or not data.signature:
                raise ValidationError("Payment verification fields required for online payment")
            from app.domains.payments.razorpay_stub import verify_payment_stub

            result = verify_payment_stub(data.order_id, data.payment_id, data.signature)
            if result.get("status") == "not_configured":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Razorpay not configured",
                )
            booking.payment_id = data.payment_id

        booking.payment_status = "paid"
        points = await self.award_gc_points(user_id, booking)
        booking.gc_points_earned = points
        await self.session.commit()
        await self.session.refresh(booking)
        return await self._to_response(booking), points

    async def award_gc_points(self, user_id: UUID, booking: GamingBooking) -> int:
        if booking.final_price is None or booking.final_price <= 0:
            return 0
        points = int(booking.final_price * GC_POINTS_PER_RUPEE)
        if points <= 0:
            return 0

        balance = await self.repo.ensure_gc_points(user_id)
        balance.balance += points
        balance.lifetime_earned += points
        balance.updated_at = datetime.now(UTC)

        await self.repo.add_gc_transaction(
            GCPointsTransaction(
                user_id=user_id,
                amount=points,
                transaction_type="earn",
                booking_id=booking.id,
                description=f"Earned from booking {booking.booking_ref}",
            )
        )
        return points

    async def cancel_booking(
        self,
        booking_id: UUID,
        user_id: UUID,
        data: CancelBookingRequest,
    ) -> GamingBookingResponse:
        booking = await self._get_user_booking(booking_id, user_id)
        if booking.booking_status == "cancelled":
            raise ValidationError("Booking is already cancelled")

        reason_label = data.cancellation_reason
        if data.reason_id:
            reason = await self.repo.get_cancellation_reason(data.reason_id)
            if reason is None:
                raise NotFoundError("Cancellation reason not found")
            reason_label = reason.label
            if reason.requires_detail and not data.cancellation_detail:
                raise ValidationError("Additional detail required for this cancellation reason")

        if not booking.is_cancellation_free and not booking.is_non_refundable:
            if booking.free_cancellation_before and datetime.now(UTC) >= booking.free_cancellation_before.replace(
                tzinfo=UTC
            ):
                booking.refund_amount = Decimal("0")
                booking.refund_status = "not_applicable"
        elif booking.is_cancellation_free and booking.final_price:
            booking.refund_amount = booking.final_price
            booking.refund_status = "pending"
        elif booking.is_non_refundable:
            booking.refund_amount = Decimal("0")
            booking.refund_status = "not_applicable"

        booking.booking_status = "cancelled"
        booking.cancellation_reason = reason_label
        booking.cancellation_detail = data.cancellation_detail
        booking.cancelled_at = datetime.now(UTC)

        if booking.slot_id:
            result = await self.session.execute(
                select(GamingSlot).where(GamingSlot.id == booking.slot_id).with_for_update()
            )
            slot = result.scalar_one_or_none()
            if slot:
                slot.current_bookings = max(0, slot.current_bookings - booking.num_players)
                slot.is_available = True

        await self.session.commit()
        await self.session.refresh(booking)
        return await self._to_response(booking)

    async def get_user_bookings(
        self,
        user_id: UUID,
        *,
        status_filter: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[GamingBookingResponse], int]:
        page = max(page, 1)
        limit = min(max(limit, 1), 50)
        offset = (page - 1) * limit
        bookings, total = await self.repo.list_user_bookings(
            user_id, status=status_filter, limit=limit, offset=offset
        )
        items = [await self._to_response(b) for b in bookings]
        return items, total

    async def update_guest_name(
        self, booking_id: UUID, user_id: UUID, guest_name: str
    ) -> GamingBookingResponse:
        booking = await self._get_user_booking(booking_id, user_id)
        booking.guest_name = guest_name
        await self.session.commit()
        await self.session.refresh(booking)
        return await self._to_response(booking)

    async def update_gstin(
        self, booking_id: UUID, user_id: UUID, gstin: str
    ) -> GamingBookingResponse:
        booking = await self._get_user_booking(booking_id, user_id)
        booking.gstin = gstin.upper()
        await self.session.commit()
        await self.session.refresh(booking)
        return await self._to_response(booking)

    async def get_booking(self, booking_id: UUID, user_id: UUID | None = None) -> GamingBookingResponse:
        booking = await self.repo.get_booking_by_id(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if user_id and booking.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return await self._to_response(booking)

    async def get_booking_by_ref(
        self, booking_ref: str, user_id: UUID | None = None
    ) -> GamingBookingResponse:
        booking = await self.repo.get_booking_by_ref(booking_ref)
        if booking is None:
            raise NotFoundError("Booking not found")
        if user_id and booking.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return await self._to_response(booking)

    async def _get_user_booking(self, booking_id: UUID, user_id: UUID) -> GamingBooking:
        booking = await self.repo.get_booking_by_id(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if booking.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return booking

    async def _to_response(self, booking: GamingBooking) -> GamingBookingResponse:
        parlour_name = None
        place = await self.repo.get_place(booking.parlour_id)
        if place:
            parlour_name = place.name

        data = GamingBookingResponse.model_validate(booking)
        return data.model_copy(
            update={
                "parlour_name": parlour_name,
                "is_cancellation_free": booking.is_cancellation_free,
            }
        )


class ParlourBookingViewService:
    """OYO-style parlor detail, search, slots, offers, gallery, ratings."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = GamingBookingRepository(session)
        self.parlor_repo = ParlorRepository(session)

    async def get_detail(
        self,
        parlour_id: UUID,
        *,
        lat: float | None = None,
        lng: float | None = None,
        user_id: UUID | None = None,
    ):
        from app.domains.gaming_booking.schemas import ParlourDetailResponse

        place = await self.repo.get_place(parlour_id)
        if place is None:
            raise NotFoundError("Parlor not found")

        ext = await self.repo.get_extension(parlour_id)
        view = to_view(place, ext)
        city, state, _ = extract_locality(place)
        images = extract_images(place)

        distance = None
        if lat is not None and lng is not None and place.latitude and place.longitude:
            from app.domains.geo.service import GeoService

            distance = await GeoService(self.session)._distance_meters(
                lat, lng, place.latitude, place.longitude
            )

        if user_id is not None:
            await self.repo.record_parlour_view(
                user_id,
                parlour_id=parlour_id,
                parlour_name=view.name,
                city=city,
            )
            await self.session.commit()

        return ParlourDetailResponse(
            id=view.id,
            name=view.name,
            address=view.address,
            city=city,
            state=state,
            lat=view.latitude,
            lng=view.longitude,
            rating=view.rating,
            phone=view.phone,
            website=view.website,
            images=images,
            is_verified=view.is_verified,
            is_open=is_open_now(place),
            price_per_hour=ext.price_per_hour if ext else None,
            original_price=ext.original_price if ext else None,
            discount_percent=ext.discount_percent if ext else None,
            base_tax_rate=Decimal(str(ext.base_tax_rate)) if ext and ext.base_tax_rate else DEFAULT_TAX_RATE,
            equipment_rating=float(ext.equipment_rating) if ext and ext.equipment_rating else None,
            staff_rating=float(ext.staff_rating) if ext and ext.staff_rating else None,
            checkin_rating=float(ext.checkin_rating) if ext and ext.checkin_rating else None,
            is_wizard_enabled=ext.is_wizard_enabled if ext else False,
            is_couples_allowed=ext.is_couples_allowed if ext else False,
            game_types=view.game_types,
            distance_meters=distance,
        )

    async def get_gallery(self, parlour_id: UUID):
        from app.domains.gaming_booking.schemas import ParlourGalleryResponse

        place = await self.repo.get_place(parlour_id)
        if place is None:
            raise NotFoundError("Parlor not found")
        images = extract_images(place)
        if place.image_url:
            hero = resolve_media_url(place.image_url)
            if hero and hero not in images:
                images = [hero, *images]
        return ParlourGalleryResponse(parlour_id=parlour_id, images=images)

    async def get_slots(self, parlour_id: UUID, slot_date: date | None = None):
        from app.domains.gaming_booking.schemas import GamingSlotResponse, SlotListResponse
        from app.domains.gaming_booking.slot_engine import SlotEngine

        place = await self.repo.get_place(parlour_id)
        if place is None:
            raise NotFoundError("Parlor not found")

        # Auto-materialize virtual hourly slots when inventory is empty
        # (fixes Flutter "No slots for this date" for catalog parlors).
        target = slot_date or date.today()
        engine = SlotEngine(self.session)
        await engine.ensure_slots_for_date(parlour_id, target)

        slots = await self.repo.list_slots(parlour_id, slot_date=slot_date)
        return SlotListResponse(
            parlour_id=parlour_id,
            slot_date=slot_date,
            slots=[GamingSlotResponse.model_validate(s) for s in slots],
        )

    async def get_offers(self, parlour_id: UUID):
        from app.domains.gaming_booking.schemas import OfferListResponse, ParlourOfferResponse

        place = await self.repo.get_place(parlour_id)
        if place is None:
            raise NotFoundError("Parlor not found")
        offers = await self.repo.list_active_offers(parlour_id)
        return OfferListResponse(
            parlour_id=parlour_id,
            offers=[ParlourOfferResponse.model_validate(o) for o in offers],
        )

    async def get_ratings(self, parlour_id: UUID, *, page: int = 1, limit: int = 20):
        from app.domains.gaming_booking.schemas import ParlourRatingResponse, ParlourRatingsSummary

        place = await self.repo.get_place(parlour_id)
        if place is None:
            raise NotFoundError("Parlor not found")

        page = max(page, 1)
        limit = min(max(limit, 1), 50)
        offset = (page - 1) * limit
        ratings, summary = await self.repo.list_ratings(
            parlour_id, limit=limit, offset=offset
        )
        return ParlourRatingsSummary(
            average_rating=summary["average_rating"],
            total_reviews=summary["total_reviews"],
            equipment_rating=summary["equipment_rating"],
            staff_rating=summary["staff_rating"],
            location_rating=summary["location_rating"],
            cleanliness_rating=summary["cleanliness_rating"],
            checkin_rating=summary["checkin_rating"],
            reviews=[
                ParlourRatingResponse.model_validate(r).model_copy(
                    update={"review_photos": r.review_photos or []}
                )
                for r in ratings
            ],
        )

    async def search_parlors(
        self,
        lat: float,
        lng: float,
        *,
        radius_m: float = 5000,
        q: str | None = None,
        min_rating: float | None = None,
        open_now: bool | None = None,
        city: str | None = None,
        page: int = 1,
        limit: int = 20,
        user_id: UUID | None = None,
        redis: aioredis.Redis | None = None,
    ):
        from app.domains.geo.service import GeoService
        from app.domains.gaming_booking.schemas import ParlourSearchItem, ParlourSearchResult

        geo = GeoService(self.session)
        rows = await geo.get_nearby_parlors_sorted(
            lat, lng, radius_m, limit=limit * page, redis=redis
        )

        if q or min_rating or open_now or city:
            filtered = []
            needle = q.strip().lower() if q else None
            city_needle = city.strip().lower() if city else None
            for place, view, distance in rows:
                if min_rating and (place.rating or 0) < min_rating:
                    continue
                if open_now and not is_open_now(place):
                    continue
                loc_city, _, _ = extract_locality(place)
                if city_needle:
                    hay = f"{loc_city or ''} {place.address or ''}".lower()
                    if city_needle not in hay:
                        continue
                if needle:
                    haystack = f"{place.name} {place.address or ''}".lower()
                    if needle not in haystack:
                        continue
                filtered.append((place, view, distance))
            rows = filtered

        page = max(page, 1)
        limit = min(max(limit, 1), 50)
        offset = (page - 1) * limit
        total = len(rows)
        page_rows = rows[offset : offset + limit]

        items = []
        for place, view, distance in page_rows:
            ext = await self.repo.get_extension(place.id)
            city_name, state, _ = extract_locality(place)
            items.append(
                ParlourSearchItem(
                    id=view.id,
                    name=view.name,
                    address=view.address,
                    city=city_name,
                    state=state,
                    lat=view.latitude,
                    lng=view.longitude,
                    rating=view.rating,
                    phone=view.phone,
                    website=view.website,
                    images=extract_images(place),
                    is_verified=view.is_verified,
                    is_open=is_open_now(place),
                    price_per_hour=ext.price_per_hour if ext else None,
                    original_price=ext.original_price if ext else None,
                    discount_percent=ext.discount_percent if ext else None,
                    base_tax_rate=Decimal(str(ext.base_tax_rate))
                    if ext and ext.base_tax_rate
                    else DEFAULT_TAX_RATE,
                    equipment_rating=float(ext.equipment_rating)
                    if ext and ext.equipment_rating
                    else None,
                    staff_rating=float(ext.staff_rating) if ext and ext.staff_rating else None,
                    checkin_rating=float(ext.checkin_rating)
                    if ext and ext.checkin_rating
                    else None,
                    is_wizard_enabled=ext.is_wizard_enabled if ext else False,
                    is_couples_allowed=ext.is_couples_allowed if ext else False,
                    game_types=view.game_types,
                    distance_meters=distance,
                )
            )

        if user_id and (q or city):
            await self.repo.record_search(
                user_id, query=q, city=city, filters={"min_rating": min_rating, "open_now": open_now}
            )
            await self.session.commit()

        return ParlourSearchResult(
            items=items,
            total=total,
            page=page,
            limit=limit,
            has_more=(offset + len(items)) < total,
        )