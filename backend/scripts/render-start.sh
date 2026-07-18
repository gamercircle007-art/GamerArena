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

echo "Starting uvicorn on port ${PORT} (workers=${WORKERS})..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
