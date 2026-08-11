#include <TFT_eSPI.h>
#include "DeviceUi.h"

TFT_eSPI tft = TFT_eSPI();
DeviceUi ui(tft);

constexpr int PIN_OK = 32;
constexpr int PIN_SOS = 33;

DeviceState state = DeviceState::Safe;
uint8_t countdownSeconds = 10;
unsigned long lastCountdownTick = 0;
unsigned long lastAutoDemoTick = 0;

VitalSigns safeVitals = {
  76,
  118,
  76,
  14,
  "NORMAL"
};

VitalSigns warningVitals = {
  118,
  178,
  108,
  78,
  "UNSTABLE"
};

VitalSigns emergencyVitals = {
  54,
  190,
  120,
  94,
  "LOW"
};

void setup() {
  pinMode(PIN_OK, INPUT_PULLUP);
  pinMode(PIN_SOS, INPUT_PULLUP);

  ui.begin();
  ui.showSafe(safeVitals);
}

void loop() {
  handleButtons();
  handleWarningCountdown();
  handleAutoDemo();
}

void handleButtons() {
  if (digitalRead(PIN_SOS) == LOW) {
    enterEmergency();
    delay(250);
  }

  if (digitalRead(PIN_OK) == LOW) {
    if (state == DeviceState::Warning || state == DeviceState::Emergency) {
      enterSafe();
    }
    delay(250);
  }
}

void handleWarningCountdown() {
  if (state != DeviceState::Warning) {
    return;
  }

  unsigned long now = millis();
  if (now - lastCountdownTick < 1000) {
    return;
  }

  lastCountdownTick = now;

  if (countdownSeconds > 0) {
    countdownSeconds -= 1;
    ui.showWarning(warningVitals, countdownSeconds);
  }

  if (countdownSeconds == 0) {
    enterEmergency();
  }
}

void handleAutoDemo() {
  unsigned long now = millis();

  if (now - lastAutoDemoTick < 15000) {
    return;
  }

  lastAutoDemoTick = now;

  if (state == DeviceState::Safe) {
    enterWarning();
  }
}

void enterSafe() {
  state = DeviceState::Safe;
  countdownSeconds = 10;
  ui.showSafe(safeVitals);
}

void enterWarning() {
  state = DeviceState::Warning;
  countdownSeconds = 10;
  lastCountdownTick = millis();
  ui.showWarning(warningVitals, countdownSeconds);
}

void enterEmergency() {
  state = DeviceState::Emergency;
  countdownSeconds = 10;
  ui.showEmergency(emergencyVitals);
}

