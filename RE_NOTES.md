# Breitbandmessung App Analysis Results

## App Architecture
- **Type**: Electron App
- **Core Logic**: `resources/app.asar`
- **Main entry**: `electron.js` / `ias_desktop.js`

## Hidden CLI Parameters
- `dev=true`: As the 4th argument, this enables `console.log` and automatically opens Chrome DevTools.
- `ias.v=3`: Found in logic related to versioning/initialization.
- `--no-sandbox`: Standard Electron flag (required for root).
- `--force-renderer-accessibility`: Enables full AT-SPI tree generation.

## Automation Workflow (AT-SPI based)

Successfully navigated the app setup via Accessibility Bus (`pyatspi`):

1.  **Accept Terms**: `[button] Name: 'Akzeptieren'`
2.  **Navigate to Speedtest**: `[menu item] Name: 'Einzelmessung starten'` or `'Messkampagne'`
3.  **Select Provider**:
    - Focus `[combo box] Name: 'Bitte wählen Sie Ihren Anbieter'`
    - Type Name (e.g., 'Telekom') and press Enter.
    - Click `[button] Name: 'weiter'`
4.  **Select Tariff**:
    - Focus `[combo box] Name: 'Bitte wählen Sie Ihren Tarif'`
    - Type/Select and press Enter.
    - Click `[button] Name: 'weiter'`
5.  **Throttling**:
    - Click `[radio button] Name: 'Nein'`
    - Click `[button] Name: 'weiter'`
6.  **PLZ**:
    - Focus `[entry] Name: 'PLZ...'`
    - Type Zip Code.
    - Click `[button] Name: 'weiter'`
7.  **Rating**:
    - Click `[radio button] Name: 'Gut'` (or others)
    - Click `[button] Name: 'Einzelmessung starten'` or `'Konfiguration abschließen'`
8.  **Technical Requirements**:
    - Check all 6 checkboxes on the hints page.
    - Click `[button] Name: 'Messung starten'`

### Master Automation Script
A Python script `rootfs/usr/local/bin/master-automation.py` has been developed to fully automate the "Messkampagne" setup and start.

#### Usage in Docker
```bash
docker exec -u app -e AT_SPI_BUS_ADDRESS=unix:path=/tmp/run/user/app/at-spi/bus_0 \
  breitband-dev python3 /usr/local/bin/master-automation.py
```

### Automation Findings & Constraints
- **Cooldown Period**: The "Messkampagne" has mandatory cooldowns (e.g., 5 minutes between tests, 3 hours after 5 tests). The UI reflects this with `Sie können die Messung in X Minuten starten`. The automation script can detect this state.
- **Persistence**: Using a volume for `/config` preserves the "Terms of Service" acceptance and "User Info" (Anbieter/Tarif), making subsequent runs faster.
- **Robustness**: The AT-SPI approach is immune to window resizing or theme changes, as it looks for element names.

## IPC (Inter-Process Communication) Channels
Found in `ias_desktop.js`:
- `measurementControl`: Used to control the speedtest.
    - Message `measurementStart`: Likely triggers the test.
- `appControl`: General app management.
- `windowControl`: Window sizing/visibility.

## Storage Locations
- **Config & Logs**: `/config/xdg/config/Breitbandmessung`
- **PDF Protocols**: Typically saved in the Downloads folder or a subfolder of the config.
