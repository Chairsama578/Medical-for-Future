#include "ApiClient.h"
#include <ArduinoJson.h>

ApiClient::ApiClient(const char* host, uint16_t port)
  : apiHost(host), apiPort(port) {}

bool ApiClient::connectWiFi(const char* ssid, const char* password) {
  WiFi.begin(ssid, password);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - start > 15000) return false;
    delay(250);
  }
  return true;
}

bool ApiClient::isConnected() {
  return WiFi.status() == WL_CONNECTED;
}

String ApiClient::httpGet(const char* path) {
  if (!client.connect(apiHost, apiPort)) return "";

  client.print("GET ");
  client.print(path);
  client.println(" HTTP/1.1");
  client.print("Host: ");
  client.println(apiHost);
  client.println("Connection: close");
  client.println();

  unsigned long timeout = millis() + 3000;
  while (client.connected() && millis() < timeout) {
    if (client.available()) {
      String response = "";
      bool headersEnded = false;
      while (client.connected() || client.available()) {
        String line = client.readStringUntil('\n');
        if (!headersEnded) {
          if (line == "\r" || line == "") {
            headersEnded = true;
            continue;
          }
        } else {
          response += line;
        }
        if (millis() > timeout) break;
      }
      client.stop();
      return response;
    }
  }
  client.stop();
  return "";
}

String ApiClient::httpPost(const char* path, const char* body) {
  if (!client.connect(apiHost, apiPort)) return "";

  client.print("POST ");
  client.print(path);
  client.println(" HTTP/1.1");
  client.print("Host: ");
  client.println(apiHost);
  client.println("Content-Type: application/json");
  if (body) {
    client.print("Content-Length: ");
    client.println(strlen(body));
  }
  client.println("Connection: close");
  client.println();

  if (body) {
    client.print(body);
  }

  unsigned long timeout = millis() + 3000;
  while (client.connected() && millis() < timeout) {
    if (client.available()) {
      String response = "";
      bool headersEnded = false;
      while (client.connected() || client.available()) {
        String line = client.readStringUntil('\n');
        if (!headersEnded) {
          if (line == "\r" || line == "") {
            headersEnded = true;
            continue;
          }
        } else {
          response += line;
        }
        if (millis() > timeout) break;
      }
      client.stop();
      return response;
    }
  }
  client.stop();
  return "";
}

bool ApiClient::checkHealth() {
  String response = httpGet("/health");
  if (response.length() == 0) return false;

  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, response);
  if (error) return false;

  const char* status = doc["status"];
  return status && strcmp(status, "ok") == 0;
}

bool ApiClient::fetchSensorData(VitalSigns& vitals, DeviceState& state, bool& emergency) {
  String response = httpGet("/sensor");
  if (response.length() == 0) return false;

  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, response);
  if (error) return false;

  JsonObject sensor = doc["sensor"];
  JsonObject decision = doc["decision"];

  if (sensor.isNull() || decision.isNull()) return false;

  vitals.heartRate = sensor["heart_rate_bpm"].as<uint8_t>();
  vitals.systolic = sensor["systolic_bp_mmhg"].as<uint16_t>();
  vitals.diastolic = sensor["diastolic_bp_mmhg"].as<uint16_t>();
  vitals.spo2 = sensor["spo2_pct"].as<uint8_t>();
  vitals.battery = sensor["battery_pct"].as<uint8_t>();
  vitals.sensorQuality = sensor["sensor_quality"].as<float>();

  float score = decision["score"].as<float>();
  vitals.riskScore = (uint8_t)(score * 100.0f);

  const char* stateStr = decision["state"];
  state = mapState(String(stateStr));

  emergency = decision["emergency"].as<bool>();

  return true;
}

bool ApiClient::triggerSOS() {
  String response = httpPost("/sos");
  if (response.length() == 0) return false;

  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, response);
  if (error) return false;

  return doc["emergency"].as<bool>();
}

DeviceState ApiClient::mapState(const String& stateStr) {
  if (stateStr == "NORMAL") return DeviceState::Safe;
  if (stateStr == "WARNING") return DeviceState::Warning;
  if (stateStr == "CRITICAL") return DeviceState::Emergency;
  if (stateStr == "SENSOR_ERROR") return DeviceState::SensorError;
  return DeviceState::Safe;
}
