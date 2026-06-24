#!/usr/bin/env python3
"""
Run Paythan locally without Docker.

Uses SQLite + FakeRedis so you can test immediately when Postgres/Redis
are not installed. For production-like setup, use docker compose instead.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/run_dev.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test_jwt_secret_key_for_local_development_only_32chars",
)
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("DEBUG", "true")
# Fixed OTP for local dev — change or clear to use random OTPs
os.environ.setdefault("OTP_DEV_BYPASS_CODE", "123456")
os.environ.setdefault(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:8080,http://127.0.0.1:8080,"
    "http://localhost:8000,http://127.0.0.1:8000",
)
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{BACKEND_ROOT / 'dev.db'}",
)
# Force dev-mode OTP logging (skip Twilio when placeholders are in .env)
os.environ["TWILIO_ACCOUNT_SID"] = ""
os.environ["TWILIO_AUTH_TOKEN"] = ""

from fakeredis import aioredis as fake_aioredis

from app.core.config import get_settings
from app.core.dependencies import get_redis_client
from app.db.base import Base
from app.db import session as db_session
from app.domains.user.models import User  # noqa: F401

get_settings.cache_clear()
db_session._engine = None
db_session._session_factory = None

_fake_redis = fake_aioredis.FakeRedis(decode_responses=True)


async def _override_redis() -> AsyncGenerator[fake_aioredis.FakeRedis, None]:
    yield _fake_redis


async def init_db() -> None:
    engine = db_session.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def main() -> None:
    from app.main import app
    import uvicorn

    app.dependency_overrides[get_redis_client] = _override_redis
    asyncio.run(init_db())

    print("Paythan dev server → http://localhost:8000")
    print("API docs         → http://localhost:8000/docs")
    print("Health check     → http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()