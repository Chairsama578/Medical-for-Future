from pathlib import Path
import re

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "raw" / "physiology" / "bidmc" / "bidmc_csv"
OUTPUT = PROJECT_ROOT / "data" / "unified"
OUTPUT.mkdir(parents=True, exist_ok=True)
rows = []
for path in ROOT.rglob("*_Numerics.csv"):
    data = pd.read_csv(path)
    columns = {str(column).strip().lower(): column for column in data.columns}

    def pick(*names):
        for name in names:
            if name in columns:
                return columns[name]
        return None

    heart_rate = pick("hr", "heart rate")
    spo2 = pick("spo2", "sp02", "oxygen saturation")
    respiration = pick("resp", "respiratory rate")
    timestamp = pick("time [s]", "time")
    if not (heart_rate or spo2 or respiration):
        continue
    record_match = re.search(r"bidmc[_-]?(\d+)", path.name, re.I)
    record_id = record_match.group(1) if record_match else path.stem
    frame = pd.DataFrame({
        "timestamp": pd.to_numeric(data[timestamp], errors="coerce") if timestamp else np.arange(len(data)),
        "record_id": f"bidmc_{record_id}",
        "subject_id": f"bidmc_{record_id}",
        "source_dataset": "bidmc",
        "source_sample_rate_hz": 1.0,
        "heart_rate_bpm": pd.to_numeric(data[heart_rate], errors="coerce") if heart_rate else np.nan,
        "spo2_pct": pd.to_numeric(data[spo2], errors="coerce") if spo2 else np.nan,
        "respiration_rate": pd.to_numeric(data[respiration], errors="coerce") if respiration else np.nan,
        "systolic_bp_mmhg": np.nan,
        "diastolic_bp_mmhg": np.nan,
        "ppg": np.nan,
        "ecg": np.nan,
        "sensor_quality": 1.0,
        "physiology_state": "UNKNOWN",
    })
    rows.append(frame)
if rows:
    pd.concat(rows, ignore_index=True).to_csv(OUTPUT / "bidmc_physiology.csv", index=False)
else:
    print("No BIDMC numerics found.")
print("BIDMC conversion finished.")
