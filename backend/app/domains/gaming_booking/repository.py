"""Gaming booking data access layer."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gaming_booking.gc_points import GCPoints, GCPointsTransaction
from app.domains.gaming_booking.models import (
    CancellationReason,
    GamingBooking,
    GamingSlot,
    ParlourOffer,
    ParlourRating,
    UserSearchHistory,
)
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension


class GamingBookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Slots ---

    async def get_slot_by_id(self, slot_id: UUID) -> GamingSlot | None:
        result = await self.session.execute(
            select(GamingSlot).where(GamingSlot.id == slot_id)
        )
        return result.scalar_one_or_none()

    async def list_slots(
        self,
        parlour_id: UUID,
        *,
        slot_date: date | None = None,
        available_only: bool = True,
    ) -> list[GamingSlot]:
        query = select(GamingSlot).where(GamingSlot.parlour_id == parlour_id)
        if slot_date is not None:
            query = query.where(GamingSlot.slot_date == slot_date)
        if available_only:
            query = query.where(GamingSlot.is_available.is_(True))
        query = query.order_by(GamingSlot.slot_date.asc(), GamingSlot.start_time.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_slot(self, slot: GamingSlot) -> GamingSlot:
        self.session.add(slot)
        await self.session.flush()
        return slot

    # --- Offers ---

    async def get_offer_by_id(self, offer_id: UUID) -> ParlourOffer | None:
        result = await self.session.execute(
            select(ParlourOffer).where(ParlourOffer.id == offer_id)
        )
        return result.scalar_one_or_none()

    async def list_active_offers(self, parlour_id: UUID) -> list[ParlourOffer]:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(ParlourOffer)
            .where(
                ParlourOffer.parlour_id == parlour_id,
                ParlourOffer.is_active.is_(True),
            )
            .where(
                (ParlourOffer.valid_from.is_(None)) | (ParlourOffer.valid_from <= now)
            )
            .where(
                (ParlourOffer.valid_until.is_(None)) | (ParlourOffer.valid_until >= now)
            )
            .order_by(ParlourOffer.discount_percent.desc())
        )
        return list(result.scalars().all())

    async def create_offer(self, offer: ParlourOffer) -> ParlourOffer:
        self.session.add(offer)
        await self.session.flush()
        return offer

    # --- Bookings ---

    async def get_booking_by_id(self, booking_id: UUID) -> GamingBooking | None:
        result = await self.session.execute(
            select(GamingBooking).where(GamingBooking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_booking_by_ref(self, booking_ref: str) -> GamingBooking | None:
        result = await self.session.execute(
            select(GamingBooking).where(GamingBooking.booking_ref == booking_ref)
        )
        return result.scalar_one_or_none()

    async def list_user_bookings(
        self,
        user_id: UUID,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GamingBooking], int]:
        query = select(GamingBooking).where(GamingBooking.user_id == user_id)
        count_query = select(func.count()).select_from(GamingBooking).where(
            GamingBooking.user_id == user_id
        )
        if status:
            query = query.where(GamingBooking.booking_status == status)
            count_query = count_query.where(GamingBooking.booking_status == status)

        total = int(await self.session.scalar(count_query) or 0)
        result = await self.session.execute(
            query.order_by(GamingBooking.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_all_bookings(
        self,
        *,
        parlour_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GamingBooking], int]:
        query = select(GamingBooking)
        count_query = select(func.count()).select_from(GamingBooking)
        if parlour_id:
            query = query.where(GamingBooking.parlour_id == parlour_id)
            count_query = count_query.where(GamingBooking.parlour_id == parlour_id)
        if status:
            query = query.where(GamingBooking.booking_status == status)
            count_query = count_query.where(GamingBooking.booking_status == status)

        total = int(await self.session.scalar(count_query) or 0)
        result = await self.session.execute(
            query.order_by(GamingBooking.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def create_booking(self, booking: GamingBooking) -> GamingBooking:
        self.session.add(booking)
        await self.session.flush()
        return booking

    # --- Cancellation reasons ---

    async def list_cancellation_reasons(self) -> list[CancellationReason]:
        result = await self.session.execute(
            select(CancellationReason)
            .where(CancellationReason.is_active.is_(True))
            .order_by(CancellationReason.sort_order.asc())
        )
        return list(result.scalars().all())

    async def get_cancellation_reason(self, reason_id: UUID) -> CancellationReason | None:
        result = await self.session.execute(
            select(CancellationReason).where(CancellationReason.id == reason_id)
        )
        return result.scalar_one_or_none()

    # --- Ratings ---

    async def list_ratings(
        self,
        parlour_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ParlourRating], dict[str, float | int | None]]:
        count = int(
            await self.session.scalar(
                select(func.count())
                .select_from(ParlourRating)
                .where(ParlourRating.gaming_place_id == parlour_id)
            )
            or 0
        )
        result = await self.session.execute(
            select(ParlourRating)
            .where(ParlourRating.gaming_place_id == parlour_id)
            .order_by(ParlourRating.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        ratings = list(result.scalars().all())

        agg = await self.session.execute(
            select(
                func.avg(ParlourRating.rating),
                func.avg(ParlourRating.equipment_rating),
                func.avg(ParlourRating.staff_rating),
                func.avg(ParlourRating.location_rating),
                func.avg(ParlourRating.cleanliness_rating),
                func.avg(ParlourRating.checkin_rating),
            ).where(ParlourRating.gaming_place_id == parlour_id)
        )
        row = agg.one()
        summary = {
            "average_rating": float(row[0]) if row[0] is not None else None,
            "total_reviews": count,
            "equipment_rating": float(row[1]) if row[1] is not None else None,
            "staff_rating": float(row[2]) if row[2] is not None else None,
            "location_rating": float(row[3]) if row[3] is not None else None,
            "cleanliness_rating": float(row[4]) if row[4] is not None else None,
            "checkin_rating": float(row[5]) if row[5] is not None else None,
        }
        return ratings, summary

    # --- Extension ---

    async def get_extension(self, parlour_id: UUID) -> GamingPlaceExtension | None:
        result = await self.session.execute(
            select(GamingPlaceExtension).where(
                GamingPlaceExtension.gaming_place_id == parlour_id
            )
        )
        return result.scalar_one_or_none()

    async def get_place(self, parlour_id: UUID) -> GamingPlace | None:
        result = await self.session.execute(
            select(GamingPlace).where(GamingPlace.id == parlour_id)
        )
        return result.scalar_one_or_none()

    # --- GC Points ---

    async def get_gc_points(self, user_id: UUID) -> GCPoints | None:
        result = await self.session.execute(
            select(GCPoints).where(GCPoints.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def ensure_gc_points(self, user_id: UUID) -> GCPoints:
        points = await self.get_gc_points(user_id)
        if points is not None:
            return points
        points = GCPoints(user_id=user_id, balance=0, lifetime_earned=0)
        self.session.add(points)
        await self.session.flush()
        return points

    async def add_gc_transaction(self, tx: GCPointsTransaction) -> GCPointsTransaction:
        self.session.add(tx)
        await self.session.flush()
        return tx

    async def list_gc_transactions(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GCPointsTransaction], int]:
        total = int(
            await self.session.scalar(
                select(func.count())
                .select_from(GCPointsTransaction)
                .where(GCPointsTransaction.user_id == user_id)
            )
            or 0
        )
        result = await self.session.execute(
            select(GCPointsTransaction)
            .where(GCPointsTransaction.user_id == user_id)
            .order_by(GCPointsTransaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    # --- Search history ---

    async def record_search(
        self,
        user_id: UUID,
        *,
        query: str | None,
        city: str | None,
        filters: dict | None,
    ) -> None:
        entry = UserSearchHistory(
            user_id=user_id,
            query=query,
            city=city,
            filters=filters,
        )
        self.session.add(entry)
        await self.session.flush()