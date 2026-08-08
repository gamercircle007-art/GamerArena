"""Availability computation + booking create with holds (spec Phase 2)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.club_ops.pricing import PriceResolver, resource_type_for
from app.domains.club_ops.promotions import PromotionService
from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.gaming_booking.booking_ref import generate_booking_ref
from app.domains.gaming_booking.inventory_models import (
    BookingAudit,
    BookingHold,
    ParlorClosure,
    ParlorHours,
    ParlorStation,
    PaymentLedger,
)
from app.domains.gaming_booking.models import GamingBooking, GamingSlot
from app.domains.gaming_booking.slot_engine import (
    DEFAULT_CAPACITY,
    DEFAULT_CLOSE,
    DEFAULT_OPEN,
    DEFAULT_PRICE,
    SlotEngine,
    _hourly_starts,
)
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension

IST = ZoneInfo("Asia/Kolkata")
HOLD_MINUTES = 7
LEAD_MINUTES = 30
COMMISSION_BPS = 1000  # 10%


def _overlap_hours(
    b_start: time, b_duration: int, s_start: time
) -> bool:
    """True if booking [b_start, b_start+duration) covers hourly slot s_start."""
    b0 = datetime.combine(date.today(), b_start)
    b1 = b0 + timedelta(hours=b_duration)
    s0 = datetime.combine(date.today(), s_start)
    s1 = s0 + timedelta(hours=1)
    return b0 < s1 and s0 < b1


class AvailabilityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _stations(self, parlor_id: UUID, station_type: str | None = None) -> list[ParlorStation]:
        q = select(ParlorStation).where(
            ParlorStation.parlor_id == parlor_id,
            ParlorStation.is_active.is_(True),
        )
        if station_type:
            q = q.where(ParlorStation.station_type == station_type)
        rows = (await self.session.execute(q)).scalars().all()
        if rows:
            return list(rows)
        # Default synthetic station if none configured
        ext = (
            await self.session.execute(
                select(GamingPlaceExtension).where(
                    GamingPlaceExtension.gaming_place_id == parlor_id
                )
            )
        ).scalar_one_or_none()
        price = DEFAULT_PRICE
        if ext and ext.price_per_hour:
            price = Decimal(str(ext.price_per_hour))
        price_paise = int(price * 100)
        st = station_type or "PC"
        return [
            ParlorStation(
                id=uuid.uuid4(),
                parlor_id=parlor_id,
                station_type=st,
                total_count=DEFAULT_CAPACITY,
                hourly_price_paise=price_paise,
                is_active=True,
            )
        ]

    async def _hours_for(self, parlor_id: UUID, d: date) -> list[tuple[time, time]]:
        weekday = d.weekday()  # Mon=0
        rows = (
            await self.session.execute(
                select(ParlorHours).where(
                    ParlorHours.parlor_id == parlor_id,
                    ParlorHours.weekday == weekday,
                )
            )
        ).scalars().all()
        if rows:
            return [(r.open_time, r.close_time) for r in rows]
        return [(DEFAULT_OPEN, DEFAULT_CLOSE)]

    async def _is_closed(self, parlor_id: UUID, d: date) -> bool:
        row = (
            await self.session.execute(
                select(ParlorClosure).where(
                    ParlorClosure.parlor_id == parlor_id,
                    ParlorClosure.date == d,
                )
            )
        ).scalar_one_or_none()
        return row is not None

    async def compute_availability(
        self,
        parlor_id: UUID,
        d: date,
        station_type: str = "PC",
    ) -> list[dict]:
        place = (
            await self.session.execute(select(GamingPlace).where(GamingPlace.id == parlor_id))
        ).scalar_one_or_none()
        if place is None:
            raise NotFoundError("Parlor not found")
        if await self._is_closed(parlor_id, d):
            return []

        stations = await self._stations(parlor_id, station_type)
        if not stations:
            return []
        station = stations[0]
        total = station.total_count

        shifts = await self._hours_for(parlor_id, d)
        now_ist = datetime.now(IST)
        candidates: list[time] = []
        for open_t, close_t in shifts:
            for st in _hourly_starts(open_t, close_t):
                if d == now_ist.date():
                    start_ist = datetime.combine(d, st, tzinfo=IST)
                    if start_ist < now_ist + timedelta(minutes=LEAD_MINUTES):
                        continue
                candidates.append(st)

        # Confirmed / pending bookings + active holds
        bookings = (
            await self.session.execute(
                select(GamingBooking).where(
                    GamingBooking.parlour_id == parlor_id,
                    GamingBooking.slot_date == d,
                    or_(
                        GamingBooking.station_type == station_type,
                        GamingBooking.station_type.is_(None),
                    ),
                    GamingBooking.booking_status.in_(
                        ("confirmed", "payment_pending", "initiated")
                    ),
                )
            )
        ).scalars().all()

        holds = (
            await self.session.execute(
                select(BookingHold).where(
                    BookingHold.parlor_id == parlor_id,
                    BookingHold.date == d,
                    BookingHold.station_type == station_type,
                    BookingHold.released.is_(False),
                    BookingHold.expires_at > datetime.now(UTC),
                )
            )
        ).scalars().all()

        # Price each hour through the club-ops resolver so the slot list, the pricing
        # preview and the actual charge all come from one place. With no pricing rules
        # configured the resolver falls back to this station's hourly_price_paise, i.e.
        # identical output to the previous flat calculation.
        resolver = PriceResolver(self.session)
        resource_type = resource_type_for(station_type)

        result = []
        for st in candidates:
            used = 0
            for b in bookings:
                b_start = b.start_time
                b_dur = b.duration_hours or 1
                b_units = b.units or b.num_players or 1
                if b_start and _overlap_hours(b_start, int(b_dur), st):
                    used += int(b_units)
            for h in holds:
                if _overlap_hours(h.start_time, h.duration_hours, st):
                    used += h.units
            available = max(0, total - used)

            hour_price = await resolver.resolve(
                parlor_id=parlor_id,
                resource_type=resource_type,
                booking_date=d,
                start_time=st,
                duration_hours=1,
                units=1,
            )
            result.append(
                {
                    "start_time": st.strftime("%H:%M:%S"),
                    "available_units": available,
                    "price_paise": hour_price.subtotal_paise,
                    "price_per_hour": str(Decimal(hour_price.subtotal_paise) / 100),
                    "price_source": hour_price.source,
                    "slab_label": hour_price.per_hour[0].slab_label
                    if hour_price.per_hour
                    else None,
                    "disabled": available <= 0,
                    "station_type": station_type,
                }
            )
        return result

    async def list_station_types(self, parlor_id: UUID) -> list[dict]:
        rows = await self._stations(parlor_id)
        # Deduplicate by type
        seen: dict[str, ParlorStation] = {}
        for r in rows:
            seen[r.station_type] = r
        return [
            {
                "station_type": s.station_type,
                "total_count": s.total_count,
                "hourly_price_paise": s.hourly_price_paise,
                "price_per_hour": str(Decimal(s.hourly_price_paise) / 100),
            }
            for s in seen.values()
        ]

    async def create_booking_v2(
        self,
        *,
        user_id: UUID,
        parlor_id: UUID,
        station_type: str,
        slot_date: date,
        start_time: time,
        duration_hours: int,
        units: int,
        idempotency_key: str,
        contact_phone: str | None = None,
        guest_name: str | None = None,
        payment_mode: str = "online",
        promo_code: str | None = None,
    ) -> GamingBooking:
        if duration_hours < 1 or duration_hours > 3:
            raise ValidationError("duration_hours must be 1–3")
        if units < 1 or units > 4:
            raise ValidationError("units must be 1–4")

        # Idempotency
        existing = (
            await self.session.execute(
                select(GamingBooking).where(GamingBooking.idempotency_key == idempotency_key)
            )
        ).scalar_one_or_none()
        if existing:
            return existing

        place = (
            await self.session.execute(select(GamingPlace).where(GamingPlace.id == parlor_id))
        ).scalar_one_or_none()
        if place is None:
            raise NotFoundError("Parlor not found")
        if await self._is_closed(parlor_id, slot_date):
            raise ValidationError("Parlor closed on this date")

        # Lock station row if real; else proceed with defaults
        station_row = (
            await self.session.execute(
                select(ParlorStation)
                .where(
                    ParlorStation.parlor_id == parlor_id,
                    ParlorStation.station_type == station_type,
                    ParlorStation.is_active.is_(True),
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

        avail = await self.compute_availability(parlor_id, slot_date, station_type)
        by_start = {a["start_time"]: a for a in avail}
        for h in range(duration_hours):
            t = (datetime.combine(slot_date, start_time) + timedelta(hours=h)).time()
            key = t.strftime("%H:%M:%S")
            # also try without seconds mismatch
            slot_info = by_start.get(key) or by_start.get(t.strftime("%H:%M") + ":00")
            if not slot_info or slot_info["available_units"] < units:
                raise ValidationError(
                    f"Not enough capacity at {key}",
                )

        stations = await self._stations(parlor_id, station_type)

        # One price authority for both booking paths (see club_ops.pricing). Falls back
        # to stations[0].hourly_price_paise when the club has no pricing rules, so this
        # is behaviour-preserving for clubs that have not configured Club Management.
        resource_type = resource_type_for(station_type)
        breakdown = await PriceResolver(self.session).resolve(
            parlor_id=parlor_id,
            resource_type=resource_type,
            booking_date=slot_date,
            start_time=start_time,
            duration_hours=duration_hours,
            units=units,
        )
        subtotal_paise = breakdown.subtotal_paise

        # Resolve the club's customer record first: first_visit and loyalty promos are
        # evaluated against visit_count / loyalty_points, so this must exist before
        # promotions are considered.
        from app.domains.club_ops.service import CustomerService

        club_customer = await CustomerService(self.session).ensure_for_user(parlor_id, user_id)
        if club_customer.is_banned:
            raise ValidationError("You are not permitted to book at this club")

        # Club promotions apply to customer-app bookings too — that is the point of a
        # happy-hour or first-visit promo. An explicit code is validated strictly;
        # automatic promos are best-value.
        promo_outcome = await PromotionService(self.session).apply_best(
            parlor_id=parlor_id,
            subtotal_paise=subtotal_paise,
            resource_type=resource_type,
            booking_date=slot_date,
            start_time=start_time,
            code=promo_code,
            club_customer_id=club_customer.id,
        )
        if promo_code and not promo_outcome.valid:
            raise ValidationError(promo_outcome.reason or "Promotion is not valid")

        club_discount = promo_outcome.discount_paise if promo_outcome.valid else 0
        price_paise = max(0, subtotal_paise - club_discount)
        commission = (price_paise * COMMISSION_BPS) // 10000
        amount = Decimal(price_paise) / Decimal(100)
        end_time = (datetime.combine(slot_date, start_time) + timedelta(hours=duration_hours)).time()

        # Materialize a gaming_slot for legacy UI compatibility
        engine = SlotEngine(self.session)
        await engine.ensure_slots_for_date(parlor_id, slot_date)
        slot = (
            await self.session.execute(
                select(GamingSlot)
                .where(
                    GamingSlot.parlour_id == parlor_id,
                    GamingSlot.slot_date == slot_date,
                    GamingSlot.start_time == start_time,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

        if slot is None:
            slot = GamingSlot(
                parlour_id=parlor_id,
                slot_date=slot_date,
                start_time=start_time,
                end_time=end_time,
                price_per_hour=Decimal(stations[0].hourly_price_paise) / 100,
                max_players=stations[0].total_count,
                current_bookings=0,
                is_available=True,
            )
            self.session.add(slot)
            await self.session.flush()

        remaining = slot.max_players - slot.current_bookings
        if remaining < units:
            raise ValidationError("Not enough capacity in this slot")

        booking_ref = await generate_booking_ref(self.session)
        expires = datetime.now(UTC) + timedelta(minutes=HOLD_MINUTES)
        free_cancel = datetime.combine(slot_date, start_time, tzinfo=IST).astimezone(UTC) - timedelta(
            hours=2
        )

        booking = GamingBooking(
            booking_ref=booking_ref,
            user_id=user_id,
            parlour_id=parlor_id,
            slot_id=slot.id,
            guest_name=guest_name,
            num_players=units,
            slot_date=slot_date,
            start_time=start_time,
            end_time=end_time,
            hours_booked=Decimal(duration_hours),
            price_per_hour=Decimal(breakdown.base_rate_paise) / 100,
            total_price=Decimal(subtotal_paise) / Decimal(100),
            tax_amount=Decimal("0"),
            discount_amount=Decimal("0"),
            final_price=amount,
            payment_mode=payment_mode,
            payment_status="pending",
            booking_status="payment_pending" if payment_mode == "online" else "confirmed",
            free_cancellation_before=free_cancel,
            is_non_refundable=False,
            contact_phone=contact_phone,
            station_type=station_type,
            duration_hours=duration_hours,
            units=units,
            amount_paise=price_paise,
            commission_paise=commission,
            idempotency_key=idempotency_key,
            hold_expires_at=expires if payment_mode == "online" else None,
            club_promotion_id=promo_outcome.promotion_id if promo_outcome.valid else None,
            club_discount_paise=club_discount,
            # Owner-side CRM covers app bookings, not just walk-ins.
            club_customer_id=club_customer.id,
            updated_at=datetime.now(UTC),
        )
        self.session.add(booking)
        await self.session.flush()

        if promo_outcome.valid and promo_outcome.promotion_id is not None:
            promo_row = await PromotionService(self.session).get_scoped(
                parlor_id, promo_outcome.promotion_id
            )
            await PromotionService(self.session).consume(promo_row)

        slot.current_bookings += units
        if slot.current_bookings >= slot.max_players:
            slot.is_available = False

        if payment_mode == "online":
            self.session.add(
                BookingHold(
                    booking_id=booking.id,
                    parlor_id=parlor_id,
                    station_type=station_type,
                    date=slot_date,
                    start_time=start_time,
                    duration_hours=duration_hours,
                    units=units,
                    expires_at=expires,
                    released=False,
                )
            )

        self.session.add(
            BookingAudit(
                booking_id=booking.id,
                from_status=None,
                to_status=booking.booking_status,
                actor="user",
                actor_id=user_id,
                reason="create_booking_v2",
            )
        )
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def expire_hold(self, booking_id: UUID) -> None:
        booking = (
            await self.session.execute(
                select(GamingBooking).where(GamingBooking.id == booking_id).with_for_update()
            )
        ).scalar_one_or_none()
        if booking is None:
            return
        if booking.booking_status not in ("payment_pending", "initiated"):
            return
        old = booking.booking_status
        booking.booking_status = "expired"
        booking.updated_at = datetime.now(UTC)
        hold = (
            await self.session.execute(
                select(BookingHold).where(BookingHold.booking_id == booking_id).with_for_update()
            )
        ).scalar_one_or_none()
        if hold and not hold.released:
            hold.released = True
            if booking.slot_id:
                slot = (
                    await self.session.execute(
                        select(GamingSlot).where(GamingSlot.id == booking.slot_id).with_for_update()
                    )
                ).scalar_one_or_none()
                if slot:
                    slot.current_bookings = max(0, slot.current_bookings - (booking.units or 1))
                    slot.is_available = True
        self.session.add(
            BookingAudit(
                booking_id=booking.id,
                from_status=old,
                to_status="expired",
                actor="system",
                reason="hold_expired",
            )
        )
        await self.session.commit()

    async def confirm_payment(
        self,
        booking_id: UUID,
        *,
        cf_reference: str | None,
        event_id: str | None,
        actor: str = "webhook",
    ) -> GamingBooking:
        booking = (
            await self.session.execute(
                select(GamingBooking).where(GamingBooking.id == booking_id).with_for_update()
            )
        ).scalar_one_or_none()
        if booking is None:
            raise NotFoundError("Booking not found")
        if booking.booking_status == "confirmed" and booking.payment_status == "paid":
            return booking
        if booking.booking_status == "expired":
            # late pay → mark refund_pending (caller may refund)
            booking.booking_status = "refund_pending"
            booking.payment_status = "paid"
            booking.updated_at = datetime.now(UTC)
            await self.session.commit()
            await self.session.refresh(booking)
            return booking

        old = booking.booking_status
        booking.booking_status = "confirmed"
        booking.payment_status = "paid"
        booking.payment_id = cf_reference
        booking.updated_at = datetime.now(UTC)
        hold = (
            await self.session.execute(
                select(BookingHold).where(BookingHold.booking_id == booking_id)
            )
        ).scalar_one_or_none()
        if hold:
            hold.released = True

        amount = booking.amount_paise or int((booking.final_price or 0) * 100)
        self.session.add(
            PaymentLedger(
                booking_id=booking.id,
                entry_type="payment",
                amount_paise=amount,
                cf_reference=cf_reference,
                cf_event_id=event_id,
                balance_direction="credit",
            )
        )
        if booking.commission_paise:
            self.session.add(
                PaymentLedger(
                    booking_id=booking.id,
                    entry_type="commission",
                    amount_paise=booking.commission_paise,
                    cf_reference=cf_reference,
                    balance_direction="debit",
                )
            )
        self.session.add(
            BookingAudit(
                booking_id=booking.id,
                from_status=old,
                to_status="confirmed",
                actor=actor,
                reason="payment_success",
            )
        )
        await self.session.commit()
        await self.session.refresh(booking)
        return booking
