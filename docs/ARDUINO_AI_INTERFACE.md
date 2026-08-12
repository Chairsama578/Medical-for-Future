# Arduino AI Interface

This document is the Member 2 handoff for connecting Arduino sensor data to
the existing Python runtime.

## Transport

```text
Arduino -> USB Serial -> Python bridge
Baud: 115200
Format: one JSON object per line
```

The Python bridge converts the JSON object to the existing v3 `SensorPacket`.
No Arduino firmware changes are required by this interface.

## Input Packet

```json
{"timestamp":1723456789000,"heart_rate_bpm":82,"spo2_pct":98,"systolic_bp_mmhg":null,"diastolic_bp_mmhg":null,"accel_x_g":0.02,"accel_y_g":0.98,"accel_z_g":0.05,"sensor_quality":1.0,"battery_pct":87,"sos_pressed":false}
```

Required fields:

| Field | Unit | Range | Meaning |
|---|---|---|---|
| `timestamp` | Unix milliseconds recommended | finite numeric | Packet timestamp |
| `accel_x_g` | g | -16 to 16 | IMU X axis |
| `accel_y_g` | g | -16 to 16 | IMU Y axis |
| `accel_z_g` | g | -16 to 16 | IMU Z axis |

Optional fields:

| Field | Unit | Range | Meaning |
|---|---|---|---|
| `heart_rate_bpm` | BPM | 30 to 220 | Real HR sensor value |
| `spo2_pct` | percent | 50 to 100 | Real SpO2 sensor value |
| `systolic_bp_mmhg` | mmHg | 50 to 300 | Actual BP sensor only |
| `diastolic_bp_mmhg` | mmHg | 20 to 200 | Actual BP sensor only |
| `sensor_quality` | 0 to 1 | 0 to 1 | Hardware quality estimate |
| `battery_pct` | percent | 0 to 100 | Battery reading |
| `sos_pressed` | boolean | true/false | Manual SOS button |

BP must be `null` or omitted when no BP hardware is connected. Do not send
zero as a substitute for unavailable BP.

Real sensor data must be clearly distinguished from demo data. The simulator
uses the same JSON shape but is marked in its output as synthetic.

## Runtime Behavior

The runtime keeps a 40-sample rolling window. Before the window is ready,
Activity and Physiology report warm-up/unknown behavior while SOS and B.E.
FAST remain immediate safety paths.

Invalid or missing required values produce `SENSOR_ERROR` or `UNKNOWN`; they
are not silently replaced with physiological values.

The Fall branch currently reports:

```text
fall_model_status: NOT_AVAILABLE
fall_detected: false
fall_confidence: 0.0
```

Activity is context only. It does not diagnose stroke. Physiology is an
engineering risk indicator, not a clinical diagnosis.
