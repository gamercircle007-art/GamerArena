#!/usr/bin/env bash
# E2E verification: Docker stack + migrations + seed + API smoke tests
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Starting Docker stack..."
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose up -d --build
elif docker compose version >/dev/null 2>&1; then
  docker compose up -d --build
else
  echo "ERROR: docker compose not available. Install Docker Desktop."
  exit 1
fi

echo "==> Waiting for backend health..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "Backend healthy."
    break
  fi
  sleep 2
  if [ "$i" -eq 30 ]; then
    echo "ERROR: Backend did not become healthy in time."
    exit 1
  fi
done

echo "==> Running migrations (if not auto-applied)..."
docker exec paythan-backend alembic upgrade head || true

echo "==> Seeding dev data..."
docker exec paythan-backend python scripts/seed_dev_data.py || true

echo "==> API smoke checks..."
curl -sf http://localhost:8000/health | python3 -m json.tool
curl -sf http://localhost:8000/api/v1/payments/razorpay/config | python3 -m json.tool
OPENAPI_COUNT=$(curl -sf http://localhost:8000/openapi.json | python3 -c "import sys,json; print(len(json.load(sys.stdin)['paths']))")
echo "OpenAPI paths: $OPENAPI_COUNT"

echo "==> Backend unit tests..."
cd "$ROOT/backend" && .venv/bin/python -m pytest tests/ -q

echo ""
echo "E2E verification complete."
echo "  Swagger: http://localhost:8000/docs"
echo "  Flutter: cd frontend/gamer_circle && flutter run"