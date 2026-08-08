"""Virtual slot generation + materialization into gaming_slots.

Fixes empty parlor detail ("No slots for this date") by ensuring hourly
slots exist for the requested date (default open hours + capacity).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gaming_booking.models import GamingSlot
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension

IST = ZoneInfo("Asia/Kolkata")

# Defaults when parlor has no stations/hours configured
DEFAULT_OPEN = time(10, 0)
DEFAULT_CLOSE = time(23, 0)
DEFAULT_PRICE = Decimal("99.00")
DEFAULT_CAPACITY = 4
LEAD_MINUTES = 30


def _hourly_starts(open_t: time, close_t: time) -> list[time]:
    starts: list[time] = []
    cursor = datetime.combine(date.today(), open_t)
    end = datetime.combine(date.today(), close_t)
    while cursor + timedelta(hours=1) <= end:
        starts.append(cursor.time().replace(second=0, microsecond=0))
        cursor += timedelta(hours=1)
    return starts


def _default_price_for_place(place: GamingPlace, ext: GamingPlaceExtension | None) -> Decimal:
    # Prefer extension hourly if present
    if ext is not None:
        for attr in ("hourly_price", "price_per_hour", "starting_price", "min_price"):
            val = getattr(ext, attr, None)
            if val is not None:
                try:
                    d = Decimal(str(val))
                    if d > 0:
                        return d.quantize(Decimal("0.01"))
                except Exception:  # noqa: BLE001
                    pass
    return DEFAULT_PRICE


def _default_capacity(ext: GamingPlaceExtension | None) -> int:
    if ext is not None:
        for attr in ("pc_count", "total_stations", "capacity", "max_players"):
            val = getattr(ext, attr, None)
            if isinstance(val, int) and val > 0:
                return min(val, 32)
    return DEFAULT_CAPACITY


class SlotEngine:
    """Ensure bookable gaming_slots rows exist for a parlor+date."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_slots_for_date(
        self,
        parlour_id: UUID,
        slot_date: date,
        *,
        open_time: time = DEFAULT_OPEN,
        close_time: time = DEFAULT_CLOSE,
    ) -> list[GamingSlot]:
        place = (
            await self.session.execute(
                select(GamingPlace).where(GamingPlace.id == parlour_id)
            )
        ).scalar_one_or_none()
        if place is None:
            return []

        existing = (
            await self.session.execute(
                select(GamingSlot)
                .where(
                    GamingSlot.parlour_id == parlour_id,
                    GamingSlot.slot_date == slot_date,
                )
                .order_by(GamingSlot.start_time.asc())
            )
        ).scalars().all()
        if existing:
            return list(existing)

        ext = (
            await self.session.execute(
                select(GamingPlaceExtension).where(
                    GamingPlaceExtension.gaming_place_id == parlour_id
                )
            )
        ).scalar_one_or_none()

        price = _default_price_for_place(place, ext)
        capacity = _default_capacity(ext)
        now_ist = datetime.now(IST)
        created: list[GamingSlot] = []

        for start_t in _hourly_starts(open_time, close_time):
            end_dt = datetime.combine(slot_date, start_t) + timedelta(hours=1)
            end_t = end_dt.time()
            # Skip past slots for today (IST lead time)
            if slot_date == now_ist.date():
                slot_start_ist = datetime.combine(slot_date, start_t, tzinfo=IST)
                if slot_start_ist < now_ist + timedelta(minutes=LEAD_MINUTES):
                    continue

            slot = GamingSlot(
                parlour_id=parlour_id,
                slot_date=slot_date,
                start_time=start_t,
                end_time=end_t,
                price_per_hour=price,
                original_price=price,
                max_players=capacity,
                current_bookings=0,
                is_available=True,
            )
            self.session.add(slot)
            created.append(slot)

        if created:
            await self.session.commit()
            for s in created:
                await self.session.refresh(s)
        return created

    async def ensure_range(
        self,
        parlour_id: UUID,
        *,
        days: int = 14,
    ) -> int:
        """Pre-generate slots for next N days (boot/seed)."""
        today = datetime.now(IST).date()
        total = 0
        for i in range(days):
            d = today + timedelta(days=i)
            slots = await self.ensure_slots_for_date(parlour_id, d)
            total += len(slots)
        return total
