#!/usr/bin/env bash
set -euo pipefail

mkdir -p /build/workspace /output
cd /build/workspace

tar -xzf /build/context.tar.gz -C /build/workspace --strip-components=1 2>/dev/null || tar -xzf /build/context.tar.gz -C /build/workspace

ENTRY="${ENTRY_POINT:-main.py}"
if [ -f pyforge_manifest.json ]; then
  ENTRY=$(python3 -c "import json; print(json.load(open('pyforge_manifest.json'))['entry_point'])")
fi

APP_NAME="${APP_NAME:-MyApp}"
TARGET="${BUILD_TARGET:-desktop_linux}"

echo "[PyForge] Building desktop binary for ${TARGET}..."

SPEC=$(ls -1 *.spec 2>/dev/null | head -1 || true)
if [ -n "$SPEC" ] && [ -f "$SPEC" ]; then
  pyinstaller --distpath /output --workpath /build/work "$SPEC"
else
  CONSOLE_FLAG="--console"
  if grep -qiE 'tkinter|PyQt|kivy|wx' "$ENTRY" 2>/dev/null; then
    CONSOLE_FLAG="--windowed"
  fi
  pyinstaller --onefile $CONSOLE_FLAG --name "$APP_NAME" --distpath /output --workpath /build/work "$ENTRY"
fi

ARTIFACT=$(find /output -maxdepth 2 -type f \( -name "$APP_NAME" -o -name "$APP_NAME.exe" -o -name "*.exe" \) | head -1)
if [ -z "$ARTIFACT" ]; then
  ARTIFACT=$(find /output -maxdepth 3 -type f | head -1)
fi

if [ -z "$ARTIFACT" ]; then
  echo "[PyForge] ERROR: No artifact produced."
  exit 1
fi

cp "$ARTIFACT" "/output/${APP_NAME}$(echo "$ARTIFACT" | grep -q '\.exe$' && echo .exe || true)"
echo "[PyForge] Build complete: $(basename "$ARTIFACT")"
