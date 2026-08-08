"""Celery tasks: occupancy rollups for Club Management analytics (Phase 2.5).

Follows the same shape as `booking_tasks.py` — a sync Celery task wrapping an
`asyncio.run(_run())` over a session from `get_session_factory()`.

All three tasks are safe to re-run: `RollupService` recomputes each bucket from source
and assigns absolute values, so an overlapping beat tick, a retry, or a manual backfill
over an already-computed range cannot double-count.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from uuid import UUID

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="club_ops.refresh_occupancy_rollups")
def refresh_occupancy_rollups(hours: int = 3) -> int:
    """Hourly: refresh the trailing `hours` buckets for every active club.

    A trailing window (not just the previous hour) because late check-outs, extensions
    and retroactive no-show marks change buckets already computed.
    """
    import asyncio

    from app.db.session import get_session_factory
    from app.domains.club_ops.rollup_service import RollupService

    async def _run() -> int:
        factory = get_session_factory()
        async with factory() as session:
            return await RollupService(session).rebuild_recent_for_all_clubs(hours=hours)

    try:
        written = asyncio.run(_run())
        logger.info("club_ops_rollups_refreshed rows=%s hours=%s", written, hours)
        return written
    except Exception:  # noqa: BLE001
        logger.exception("club_ops_rollup_refresh_failed hours=%s", hours)
        return 0


@celery_app.task(name="club_ops.backfill_occupancy_rollups")
def backfill_occupancy_rollups(
    parlor_id: str, from_date: str, to_date: str
) -> int:
    """Backfill one club's historical buckets over an inclusive IST date range.

    Invoke for a new club, or after changing how occupancy is derived:
        celery -A app.tasks.celery_app call club_ops.backfill_occupancy_rollups \\
            --args='["<parlor-uuid>", "2026-07-01", "2026-07-31"]'
    """
    import asyncio

    from app.db.session import get_session_factory
    from app.domains.club_ops.rollup_service import RollupService

    async def _run() -> int:
        factory = get_session_factory()
        async with factory() as session:
            return await RollupService(session).rebuild_range(
                UUID(parlor_id),
                from_date=date.fromisoformat(from_date),
                to_date=date.fromisoformat(to_date),
            )

    try:
        written = asyncio.run(_run())
        logger.info(
            "club_ops_backfill_done parlor_id=%s from=%s to=%s rows=%s",
            parlor_id,
            from_date,
            to_date,
            written,
        )
        return written
    except Exception:  # noqa: BLE001
        logger.exception("club_ops_backfill_failed parlor_id=%s", parlor_id)
        return 0


@celery_app.task(name="club_ops.nightly_rollup_repair")
def nightly_rollup_repair(days: int = 2) -> int:
    """Nightly: recompute the last `days` days for every club.

    Catches anything the hourly trailing window missed — a session left checked-in
    overnight, or a booking edited well after its slot. Cheap because it is bounded and
    idempotent.
    """
    import asyncio

    from sqlalchemy import select

    from app.db.session import get_session_factory
    from app.domains.club_ops.rollup_service import IST, RollupService
    from app.domains.gaming_place.models import GamingPlaceExtension

    async def _run() -> int:
        factory = get_session_factory()
        written = 0
        async with factory() as session:
            club_ids = (
                await session.execute(
                    select(GamingPlaceExtension.gaming_place_id).where(
                        GamingPlaceExtension.is_deleted.is_(False)
                    )
                )
            ).scalars().all()
            today = datetime.now(IST).date()
            start = today - timedelta(days=max(0, days - 1))
            service = RollupService(session)
            for club_id in club_ids:
                written += await service.rebuild_range(
                    club_id, from_date=start, to_date=today
                )
        return written

    try:
        written = asyncio.run(_run())
        logger.info("club_ops_nightly_repair_done rows=%s days=%s", written, days)
        return written
    except Exception:  # noqa: BLE001
        logger.exception("club_ops_nightly_repair_failed days=%s", days)
        return 0
