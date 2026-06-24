#!/usr/bin/env bash
# Run GamerCircle Flutter web app (bound to Paythan backend on :8000).
# Usage: bash scripts/run_frontend.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$ROOT/frontend/gamer_circle"
WEB_PORT="${FRONTEND_PORT:-8080}"

echo "Stopping anything on port ${WEB_PORT}..."
lsof -ti:"${WEB_PORT}" | xargs kill -9 2>/dev/null || true

cd "$FRONTEND_DIR"
flutter pub get

echo ""
echo "=== Starting frontend (Flutter web) ==="
echo "App       → http://localhost:${WEB_PORT}"
echo "Backend   → http://localhost:8000/api/v1"
echo ""

exec flutter run -d chrome \
  --web-port="${WEB_PORT}" \
  --web-hostname=localhost \
  --dart-define=API_BASE_URL=http://localhost:8000/api/v1