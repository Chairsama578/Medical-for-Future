# ST7789 Device UI Code

This folder contains the static UI code for the medical demo device display.

Target hardware:

- Display: 1.83 inch IPS LCD
- Driver: ST7789
- Resolution: 240x280
- Interface: SPI
- Recommended Arduino display library: TFT_eSPI

## UI States

The device UI has 3 states:

1. SAFE
   - Shows heart rate, blood pressure, and AI risk.
   - Main action: SOS.

2. WARNING
   - Shows abnormal BP/HR warning.
   - Shows risk score and countdown.
   - Main action: I'M OK.
   - If there is no response before countdown ends, switch to EMERGENCY.

3. EMERGENCY
   - Shows SOS.
   - Shows family notified, location shared, help requested.
   - Main action: I'M SAFE.

## Files

- `medical_device_ui_demo.ino`: Arduino demo sketch.
- `DeviceUi.h`: public UI types and renderer API.
- `DeviceUi.cpp`: ST7789 drawing implementation.
- `ui_contract.json`: mock data contract for backend/member integration.

## Arduino Setup

Install `TFT_eSPI` in Arduino IDE.

Configure `TFT_eSPI/User_Setup.h` for your board and ST7789 pins. The important display values are:

```cpp
#define ST7789_DRIVER
#define TFT_WIDTH  240
#define TFT_HEIGHT 280
```

Then open `medical_device_ui_demo.ino` and upload.

The demo uses mock data and cycles by button pins if configured. Backend integration can later call:

- `ui.showSafe(vitals)`
- `ui.showWarning(vitals, countdownSeconds)`
- `ui.showEmergency(vitals)`

