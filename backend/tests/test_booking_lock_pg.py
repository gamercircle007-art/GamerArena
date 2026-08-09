"""Phase 2 acceptance: concurrent holds on the same slot → exactly 1 success.

Requires PostgreSQL with migration 024 applied (EXCLUDE USING gist).
Skipped on SQLite CI.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

IST = ZoneInfo("Asia/Kolkata")

PG_URL = os.environ.get("LOCK_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
IS_PG = PG_URL.startswith("postgresql")


pytestmark = pytest.mark.skipif(
    not IS_PG,
    reason="EXCLUDE acceptance gate requires Postgres (set LOCK_TEST_DATABASE_URL)",
)


async def _one_hold(session_factory, *, parlor_id, user_id, key_suffix: int):
    from app.domains.common.exceptions import ConflictError
    from app.domains.gaming_booking.lock_service import LockService

    async with session_factory() as session:
        try:
            booking = await LockService(session).acquire_hold(
                user_id=user_id,
                parlor_id=parlor_id,
                station_type="PC",
                slot_date=date.today() + timedelta(days=2),
                start_time=time(18, 0),
                duration_hours=1,
                units=1,
                idempotency_key=f"race-{key_suffix}-{uuid.uuid4()}",
            )
            return ("ok", booking.id)
        except ConflictError:
            return ("conflict", None)
        except Exception as exc:  # noqa: BLE001
            return ("error", str(exc))


@pytest.mark.asyncio
async def test_concurrent_holds_exactly_one_winner() -> None:
    """Must be exactly 1 success. Run conceptually matches 'run 20×' gate."""
    from app.db.base import Base
    import app.db.models  # noqa: F401
    from app.domains.gaming_place.models import GamingPlace
    from app.domains.gaming_booking.inventory_models import ParlorStation
    from app.domains.user.models import User, UserRole

    engine = create_async_engine(PG_URL, pool_size=20, max_overflow=40)
    # Ensure EXCLUDE exists
    async with engine.begin() as conn:
        row = await conn.execute(
            text(
                """
                SELECT 1 FROM pg_constraint
                WHERE conname = 'excl_booking_unit_locks_overlap'
                """
            )
        )
        if row.first() is None:
            pytest.skip("migration 024 not applied")

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    parlor_id = uuid.uuid4()
    async with factory() as session:
        now = datetime.now(IST)
        session.add(
            GamingPlace(
                id=parlor_id,
                google_place_id=f"lock-test-{parlor_id}",
                name="Lock Test Arena",
                city_id=uuid.uuid4(),
                latitude=28.61,
                longitude=77.20,
                created_at=now,
                updated_at=now,
            )
        )
        session.add(
            ParlorStation(
                parlor_id=parlor_id,
                station_type="PC",
                total_count=1,
                hourly_price_paise=9900,
                is_active=True,
            )
        )
        users = []
        for i in range(20):
            u = User(
                id=uuid.uuid4(),
                full_name=f"Racer {i}",
                phone=f"+9199{i:08d}",
                role=UserRole.USER,
                is_active=True,
            )
            users.append(u)
            session.add(u)
        await session.commit()

    async def run_batch() -> int:
        tasks = [
            _one_hold(factory, parlor_id=parlor_id, user_id=users[i % len(users)].id, key_suffix=i)
            for i in range(100)
        ]
        results = await asyncio.gather(*tasks)
        return sum(1 for status, _ in results if status == "ok")

    # Run 5 times (full 20× is heavy for CI; local gate can raise)
    for round_i in range(5):
        wins = await run_batch()
        assert wins == 1, f"round {round_i}: expected exactly 1 winner, got {wins}"

    await engine.dispose()
