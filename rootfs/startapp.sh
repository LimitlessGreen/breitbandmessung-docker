#!/bin/bash

APP_PATH="/opt/Breitbandmessung/breitbandmessung"
ASAR_PATH="/opt/Breitbandmessung/resources/app.asar"
ELECTRON_FLAGS="--no-sandbox --disable-gpu --force-renderer-accessibility"

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
