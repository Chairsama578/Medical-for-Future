# UNO Q MCU firmware

## Upload
Use Arduino IDE 2+ or Arduino App Lab. Select the UNO Q board and upload the sketch to the MCU.

## Bridge rule
`Serial1` and `/dev/ttyHS1` belong to `arduino-router`. Do not open them yourself.

## Current state
The firmware is deliberately in simulation mode until the team confirms:
1. exact IMU part number
2. exact PPG/SpO2 part number
3. exact BP measurement module
4. battery gauge
5. buzzer/LED wiring
6. SOS button GPIO

## Sensor contract
The Linux side expects a JSON object with:
`timestamp_ms, heart_rate_bpm, spo2_pct, systolic_bp_mmhg, diastolic_bp_mmhg, accel_x_g, accel_y_g, accel_z_g, sensor_quality, battery_pct, sos_pressed`.

Do not change the field names without updating the Python domain model.
