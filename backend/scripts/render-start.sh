#!/usr/bin/env bash
# Render free-tier start: bind $PORT as fast as possible.
# DB wait / migrate / seed are time-boxed so health checks can pass.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

PORT="${PORT:-10000}"
WORKERS="${WEB_CONCURRENCY:-1}"

start_api() {
  echo "=== Starting uvicorn host=0.0.0.0 port=${PORT} workers=${WORKERS} ==="
  # shellcheck disable=SC2086
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}" --timeout-keep-alive 5
}

# JWT required by pydantic (min 32)
if [ -z "${JWT_SECRET_KEY:-}" ] || [ "${#JWT_SECRET_KEY}" -lt 32 ]; then
  export JWT_SECRET_KEY="gc-render-fallback-jwt-secret-key-min-32-chars-ok"
  echo "WARNING: JWT_SECRET_KEY missing/short — ephemeral fallback"
fi

echo "=== env (no secrets) ==="
python - <<'PY' || true
import os
from app.core.config import get_settings
try:
    s = get_settings()
    print(f"  APP_ENV={s.app_env} JWT_ok={len(s.jwt_secret_key)>=32}")
    print(f"  REDIS_set={bool((s.redis_url or '').strip())}")
    print(f"  Twilio={s.twilio_configured} OTP_bypass={s.use_otp_dev_bypass}")
    print(f"  PORT={os.environ.get('PORT')}")
except Exception as e:
    print(f"  settings_error={type(e).__name__}: {e}")
PY

# Optional prework: skip entirely if SKIP_BOOT_TASKS=1
if [ "${SKIP_BOOT_TASKS:-0}" = "1" ]; then
  echo "SKIP_BOOT_TASKS=1 — uvicorn only"
  start_api
fi

echo "=== DB wait (hard-capped ~16s) ==="
DB_OK=0
python - <<'PY' && DB_OK=1 || DB_OK=0
import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

MAX = int(os.environ.get("DB_WAIT_ATTEMPTS", "4"))
PER_TRY = float(os.environ.get("DB_WAIT_TIMEOUT_SEC", "4"))


async def once() -> None:
    url = get_settings().database_url
    engine = create_async_engine(
        url,
        pool_pre_ping=True,
        connect_args={"timeout": PER_TRY},
    )
    try:
        async with engine.connect() as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=PER_TRY)
    finally:
        await engine.dispose()


async def main() -> int:
    last = ""
    for i in range(1, MAX + 1):
        try:
            await once()
            print(f"PostgreSQL ready attempt={i}")
            return 0
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
            print(f"DB not ready ({i}/{MAX}): {last[:180]}")
            await asyncio.sleep(0.5)
    print(f"DB unreachable after {MAX} tries: {last[:200]}")
    return 1


sys.exit(asyncio.run(main()))
PY

if [ "${DB_OK}" = "1" ]; then
  echo "=== PostGIS (best-effort, 8s) ==="
  if command -v timeout >/dev/null 2>&1; then
    timeout 8 python - <<'PY' || echo "PostGIS skip"
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

async def main():
    eng = create_async_engine(get_settings().database_url, pool_pre_ping=True, connect_args={"timeout": 5})
    try:
        async with eng.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        print("PostGIS OK")
    finally:
        await eng.dispose()
asyncio.run(main())
PY
  fi

  echo "=== alembic upgrade head (best-effort, 45s) ==="
  if command -v timeout >/dev/null 2>&1; then
    timeout 45 alembic upgrade head && echo "Migrations OK" || echo "WARNING: alembic failed/timeout — continuing"
  else
    alembic upgrade head && echo "Migrations OK" || echo "WARNING: alembic failed — continuing"
  fi

  if [ "${SEED_ON_BOOT:-0}" = "1" ]; then
    echo "=== seed (cap 30s) ==="
    SEED_TIMEOUT="${SEED_TIMEOUT_SECONDS:-30}"
    if command -v timeout >/dev/null 2>&1; then
      timeout "${SEED_TIMEOUT}" python scripts/render_seed_boot.py || echo "seed skip"
    else
      python scripts/render_seed_boot.py || echo "seed skip"
    fi
  else
    echo "SEED_ON_BOOT=0 — skip seed (set SEED_ON_BOOT=1 or FORCE_SEED=1 later)"
  fi
else
  echo "DB not ready — starting API without migrate/seed so /health works"
fi

start_api
