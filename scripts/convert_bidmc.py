from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "raw" / "bidmc"
OUTPUT = PROJECT_ROOT / "data" / "unified"
OUTPUT.mkdir(parents=True, exist_ok=True)
rows = []
for path in ROOT.rglob("*_Numerics.csv"):
    data = pd.read_csv(path)
    columns = {str(column).lower(): column for column in data.columns}

    def pick(*names):
        for name in names:
            if name in columns:
                return columns[name]
        return None

    heart_rate = pick("hr", "heart rate")
    spo2 = pick("spo2", "sp02", "oxygen saturation")
    if not (heart_rate or spo2):
        continue
    frame = pd.DataFrame({
        "timestamp": np.arange(len(data)),
        "subject_id": path.stem,
        "source_dataset": "bidmc",
        "heart_rate": pd.to_numeric(data[heart_rate], errors="coerce") if heart_rate else np.nan,
        "spo2": pd.to_numeric(data[spo2], errors="coerce") if spo2 else np.nan,
        "activity": "UNKNOWN", "fall_state": "NO_FALL", "physiology_state": "UNKNOWN",
    })
    rows.append(frame)
if rows:
    pd.concat(rows, ignore_index=True).to_csv(OUTPUT / "bidmc.csv", index=False)
else:
    print("No BIDMC numerics found.")
print("BIDMC conversion finished.")
