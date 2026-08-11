from pathlib import Path
import re

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "raw" / "upfall"
OUTPUT = PROJECT_ROOT / "data" / "unified"
OUTPUT.mkdir(parents=True, exist_ok=True)
ACTIVITY = {
    1: "FALL", 2: "FALL", 3: "FALL", 4: "FALL", 5: "FALL",
    6: "WALKING", 7: "STANDING", 8: "PICKING_OBJECT", 9: "SITTING",
    10: "JUMPING", 11: "LYING",
}
rows = []
for path in ROOT.rglob("*.csv"):
    try:
        data = pd.read_csv(path)
    except Exception:
        continue
    columns = {str(column).lower(): column for column in data.columns}

    def pick(keys):
        for key in keys:
            if key in columns:
                return columns[key]
        for column in columns:
            if any(key in column for key in keys):
                return columns[column]
        return None

    axes = [pick(keys) for keys in [["accel_x", "acc_x", "x"], ["accel_y", "acc_y", "y"], ["accel_z", "acc_z", "z"]]]
    if not all(axes):
        continue
    gyro = [pick(keys) for keys in [["gyro_x", "gyr_x"], ["gyro_y", "gyr_y"], ["gyro_z", "gyr_z"]]]
    frame = pd.DataFrame({
        "accel_x": data[axes[0]], "accel_y": data[axes[1]], "accel_z": data[axes[2]],
        "gyro_x": data[gyro[0]] if gyro[0] else np.nan,
        "gyro_y": data[gyro[1]] if gyro[1] else np.nan,
        "gyro_z": data[gyro[2]] if gyro[2] else np.nan,
    })
    subject = re.search(r"(?:subject|user|subj)[_-]?(\d+)", str(path), re.I)
    activity = re.search(r"(?:activity|act)[_-]?(\d+)", str(path), re.I)
    activity_id = int(activity.group(1)) if activity else -1
    frame["subject_id"] = subject.group(1) if subject else "unknown"
    frame["source_dataset"] = "upfall"
    frame["activity"] = ACTIVITY.get(activity_id, "UNKNOWN")
    frame["fall_state"] = "FALL" if activity_id in range(1, 6) else "NO_FALL"
    frame["physiology_state"] = "UNKNOWN"
    rows.append(frame)
if rows:
    pd.concat(rows, ignore_index=True).to_csv(OUTPUT / "upfall.csv", index=False)
else:
    print("No compatible UP-Fall CSV found.")
print("UP-Fall conversion finished.")
