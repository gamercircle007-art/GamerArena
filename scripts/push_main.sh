#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Git status (before) ==="
git status

echo ""
echo "=== Staging all changes ==="
git add -A

echo ""
echo "=== Committing ==="
git commit -m "chore: backend-only repo with Docker Compose setup

- Remove Flutter frontend (backend-only BE-python repo)
- Add Docker entrypoint with auto-migrations on startup
- Add .dockerignore, docker-up.sh, run_backend.sh helpers
- Commit poetry.lock for reproducible Docker builds
- Update README for backend + Docker quick start" || echo "Nothing new to commit."

echo ""
echo "=== Pushing to origin main ==="
git push origin main

echo ""
echo "=== Done ==="
git log --oneline -3