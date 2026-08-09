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
HOLD_MINUTES = 8  # expires_at is authoritative; Redis PX is a hint only
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

        # Occupancy from active unit locks (single source — avoids hold+booking double-count).
        # Fallback to legacy bookings if lock table empty / pre-migration rows.
        from app.domains.gaming_booking.inventory_models import BookingUnitLock
        from app.domains.gaming_booking.lock_service import build_during

        day_start, _ = build_during(d, time(0, 0), 1)
        # End of civil day in IST
        day_end = day_start + timedelta(hours=24)

        locks = (
            await self.session.execute(
                select(BookingUnitLock).where(
                    BookingUnitLock.parlor_id == parlor_id,
                    BookingUnitLock.station_type == station_type,
                    BookingUnitLock.is_active.is_(True),
                    BookingUnitLock.during_start < day_end,
                    BookingUnitLock.during_end > day_start,
                )
            )
        ).scalars().all()

        # Legacy fallback when no locks exist yet for this parlor/day
        bookings: list[GamingBooking] = []
        if not locks:
            bookings = list(
                (
                    await self.session.execute(
                        select(GamingBooking).where(
                            GamingBooking.parlour_id == parlor_id,
                            GamingBooking.slot_date == d,
                            or_(
                                GamingBooking.station_type == station_type,
                                GamingBooking.station_type.is_(None),
                            ),
                            GamingBooking.booking_status.in_(
                                ("held", "confirmed", "payment_pending", "checked_in", "initiated")
                            ),
                        )
                    )
                ).scalars().all()
            )

        # Price each hour through the club-ops resolver so the slot list, the pricing
        # preview and the actual charge all come from one place. With no pricing rules
        # configured the resolver falls back to this station's hourly_price_paise, i.e.
        # identical output to the previous flat calculation.
        resolver = PriceResolver(self.session)
        resource_type = resource_type_for(station_type)

        result = []
        for st in candidates:
            used = 0
            slot_start, slot_end = build_during(d, st, 1)
            if locks:
                for lk in locks:
                    if lk.during_start < slot_end and slot_start < lk.during_end:
                        used += 1
            else:
                for b in bookings:
                    b_start = b.start_time
                    b_dur = b.duration_hours or 1
                    b_units = b.units or b.num_players or 1
                    if b_start and _overlap_hours(b_start, int(b_dur), st):
                        used += int(b_units)
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
        redis=None,
    ) -> GamingBooking:
        """Online/pay-at-parlor both acquire locks via LockService (EXCLUDE / no TOCTOU)."""
        if await self._is_closed(parlor_id, slot_date):
            raise ValidationError("Parlor closed on this date")

        from app.domains.gaming_booking.lock_service import LockService

        lock = LockService(self.session, redis)
        booking = await lock.acquire_hold(
            user_id=user_id,
            parlor_id=parlor_id,
            station_type=station_type,
            slot_date=slot_date,
            start_time=start_time,
            duration_hours=duration_hours,
            units=units,
            idempotency_key=idempotency_key,
            contact_phone=contact_phone,
            guest_name=guest_name,
            promo_code=promo_code,
        )
        if payment_mode != "online":
            from sqlalchemy import update

            await self.session.execute(
                update(GamingBooking)
                .where(
                    GamingBooking.id == booking.id,
                    GamingBooking.booking_status == "held",
                )
                .values(
                    booking_status="confirmed",
                    payment_mode="pay_at_parlor",
                    hold_expires_at=None,
                    updated_at=datetime.now(UTC),
                )
            )
            hold = (
                await self.session.execute(
                    select(BookingHold).where(BookingHold.booking_id == booking.id)
                )
            ).scalar_one_or_none()
            if hold:
                hold.released = True
            self.session.add(
                BookingAudit(
                    booking_id=booking.id,
                    from_status="held",
                    to_status="confirmed",
                    actor="user",
                    actor_id=user_id,
                    reason="pay_at_parlor",
                )
            )
            await self.session.commit()
            await self.session.refresh(booking)
        return booking

    async def expire_hold(self, booking_id: UUID) -> None:
        from app.domains.gaming_booking.lock_service import LockService

        rows = await LockService(self.session).expire_stale_holds()
        # Also force-expire this id if still live but past TTL (targeted)
        booking = (
            await self.session.execute(
                select(GamingBooking).where(GamingBooking.id == booking_id)
            )
        ).scalar_one_or_none()
        if booking and booking.booking_status in ("held", "payment_pending"):
            if booking.hold_expires_at and booking.hold_expires_at <= datetime.now(UTC):
                await LockService(self.session).expire_stale_holds()
            else:
                # Countdown task: treat as expired now
                booking.hold_expires_at = datetime.now(UTC)
                await self.session.commit()
                await LockService(self.session).expire_stale_holds()
        _ = rows

    async def confirm_payment(
        self,
        booking_id: UUID,
        *,
        cf_reference: str | None,
        event_id: str | None,
        actor: str = "webhook",
    ) -> GamingBooking:
        from app.domains.gaming_booking.lock_service import LockService

        return await LockService(self.session).confirm_payment(
            booking_id,
            cf_reference=cf_reference,
            event_id=event_id,
            actor=actor,
        )

