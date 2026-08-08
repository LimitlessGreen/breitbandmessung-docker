#!/bin/bash

APP_PATH="/opt/Breitbandmessung/breitbandmessung"
ASAR_PATH="/opt/Breitbandmessung/resources/app.asar"
ELECTRON_FLAGS="--no-sandbox --disable-gpu --force-renderer-accessibility"

# Patch app.asar to bypass architecture checks on ARM
if [ "$(uname -m)" != "x86_64" ] && [ -f "$ASAR_PATH" ]; then
    PATCH_FLAG="/opt/Breitbandmessung/resources/.patched"
    if [ ! -f "$PATCH_FLAG" ]; then
        echo "[Patcher] ARM architecture detected. Patching app.asar..."
        cd /opt/Breitbandmessung/resources
        asar extract app.asar app-extracted

        # Find the main JS file and replace OS/Arch checks
        # We replace process.arch with 'x64' and process.platform with 'linux'
        # directly in the app code so internal electron modules stay untouched.
        find app-extracted -name "main.*.js" -exec sed -i 's/process\.arch/"x64"/g' {} +
        find app-extracted -name "main.*.js" -exec sed -i 's/process\.platform/"linux"/g' {} +

        asar pack app-extracted app.asar
        rm -rf app-extracted
        touch "$PATCH_FLAG"
        echo "[Patcher] Patching complete."
    fi
fi

if [ -f "$APP_PATH" ] && [ "$(uname -m)" = "x86_64" ]; then
    echo "[Launcher] Starting official x64 binary..."
    exec "$APP_PATH" $ELECTRON_FLAGS
elif [ -f "$ASAR_PATH" ]; then
    echo "[Launcher] Starting native Electron with extracted app.asar..."
    # Check if electron is installed
    if ! command -v electron >/dev/null 2>&1; then
        echo "[Error] Native Electron not found! Architecture: $(uname -m)"
        exit 1
    fi
    exec electron "$ASAR_PATH" $ELECTRON_FLAGS
else
    echo "[Error] Breitbandmessung not installed correctly!"
    exit 1
fi
