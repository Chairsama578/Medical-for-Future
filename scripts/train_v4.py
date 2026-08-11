from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, classification_report
from sklearn.model_selection import GroupShuffleSplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAINING = PROJECT_ROOT / "data" / "unified" / "training"
MODELS = PROJECT_ROOT / "models" / "v4"
MODELS.mkdir(parents=True, exist_ok=True)


def train(name, label):
    path = TRAINING / f"{name}.csv"
    if not path.exists():
        print("[SKIP]", name)
        return
    data = pd.read_csv(path)
    data = data[data[label].notna()]
    excluded = {
        label, "subject_id", "source_dataset", "activity", "fall_state",
        "physiology_state",
    }
    features = [
        column for column in data.columns
        if column not in excluded and pd.api.types.is_numeric_dtype(data[column])
    ]
    X = data[features].fillna(0)
    y = data[label].astype(str)
    groups = data.subject_id.astype(str)
    if y.nunique() < 2:
        print("[SKIP]", name, "classes:", y.unique())
        return
    train_idx, test_idx = next(
        GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42).split(
            X, y, groups
        )
    )
    classifier = RandomForestClassifier(
        n_estimators=250,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    ).fit(X.iloc[train_idx], y.iloc[train_idx])
    prediction = classifier.predict(X.iloc[test_idx])
    print(name, "balanced_accuracy=", balanced_accuracy_score(y.iloc[test_idx], prediction))
    print(classification_report(y.iloc[test_idx], prediction, zero_division=0))
    joblib.dump(
        {"model": classifier, "features": features, "label": label},
        MODELS / f"{name}.joblib",
    )


for branch, label in [
    ("activity", "activity"),
    ("fall", "fall_state"),
    ("physiology", "physiology_state"),
]:
    train(branch, label)
