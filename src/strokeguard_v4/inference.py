from pathlib import Path

import joblib
import pandas as pd


class MultiBranchInference:
    """Load whichever independently trained v4 branches are available."""

    def __init__(self, model_dir="models/v4"):
        self.models = {}
        for name in ["activity", "fall", "physiology"]:
            path = Path(model_dir) / f"{name}.joblib"
            if path.exists():
                self.models[name] = joblib.load(path)

    def predict(self, features):
        values = pd.DataFrame([features])
        predictions = {}
        for name, bundle in self.models.items():
            columns = bundle["features"]
            for column in columns:
                if column not in values:
                    values[column] = 0.0
            inputs = values[columns].apply(pd.to_numeric, errors="coerce").fillna(0)
            probabilities = bundle["model"].predict_proba(inputs)[0]
            predictions[name] = {
                "label": str(bundle["model"].predict(inputs)[0]),
                "probabilities": {
                    str(label): float(probability)
                    for label, probability in zip(
                        bundle["model"].classes_, probabilities
                    )
                },
            }
        return predictions
