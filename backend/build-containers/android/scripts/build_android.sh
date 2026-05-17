#!/usr/bin/env bash
set -euo pipefail

mkdir -p /build/workspace /output
cd /build/workspace

tar -xzf /build/context.tar.gz -C /build/workspace --strip-components=1 2>/dev/null || tar -xzf /build/context.tar.gz -C /build/workspace

APP_NAME="${APP_NAME:-MyApp}"
echo "[PyForge] Android APK build started for ${APP_NAME}..."

if [ ! -f buildozer.spec ]; then
  echo "[PyForge] No buildozer.spec found; generating minimal spec..."
  buildozer init
  sed -i "s/^title = .*/title = ${APP_NAME}/" buildozer.spec 2>/dev/null || true
  sed -i "s/^package.name = .*/package.name = ${APP_NAME,,}/" buildozer.spec 2>/dev/null || true
fi

export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-/root/.buildozer/android/platform/android-sdk}"
export ANDROID_NDK_ROOT="${ANDROID_NDK_ROOT:-/root/.buildozer/android/platform/android-ndk}"

echo "[PyForge] Running buildozer android debug (this may take a long time on first run)..."
buildozer -v android debug 2>&1 | tee /build/buildozer.log || {
  echo "[PyForge] Buildozer failed. For production Android builds, ensure SDK/NDK are cached in the image."
  echo "[PyForge] Packaging project source as fallback artifact..."
  zip -r "/output/${APP_NAME}-android-project.zip" . -x "*/.buildozer/*" 2>/dev/null || true
  exit 0
}

APK=$(find . -name "*.apk" -type f | head -1)
if [ -n "$APK" ]; then
  cp "$APK" "/output/${APP_NAME}.apk"
  echo "[PyForge] APK ready: ${APP_NAME}.apk"
else
  echo "[PyForge] No APK found; check buildozer.log"
  exit 1
fi
