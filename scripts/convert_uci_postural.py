"""Convert the UCI transition-aware raw signals into the v4 row schema.

The source labels use one-based, inclusive sample boundaries. Raw files are
matched by the experiment and user IDs embedded in their filenames rather than
by directory ordering.
"""

from pathlib import Path
import re

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "raw" / "uci_postural"
OUTPUT = PROJECT_ROOT / "data" / "unified" / "uci_postural.csv"
SOURCE_RATE_HZ = 50.0

ACTIVITY_NAMES = {
    1: "WALKING",
    2: "WALKING_UPSTAIRS",
    3: "WALKING_DOWNSTAIRS",
    4: "SITTING",
    5: "STANDING",
    6: "LAYING",
    7: "STAND_TO_SIT",
    8: "SIT_TO_STAND",
    9: "SIT_TO_LIE",
    10: "LIE_TO_SIT",
    11: "STAND_TO_LIE",
    12: "LIE_TO_STAND",
}
POSTURES = {"SITTING", "STANDING", "LAYING"}
TRANSITIONS = {
    "STAND_TO_SIT", "SIT_TO_STAND", "SIT_TO_LIE",
    "LIE_TO_SIT", "STAND_TO_LIE", "LIE_TO_STAND",
}
FILE_PATTERN = re.compile(r"^(acc|gyro)_exp(\d+)_user(\d+)\.txt$")


def read_labels():
    labels = pd.read_csv(
        ROOT / "RawData" / "labels.txt",
        sep=r"\s+",
        header=None,
        names=["experiment_id", "subject_id", "activity_id", "start_sample", "end_sample"],
    )
    if labels.isna().any().any():
        raise ValueError("labels.txt contains malformed or missing fields")
    labels = labels.astype({
        "experiment_id": int,
        "subject_id": int,
        "activity_id": int,
        "start_sample": int,
        "end_sample": int,
    })
    unknown = sorted(set(labels.activity_id) - set(ACTIVITY_NAMES))
    if unknown:
        raise ValueError(f"Unknown activity IDs in labels.txt: {unknown}")
    if (labels.start_sample < 1).any() or (labels.end_sample < labels.start_sample).any():
        raise ValueError("labels.txt contains invalid sample boundaries")
    return labels


def index_raw_files():
    files = {}
    for path in (ROOT / "RawData").glob("*.txt"):
        match = FILE_PATTERN.match(path.name)
        if not match:
            continue
        signal, experiment, subject = match.groups()
        key = (int(experiment), int(subject), signal)
        if key in files:
            raise ValueError(f"Duplicate raw file mapping: {path.name}")
        files[key] = path
    return files


def convert():
    labels = read_labels()
    raw_files = index_raw_files()
    pairs = sorted({key[:2] for key in raw_files})
    expected_pairs = set(map(tuple, labels[["experiment_id", "subject_id"]].drop_duplicates().to_numpy()))
    if set(pairs) != expected_pairs:
        missing = sorted(expected_pairs - set(pairs))
        extra = sorted(set(pairs) - expected_pairs)
        raise ValueError(f"Raw/label mapping mismatch; missing={missing}, extra={extra}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    first = True
    total_rows = 0
    for experiment_id, subject_id in pairs:
        acc_path = raw_files[(experiment_id, subject_id, "acc")]
        gyro_path = raw_files[(experiment_id, subject_id, "gyro")]
        acc = pd.read_csv(acc_path, sep=r"\s+", header=None, names=["accel_x", "accel_y", "accel_z"])
        gyro = pd.read_csv(gyro_path, sep=r"\s+", header=None, names=["gyro_x", "gyro_y", "gyro_z"])
        if len(acc) != len(gyro):
            raise ValueError(
                f"Signal length mismatch for experiment {experiment_id}, subject {subject_id}: "
                f"acc={len(acc)}, gyro={len(gyro)}"
            )
        if acc.isna().any().any() or gyro.isna().any().any():
            raise ValueError(f"Malformed numeric values in experiment {experiment_id}, subject {subject_id}")

        count = len(acc)
        activity_id = np.full(count, np.nan)
        interval_start = np.full(count, np.nan)
        interval_end = np.full(count, np.nan)
        source_labels = labels[
            (labels.experiment_id == experiment_id) & (labels.subject_id == subject_id)
        ]
        occupied = np.zeros(count, dtype=bool)
        for row in source_labels.itertuples(index=False):
            start = row.start_sample - 1
            end = row.end_sample
            if end > count:
                raise ValueError(
                    f"Label boundary exceeds raw signal for experiment {experiment_id}, "
                    f"subject {subject_id}: end={end}, samples={count}"
                )
            if occupied[start:end].any():
                raise ValueError(f"Overlapping label intervals for experiment {experiment_id}, subject {subject_id}")
            occupied[start:end] = True
            activity_id[start:end] = row.activity_id
            interval_start[start:end] = row.start_sample
            interval_end[start:end] = row.end_sample

        activity = pd.Series(activity_id).map(ACTIVITY_NAMES).fillna("UNKNOWN")
        frame = pd.concat([acc, gyro], axis=1)
        frame["timestamp"] = np.arange(count, dtype=np.float64) / SOURCE_RATE_HZ
        frame["sample_index"] = np.arange(1, count + 1, dtype=np.int64)
        frame["subject_id"] = subject_id
        frame["experiment_id"] = experiment_id
        frame["activity_id"] = pd.array(activity_id, dtype="Int64")
        frame["activity"] = activity.to_numpy()
        frame["posture"] = activity.where(activity.isin(POSTURES), "UNKNOWN").to_numpy()
        frame["transition"] = activity.where(activity.isin(TRANSITIONS), "UNKNOWN").to_numpy()
        frame["start_sample"] = pd.array(interval_start, dtype="Int64")
        frame["end_sample"] = pd.array(interval_end, dtype="Int64")
        frame["source_dataset"] = "uci_postural_v2.1"
        frame["source_sample_rate_hz"] = SOURCE_RATE_HZ
        frame["fall_state"] = "UNKNOWN"
        frame["physiology_state"] = "UNKNOWN"
        frame["heart_rate"] = np.nan
        frame["spo2"] = np.nan
        frame["sbp"] = np.nan
        frame["dbp"] = np.nan

        frame.to_csv(OUTPUT, mode="w" if first else "a", header=first, index=False)
        first = False
        total_rows += count

    print(f"UCI Postural converted: {OUTPUT} rows={total_rows} experiments={len(pairs)}")


if __name__ == "__main__":
    convert()
