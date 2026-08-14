# Member 2 Arduino Handoff

## Architecture

```text
Arduino
  -> accelerometer, heart-rate, SpO2, optional BP, battery, SOS
  -> one JSON packet per line
  -> USB Serial at 115200 baud
  -> Python bridge
  -> StrokeGuard AI runtime
  -> compact risk JSON
  -> PC/display or future Arduino response handling
```

Arduino acquires sensors. Python on the laptop runs Activity AI and the
Physiology Risk Engine. Arduino does not run the RandomForest model in this
demo.

## Exact Input Packet

```json
{"timestamp":1723456789000,"heart_rate_bpm":82,"spo2_pct":98,"systolic_bp_mmhg":null,"diastolic_bp_mmhg":null,"accel_x_g":0.02,"accel_y_g":0.98,"accel_z_g":0.05,"sensor_quality":1.0,"battery_pct":87,"sos_pressed":false}
```

If BP is unavailable, send the same packet with:

```json
{"systolic_bp_mmhg":null,"diastolic_bp_mmhg":null}
```

Do not send zero for unavailable BP.

## Field Rules

| Field | Required | Unit/range |
|---|---|---|
| `timestamp` | Yes | Unix milliseconds, finite numeric |
| `heart_rate_bpm` | Recommended | 30-220 BPM, or `null` if unavailable |
| `spo2_pct` | Recommended | 50-100%, or `null` if unavailable |
| `systolic_bp_mmhg` | Optional | 50-300 mmHg, actual BP sensor only |
| `diastolic_bp_mmhg` | Optional | 20-200 mmHg, actual BP sensor only |
| `accel_x_g` | Yes | finite, approximately -16 to 16 g |
| `accel_y_g` | Yes | finite, approximately -16 to 16 g |
| `accel_z_g` | Yes | finite, approximately -16 to 16 g |
| `sensor_quality` | Recommended | 0.0-1.0 |
| `battery_pct` | Optional | 0-100% |
| `sos_pressed` | Recommended | boolean |

Real sensor values must be used for hardware. The simulator and files under
`data/demo/` are demo data only.

## Rate and Window

Send packets at approximately 5 Hz for the current 40-sample runtime window.
That produces an 8-second window. The laptop performs inference after warm-up.
The Arduino is not required to run Activity AI.

## Run Commands

Hardware:

```powershell
$env:PYTHONPATH="src"
python scripts/run_hardware_demo.py --port COM5 --baud 115200
```

Simulation:

```powershell
python scripts/run_hardware_demo.py --simulate normal
python scripts/run_hardware_demo.py --simulate critical
python scripts/run_hardware_demo.py --simulate sos
python scripts/run_hardware_demo.py --simulate sensor_error
```

## Fall Limitation

Fall AI is not available:

```text
fall_model_status = NOT_AVAILABLE
fall_detected = false
```

The current demo must not claim AI fall detection.
