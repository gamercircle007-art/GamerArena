"""Occupancy rollup computation (Phase 2.5).

Turns raw `gaming_bookings` rows into hourly `club_occupancy_rollups` buckets at four
grains (club / resource_type / zone / resource) so the analytics endpoints never scan
bookings across a month.

**Idempotency** is the property that matters here: a bucket is *recomputed from source
and overwritten*, never incremented. Re-running any bucket — or the whole range twice —
converges on the same numbers, so a retried Celery task, an overlapping beat tick and a
manual backfill cannot double-count. That is enforced by `_upsert`, which selects on the
(parlor_id, bucket_start, grain, grain_key) unique key and assigns absolute values.

Buckets are IST hour boundaries (`bucket_start` is stored aware-UTC but always lands on
an IST hour), because the heatmap axes and the business day are Asia/Kolkata.
"""

from __future__ import annotations

from datetime import UTC, date as date_cls, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.club_ops.enums import (
    BOOKING_STATUS_NO_SHOW,
    COMPLETED_STATUSES,
    OCCUPYING_STATUSES,
    RollupGrain,
)
from app.domains.club_ops.models import ClubResource, OccupancyRollup
from app.domains.club_ops.pricing import resource_type_for
from app.domains.gaming_booking.inventory_models import ParlorStation
from app.domains.gaming_booking.models import GamingBooking
from app.domains.gaming_place.models import GamingPlaceExtension

IST = ZoneInfo("Asia/Kolkata")

BUCKET_MINUTES = 60


def ist_hour_floor(moment: datetime) -> datetime:
    """Floor a moment to its IST hour boundary, returned as an aware IST datetime."""
    local = moment.astimezone(IST)
    return local.replace(minute=0, second=0, microsecond=0)


class _Accumulator:
    """Mutable tally for one (grain, grain_key) within one bucket."""

    __slots__ = (
        "occupied_minutes",
        "capacity_minutes",
        "booking_count",
        "no_show_count",
        "revenue_paise",
        "commission_paise",
    )

    def __init__(self) -> None:
        self.occupied_minutes = 0
        self.capacity_minutes = 0
        self.booking_count = 0
        self.no_show_count = 0
        self.revenue_paise = 0
        self.commission_paise = 0


class RollupService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def rebuild_bucket(self, parlor_id: UUID, bucket_start: datetime) -> int:
        """Recompute one hourly bucket for one club. Returns rows written."""
        bucket = ist_hour_floor(bucket_start)
        bucket_end = bucket + timedelta(minutes=BUCKET_MINUTES)

        resources = (
            await self.session.execute(
                select(ClubResource).where(
                    ClubResource.parlor_id == parlor_id,
                    ClubResource.is_active.is_(True),
                )
            )
        ).scalars().all()
        resource_by_id = {r.id: r for r in resources}

        capacity_units, per_type_capacity = await self._capacity(parlor_id, resources)

        # A booking can only touch this bucket if it is on the bucket's IST date or the
        # day before (a late-night session that runs past midnight).
        bookings = (
            await self.session.execute(
                select(GamingBooking).where(
                    GamingBooking.parlour_id == parlor_id,
                    GamingBooking.slot_date.in_(
                        (bucket.date(), bucket.date() - timedelta(days=1))
                    ),
                )
            )
        ).scalars().all()

        tallies: dict[tuple[str, str], _Accumulator] = {}

        def tally(grain: str, key: str) -> _Accumulator:
            return tallies.setdefault((grain, key), _Accumulator())

        # Seed capacity so a fully idle hour still records its capacity (utilisation 0%
        # is a real, meaningful data point — an absent row would look like "no data").
        club_acc = tally(RollupGrain.CLUB.value, "")
        club_acc.capacity_minutes = capacity_units * BUCKET_MINUTES
        for rtype, units in per_type_capacity.items():
            tally(RollupGrain.RESOURCE_TYPE.value, rtype).capacity_minutes = (
                units * BUCKET_MINUTES
            )
        for resource in resources:
            tally(RollupGrain.RESOURCE.value, str(resource.id)).capacity_minutes = (
                BUCKET_MINUTES
            )
            if resource.zone_id is not None:
                zone_acc = tally(RollupGrain.ZONE.value, str(resource.zone_id))
                zone_acc.capacity_minutes += BUCKET_MINUTES

        for booking in bookings:
            overlap = self._overlap_minutes(booking, bucket, bucket_end)
            status = booking.booking_status
            is_no_show = status == BOOKING_STATUS_NO_SHOW
            counts_occupancy = status in OCCUPYING_STATUSES or status == "completed"

            # A no-show still "starts" in this bucket for rate purposes but occupies
            # nothing — the seat sat empty, which is the whole point of tracking it.
            starts_here = self._starts_in_bucket(booking, bucket, bucket_end)
            if overlap <= 0 and not starts_here:
                continue

            units = int(booking.units or booking.num_players or 1)
            occupied = overlap * units if counts_occupancy else 0

            revenue = 0
            commission = 0
            if starts_here and status in COMPLETED_STATUSES:
                revenue = int(booking.amount_paise or 0)
                if revenue == 0 and booking.final_price is not None:
                    revenue = int(Decimal(str(booking.final_price)) * 100)
                commission = int(booking.commission_paise or 0)

            targets: list[tuple[str, str]] = [(RollupGrain.CLUB.value, "")]

            resource = resource_by_id.get(booking.resource_id) if booking.resource_id else None
            rtype = (
                resource.resource_type
                if resource is not None
                else resource_type_for(booking.station_type)
            )
            targets.append((RollupGrain.RESOURCE_TYPE.value, rtype))
            if resource is not None:
                targets.append((RollupGrain.RESOURCE.value, str(resource.id)))
                if resource.zone_id is not None:
                    targets.append((RollupGrain.ZONE.value, str(resource.zone_id)))

            for grain, key in targets:
                acc = tally(grain, key)
                # A per-resource row tracks that one unit, so units don't multiply there.
                acc.occupied_minutes += overlap if grain == RollupGrain.RESOURCE.value else occupied
                if starts_here:
                    acc.booking_count += 1
                    if is_no_show:
                        acc.no_show_count += 1
                    acc.revenue_paise += revenue
                    acc.commission_paise += commission

        written = 0
        for (grain, key), acc in tallies.items():
            await self._upsert(parlor_id, bucket, grain, key, acc)
            written += 1
        await self.session.commit()
        return written

    async def rebuild_range(
        self,
        parlor_id: UUID,
        *,
        from_date: date_cls,
        to_date: date_cls,
    ) -> int:
        """Recompute every hourly bucket in an inclusive IST date range."""
        written = 0
        cursor = datetime.combine(from_date, time.min, tzinfo=IST)
        end = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=IST)
        while cursor < end:
            written += await self.rebuild_bucket(parlor_id, cursor)
            cursor += timedelta(minutes=BUCKET_MINUTES)
        return written

    async def rebuild_recent_for_all_clubs(self, *, hours: int = 3) -> int:
        """Hourly beat entry point: refresh the trailing window for every active club.

        A trailing window rather than only the last hour, because a session that was
        checked out late, extended, or marked no-show retroactively changes buckets that
        have already been computed once.
        """
        club_ids = (
            await self.session.execute(
                select(GamingPlaceExtension.gaming_place_id).where(
                    GamingPlaceExtension.is_deleted.is_(False)
                )
            )
        ).scalars().all()

        now = ist_hour_floor(datetime.now(UTC))
        written = 0
        for club_id in club_ids:
            for offset in range(hours):
                written += await self.rebuild_bucket(club_id, now - timedelta(hours=offset))
        return written

    # ---- internals -------------------------------------------------------------

    async def _capacity(
        self, parlor_id: UUID, resources: list[ClubResource]
    ) -> tuple[int, dict[str, int]]:
        """Bookable units for this club, by type and in total.

        Prefers typed `ClubResource` rows; falls back to `ParlorStation.total_count` for
        clubs that have not yet configured Club Management, so their rollups are still
        meaningful rather than showing 0% of 0 capacity.
        """
        if resources:
            per_type: dict[str, int] = {}
            for resource in resources:
                per_type[resource.resource_type] = per_type.get(resource.resource_type, 0) + 1
            return len(resources), per_type

        stations = (
            await self.session.execute(
                select(ParlorStation).where(
                    ParlorStation.parlor_id == parlor_id,
                    ParlorStation.is_active.is_(True),
                )
            )
        ).scalars().all()
        per_type = {}
        total = 0
        for station in stations:
            rtype = resource_type_for(station.station_type)
            per_type[rtype] = per_type.get(rtype, 0) + int(station.total_count or 0)
            total += int(station.total_count or 0)
        return total, per_type

    @staticmethod
    def _booking_span(booking: GamingBooking) -> tuple[datetime, datetime] | None:
        """The booking's occupied interval in IST, including any extension."""
        if booking.slot_date is None or booking.start_time is None:
            return None
        hours = int(booking.duration_hours or 1) + int(booking.extended_hours or 0)
        start = datetime.combine(booking.slot_date, booking.start_time, tzinfo=IST)

        # A checked-out session's real span is check-in -> check-out; that is what the
        # seat was actually busy for, and it is what utilisation should reflect.
        if booking.checked_in_at is not None and booking.checked_out_at is not None:
            checked_in = booking.checked_in_at
            checked_out = booking.checked_out_at
            if checked_in.tzinfo is None:
                checked_in = checked_in.replace(tzinfo=UTC)
            if checked_out.tzinfo is None:
                checked_out = checked_out.replace(tzinfo=UTC)
            if checked_out > checked_in:
                return checked_in.astimezone(IST), checked_out.astimezone(IST)

        return start, start + timedelta(hours=max(1, hours))

    def _overlap_minutes(
        self, booking: GamingBooking, bucket: datetime, bucket_end: datetime
    ) -> int:
        span = self._booking_span(booking)
        if span is None:
            return 0
        start, end = span
        overlap_start = max(start, bucket)
        overlap_end = min(end, bucket_end)
        if overlap_end <= overlap_start:
            return 0
        return int((overlap_end - overlap_start).total_seconds() // 60)

    def _starts_in_bucket(
        self, booking: GamingBooking, bucket: datetime, bucket_end: datetime
    ) -> bool:
        """Attribute a booking's count/revenue to exactly one bucket — the one it starts
        in — so summing buckets over a range gives the true booking count."""
        if booking.slot_date is None or booking.start_time is None:
            return False
        start = datetime.combine(booking.slot_date, booking.start_time, tzinfo=IST)
        return bucket <= start < bucket_end

    async def _upsert(
        self,
        parlor_id: UUID,
        bucket: datetime,
        grain: str,
        grain_key: str,
        acc: _Accumulator,
    ) -> None:
        """Write absolute values for this bucket — never increment.

        Assignment (not `+=`) is what makes the whole job idempotent.
        """
        bucket_utc = bucket.astimezone(UTC)
        existing = (
            await self.session.execute(
                select(OccupancyRollup).where(
                    OccupancyRollup.parlor_id == parlor_id,
                    OccupancyRollup.bucket_start == bucket_utc,
                    OccupancyRollup.grain == grain,
                    OccupancyRollup.grain_key == grain_key,
                )
            )
        ).scalar_one_or_none()

        if existing is None:
            existing = OccupancyRollup(
                parlor_id=parlor_id,
                bucket_start=bucket_utc,
                grain=grain,
                grain_key=grain_key,
            )
            self.session.add(existing)

        existing.ist_hour = bucket.hour
        existing.ist_weekday = bucket.weekday()
        existing.occupied_minutes = acc.occupied_minutes
        existing.capacity_minutes = acc.capacity_minutes
        existing.booking_count = acc.booking_count
        existing.no_show_count = acc.no_show_count
        existing.revenue_paise = acc.revenue_paise
        existing.commission_paise = acc.commission_paise
        existing.computed_at = datetime.now(UTC)
        await self.session.flush()
