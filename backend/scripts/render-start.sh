#!/usr/bin/env bash
# Render start — ALWAYS bind $PORT so free-tier can leave "Failed".
# Migrations/seed are best-effort and time-boxed; never block uvicorn forever.
set -uo pipefail
# Intentionally no `set -e`: every stage is guarded; final exec always runs.

cd "$(dirname "$0")/.." || exit 1

PORT="${PORT:-8000}"
WORKERS="${WEB_CONCURRENCY:-1}"

start_api() {
  echo "=== Starting uvicorn on 0.0.0.0:${PORT} workers=${WORKERS} ==="
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
}

# --- JWT (>=32) required by pydantic Settings ---
if [ -z "${JWT_SECRET_KEY:-}" ] || [ "${#JWT_SECRET_KEY}" -lt 32 ]; then
  export JWT_SECRET_KEY="gc-render-fallback-$(head -c 48 /dev/urandom 2>/dev/null | od -An -tx1 2>/dev/null | tr -d ' \n' | head -c 48)"
  if [ "${#JWT_SECRET_KEY}" -lt 32 ]; then
    export JWT_SECRET_KEY="gc-render-fallback-jwt-secret-key-min-32-chars-xx"
  fi
  echo "WARNING: JWT_SECRET_KEY missing/short — using ephemeral fallback"
fi

echo "=== render-start: env diagnostics (no secrets) ==="
if ! python - <<'PY'
import os
from app.core.config import get_settings

try:
    s = get_settings()
except Exception as exc:  # noqa: BLE001
    print(f"FATAL: settings failed to load: {type(exc).__name__}: {exc}")
    print("Check JWT_SECRET_KEY (>=32 chars), DATABASE_URL, REDIS_URL on Render.")
    raise SystemExit(1)

url = s.database_url
masked = url
if "@" in url and "://" in url:
    try:
        scheme, rest = url.split("://", 1)
        creds, hostpart = rest.split("@", 1)
        if ":" in creds:
            user = creds.split(":", 1)[0]
            masked = f"{scheme}://{user}:***@{hostpart}"
    except Exception:
        masked = url[:32] + "..."

print(f"  APP_ENV={s.app_env}")
print(f"  DEBUG={s.debug}")
print(f"  DATABASE_URL={masked}")
print(f"  REDIS_URL set={bool((s.redis_url or '').strip())}")
print(f"  JWT ok={len(s.jwt_secret_key or '') >= 32}")
print(f"  Twilio configured={s.twilio_configured}")
print(f"  OTP bypass active={s.use_otp_dev_bypass}")
print(f"  PORT={os.environ.get('PORT', '8000')}")
PY
then
  echo "WARNING: settings diagnostics failed — still starting API"
  start_api
fi

echo "=== Waiting for PostgreSQL (soft, capped) ==="
DB_READY=0
if python - <<'PY'
import asyncio
import os
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

MAX = int(os.environ.get("DB_WAIT_ATTEMPTS", "8"))


async def wait_for_db() -> bool:
    url = get_settings().database_url
    last = ""
    for attempt in range(1, MAX + 1):
        engine = create_async_engine(url, pool_pre_ping=True)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print(f"PostgreSQL is ready (attempt {attempt})")
            return True
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            print(f"DB not ready ({attempt}/{MAX}): {exc}")
            time.sleep(1)
        finally:
            await engine.dispose()
    print(f"PostgreSQL not ready after {MAX} attempts: {last}")
    print("Starting API anyway so /health can respond.")
    return False


ok = asyncio.run(wait_for_db())
raise SystemExit(0 if ok else 2)
PY
then
  DB_READY=1
else
  DB_READY=0
fi

if [ "$DB_READY" != "1" ]; then
  echo "Skipping PostGIS / migrations / seed (DB not ready)"
  start_api
fi

echo "=== Ensuring PostGIS extension (best-effort) ==="
python - <<'PY' || echo "PostGIS skipped"
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
        print(f"PostGIS skipped/failed (geo may fail): {exc}")
    finally:
        await engine.dispose()

asyncio.run(ensure_postgis())
PY

echo "=== Running database migrations (alembic upgrade head) ==="
if alembic upgrade head; then
  echo "Migrations OK"
else
  echo "WARNING: alembic upgrade head failed — continuing to uvicorn" >&2
fi

echo "=== Seed / ensure admin (time-boxed) ==="
if [ "${SEED_ON_BOOT:-1}" = "1" ]; then
  SEED_TIMEOUT="${SEED_TIMEOUT_SECONDS:-40}"
  if command -v timeout >/dev/null 2>&1; then
    timeout "${SEED_TIMEOUT}" python scripts/render_seed_boot.py \
      || echo "WARNING: seed timed out/failed (rc=$?) — starting API"
  else
    python scripts/render_seed_boot.py || echo "WARNING: seed failed — starting API"
  fi
else
  echo "SEED_ON_BOOT=0 — skip seed"
fi

start_api
