#!/usr/bin/env bash
# Build production release APK → Render API. Replaces prior release under releases/.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend/gamer_circle"

API_BASE_URL="${API_BASE_URL:-https://gamer-circle-api.onrender.com/api/v1}"
APP_FLAVOR="${APP_FLAVOR:-prod}"
OUT_DIR="$ROOT/releases"
mkdir -p "$OUT_DIR"

echo "Building PRODUCTION APK"
echo "  API_BASE_URL=$API_BASE_URL"
echo "  APP_FLAVOR=$APP_FLAVOR"

# Drop stale release so install never confuses old builds
rm -f "$OUT_DIR/gamer-circle-render.apk" \
  build/app/outputs/flutter-apk/app-release.apk 2>/dev/null || true

flutter pub get
flutter build apk --release \
  --dart-define="API_BASE_URL=${API_BASE_URL}" \
  --dart-define="APP_FLAVOR=${APP_FLAVOR}"

APK="build/app/outputs/flutter-apk/app-release.apk"
cp -f "$APK" "$OUT_DIR/gamer-circle-render.apk"
STAMP="$OUT_DIR/gamer-circle-render-$(date +%Y%m%d-%H%M).apk"
cp -f "$APK" "$STAMP"

echo ""
echo "APK ready:"
echo "  $OUT_DIR/gamer-circle-render.apk"
echo "  $STAMP"
echo "Install: adb install -r $OUT_DIR/gamer-circle-render.apk"
echo "Verify base URL in app errors (E_API_TIMEOUT shows full host)."
