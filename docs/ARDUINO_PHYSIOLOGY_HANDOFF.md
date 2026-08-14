# Arduino Physiology Handoff

Arduino sends one JSON object per line over USB Serial at 115200 baud. Python
runs physiology validation and inference on the laptop/Edge runtime.

```json
{"timestamp":1723456789000,"heart_rate_bpm":82,"spo2_pct":98,"systolic_bp_mmhg":null,"diastolic_bp_mmhg":null,"accel_x_g":0.02,"accel_y_g":0.98,"accel_z_g":0.05,"sensor_quality":1.0,"battery_pct":87,"sos_pressed":false}
```

BP fields must stay `null` when BP hardware is unavailable. They must never be
filled from HR or SpO2.

The current runtime uses a 40-sample window at approximately 5 Hz. It produces:

```text
NORMAL
WARNING
CRITICAL
SENSOR_ERROR
```

Physiology states are:

```text
NORMAL
PHYSIO_WARNING
PHYSIO_CRITICAL
SENSOR_ERROR
UNKNOWN
```

Manual SOS and B.E. FAST are immediate `CRITICAL` paths. Invalid or missing HR,
SpO2, or IMU values result in `SENSOR_ERROR`/`UNKNOWN`; values are not silently
repaired.

The current physiology engine is rule-based. BIDMC is not locally installed,
and no physiology ML model is trained. StrokeGuard does not diagnose stroke.
