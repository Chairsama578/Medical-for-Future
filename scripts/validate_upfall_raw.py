"""Read-only inspection of a manually acquired UP-Fall dataset."""

from pathlib import Path
import re
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "raw" / "upfall"
SUBJECT_PATTERN = re.compile(r"(?:subject|user|subj)[_-]?(\d+)", re.I)
ACTIVITY_PATTERN = re.compile(r"(?:activity|act)[_-]?(\d+)", re.I)


def axis_column(columns, axis, kind):
    normalized = {str(column).strip().lower(): column for column in columns}
    candidates = [
        f"{kind}_{axis}", f"{kind[:3]}_{axis}", f"{kind}{axis}", axis,
    ]
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    return None


def inspect_csv(path):
    header = pd.read_csv(path, nrows=0)
    columns = list(header.columns)
    accelerometer = {axis: axis_column(columns, axis, "accel") for axis in "xyz"}
    gyroscope = {axis: axis_column(columns, axis, "gyro") for axis in "xyz"}
    sensor_columns = [column for column in [*accelerometer.values(), *gyroscope.values()] if column]
    rows = 0
    missing = 0
    malformed = 0
    for chunk in pd.read_csv(path, chunksize=100000):
        rows += len(chunk)
        for column in sensor_columns:
            values = chunk[column]
            missing += int(values.isna().sum())
            malformed += int(pd.to_numeric(values, errors="coerce").isna().sum() - values.isna().sum())
    relative = path.relative_to(PROJECT_ROOT)
    subject_tokens = sorted(set(SUBJECT_PATTERN.findall(str(path))))
    activity_tokens = sorted(set(ACTIVITY_PATTERN.findall(str(path))))
    label_columns = [
        column for column in columns
        if str(column).strip().lower() in {"activity", "activity_id", "label", "fall", "fall_state", "class"}
    ]
    timestamp_columns = [
        column for column in columns
        if any(token in str(column).strip().lower() for token in ("timestamp", "time", "sample"))
    ]
    metadata_columns = [
        column for column in columns
        if any(token in str(column).strip().lower() for token in ("subject", "user", "trial", "experiment", "activity", "label", "fall"))
    ]
    print(f"FILE: {relative}")
    print(f"  columns={columns}")
    print(f"  rows={rows}")
    print(f"  accelerometer={accelerometer}")
    print(f"  gyroscope={gyroscope}")
    print(f"  subject_filename_tokens={subject_tokens}")
    print(f"  activity_filename_tokens={activity_tokens}")
    print(f"  label_columns={label_columns}")
    print(f"  timestamp_columns={timestamp_columns}")
    print(f"  metadata_columns={metadata_columns}")
    print(f"  sensor_missing_values={missing}")
    print(f"  sensor_malformed_numeric_values={malformed}")
    return rows, missing, malformed


def main():
    if not ROOT.exists() or not any(ROOT.rglob("*")):
        print("UP-FALL RAW SENSOR DATA NOT INSTALLED")
        return 2
    files = sorted(path for path in ROOT.rglob("*") if path.is_file())
    csv_files = [path for path in files if path.suffix.lower() == ".csv"]
    print(f"ROOT: {ROOT}")
    print(f"FILES: {len(files)}")
    print(f"CSV_FILES: {len(csv_files)}")
    if not csv_files:
        print("UP-FALL CSV FILES NOT FOUND")
        return 2
    totals = [inspect_csv(path) for path in csv_files]
    print(f"TOTAL_ROWS: {sum(item[0] for item in totals)}")
    print(f"TOTAL_SENSOR_MISSING: {sum(item[1] for item in totals)}")
    print(f"TOTAL_SENSOR_MALFORMED: {sum(item[2] for item in totals)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
