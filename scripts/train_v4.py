from datetime import datetime, timezone
from pathlib import Path
import json
import time

import joblib
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import GroupShuffleSplit


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAINING = PROJECT_ROOT / "data" / "unified" / "training"
MODELS = PROJECT_ROOT / "models" / "v4"
CONFIG_PATH = PROJECT_ROOT / "config" / "v4.yaml"
DATASET_PATH = TRAINING / "activity.csv"
MODEL_PATH = MODELS / "activity.joblib"
MANIFEST_PATH = MODELS / "activity_training_manifest.json"
RANDOM_SEED = 42
VALIDATION_SEED = 43

NON_FEATURE_COLUMNS = {
    "activity", "subject_id", "source_dataset", "experiment_id", "activity_id",
    "posture", "transition", "fall_state", "physiology_state", "timestamp",
    "sample_index", "start_sample", "end_sample", "source_sample_rate_hz",
}
PHYSIOLOGY_PREFIXES = ("heart_rate_", "spo2_", "sbp_", "dbp_")


def metric_report(y_true, prediction, classes):
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, prediction, labels=classes, zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(y_true, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, prediction)),
        "macro_precision": float(precision.mean()),
        "macro_recall": float(recall.mean()),
        "macro_f1": float(f1.mean()),
        "per_class": {
            label: {
                "precision": float(p),
                "recall": float(r),
                "f1": float(score),
                "support": int(count),
            }
            for label, p, r, score, count in zip(
                classes, precision, recall, f1, support
            )
        },
        "confusion_matrix": confusion_matrix(
            y_true, prediction, labels=classes
        ).tolist(),
    }


def split_by_subject(data):
    groups = data["subject_id"].astype(str)
    train_validation_idx, test_idx = next(
        GroupShuffleSplit(
            n_splits=1, test_size=0.20, random_state=RANDOM_SEED
        ).split(data, data["activity"], groups)
    )
    train_validation = data.iloc[train_validation_idx]
    train_idx, validation_idx = next(
        GroupShuffleSplit(
            n_splits=1, test_size=0.25, random_state=VALIDATION_SEED
        ).split(
            train_validation,
            train_validation["activity"],
            train_validation["subject_id"].astype(str),
        )
    )
    return (
        train_validation.iloc[train_idx],
        train_validation.iloc[validation_idx],
        data.iloc[test_idx],
    )


def select_features(data):
    features = [
        column for column in data.columns
        if column not in NON_FEATURE_COLUMNS
        and pd.api.types.is_numeric_dtype(data[column])
    ]
    unavailable_physiology = [
        column for column in features
        if column.startswith(PHYSIOLOGY_PREFIXES)
        and data[column].fillna(0).eq(0).all()
    ]
    features = [column for column in features if column not in unavailable_physiology]
    if not features:
        raise ValueError("No legitimate numeric sensor features found")
    if data[features].isna().any().any():
        raise ValueError("NaN detected in Activity features; refusing silent repair")
    return features, unavailable_physiology


def train_activity():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(DATASET_PATH)
    data = pd.read_csv(DATASET_PATH)
    if data["activity"].isna().any() or data["subject_id"].isna().any():
        raise ValueError("Activity target or subject_id contains NaN")

    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    n_estimators = int(config["activity"]["n_estimators"])
    features, excluded_unavailable = select_features(data)
    train, validation, test = split_by_subject(data)

    all_classes = sorted(data["activity"].astype(str).unique())
    split_data = {"train": train, "validation": validation, "test": test}
    missing_classes = {
        name: sorted(set(all_classes) - set(part["activity"].astype(str)))
        for name, part in split_data.items()
    }
    if any(missing_classes.values()):
        raise ValueError(f"Classes missing from subject split: {missing_classes}")

    train_subjects = sorted(train["subject_id"].astype(str).unique())
    validation_subjects = sorted(validation["subject_id"].astype(str).unique())
    test_subjects = sorted(test["subject_id"].astype(str).unique())
    if (
        set(train_subjects) & set(validation_subjects)
        or set(train_subjects) & set(test_subjects)
        or set(validation_subjects) & set(test_subjects)
    ):
        raise ValueError("Subject leakage detected between splits")

    classifier = RandomForestClassifier(
        n_estimators=n_estimators,
        class_weight="balanced_subsample",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    started = time.perf_counter()
    classifier.fit(train[features], train["activity"].astype(str))
    training_seconds = time.perf_counter() - started

    validation_prediction = classifier.predict(validation[features])
    test_prediction = classifier.predict(test[features])
    validation_metrics = metric_report(
        validation["activity"].astype(str), validation_prediction, all_classes
    )
    test_metrics = metric_report(
        test["activity"].astype(str), test_prediction, all_classes
    )

    benchmark_rows = test[features].iloc[: min(1000, len(test))]
    benchmark_started = time.perf_counter()
    for index in range(len(benchmark_rows)):
        classifier.predict(benchmark_rows.iloc[[index]])
    inference_seconds = time.perf_counter() - benchmark_started
    inference_ms = inference_seconds / len(benchmark_rows) * 1000

    timestamp = datetime.now(timezone.utc).isoformat()
    bundle = {
        "model": classifier,
        "features": features,
        "feature_names": features,
        "feature_count": len(features),
        "label": "activity",
        "version": "activity-baseline-v1",
        "dataset": "uci_har_v1+uci_postural_v2.1",
        "classes": all_classes,
        "training_subjects": train_subjects,
        "validation_subjects": validation_subjects,
        "test_subjects": test_subjects,
        "random_seed": RANDOM_SEED,
        "metrics": {
            "validation": validation_metrics,
            "test": test_metrics,
            "training_seconds": training_seconds,
            "inference_ms_per_window": inference_ms,
        },
    }
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_PATH)

    manifest = {
        "timestamp_utc": timestamp,
        "dataset": bundle["dataset"],
        "dataset_path": str(DATASET_PATH.relative_to(PROJECT_ROOT)),
        "feature_names": features,
        "feature_count": len(features),
        "excluded_unavailable_features": excluded_unavailable,
        "classes": all_classes,
        "random_seed": RANDOM_SEED,
        "validation_seed": VALIDATION_SEED,
        "model_configuration": {
            "classifier": "RandomForestClassifier",
            "n_estimators": n_estimators,
            "class_weight": "balanced_subsample",
            "scaling": "none",
        },
        "subject_split": {
            "train": train_subjects,
            "validation": validation_subjects,
            "test": test_subjects,
        },
        "row_counts": {name: len(part) for name, part in split_data.items()},
        "class_counts": {
            name: part["activity"].value_counts().sort_index().to_dict()
            for name, part in split_data.items()
        },
        "metrics": bundle["metrics"],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("TRAINING STATUS: PASS")
    print("MODEL:", MODEL_PATH)
    print("FEATURE COUNT:", len(features))
    print("FEATURES:", features)
    print("EXCLUDED UNAVAILABLE FEATURES:", excluded_unavailable)
    print("TRAIN SUBJECTS:", train_subjects)
    print("VALIDATION SUBJECTS:", validation_subjects)
    print("TEST SUBJECTS:", test_subjects)
    print("VALIDATION METRICS:", json.dumps(validation_metrics))
    print("TEST METRICS:", json.dumps(test_metrics))
    print("TRAINING SECONDS:", training_seconds)
    print("INFERENCE MS PER WINDOW:", inference_ms)
    print("MODEL SIZE:", MODEL_PATH.stat().st_size)
    print("MANIFEST:", MANIFEST_PATH)


if __name__ == "__main__":
    train_activity()
