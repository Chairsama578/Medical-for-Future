#pragma once

#include <Arduino.h>
#include <WiFiClient.h>
#include "DeviceUi.h"

class ApiClient {
public:
  ApiClient(const char* host, uint16_t port);

  bool connectWiFi(const char* ssid, const char* password);
  bool isConnected();
  bool checkHealth();
  bool fetchSensorData(VitalSigns& vitals, DeviceState& state, bool& emergency);
  bool triggerSOS();

private:
  WiFiClient client;
  const char* apiHost;
  uint16_t apiPort;

  String httpGet(const char* path);
  String httpPost(const char* path, const char* body = nullptr);
  DeviceState mapState(const String& stateStr);
};
