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
    "http://localhost:4200,http://127.0.0.1:4200,"
    "http://localhost:8080,http://127.0.0.1:8080,"
    "http://localhost:8000,http://127.0.0.1:8000",
)
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{BACKEND_ROOT / 'dev.db'}",
)
os.environ.setdefault(
    "GAMING_PLACES_DATABASE_URL",
    "postgresql://projectx:projectx@localhost:5432/projectx",
)
os.environ.setdefault("GAMING_PLACES_MEDIA_BASE_URL", "http://localhost:8001")
# Force dev-mode OTP logging (skip Twilio when placeholders are in .env)
os.environ["TWILIO_ACCOUNT_SID"] = ""
os.environ["TWILIO_AUTH_TOKEN"] = ""

from fakeredis import aioredis as fake_aioredis

from app.core.config import get_settings
from app.core.dependencies import get_redis_client
from app.db.base import Base
from app.db import session as db_session
import app.db.models  # noqa: F401

get_settings.cache_clear()
db_session._engine = None
db_session._session_factory = None

_fake_redis = fake_aioredis.FakeRedis(decode_responses=True)


async def _override_redis() -> AsyncGenerator[fake_aioredis.FakeRedis, None]:
    yield _fake_redis


async def init_db() -> None:
    settings = get_settings()
    if os.environ.get("DEV_RESET_DB") == "1" and settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.split("///", 1)[-1]
        path = Path(db_path)
        if path.exists():
            path.unlink()
            print(f"Reset SQLite dev DB → {path}")

    engine = db_session.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    settings = get_settings()
    if settings.gaming_places_database_url:
        from app.domains.gaming_place.sync import sync_gaming_places

        factory = db_session.get_session_factory()
        async with factory() as session:
            count = await sync_gaming_places(session, settings.gaming_places_database_url)
            print(f"Gaming places synced → {count} venues from gaming_places table")


def main() -> None:
    from app.main import app
    import uvicorn

    app.dependency_overrides[get_redis_client] = _override_redis
    asyncio.run(init_db())

    import importlib.util

    seed_path = BACKEND_ROOT / "scripts" / "seed_admin_user.py"
    spec = importlib.util.spec_from_file_location("seed_admin_user", seed_path)
    seed_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(seed_module)
    asyncio.run(seed_module.seed_admin())

    seed_booking_path = BACKEND_ROOT / "scripts" / "seed_gaming_booking.py"
    spec2 = importlib.util.spec_from_file_location("seed_gaming_booking", seed_booking_path)
    seed_booking = importlib.util.module_from_spec(spec2)
    assert spec2.loader is not None
    spec2.loader.exec_module(seed_booking)
    asyncio.run(seed_booking.seed())

    print("Paythan dev server → http://localhost:8000")
    print("Admin login      → username: admin  password: Admin@123")
    print("Admin OTP login  → phone: 9999999999  OTP: 123456")
    print("API docs         → http://localhost:8000/docs")
    print("Health check     → http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()