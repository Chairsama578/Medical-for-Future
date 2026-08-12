#include <TFT_eSPI.h>
#include "DeviceUi.h"
#include "ApiClient.h"

TFT_eSPI tft = TFT_eSPI();
DeviceUi ui(tft);

const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASS";
const char* API_HOST = "192.168.x.x";
const uint16_t API_PORT = 8080;

ApiClient api(API_HOST, API_PORT);

constexpr int PIN_OK = 32;
constexpr int PIN_SOS = 33;
constexpr unsigned long POLL_INTERVAL = 500;

DeviceState state = DeviceState::Safe;
VitalSigns vitals = {76, 120, 80, 0, 98, 100, 1.0f};
uint8_t countdownSeconds = 10;
unsigned long lastCountdownTick = 0;
unsigned long lastPollTick = 0;
bool apiConnected = false;

void setup() {
  pinMode(PIN_OK, INPUT_PULLUP);
  pinMode(PIN_SOS, INPUT_PULLUP);

  ui.begin();
  ui.showSafe(vitals);

  apiConnected = api.connectWiFi(WIFI_SSID, WIFI_PASS);
  if (apiConnected) {
    api.checkHealth();
  }
}

void loop() {
  handlePolling();
  handleButtons();
  handleWarningCountdown();
}

void handlePolling() {
  unsigned long now = millis();
  if (now - lastPollTick < POLL_INTERVAL) return;
  lastPollTick = now;

  if (!api.isConnected()) return;

  VitalSigns newVitals;
  DeviceState newState;
  bool emergency = false;

  if (api.fetchSensorData(newVitals, newState, emergency)) {
    vitals = newVitals;

    if (newState != state) {
      state = newState;
      switch (state) {
        case DeviceState::Safe:
          countdownSeconds = 10;
          ui.showSafe(vitals);
          break;
        case DeviceState::Warning:
          countdownSeconds = 10;
          lastCountdownTick = millis();
          ui.showWarning(vitals, countdownSeconds);
          break;
        case DeviceState::Emergency:
          ui.showEmergency(vitals);
          break;
        case DeviceState::SensorError:
          ui.showSensorError(vitals);
          break;
      }
    } else {
      updateDisplay();
    }

    if (emergency && state != DeviceState::Emergency) {
      state = DeviceState::Emergency;
      ui.showEmergency(vitals);
    }
  }
}

void handleButtons() {
  if (digitalRead(PIN_SOS) == LOW) {
    api.triggerSOS();
    state = DeviceState::Emergency;
    ui.showEmergency(vitals);
    delay(250);
  }

  if (digitalRead(PIN_OK) == LOW) {
    if (state == DeviceState::Warning || state == DeviceState::Emergency) {
      state = DeviceState::Safe;
      countdownSeconds = 10;
      ui.showSafe(vitals);
    } else if (state == DeviceState::SensorError) {
      state = DeviceState::Safe;
      ui.showSafe(vitals);
    }
    delay(250);
  }
}

void handleWarningCountdown() {
  if (state != DeviceState::Warning) return;

  unsigned long now = millis();
  if (now - lastCountdownTick < 1000) return;
  lastCountdownTick = now;

  if (countdownSeconds > 0) {
    countdownSeconds -= 1;
    ui.showWarning(vitals, countdownSeconds);
  }

  if (countdownSeconds == 0) {
    api.triggerSOS();
    state = DeviceState::Emergency;
    ui.showEmergency(vitals);
  }
}

void updateDisplay() {
  switch (state) {
    case DeviceState::Safe:
      ui.showSafe(vitals);
      break;
    case DeviceState::Warning:
      ui.showWarning(vitals, countdownSeconds);
      break;
    case DeviceState::Emergency:
      ui.showEmergency(vitals);
      break;
    case DeviceState::SensorError:
      ui.showSensorError(vitals);
      break;
  }
}
