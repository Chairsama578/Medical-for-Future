# StrokeGuard AI v3 — Member 1
## AI + Edge AI Lead | Arduino UNO Q 2GB

StrokeGuard AI is a **research/prototype** wearable safety system. It combines:
- STM32U585 MCU: deterministic sensor sampling, local hardware safety/alert control.
- Qualcomm Dragonwing QRB2210 MPU: Debian Linux, Python AI inference, risk fusion, SOS/network services.
- Arduino Bridge / MessagePack RPC: Linux ↔ MCU communication.
- Local-first inference: the AI pipeline does not require Internet.
- B.E. FAST symptom workflow: a manual symptom confirmation path for suspected stroke.

> **Medical safety:** This software is not a medical device and does not diagnose stroke. A real suspected stroke is an emergency. The prototype must direct the user/caregiver to contact the local emergency service immediately when acute stroke warning signs are present. Thresholds and model outputs must be clinically validated before any real-world medical use.

## Hardware target

Verified from Arduino's current UNO Q documentation:
- Qualcomm Dragonwing QRB2210, quad-core Arm Cortex-A53, Linux/Debian
- STM32U585 Cortex-M33 MCU, Arduino Core on Zephyr
- 2 GB LPDDR4X + 16 GB eMMC for the 2GB SKU
- Wi-Fi 5 and Bluetooth 5.1
- Bridge/RPC between Linux and MCU

Official docs:
- https://docs.arduino.cc/hardware/uno-q
- https://docs.arduino.cc/resources/datasheets/ABX00162-ABX00173-datasheet.pdf

## Architecture

```text
                     STROKEGUARD AI
                           |
             +-------------+-------------+
             |                           |
      STM32U585 MCU                QRB2210 MPU
      REAL-TIME LAYER              EDGE AI LAYER
             |                           |
      +------+------+             +------+------+
      |      |      |             |      |      |
     IMU    PPG   BP*          Features  ML    SOS/API
      |      |      |             |      |      |
      +------+------+\            +------+------+
             |       \                   |
        sensor quality                  risk
             |                           |
             +-------- Bridge/RPC -------+
                         |
                   Safety Fusion
                         |
             +-----------+-----------+
             |           |           |
          NORMAL      WARNING      CRITICAL
                                     |
                               local alert
                                     |
                              BLE / Wi-Fi SOS
```

`BP*`: blood pressure requires a dedicated validated measurement method/module. Do not claim that BP is directly measured from IMU/PPG alone.

## Indicators

The prototype data contract supports:
- Heart rate (bpm)
- SpO2 (%)
- Systolic BP (mmHg, optional)
- Diastolic BP (mmHg, optional)
- Accelerometer X/Y/Z (g)
- Motion magnitude / jerk-derived features
- Sensor quality
- Battery percentage (optional)
- Manual B.E. FAST symptoms
- Manual SOS button

### B.E. FAST
The symptom workflow covers:
- B: Balance loss
- E: Eye/vision changes
- F: Face drooping
- A: Arm weakness
- S: Speech difficulty
- T: Time / symptom onset timestamp

A manual symptom flag must be treated as a high-priority emergency signal, not as an ML diagnosis.

## AI pipeline

```text
Sensor packet
  -> schema validation
  -> range + quality gate
  -> rolling window
  -> signal statistics / motion features
  -> normalization
  -> ML model
  -> calibrated risk score
  -> temporal persistence
  -> safety fusion
  -> NORMAL / WARNING / CRITICAL
  -> local alert + SOS event
```

The repository contains a synthetic dataset only to verify the software pipeline. It is **not clinical data** and its accuracy must not be presented as StrokeGuard performance.

## Project layout

```text
StrokeGuard_AI_v3_Member1/
├── src/strokeguard/
│   ├── ai/              # model, training, inference
│   ├── api/             # local HTTP API for UI/app integration
│   ├── bridge/          # UNO Q Bridge RPC client
│   ├── core/            # config, domain types
│   ├── safety/          # B.E. FAST + risk fusion + alert policy
│   └── sensors/         # simulator + sensor contract
├── arduino/StrokeGuardUNOQ/
│   ├── StrokeGuardUNOQ.ino
│   └── include/
├── scripts/
│   ├── generate_dataset.py
│   ├── train.py
│   ├── evaluate.py
│   └── run_demo.py
├── systemd/
│   └── strokeguard-ai.service
├── config/
│   └── config.example.yaml
├── tests/
├── requirements.txt
└── pyproject.toml
```

## Development on Windows / VS Code

Use Python 3.11+.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

$env:PYTHONPATH="src"

python scripts/generate_dataset.py
python scripts/train.py
python scripts/evaluate.py
python scripts/run_demo.py --scenario normal
python scripts/run_demo.py --scenario warning
python scripts/run_demo.py --scenario critical
python -m pytest -q
```

The Windows development mode uses the simulator. It does not require an UNO Q.

## Deployment on UNO Q Linux

On the UNO Q Linux side:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-msgpack

git clone <YOUR_REPOSITORY_URL>
cd StrokeGuard_AI_v3_Member1

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PYTHONPATH=$PWD/src
python scripts/run_demo.py --scenario normal
python -m strokeguard.api.server
```

For real Bridge operation, make sure `arduino-router` is running:

```bash
systemctl status arduino-router
sudo systemctl restart arduino-router
```

Do **not** open `/dev/ttyHS1` directly; Arduino reserves it for the Router/Bridge.

## Arduino side

Open `arduino/StrokeGuardUNOQ/StrokeGuardUNOQ.ino` in Arduino IDE 2+ or Arduino App Lab and upload it to the MCU side.

The sketch exposes:
- `get_sensor_snapshot`
- `set_local_alert`
- `clear_local_alert`
- `set_sensor_mode`
- `get_device_status`
- `manual_sos`

The default firmware is **SIMULATION mode** so the team can validate the whole Bridge/AI pipeline before attaching sensors.

When the exact sensor BOM is fixed, implement the `readRealSensors()` adapter without changing the Linux AI contract.

## Safety design

1. Manual SOS overrides ML.
2. B.E. FAST symptom confirmation overrides ML.
3. Sensor quality failure must never be silently converted to a medical-risk prediction.
4. ML predictions are temporally debounced/persisted.
5. Network failure must not disable local alerts.
6. AI is local-first; network is used only for optional notifications.
7. No medication, diagnosis, or treatment instruction is generated by this software.

## What Member 1 owns

- Data schema
- Preprocessing
- Feature engineering
- ML training/evaluation
- Model export
- Linux edge inference
- Risk fusion
- Safety policy
- Bridge integration
- Latency/resource benchmarking
- AI-to-MCU interface contract

## What remains hardware-dependent

The exact sensor drivers are intentionally isolated because the current board is known but the team's actual sensor modules are not yet specified. Once the team provides the exact PPG/SpO2, IMU and BP hardware part numbers, only the MCU sensor adapter needs to be replaced.

## v4 Upgrade Layer

Version 4 is a drop-in upgrade layer over the v3 runtime. It adds independent
activity/posture, fall, and physiology branches without changing the v3 sensor
contract or safety API:

```text
v3 sensor packets -> v4 window features -> activity/fall/physiology models
                  -> v4 SafetyFusion -> existing alerts/API integration
```

The v4 public datasets are not a synchronized multimodal clinical dataset.
Train each branch from its appropriate source and fuse predictions at runtime.
The datasets and benchmark results are for software validation only, not
clinical performance claims.

```powershell
python scripts/build_training_tables.py
python scripts/train_v4.py
```

See `docs/DATASET_MATRIX.md` and `config/v4.yaml` for the v4 data and safety
configuration.
