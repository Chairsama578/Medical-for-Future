#pragma once

#include <Arduino.h>
#include <TFT_eSPI.h>

enum class DeviceState {
  Safe,
  Warning,
  Emergency,
  SensorError
};

struct VitalSigns {
  uint8_t heartRate;
  uint16_t systolic;
  uint16_t diastolic;
  uint8_t riskScore;
  uint8_t spo2;
  uint8_t battery;
  float sensorQuality;
};

class DeviceUi {
public:
  explicit DeviceUi(TFT_eSPI& display);

  void begin();
  void showSafe(const VitalSigns& vitals);
  void showWarning(const VitalSigns& vitals, uint8_t countdownSeconds);
  void showEmergency(const VitalSigns& vitals);
  void showSensorError(const VitalSigns& vitals);

private:
  TFT_eSPI& tft;

  void clearScreen();
  void drawHeader(const char* status, uint16_t color);
  void drawSoftButton(const char* label, uint16_t color);
  void drawReadingCard(int16_t x, int16_t y, int16_t w, int16_t h, const char* label, const String& value, const char* unit, uint16_t valueColor);
  void drawCenteredText(const char* text, int16_t y, uint8_t textSize, uint16_t color);
  void drawRiskRing(uint8_t riskScore, uint16_t color);
};

