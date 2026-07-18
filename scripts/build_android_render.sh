#!/usr/bin/env bash
# Build a release APK pointed at the Render staging API.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend/gamer_circle"

API_BASE_URL="${API_BASE_URL:-https://gamer-circle-api.onrender.com/api/v1}"

echo "Building APK with API_BASE_URL=${API_BASE_URL}"
flutter pub get
flutter build apk --release --dart-define="API_BASE_URL=${API_BASE_URL}"

APK="build/app/outputs/flutter-apk/app-release.apk"
echo ""
echo "APK ready: $ROOT/frontend/gamer_circle/${APK}"
echo "Install: adb install -r $ROOT/frontend/gamer_circle/${APK}"
