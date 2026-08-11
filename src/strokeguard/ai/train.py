from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, balanced_accuracy_score
from joblib import dump
from strokeguard.ai.features import FEATURE_NAMES

def train(csv_path="data/generated/strokeguard_windows.csv",
          model_path="models/strokeguard_edge.json",
          joblib_path="models/strokeguard_linear.joblib"):
    df = pd.read_csv(csv_path)
    X = df[FEATURE_NAMES].values
    y = df["risk_state"].values
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced"))
    ])
    pipe.fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    print(classification_report(yte, pred, zero_division=0))
    print("balanced_accuracy:", balanced_accuracy_score(yte, pred))
    dump(pipe, joblib_path)

    scaler = pipe.named_steps["scaler"]
    clf = pipe.named_steps["clf"]
    payload = {
        "version": "strokeguard-edge-linear-1.0",
        "feature_names": FEATURE_NAMES,
        "classes": [str(x) for x in clf.classes_],
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "coefficients": clf.coef_.tolist(),
        "intercepts": clf.intercept_.tolist()
    }
    Path(model_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return pipe

if __name__ == "__main__":
    train()
