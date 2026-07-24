#!/usr/bin/env bash
# Production redeploy helper for gamer-circle-api (branch sit) + optional Flutter APK.
# Usage:
#   export RENDER_API_KEY=rnd_...   # optional but recommended
#   bash scripts/redeploy_production.sh
#   bash scripts/redeploy_production.sh --apk
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SERVICE_ID="${RENDER_SERVICE_ID:-srv-d9dlbtrtqb8s738uohkg}"
API_URL="${API_URL:-https://gamer-circle-api.onrender.com}"
BRANCH="${BRANCH:-sit}"
BUILD_APK=0
for a in "$@"; do
  [[ "$a" == "--apk" ]] && BUILD_APK=1
done

echo "=== 1. Git: ensure on $BRANCH and push ==="
git fetch origin "$BRANCH" || true
git checkout "$BRANCH"
# empty commit forces Render autoDeploy even if tree clean
if git diff --quiet && git diff --cached --quiet; then
  git commit --allow-empty -m "chore: production redeploy $(date -u +%Y-%m-%dT%H:%MZ)"
fi
git push origin "$BRANCH"
SHA=$(git rev-parse --short HEAD)
echo "Pushed $SHA → origin/$BRANCH (Render autoDeploy branch=$BRANCH)"

echo "=== 2. Explicit Render deploy (if API key set) ==="
if [[ -n "${RENDER_DEPLOY_HOOK:-}" ]]; then
  curl -fsS -X POST "$RENDER_DEPLOY_HOOK" && echo "deploy hook OK"
elif [[ -n "${RENDER_API_KEY:-}" ]]; then
  curl -fsS -X POST \
    -H "Authorization: Bearer ${RENDER_API_KEY}" \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    "https://api.render.com/v1/services/${SERVICE_ID}/deploys" \
    -d '{"clearCache":"clear"}' | head -c 600
  echo
  echo "API deploy triggered (clear cache)"
else
  echo "No RENDER_API_KEY / RENDER_DEPLOY_HOOK — relying on autoDeploy from git push."
  echo "If service is Failed: Dashboard → Manual Deploy → Clear build cache."
  echo "  https://dashboard.render.com/web/${SERVICE_ID}"
fi

echo "=== 3. Poll /health (up to ~8 min free tier) ==="
OK=0
for i in $(seq 1 24); do
  CODE=$(curl -sS -m 20 -o /tmp/gc_health.json -w "%{http_code}" "$API_URL/health" || echo 000)
  if [[ "$CODE" == "200" ]]; then
    echo "LIVE http=200 after try $i"
    cat /tmp/gc_health.json
    echo
    OK=1
    break
  fi
  echo "try $i: http=$CODE (waiting 20s)"
  sleep 20
done

if [[ "$OK" != "1" ]]; then
  echo "STILL_DOWN — open Dashboard logs. Do NOT rebuild Flutter until /health is 200."
  exit 2
fi

echo "=== 4. /ready (DB/Redis/Twilio flags) ==="
curl -sS -m 30 "$API_URL/ready" | head -c 1200
echo

if [[ "$BUILD_APK" == "1" ]]; then
  echo "=== 5. Flutter production APK ==="
  bash "$ROOT/scripts/build_android_render.sh"
fi

echo "=== DONE ==="
echo "API: $API_URL"
echo "Flutter base: ${API_URL}/api/v1"
echo "OTP needs Twilio env on Render; password: admin / Admin@123 after seed"
