from collections import deque
import time
from strokeguard.ai.features import extract
from strokeguard.ai.model import EdgeLinearModel
from strokeguard.core.domain import Prediction, RiskState, SensorPacket

class EdgeInference:
    def __init__(self, model_path, window_size=40):
        self.model = EdgeLinearModel(model_path)
        self.window = deque(maxlen=window_size)

    def push(self, packet: SensorPacket):
        self.window.append(packet)

    def predict(self):
        if len(self.window) < max(5, self.window.maxlen // 4):
            return Prediction(RiskState.WARNING, 0.0, {}, ["warming_up"], self.model.version)
        x = extract(list(self.window))
        probs = self.model.predict_proba(x)
        p = {c: float(v) for c, v in zip(self.model.classes, probs)}
        idx = int(probs.argmax())
        state = RiskState(self.model.classes[idx])
        return Prediction(state, float(probs[idx]), p, [], self.model.version)
