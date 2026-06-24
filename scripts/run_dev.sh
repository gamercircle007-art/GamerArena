#!/usr/bin/env bash
# Start Paythan backend + GamerCircle frontend together (local dev, no Docker).
# Usage: bash scripts/run_dev.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"
LOG_DIR="$ROOT/.dev-logs"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

mkdir -p "$LOG_DIR"

kill_port() {
  local port="$1"
  if lsof -ti:"$port" >/dev/null 2>&1; then
    echo "Stopping process on port ${port}..."
    lsof -ti:"$port" | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
}

echo "=== Clearing dev ports ==="
kill_port "$BACKEND_PORT"
kill_port "$FRONTEND_PORT"

echo ""
echo "=== Starting backend on :${BACKEND_PORT} ==="
bash "$ROOT/scripts/run_backend.sh" >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

echo "Waiting for backend health check..."
for _ in $(seq 1 30); do
  if curl -sf "http://localhost:${BACKEND_PORT}/health" >/dev/null 2>&1; then
    echo "Backend is healthy."
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Backend failed to start. See $BACKEND_LOG"
    tail -30 "$BACKEND_LOG" || true
    exit 1
  fi
  sleep 1
done

if ! curl -sf "http://localhost:${BACKEND_PORT}/health" >/dev/null 2>&1; then
  echo "Backend did not become healthy. See $BACKEND_LOG"
  exit 1
fi

echo ""
echo "=== Starting frontend on :${FRONTEND_PORT} ==="
cd "$ROOT/frontend/gamer_circle"
flutter pub get
flutter run -d chrome \
  --web-port="${FRONTEND_PORT}" \
  --web-hostname=localhost \
  --dart-define=API_BASE_URL="http://localhost:${BACKEND_PORT}/api/v1" \
  >"$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

cleanup() {
  echo ""
  echo "Shutting down dev servers..."
  kill "$BACKEND_PID" 2>/dev/null || true
  kill "$FRONTEND_PID" 2>/dev/null || true
  kill_port "$BACKEND_PORT"
  kill_port "$FRONTEND_PORT"
}

trap cleanup EXIT INT TERM

echo ""
echo "========================================"
echo "  GamerCircle full-stack dev is running"
echo "========================================"
echo "Frontend  → http://localhost:${FRONTEND_PORT}"
echo "Backend   → http://localhost:${BACKEND_PORT}"
echo "API docs  → http://localhost:${BACKEND_PORT}/docs"
echo "Logs      → $LOG_DIR"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

wait "$FRONTEND_PID"