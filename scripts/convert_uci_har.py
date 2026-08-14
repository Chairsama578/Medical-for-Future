from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "raw" / "uci_har"
OUTPUT = PROJECT_ROOT / "data" / "unified"
OUTPUT.mkdir(parents=True, exist_ok=True)


def locate(name):
    return next(ROOT.rglob(name))


features_file = locate("features.txt")
features = [
    line.strip().split(None, 1)[1]
    for line in features_file.read_text(errors="ignore").splitlines()
    if len(line.split(None, 1)) == 2
]
labels = {
    1: "WALKING", 2: "WALKING_UPSTAIRS", 3: "WALKING_DOWNSTAIRS",
    4: "SITTING", 5: "STANDING", 6: "LAYING",
}
frames = []
for split in ["train", "test"]:
    values = pd.read_csv(locate(f"X_{split}.txt"), sep=r"\s+", header=None)
    activity = pd.read_csv(locate(f"y_{split}.txt"), sep=r"\s+", header=None)[0]
    subjects = pd.read_csv(locate(f"subject_{split}.txt"), sep=r"\s+", header=None)[0]
    values.columns = features[:values.shape[1]]
    selected = {}
    for target, source in [
        ("accel_x", "tBodyAcc-mean()-X"),
        ("accel_y", "tBodyAcc-mean()-Y"),
        ("accel_z", "tBodyAcc-mean()-Z"),
        ("gyro_x", "tBodyGyro-mean()-X"),
        ("gyro_y", "tBodyGyro-mean()-Y"),
        ("gyro_z", "tBodyGyro-mean()-Z"),
    ]:
        selected[target] = values[source] if source in values else 0.0
    frame = pd.DataFrame(selected)
    frame["subject_id"] = subjects
    frame["activity"] = activity.map(labels)
    frame["fall_state"] = "NO_FALL"
    frame["physiology_state"] = "UNKNOWN"
    frame["source_dataset"] = "uci_har_v1"
    frames.append(frame)
pd.concat(frames, ignore_index=True).to_csv(
    OUTPUT / "uci_har_activity.csv", index=False
)
print("UCI HAR converted.")
