"""Club revenue + occupancy analytics.

Two different read strategies, deliberately:

- **Revenue** aggregates `gaming_bookings` live. It is a small, indexed, date-bounded
  scan (`ix_gaming_bookings_owner_calendar`) and owners expect today's money to be
  accurate to the second, so a rollup lag would be a bug rather than an optimisation.
  Net revenue subtracts `commission_paise` — discovery found `AdminService.analytics()`
  reports gross only, so this does not reuse that query.

- **Occupancy** reads `club_occupancy_rollups` exclusively and never scans bookings.
  Heatmaps and utilisation rankings span weeks or months; that is what Phase 2.5's
  Celery job precomputes. If a bucket is missing, the answer is "run the rollup",
  not "fall back to a live scan" — a silent fallback would hide a broken job.

Everything is Asia/Kolkata: day boundaries, weekday indexing and hour buckets.
"""

from __future__ import annotations

from datetime import date as date_cls, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.club_ops.enums import (
    BOOKING_STATUS_NO_SHOW,
    COMPLETED_STATUSES,
    RollupGrain,
)
from app.domains.club_ops.models import ClubResource, ClubZone, OccupancyRollup
from app.domains.common.exceptions import ValidationError
from app.domains.gaming_booking.models import GamingBooking

IST = ZoneInfo("Asia/Kolkata")

BPS_ONE = 10000

#: Ranges the owner revenue screen offers.
RANGES = ("today", "week", "month")


def resolve_range(range_key: str) -> tuple[date_cls, date_cls]:
    """Translate a range key into inclusive IST date bounds."""
    today = datetime.now(IST).date()
    if range_key == "today":
        return today, today
    if range_key == "week":
        return today - timedelta(days=today.weekday()), today
    if range_key == "month":
        return today.replace(day=1), today
    raise ValidationError(f"range must be one of {', '.join(RANGES)}")


def _rupees(paise: int) -> str:
    return f"{Decimal(paise) / 100:.2f}"


def _utilization_bps(occupied: int, capacity: int) -> int:
    if capacity <= 0:
        return 0
    return min(BPS_ONE, (occupied * BPS_ONE) // capacity)


class RevenueService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def summary(
        self, parlor_id: UUID, *, range_key: str = "today"
    ) -> dict:
        from_date, to_date = resolve_range(range_key)

        rows = (
            await self.session.execute(
                select(GamingBooking).where(
                    GamingBooking.parlour_id == parlor_id,
                    GamingBooking.slot_date >= from_date,
                    GamingBooking.slot_date <= to_date,
                )
            )
        ).scalars().all()

        gross = commission = discount = 0
        booking_count = completed = cancelled = no_show = 0
        by_type: dict[str, dict] = {}
        by_method: dict[str, dict] = {}
        by_day: dict[str, dict] = {}

        for booking in rows:
            booking_count += 1
            status = booking.booking_status
            if status == "cancelled":
                cancelled += 1
                continue
            if status == BOOKING_STATUS_NO_SHOW:
                no_show += 1
                continue
            if status not in COMPLETED_STATUSES:
                # payment_pending / initiated / expired sessions are not revenue yet.
                continue

            amount = int(booking.amount_paise or 0)
            if amount == 0 and booking.final_price is not None:
                # Legacy rows predate amount_paise; fall back to the Numeric column.
                amount = int(Decimal(str(booking.final_price)) * 100)
            comm = int(booking.commission_paise or 0)

            completed += 1
            gross += amount
            commission += comm
            discount += int(booking.club_discount_paise or 0)

            type_key = (booking.station_type or "UNKNOWN").upper()
            bucket = by_type.setdefault(
                type_key, {"resource_type": type_key, "gross_paise": 0, "booking_count": 0}
            )
            bucket["gross_paise"] += amount
            bucket["booking_count"] += 1

            method_key = booking.payment_mode or "unknown"
            method = by_method.setdefault(
                method_key, {"payment_method": method_key, "gross_paise": 0, "booking_count": 0}
            )
            method["gross_paise"] += amount
            method["booking_count"] += 1

            day_key = booking.slot_date.isoformat() if booking.slot_date else "unknown"
            day = by_day.setdefault(
                day_key,
                {"date": day_key, "gross_paise": 0, "net_paise": 0, "booking_count": 0},
            )
            day["gross_paise"] += amount
            day["net_paise"] += amount - comm
            day["booking_count"] += 1

        net = gross - commission
        avg = (gross // completed) if completed else 0

        return {
            "range": range_key,
            "from_date": from_date,
            "to_date": to_date,
            "gross_paise": gross,
            "gross_rupees": _rupees(gross),
            "commission_paise": commission,
            "net_paise": net,
            "net_rupees": _rupees(net),
            "discount_paise": discount,
            "booking_count": booking_count,
            "completed_count": completed,
            "cancelled_count": cancelled,
            "no_show_count": no_show,
            "avg_session_paise": avg,
            "by_resource_type": sorted(
                by_type.values(), key=lambda r: r["gross_paise"], reverse=True
            ),
            "by_payment_method": sorted(
                by_method.values(), key=lambda r: r["gross_paise"], reverse=True
            ),
            "daily": sorted(by_day.values(), key=lambda r: r["date"]),
        }


class OccupancyService:
    """Reads precomputed rollups only. See module docstring for why."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _bounds(from_date: date_cls, to_date: date_cls) -> tuple[datetime, datetime]:
        if to_date < from_date:
            raise ValidationError("to_date must not be before from_date")
        start = datetime.combine(from_date, time.min, tzinfo=IST)
        end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=IST)
        return start, end

    async def timeseries(
        self,
        parlor_id: UUID,
        *,
        from_date: date_cls,
        to_date: date_cls,
        grain: str = RollupGrain.CLUB.value,
        grain_key: str = "",
    ) -> list[dict]:
        start, end = self._bounds(from_date, to_date)
        rows = (
            await self.session.execute(
                select(OccupancyRollup)
                .where(
                    OccupancyRollup.parlor_id == parlor_id,
                    OccupancyRollup.grain == grain,
                    OccupancyRollup.grain_key == grain_key,
                    OccupancyRollup.bucket_start >= start,
                    OccupancyRollup.bucket_start < end,
                )
                .order_by(OccupancyRollup.bucket_start.asc())
            )
        ).scalars().all()
        return [
            {
                "bucket_start": r.bucket_start,
                "occupied_minutes": r.occupied_minutes,
                "capacity_minutes": r.capacity_minutes,
                "utilization_bps": _utilization_bps(r.occupied_minutes, r.capacity_minutes),
                "booking_count": r.booking_count,
                "revenue_paise": r.revenue_paise,
            }
            for r in rows
        ]

    async def heatmap(
        self, parlor_id: UUID, *, from_date: date_cls, to_date: date_cls
    ) -> list[dict]:
        """Hour-of-day x day-of-week utilisation, summed over the range (IST)."""
        start, end = self._bounds(from_date, to_date)
        rows = (
            await self.session.execute(
                select(
                    OccupancyRollup.ist_weekday,
                    OccupancyRollup.ist_hour,
                    func.sum(OccupancyRollup.occupied_minutes),
                    func.sum(OccupancyRollup.capacity_minutes),
                    func.sum(OccupancyRollup.booking_count),
                )
                .where(
                    OccupancyRollup.parlor_id == parlor_id,
                    OccupancyRollup.grain == RollupGrain.CLUB.value,
                    OccupancyRollup.bucket_start >= start,
                    OccupancyRollup.bucket_start < end,
                )
                .group_by(OccupancyRollup.ist_weekday, OccupancyRollup.ist_hour)
                .order_by(OccupancyRollup.ist_weekday.asc(), OccupancyRollup.ist_hour.asc())
            )
        ).all()
        return [
            {
                "weekday": int(weekday),
                "hour": int(hour),
                "occupied_minutes": int(occupied or 0),
                "capacity_minutes": int(capacity or 0),
                "utilization_bps": _utilization_bps(int(occupied or 0), int(capacity or 0)),
                "booking_count": int(bookings or 0),
            }
            for weekday, hour, occupied, capacity, bookings in rows
        ]

    async def utilization(
        self,
        parlor_id: UUID,
        *,
        from_date: date_cls,
        to_date: date_cls,
        grain: str = RollupGrain.RESOURCE.value,
    ) -> list[dict]:
        """Per-resource (or per-zone / per-type) ranking, best utilised first."""
        if grain not in (
            RollupGrain.RESOURCE.value,
            RollupGrain.ZONE.value,
            RollupGrain.RESOURCE_TYPE.value,
        ):
            raise ValidationError("grain must be resource, zone or resource_type")

        start, end = self._bounds(from_date, to_date)
        rows = (
            await self.session.execute(
                select(
                    OccupancyRollup.grain_key,
                    func.sum(OccupancyRollup.occupied_minutes),
                    func.sum(OccupancyRollup.capacity_minutes),
                    func.sum(OccupancyRollup.booking_count),
                    func.sum(OccupancyRollup.revenue_paise),
                )
                .where(
                    OccupancyRollup.parlor_id == parlor_id,
                    OccupancyRollup.grain == grain,
                    OccupancyRollup.bucket_start >= start,
                    OccupancyRollup.bucket_start < end,
                )
                .group_by(OccupancyRollup.grain_key)
            )
        ).all()

        labels = await self._labels_for(parlor_id, grain)
        result = [
            {
                "grain": grain,
                "grain_key": key,
                "label": labels.get(key, key),
                "occupied_minutes": int(occupied or 0),
                "capacity_minutes": int(capacity or 0),
                "utilization_bps": _utilization_bps(int(occupied or 0), int(capacity or 0)),
                "booking_count": int(bookings or 0),
                "revenue_paise": int(revenue or 0),
            }
            for key, occupied, capacity, bookings, revenue in rows
        ]
        result.sort(key=lambda r: r["utilization_bps"], reverse=True)
        return result

    async def no_show_rate(
        self, parlor_id: UUID, *, from_date: date_cls, to_date: date_cls
    ) -> dict:
        """No-show rate from rollups, with a per-resource-type split."""
        start, end = self._bounds(from_date, to_date)
        club_row = (
            await self.session.execute(
                select(
                    func.sum(OccupancyRollup.booking_count),
                    func.sum(OccupancyRollup.no_show_count),
                ).where(
                    OccupancyRollup.parlor_id == parlor_id,
                    OccupancyRollup.grain == RollupGrain.CLUB.value,
                    OccupancyRollup.bucket_start >= start,
                    OccupancyRollup.bucket_start < end,
                )
            )
        ).one()
        bookings = int(club_row[0] or 0)
        no_shows = int(club_row[1] or 0)

        type_rows = (
            await self.session.execute(
                select(
                    OccupancyRollup.grain_key,
                    func.sum(OccupancyRollup.booking_count),
                    func.sum(OccupancyRollup.no_show_count),
                )
                .where(
                    OccupancyRollup.parlor_id == parlor_id,
                    OccupancyRollup.grain == RollupGrain.RESOURCE_TYPE.value,
                    OccupancyRollup.bucket_start >= start,
                    OccupancyRollup.bucket_start < end,
                )
                .group_by(OccupancyRollup.grain_key)
            )
        ).all()

        return {
            "from_date": from_date,
            "to_date": to_date,
            "booking_count": bookings,
            "no_show_count": no_shows,
            "no_show_rate_bps": (no_shows * BPS_ONE // bookings) if bookings else 0,
            "by_resource_type": [
                {
                    "resource_type": key,
                    "booking_count": int(count or 0),
                    "no_show_count": int(misses or 0),
                    "no_show_rate_bps": (int(misses or 0) * BPS_ONE // int(count))
                    if count
                    else 0,
                }
                for key, count, misses in type_rows
            ],
        }

    async def _labels_for(self, parlor_id: UUID, grain: str) -> dict[str, str]:
        """Human labels for grain keys, so the UI shows "PC-04" not a raw UUID."""
        if grain == RollupGrain.RESOURCE.value:
            rows = (
                await self.session.execute(
                    select(ClubResource.id, ClubResource.label).where(
                        ClubResource.parlor_id == parlor_id
                    )
                )
            ).all()
            return {str(rid): label for rid, label in rows}
        if grain == RollupGrain.ZONE.value:
            rows = (
                await self.session.execute(
                    select(ClubZone.id, ClubZone.name).where(ClubZone.parlor_id == parlor_id)
                )
            ).all()
            return {str(zid): name for zid, name in rows}
        return {}
