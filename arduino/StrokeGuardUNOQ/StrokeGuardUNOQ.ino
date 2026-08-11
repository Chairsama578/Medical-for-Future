#include <Arduino_RouterBridge.h>

/*
 * StrokeGuard AI - UNO Q MCU side
 * STM32U585 / Arduino Core on Zephyr
 *
 * Default mode = SIMULATION.
 * Replace readRealSensors() when the exact PPG/SpO2/IMU/BP modules are selected.
 *
 * IMPORTANT:
 * - Do not open Serial1 for Bridge traffic; arduino-router owns it.
 * - Bridge RPC handlers must stay short. provide_safe() is used for hardware state.
 */

enum SensorMode : uint8_t {
  MODE_SIMULATION = 0,
  MODE_REAL = 1
};

SensorMode sensorMode = MODE_SIMULATION;
String localAlert = "OFF";
bool sosLatched = false;
unsigned long lastSampleMs = 0;
uint32_t sampleCounter = 0;

struct SensorSnapshot {
  float hr;
  float spo2;
  float sbp;
  float dbp;
  float ax;
  float ay;
  float az;
  float quality;
  float battery;
  bool sos;
};

SensorSnapshot readSimulation() {
  float phase = (sampleCounter % 100) / 100.0f;
  SensorSnapshot s;
  s.hr = 72.0f + 2.0f * sinf(phase * 6.28318f);
  s.spo2 = 98.0f;
  s.sbp = 120.0f;
  s.dbp = 80.0f;
  s.ax = 0.02f;
  s.ay = -0.01f;
  s.az = 1.00f;
  s.quality = 0.98f;
  s.battery = 85.0f;
  s.sos = sosLatched;
  return s;
}

SensorSnapshot readRealSensors() {
  /*
   * Hardware adapter boundary.
   *
   * Implement ONLY this function after the team confirms exact sensor BOM.
   *
   * Required fields:
   *   hr     -> heart rate bpm
   *   spo2   -> oxygen saturation %
   *   sbp    -> systolic BP (or NAN if not available)
   *   dbp    -> diastolic BP (or NAN if not available)
   *   ax/ay/az -> acceleration in g
   *   quality -> 0..1
   *   battery -> 0..100 or NAN
   *
   * Do not infer blood pressure from IMU alone.
   */
  return readSimulation();
}

SensorSnapshot readSensors() {
  return sensorMode == MODE_REAL ? readRealSensors() : readSimulation();
}

String sensorSnapshotJson() {
  SensorSnapshot s = readSensors();
  sampleCounter++;

  String out = "{";
  out += "\"timestamp_ms\":" + String(millis());
  out += ",\"heart_rate_bpm\":" + String(s.hr, 2);
  out += ",\"spo2_pct\":" + String(s.spo2, 2);
  out += ",\"systolic_bp_mmhg\":" + String(s.sbp, 2);
  out += ",\"diastolic_bp_mmhg\":" + String(s.dbp, 2);
  out += ",\"accel_x_g\":" + String(s.ax, 4);
  out += ",\"accel_y_g\":" + String(s.ay, 4);
  out += ",\"accel_z_g\":" + String(s.az, 4);
  out += ",\"sensor_quality\":" + String(s.quality, 3);
  out += ",\"battery_pct\":" + String(s.battery, 1);
  out += ",\"sos_pressed\":" + String(s.sos ? "true" : "false");
  out += "}";
  return out;
}

String getSensorSnapshot() {
  return sensorSnapshotJson();
}

void setLocalAlertSafe(String state) {
  localAlert = state;

  if (state == "CRITICAL" || state == "SOS") {
    // Replace with actual buzzer/LED driver after hardware wiring is fixed.
    digitalWrite(LED_BUILTIN, LOW);
  } else if (state == "WARNING") {
    digitalWrite(LED_BUILTIN, LOW);
  } else {
    digitalWrite(LED_BUILTIN, HIGH);
  }
}

void setLocalAlert(String state) {
  setLocalAlertSafe(state);
}

void clearLocalAlert() {
  sosLatched = false;
  setLocalAlertSafe("OFF");
}

void setSensorMode(String mode) {
  if (mode == "REAL") sensorMode = MODE_REAL;
  else sensorMode = MODE_SIMULATION;
}

String getDeviceStatus() {
  String out = "{";
  out += "\"board\":\"Arduino UNO Q 2GB\",";
  out += "\"mpu\":\"Qualcomm Dragonwing QRB2210\",";
  out += "\"mcu\":\"STM32U585\",";
  out += "\"sensor_mode\":\"" + String(sensorMode == MODE_REAL ? "REAL" : "SIMULATION") + "\",";
  out += "\"alert\":\"" + localAlert + "\",";
  out += "\"sos_latched\":" + String(sosLatched ? "true" : "false");
  out += "}";
  return out;
}

bool manualSOS() {
  sosLatched = true;
  setLocalAlertSafe("SOS");
  return true;
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Bridge.begin();

  Bridge.provide("get_sensor_snapshot", getSensorSnapshot);
  Bridge.provide_safe("set_local_alert", setLocalAlert);
  Bridge.provide_safe("clear_local_alert", clearLocalAlert);
  Bridge.provide_safe("set_sensor_mode", setSensorMode);
  Bridge.provide("get_device_status", getDeviceStatus);
  Bridge.provide_safe("manual_sos", manualSOS);

  Serial.begin(115200);
}

void loop() {
  // Real sensor acquisition can be scheduled here.
  if (millis() - lastSampleMs >= 200) {
    lastSampleMs = millis();
  }
}
