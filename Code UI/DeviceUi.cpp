#include "DeviceUi.h"

namespace {
constexpr int16_t SCREEN_W = 240;
constexpr int16_t SCREEN_H = 280;
constexpr int16_t PADDING = 10;

constexpr uint16_t COLOR_BG = TFT_BLACK;
constexpr uint16_t COLOR_PANEL = 0x1082;
constexpr uint16_t COLOR_LINE = 0x39E7;
constexpr uint16_t COLOR_TEXT = TFT_WHITE;
constexpr uint16_t COLOR_MUTED = 0x9CF3;
constexpr uint16_t COLOR_SAFE = 0x05EE;
constexpr uint16_t COLOR_WARNING = 0xFD20;
constexpr uint16_t COLOR_DANGER = 0xF986;
constexpr uint16_t COLOR_BLUE = 0x351F;
}

DeviceUi::DeviceUi(TFT_eSPI& display) : tft(display) {}

void DeviceUi::begin() {
  tft.init();
  tft.setRotation(0);
  tft.fillScreen(COLOR_BG);
  tft.setTextDatum(TL_DATUM);
  tft.setTextWrap(false, false);
}

void DeviceUi::showSafe(const VitalSigns& vitals) {
  clearScreen();
  drawHeader("SAFE", COLOR_SAFE);

  drawReadingCard(10, 42, 105, 72, "HR", String(vitals.heartRate), "BPM", COLOR_SAFE);
  drawReadingCard(125, 42, 105, 72, "AI RISK", String(vitals.riskScore) + "%", "LOW", COLOR_SAFE);
  drawReadingCard(10, 124, 220, 72, "BLOOD PRESSURE", String(vitals.systolic) + "/" + String(vitals.diastolic), "mmHg", COLOR_BLUE);

  drawSoftButton("SOS", COLOR_DANGER);
  tft.setTextColor(COLOR_MUTED, COLOR_BG);
  tft.drawCentreString("Monitoring active", SCREEN_W / 2, 254, 1);
}

void DeviceUi::showWarning(const VitalSigns& vitals, uint8_t countdownSeconds) {
  clearScreen();
  drawHeader("WARNING", COLOR_WARNING);

  drawCenteredText("WARNING", 42, 3, COLOR_WARNING);
  drawRiskRing(vitals.riskScore, COLOR_WARNING);

  tft.setTextColor(COLOR_TEXT, COLOR_BG);
  tft.drawCentreString("Abnormal BP/HR", SCREEN_W / 2, 148, 2);
  tft.drawCentreString("Are you safe?", SCREEN_W / 2, 171, 2);

  tft.setTextColor(COLOR_TEXT, COLOR_BG);
  tft.drawCentreString("SOS in " + String(countdownSeconds) + "s", SCREEN_W / 2, 197, 2);

  drawSoftButton("I'M SAFE", COLOR_SAFE);
}

void DeviceUi::showEmergency(const VitalSigns& vitals) {
  clearScreen();
  drawHeader("EMERGENCY", COLOR_DANGER);

  drawCenteredText("SOS", 48, 4, COLOR_DANGER);
  tft.setTextColor(COLOR_TEXT, COLOR_BG);
  tft.drawCentreString("Emergency detected", SCREEN_W / 2, 92, 2);

  tft.fillRoundRect(18, 120, 204, 84, 8, COLOR_PANEL);
  tft.drawRoundRect(18, 120, 204, 84, 8, COLOR_LINE);
  tft.setTextColor(COLOR_TEXT, COLOR_PANEL);
  tft.drawString("OK Family notified", 30, 132, 2);
  tft.drawString("OK Location shared", 30, 158, 2);
  tft.drawString("OK Help requested", 30, 184, 2);

  drawSoftButton("I'M SAFE", COLOR_SAFE);
}

void DeviceUi::clearScreen() {
  tft.fillScreen(COLOR_BG);
}

void DeviceUi::drawHeader(const char* status, uint16_t color) {
  tft.fillRect(0, 0, SCREEN_W, 32, COLOR_BG);
  tft.drawFastHLine(PADDING, 31, SCREEN_W - (PADDING * 2), COLOR_LINE);
  tft.setTextColor(color, COLOR_BG);
  tft.drawString(status, PADDING, 8, 2);
  tft.setTextColor(COLOR_MUTED, COLOR_BG);
  tft.drawRightString("LIVE", SCREEN_W - PADDING, 8, 2);
}

void DeviceUi::drawSoftButton(const char* label, uint16_t color) {
  tft.fillRoundRect(10, 224, 220, 34, 8, color);
  tft.setTextColor(COLOR_TEXT, color);
  tft.drawCentreString(label, SCREEN_W / 2, 233, 2);
}

void DeviceUi::drawReadingCard(int16_t x, int16_t y, int16_t w, int16_t h, const char* label, const String& value, const char* unit, uint16_t valueColor) {
  tft.fillRoundRect(x, y, w, h, 8, COLOR_PANEL);
  tft.drawRoundRect(x, y, w, h, 8, COLOR_LINE);

  tft.setTextColor(COLOR_MUTED, COLOR_PANEL);
  tft.drawString(label, x + 8, y + 8, 1);

  tft.setTextColor(valueColor, COLOR_PANEL);
  tft.drawString(value, x + 8, y + 26, 4);

  tft.setTextColor(COLOR_MUTED, COLOR_PANEL);
  tft.drawString(unit, x + 8, y + h - 17, 1);
}

void DeviceUi::drawCenteredText(const char* text, int16_t y, uint8_t textSize, uint16_t color) {
  tft.setTextColor(color, COLOR_BG);
  tft.setTextSize(textSize);
  tft.drawCentreString(text, SCREEN_W / 2, y, 1);
  tft.setTextSize(1);
}

void DeviceUi::drawRiskRing(uint8_t riskScore, uint16_t color) {
  int16_t cx = SCREEN_W / 2;
  int16_t cy = 102;
  int16_t r = 32;

  tft.drawCircle(cx, cy, r, color);
  tft.drawCircle(cx, cy, r - 1, color);
  tft.drawCircle(cx, cy, r - 2, color);
  tft.drawCircle(cx, cy, r - 3, color);

  tft.setTextColor(COLOR_TEXT, COLOR_BG);
  tft.drawCentreString(String(riskScore) + "%", cx, cy - 10, 4);
}
