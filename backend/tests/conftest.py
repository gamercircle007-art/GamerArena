"""Pytest fixtures for API testing."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Set test env before importing app
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_minimum_32_characters_long")
os.environ.setdefault("APP_ENV", "local")

# Dedicated SQLite file for the shared smoke tests (CI has no seeded dev.db).
_TEST_DB = Path(__file__).resolve().parent / "_ci_test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

from app.core.dependencies import get_redis_client  # noqa: E402
from app.main import app  # noqa: E402


def pytest_sessionstart(session: pytest.Session) -> None:
    """Create schema + minimal seed so SQLite CI does not hit 'no such table'."""
    from app.db.base import Base
    import app.db.models  # noqa: F401
    from app.domains.gaming_place.models import GamingPlace

    if _TEST_DB.exists():
        _TEST_DB.unlink()

    sync_url = os.environ["DATABASE_URL"].replace("sqlite+aiosqlite://", "sqlite://", 1)
    engine = create_engine(sync_url)
    Base.metadata.create_all(engine)

    now = datetime.now(UTC)
    with Session(engine) as db:
        exists = db.scalar(select(GamingPlace.id).limit(1))
        if exists is None:
            db.add(
                GamingPlace(
                    id=uuid.uuid4(),
                    google_place_id="ci-seed-delhi-arcade",
                    name="CI Delhi Arcade",
                    address="Connaught Place, New Delhi",
                    city_id=uuid.uuid4(),
                    latitude=28.6139,
                    longitude=77.2090,
                    rating=4.5,
                    user_ratings_total=10,
                    business_status="OPERATIONAL",
                    primary_type="video_arcade",
                    available_now=True,
                    rating_score=4.2,
                    amenities_mask=0,
                    review_count=10,
                    created_at=now,
                    updated_at=now,
                )
            )
            db.commit()
    engine.dispose()


@pytest.fixture(autouse=True)
async def fake_redis() -> AsyncGenerator[None, None]:
    """Use in-memory Redis so tests do not require a running Redis server."""

    async def _override() -> AsyncGenerator[fakeredis.aioredis.FakeRedis, None]:
        client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        try:
            yield client
        finally:
            await client.aclose()

    app.dependency_overrides[get_redis_client] = _override
    yield
    app.dependency_overrides.pop(get_redis_client, None)


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
