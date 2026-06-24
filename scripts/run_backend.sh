#!/usr/bin/env bash
# Run Paythan backend locally (SQLite + FakeRedis, no Docker required).
# Usage: bash scripts/run_backend.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

BACKEND_PORT="${BACKEND_PORT:-8000}"

echo "Stopping anything on port ${BACKEND_PORT}..."
lsof -ti:"${BACKEND_PORT}" | xargs kill -9 2>/dev/null || true

echo ""
echo "=== Starting backend ==="
echo "API       → http://localhost:${BACKEND_PORT}"
echo "API docs  → http://localhost:${BACKEND_PORT}/docs"
echo "Health    → http://localhost:${BACKEND_PORT}/health"
echo "OTP codes are printed in backend logs (dev mode)"
echo ""

cd "$ROOT/backend"
exec "$ROOT/backend/.venv/bin/python" scripts/run_dev.py