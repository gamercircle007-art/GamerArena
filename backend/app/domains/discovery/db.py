"""asyncpg pool for the discovery hot path (one SQL, prepared statements)."""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse, urlunparse

import asyncpg

from app.core.config import get_settings

_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()


def _asyncpg_dsn(database_url: str) -> str:
    """Convert SQLAlchemy async URL → asyncpg DSN."""
    url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgres+asyncpg://", "postgresql://")
    # Drop SQLAlchemy query params asyncpg doesn't want (e.g. sslmode handled below)
    parsed = urlparse(url)
    # Render often needs SSL
    query = parsed.query
    if "ssl" not in query and "sslmode" not in query:
        # leave as-is; connect kwargs set ssl below for render hosts
        pass
    return urlunparse(parsed)


async def get_discovery_pool() -> asyncpg.Pool:
    global _pool
    if _pool is not None:
        return _pool
    async with _pool_lock:
        if _pool is not None:
            return _pool
        settings = get_settings()
        dsn = _asyncpg_dsn(settings.database_url)
        ssl: Any = None
        if "render.com" in dsn or "amazonaws.com" in dsn:
            ssl = "require"
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=5,
            max_size=20,
            statement_cache_size=200,
            max_inactive_connection_lifetime=300,
            ssl=ssl,
            command_timeout=8,
        )
        return _pool


async def close_discovery_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
