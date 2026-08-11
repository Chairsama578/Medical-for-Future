from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from strokeguard_v4.features import make_windows

UNIFIED = PROJECT_ROOT / "data" / "unified"
TRAINING = UNIFIED / "training"
TRAINING.mkdir(parents=True, exist_ok=True)

frames = []
for path in UNIFIED.glob("*.csv"):
    if path.name.startswith("cves_"):
        continue
    try:
        data = pd.read_csv(path)
        for column in [
            "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z",
            "heart_rate", "spo2", "sbp", "dbp",
        ]:
            if column not in data:
                data[column] = float("nan")
        for column in [
            "activity", "fall_state", "physiology_state", "subject_id",
            "source_dataset",
        ]:
            if column not in data:
                data[column] = "UNKNOWN"
        features, metadata = make_windows(data, 40, 20)
        if not features.empty:
            frames.append(pd.concat([features, metadata.reset_index(drop=True)], axis=1))
    except Exception as error:
        print("SKIP", path, error)

if not frames:
    raise SystemExit("No windowed data. Run converters first.")

tables = pd.concat(frames, ignore_index=True)
tables.to_csv(TRAINING / "windows_all.csv", index=False)
tables[tables.activity != "UNKNOWN"].to_csv(TRAINING / "activity.csv", index=False)
tables[tables.fall_state.isin(["FALL", "NO_FALL"])].to_csv(
    TRAINING / "fall.csv", index=False
)
tables[tables.physiology_state.isin(["NORMAL", "ABNORMAL"])].to_csv(
    TRAINING / "physiology.csv", index=False
)
print("Training tables written.")
