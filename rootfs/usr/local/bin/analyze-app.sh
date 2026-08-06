#!/bin/bash

# Breitbandmessung Analysis Helper Script
# Use this within the container to explore the app.

set -e

APP_BIN=$(which breitbandmessung || echo "/usr/bin/breitbandmessung")
APP_DIR="/opt/Breitbandmessung"

echo "--------------------------------------------------"
echo "Breitbandmessung Analysis Tool"
echo "--------------------------------------------------"

if [ ! -d "$APP_DIR" ]; then
    echo "[!] App directory $APP_DIR not found. Is the app installed?"
    exit 1
fi

echo "[+] App directory found: $APP_DIR"
echo "[+] Binary path: $APP_BIN"

# 1. Search for ASAR files
ASAR_FILE="$APP_DIR/resources/app.asar"
if [ -f "$ASAR_FILE" ]; then
    echo "[+] Found Electron ASAR archive: $ASAR_FILE"
    echo "    To list content: asar list $ASAR_FILE"
    echo "    To extract: mkdir -p /tmp/app-source && asar extract $ASAR_FILE /tmp/app-source"
else
    echo "[-] No app.asar found in standard location."
fi

# 2. Search for command line flags in the binary
echo "[+] Searching for potential CLI flags in binary..."
strings "$APP_BIN" | grep -E "^\-\-[a-z\-]+" | sort -u | head -n 20 || true
echo "    (Use 'strings $APP_BIN | grep ...' for more)"

# 3. Accessibility Info
echo ""
echo "[+] Accessibility Testing:"
echo "    1. Start the container and open the VNC desktop."
echo "    2. Start the Breitbandmessung app."
echo "    3. Run 'accerciser' in a terminal inside VNC."
echo "    4. Look for 'Breitbandmessung' in the tree to explore the UI structure."

# 4. Storage Locations
echo ""
echo "[+] Storage Locations (suspected):"
echo "    - Config: /config/xdg/config/Breitbandmessung"
echo "    - Logs: /config/xdg/config/Breitbandmessung/logs"
echo "    - Cache: /config/xdg/config/Breitbandmessung/Cache"

echo "--------------------------------------------------"
echo "Analysis environment ready."
