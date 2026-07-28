#!/usr/bin/env bash
# Render entry: best-effort migrate + admin seed, then always bind $PORT.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

PORT="${PORT:-10000}"

echo "=== boot-and-serve: migrate (best-effort) ==="
# Prefer full upgrade; if 019 stamp mismatch, stamp head of known chain then upgrade
if ! alembic upgrade head; then
  echo "WARNING: alembic upgrade failed — trying stamp + upgrade"
  alembic stamp 020_admin_parlor_soft_delete 2>/dev/null || true
  alembic upgrade head && echo "Migrations OK after stamp" || echo "WARNING: alembic still failing — continuing"
else
  echo "Migrations OK"
fi

echo "=== boot-and-serve: seed admin (best-effort) ==="
python scripts/render_seed_boot.py && echo "Seed OK" || echo "WARNING: seed failed — continuing"

echo "=== Starting uvicorn on 0.0.0.0:${PORT} ==="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
