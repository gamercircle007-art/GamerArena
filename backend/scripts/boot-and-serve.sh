#!/usr/bin/env bash
# Render entry: best-effort migrate + admin seed, then always bind $PORT.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

PORT="${PORT:-10000}"

echo "=== boot-and-serve: migrate (best-effort) ==="
alembic upgrade head && echo "Migrations OK" || echo "WARNING: alembic failed — continuing"

echo "=== boot-and-serve: seed admin (best-effort) ==="
python scripts/render_seed_boot.py && echo "Seed OK" || echo "WARNING: seed failed — continuing"

echo "=== Starting uvicorn on 0.0.0.0:${PORT} ==="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
