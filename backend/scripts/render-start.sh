#!/usr/bin/env bash
# Start script for Render (native Python or Docker override).
# Runs migrations then serves the API on $PORT.
# Never hang silently: every stage logs success/failure.
# Always reach uvicorn so free-tier can leave "Failed" and pass /health.
set -euo pipefail

cd "$(dirname "$0")/.."

PORT="${PORT:-8000}"
WORKERS="${WEB_CONCURRENCY:-1}"

# JWT must be >=32 chars or pydantic Settings crashes before uvicorn binds.
if [ -z "${JWT_SECRET_KEY:-}" ] || [ "${#JWT_SECRET_KEY}" -lt 32 ]; then
  export JWT_SECRET_KEY="gc-render-fallback-$(head -c 48 /dev/urandom | od -An -tx1 | tr -d ' \n' | head -c 48)"
  echo "WARNING: JWT_SECRET_KEY missing/short — using ephemeral fallback (set a stable key in Dashboard)"
fi

echo "=== render-start: env diagnostics (no secrets) ==="
python - <<'PY'
import os
from app.core.config import get_settings

try:
    s = get_settings()
except Exception as exc:  # noqa: BLE001
    print(f"FATAL: settings failed to load: {type(exc).__name__}: {exc}")
    print("Check JWT_SECRET_KEY (>=32 chars), DATABASE_URL, REDIS_URL on Render.")
    raise SystemExit(1)

url = s.database_url
# mask password in URL for logs
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

echo "=== Waiting for PostgreSQL ==="
python - <<'PY'
import asyncio
import os
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

# Free-tier recovery: do not hard-exit if DB is slow/missing — start API so
# status becomes Live and /health answers. /ready reports database=false.
# Cap wait so deploy health checks are not starved (default ~20s).
HARD_FAIL = os.environ.get("DB_WAIT_HARD_FAIL", "0") == "1"
MAX = int(os.environ.get("DB_WAIT_ATTEMPTS", "10"))


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
            time.sleep(2)
        finally:
            await engine.dispose()
    print(f"PostgreSQL not ready after {MAX} attempts: {last}")
    print(
        "Link DATABASE_URL from gamer-circle-db (Internal URL) in Dashboard. "
        "Starting API anyway so /health can respond."
    )
    return False


ok = asyncio.run(wait_for_db())
if not ok and HARD_FAIL:
    raise SystemExit(1)
# Export for later stages
open("/tmp/gc_db_ready", "w").write("1" if ok else "0")
PY

DB_READY=$(cat /tmp/gc_db_ready 2>/dev/null || echo 0)
if [ "$DB_READY" != "1" ]; then
  echo "Skipping PostGIS / migrations / seed (DB not ready) — starting uvicorn only"
  echo "=== Starting uvicorn on 0.0.0.0:${PORT} workers=${WORKERS} ==="
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
fi

echo "=== Ensuring PostGIS extension (best-effort) ==="
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
        print(f"PostGIS skipped/failed (geo may fail): {exc}")
    finally:
        await engine.dispose()

asyncio.run(ensure_postgis())
PY

echo "=== Running database migrations (alembic upgrade head) ==="
# Prefer success; if alembic fails, still start API so service is Live and
# /health works (free-tier recovery). /ready will show degraded DB schema.
if alembic upgrade head; then
  echo "Migrations OK"
else
  echo "WARNING: alembic upgrade head failed — diagnosing then continuing" >&2
  python - <<'PY' || true
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

async def diagnose():
    eng = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    async with eng.connect() as conn:
        try:
            rows = await conn.execute(text(
                "SELECT version_num FROM alembic_version"
            ))
            print("alembic_version:", [r[0] for r in rows])
        except Exception as e:
            print("alembic_version missing:", e)
        try:
            n = await conn.scalar(text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema='public'"
            ))
            print("public tables:", n)
        except Exception as e:
            print("table count failed:", e)
        # Emergency: apply soft-delete columns if migration 020 never ran
        try:
            await conn.execute(text("""
            DO $$
            BEGIN
              IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'gaming_place_extensions'
              ) THEN
                ALTER TABLE gaming_place_extensions
                  ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;
                ALTER TABLE gaming_place_extensions
                  ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT false;
                ALTER TABLE gaming_place_extensions
                  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ NULL;
              END IF;
            END $$;
            """))
            await conn.commit()
            print("emergency soft-delete columns applied")
        except Exception as e:
            print("emergency column patch failed:", e)
    await eng.dispose()
asyncio.run(diagnose())
PY
  echo "Continuing to start uvicorn despite migration warning"
fi

echo "=== Seed / ensure admin (time-boxed; never block uvicorn) ==="
# Full seed can OOM free-tier; admin-only is enough for login smoke.
# SEED_ON_BOOT=1 → admin ensure + optional full seed if empty
# FORCE_SEED=1 → always full seed
# SEED_ON_BOOT=0 → skip entirely
if [ "${SEED_ON_BOOT:-1}" = "1" ]; then
  SEED_TIMEOUT="${SEED_TIMEOUT_SECONDS:-45}"
  set +e
  timeout "${SEED_TIMEOUT}" python - <<'PY'
import asyncio
import os
import runpy
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

async def need_full_seed() -> bool:
    if os.environ.get("FORCE_SEED") == "1":
        return True
    eng = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        async with eng.connect() as conn:
            try:
                n = await conn.scalar(text("SELECT COUNT(*) FROM gaming_places"))
            except Exception:
                return False  # schema missing — migrations may have failed; skip full seed
            return int(n or 0) == 0
    finally:
        await eng.dispose()

async def ensure_admin_only() -> None:
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

async def main() -> None:
    # Always prefer admin ensure first so login works even if full seed is skipped.
    try:
        await ensure_admin_only()
    except Exception as exc:  # noqa: BLE001
        print(f"ensure_admin failed (non-fatal): {exc}")

    try:
        if await need_full_seed():
            print("Empty gaming_places — running seed_render_bootstrap...")
            runpy.run_path("scripts/seed_render_bootstrap.py", run_name="__main__")
        else:
            print("gaming_places populated or schema not ready — skip full seed")
    except Exception as exc:  # noqa: BLE001
        print(f"full seed failed (non-fatal): {exc}")

asyncio.run(main())
PY
  SEED_RC=$?
  set -e
  if [ "${SEED_RC}" -eq 124 ]; then
    echo "WARNING: seed timed out after ${SEED_TIMEOUT}s — starting API anyway"
  elif [ "${SEED_RC}" -ne 0 ]; then
    echo "WARNING: seed exited ${SEED_RC} — starting API anyway"
  fi
else
  echo "SEED_ON_BOOT=0 — skip seed"
fi

echo "=== Starting uvicorn on 0.0.0.0:${PORT} workers=${WORKERS} ==="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
