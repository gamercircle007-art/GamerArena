#!/usr/bin/env bash
# Start Paythan backend stack with Docker Compose.
# Usage: bash scripts/docker-up.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Creating .env from .env.example..."
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "Edit $ROOT/.env and set JWT_SECRET_KEY before production use."
fi

cd "$ROOT"
docker compose up --build -d

echo ""
echo "Waiting for backend health check..."
for _ in $(seq 1 30); do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "Backend is healthy."
    curl -s http://localhost:8000/health
    echo ""
    echo "API       → http://localhost:8000"
    echo "API docs  → http://localhost:8000/docs"
    exit 0
  fi
  sleep 2
done

echo "Backend did not become healthy in time. Check: docker compose logs backend"
exit 1