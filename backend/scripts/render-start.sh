#!/usr/bin/env bash
# Start script for Render (native Python or Docker override).
# Runs migrations then serves the API on $PORT.
set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${PORT:-8000}"
WORKERS="${WEB_CONCURRENCY:-1}"

echo "Waiting for PostgreSQL..."
python - <<'PY'
import asyncio
import sys
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings


async def wait_for_db(max_attempts: int = 30) -> None:
    url = get_settings().database_url
    for attempt in range(1, max_attempts + 1):
        engine = create_async_engine(url, pool_pre_ping=True)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print("PostgreSQL is ready")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"DB not ready ({attempt}/{max_attempts}): {exc}")
            time.sleep(2)
        finally:
            await engine.dispose()
    print("PostgreSQL did not become ready in time", file=sys.stderr)
    sys.exit(1)


asyncio.run(wait_for_db())
PY

echo "Ensuring PostGIS extension (best-effort)..."
python - <<'PY'
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings


async def ensure_postgis() -> None:
    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        print("PostGIS extension OK")
    except Exception as exc:  # noqa: BLE001
        print(f"PostGIS extension skipped/failed (geo queries may fail): {exc}")
    finally:
        await engine.dispose()


asyncio.run(ensure_postgis())
PY

echo "Running database migrations..."
alembic upgrade head

# Always ensure admin exists; full demo seed only when gaming_places empty
if [ "${SEED_ON_BOOT:-1}" = "1" ]; then
  echo "Checking / seeding demo data + admin..."
  python - <<'PY' || echo "Seed check failed (non-fatal)"
import asyncio
import runpy
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

async def need_full_seed() -> bool:
    if __import__("os").environ.get("FORCE_SEED") == "1":
        return True
    eng = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        async with eng.connect() as conn:
            try:
                n = await conn.scalar(text("SELECT COUNT(*) FROM gaming_places"))
            except Exception:
                return True
            return int(n or 0) == 0
    finally:
        await eng.dispose()

async def ensure_admin_only() -> None:
    """Lightweight admin upsert without re-seeding parlors/posts."""
    from app.db import session as db_session
    import app.db.models  # noqa: F401
    from app.domains.user.models import User, UserRole
    from app.core.security import hash_password
    from sqlalchemy import select

    db_session._engine = None
    db_session._session_factory = None
    factory = db_session.get_session_factory()
    async with factory() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        if user is None:
            phone_hit = (
                await session.execute(select(User).where(User.phone == "+919999999999"))
            ).scalar_one_or_none()
            if phone_hit is not None:
                phone_hit.username = "admin"
                phone_hit.role = UserRole.ADMIN
                phone_hit.hashed_password = hash_password("Admin@123")
                phone_hit.is_active = True
                phone_hit.is_verified = True
                phone_hit.email_verified = True
                phone_hit.phone_verified = True
                await session.commit()
                print("Admin promoted from existing user")
                return
            session.add(
                User(
                    full_name="GameConnect Admin",
                    username="admin",
                    email="admin@gameconnect.in",
                    phone="+919999999999",
                    hashed_password=hash_password("Admin@123"),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                    email_verified=True,
                    phone_verified=True,
                )
            )
            await session.commit()
            print("Admin user created: admin / Admin@123")
        else:
            if user.role != UserRole.ADMIN or not user.is_active:
                user.role = UserRole.ADMIN
                user.is_active = True
                await session.commit()
                print("Admin role/active repaired")
            else:
                print("Admin user already present")

if asyncio.run(need_full_seed()):
    print("Empty gaming_places — running seed_render_bootstrap...")
    runpy.run_path("scripts/seed_render_bootstrap.py", run_name="__main__")
else:
    print("gaming_places populated — ensuring admin only")
    asyncio.run(ensure_admin_only())
PY
fi

echo "Starting uvicorn on port ${PORT} (workers=${WORKERS})..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
