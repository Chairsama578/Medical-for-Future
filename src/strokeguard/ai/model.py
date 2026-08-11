import json
from pathlib import Path
import numpy as np

class EdgeLinearModel:
    """Tiny dependency-free linear softmax model exported from sklearn training."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.feature_names = payload["feature_names"]
        self.classes = payload["classes"]
        self.mean = np.asarray(payload["mean"], dtype=np.float32)
        self.scale = np.asarray(payload["scale"], dtype=np.float32)
        self.coef = np.asarray(payload["coefficients"], dtype=np.float32)
        self.intercept = np.asarray(payload["intercepts"], dtype=np.float32)
        self.version = payload.get("version", "edge-linear-v1")

    def predict_proba(self, x):
        x = np.asarray(x, dtype=np.float32)
        z = (x - self.mean) / np.where(self.scale == 0, 1.0, self.scale)
        logits = self.coef @ z + self.intercept
        logits -= np.max(logits)
        e = np.exp(logits)
        return e / np.sum(e)

    def predict(self, x):
        p = self.predict_proba(x)
        return self.classes[int(np.argmax(p))]
