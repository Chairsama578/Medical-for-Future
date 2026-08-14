```markdown
# StrokeGuard AI — Medical for Future

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Arduino%20UNO%20Q-green.svg)](https://docs.arduino.cc/hardware/uno-q)
[![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Research / Prototype** wearable safety system for early stroke risk detection.  
> Runs fully local on Arduino UNO Q (Edge AI + real-time MCU).  
> Combines physiological signals, motion analysis, and the B.E. FAST symptom workflow.

---

> **Medical Safety Disclaimer**  
> This software is **not a medical device** and does **not diagnose stroke**.  
> A real suspected stroke is a medical emergency. The prototype must instruct the user/caregiver to contact local emergency services immediately when acute stroke warning signs appear.  
> All thresholds and model outputs must be clinically validated before any real-world medical use.

---

## Overview

StrokeGuard AI is an edge AI prototype designed for wearable stroke risk monitoring. It runs on the **Arduino UNO Q** board, combining:

- **STM32U585 MCU** — deterministic sensor sampling and local hardware safety/alert control
- **Qualcomm Dragonwing QRB2210 MPU** — Debian Linux, Python AI inference, risk fusion, and SOS services
- **Arduino Bridge / MessagePack RPC** — reliable Linux ↔ MCU communication
- **Local-first inference** — no internet required for the core AI pipeline
- **B.E. FAST** manual symptom confirmation path

The system produces three safety states: **NORMAL**, **WARNING**, and **CRITICAL**.

---

## Key Features

- Local-first AI inference (no cloud dependency)
- Real-time sensor quality gating
- B.E. FAST symptom workflow (Balance, Eyes, Face, Arm, Speech, Time)
- Manual SOS button with highest priority override
- Risk fusion with temporal persistence / debouncing
- Fall / activity / posture detection (v4 layer)
- Local HTTP API for UI / app integration
- ST7789 device UI (SAFE / WARNING / EMERGENCY states)
- Simulation mode for development without real sensors

---

## Architecture

```
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

> **Note:** `BP*` requires a dedicated validated blood-pressure module. Do not claim BP is derived from IMU/PPG alone.

---

## Hardware Target

**Arduino UNO Q (2 GB SKU)**

| Component              | Specification                          |
|------------------------|----------------------------------------|
| Application Processor  | Qualcomm Dragonwing QRB2210 (4× Cortex-A53) |
| MCU                    | STM32U585 (Cortex-M33)                 |
| Memory                 | 2 GB LPDDR4X + 16 GB eMMC              |
| Connectivity           | Wi-Fi 5 + Bluetooth 5.1                |
| OS                     | Debian Linux on MPU + Zephyr on MCU    |

Official documentation:
- [Arduino UNO Q Hardware](https://docs.arduino.cc/hardware/uno-q)
- [Datasheet](https://docs.arduino.cc/resources/datasheets/ABX00162-ABX00173-datasheet.pdf)

---

## Supported Indicators

| Signal                    | Description                          |
|---------------------------|--------------------------------------|
| Heart rate                | bpm                                  |
| SpO₂                      | %                                    |
| Systolic / Diastolic BP   | mmHg (optional, dedicated module)    |
| Accelerometer X/Y/Z       | g                                    |
| Motion magnitude / jerk   | derived features                     |
| Sensor quality            | quality gate                         |
| Battery                   | % (optional)                         |
| Manual B.E. FAST          | symptom flags                        |
| Manual SOS                | hardware button                      |

### B.E. FAST

- **B** — Balance loss  
- **E** — Eye / vision changes  
- **F** — Face drooping  
- **A** — Arm weakness  
- **S** — Speech difficulty  
- **T** — Time / symptom onset timestamp  

A manual symptom flag is treated as a **high-priority emergency signal**, not as an ML diagnosis.

---

## AI Pipeline

```
Sensor packet
  → schema validation
  → range + quality gate
  → rolling window
  → signal statistics / motion features
  → normalization
  → ML model
  → calibrated risk score
  → temporal persistence
  → safety fusion
  → NORMAL / WARNING / CRITICAL
  → local alert + SOS event
```

The repository currently contains **synthetic data only** for pipeline verification. It is **not clinical data**.

---

## Safety Design Principles

1. Manual SOS **overrides** ML  
2. B.E. FAST symptom confirmation **overrides** ML  
3. Sensor quality failure is **never** silently converted into a medical-risk prediction  
4. ML predictions are temporally debounced / persisted  
5. Network failure must **not** disable local alerts  
6. AI is local-first; network is used only for optional notifications  
7. No medication, diagnosis, or treatment instructions are generated  

---

## Project Structure

```
Medical-for-Future/
├── src/strokeguard/
│   ├── ai/                 # model, training, inference
│   ├── api/                # local HTTP API
│   ├── bridge/             # UNO Q Bridge RPC client
│   ├── core/               # config & domain types
│   ├── safety/             # B.E. FAST + risk fusion + alert policy
│   └── sensors/            # simulator + sensor contract
├── arduino/StrokeGuardUNOQ/
│   ├── StrokeGuardUNOQ.ino
│   └── include/
├── Code UI/                # ST7789 device UI
├── scripts/
│   ├── generate_dataset.py
│   ├── train.py
│   ├── evaluate.py
│   ├── run_demo.py
│   ├── build_training_tables.py
│   └── train_v4.py
├── config/
├── docs/                   # detailed documentation
├── models/
├── systemd/
├── tests/
├── requirements.txt
└── pyproject.toml
```

---

## Quick Start (Development on Windows / VS Code)

Requirements: **Python 3.11+**

```bash
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

Windows development uses the **simulator** — no physical UNO Q required.

---

## Deployment on Arduino UNO Q (Linux)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-msgpack

git clone https://github.com/Chairsama578/Medical-for-Future.git
cd Medical-for-Future

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PYTHONPATH=$PWD/src
python scripts/run_demo.py --scenario normal
python -m strokeguard.api.server
```

Ensure the Arduino router is running:

```bash
systemctl status arduino-router
sudo systemctl restart arduino-router
```

> Do **not** open `/dev/ttyHS1` directly — it is reserved for the Arduino Router/Bridge.

---

## Arduino Firmware

Open `arduino/StrokeGuardUNOQ/StrokeGuardUNOQ.ino` in Arduino IDE 2+ or Arduino App Lab and upload to the MCU.

Exposed RPC methods:
- `get_sensor_snapshot`
- `set_local_alert` / `clear_local_alert`
- `set_sensor_mode`
- `get_device_status`
- `manual_sos`

Default firmware runs in **SIMULATION mode** so the full pipeline can be validated before real sensors are attached.

---

## Device UI (ST7789)

Located in `Code UI/`.

- Display: 1.83" IPS LCD, ST7789, 240×280, SPI
- Library: TFT_eSPI

UI states:
1. **SAFE** — shows vitals + AI risk, SOS button
2. **WARNING** — abnormal values + countdown, “I’m Safe” button
3. **EMERGENCY** — SOS active, family/location notification

See `Code UI/README.md` for setup details.

---

## v4 Upgrade Layer

Version 4 is a drop-in upgrade that adds independent activity/posture, fall, and physiology branches without changing the v3 sensor contract or safety API.

```bash
python scripts/build_training_tables.py
python scripts/train_v4.py
```

See:
- `docs/DATASET_MATRIX.md`
- `config/v4.yaml`
- `docs/runtime_v4_integration.md`

---

## Documentation

| Document | Description |
|----------|-------------|
| [DEMO_FLOW.md](docs/DEMO_FLOW.md) | Demo scenario flow |
| [EMERGENCY_FLOW.md](docs/EMERGENCY_FLOW.md) | Emergency handling logic |
| [DATASET_MATRIX.md](docs/DATASET_MATRIX.md) | Dataset overview (v4) |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Detailed deployment guide |
| [AI_CONTRACT.md](docs/AI_CONTRACT.md) | AI interface contract |
| [ARDUINO_AI_INTERFACE.md](docs/ARDUINO_AI_INTERFACE.md) | MCU ↔ Linux interface |

---

## Known Limitations

- Currently uses **synthetic data only** — not clinical performance data
- Blood pressure requires a dedicated validated module
- Exact sensor BOM (PPG, IMU, BP) is not yet finalized
- No clinical validation has been performed
- Not intended for real patient monitoring or diagnosis

---

## Team Responsibilities (Member 1 — AI + Edge AI)

- Data schema & preprocessing
- Feature engineering
- ML training / evaluation / export
- Linux edge inference
- Risk fusion & safety policy
- Bridge integration
- Latency & resource benchmarking
- AI ↔ MCU interface contract

Hardware sensor drivers remain isolated until the final BOM is confirmed.

---

## Roadmap

- [x] v3 core pipeline (simulator + Bridge)
- [x] Safety fusion + B.E. FAST
- [x] Local HTTP API
- [x] ST7789 UI prototype
- [x] v4 activity / fall / physiology branches
- [ ] Real sensor integration (final BOM)
- [ ] End-to-end latency & power benchmarking
- [ ] Clinical data collection & validation
- [ ] Mobile companion app

---

## License

This project is released under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- Arduino UNO Q platform and documentation
- Public datasets used for v4 software validation (see `docs/DATASET_MATRIX.md`)

---

**StrokeGuard AI is a research prototype. Always call emergency services in case of suspected stroke.**
```
