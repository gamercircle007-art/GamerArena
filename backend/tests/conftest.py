"""Pytest fixtures for API testing."""

import os
from collections.abc import AsyncGenerator

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient

# Set test env before importing app
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key_minimum_32_characters_long")
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://paythan:test@localhost:5432/paythan_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

from app.core.dependencies import get_redis_client  # noqa: E402
from app.main import app  # noqa: E402


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