from collections import deque
from strokeguard.core.domain import FastSymptoms, Prediction, RiskDecision, RiskState, SensorPacket
from strokeguard.safety.fast import evaluate
import time

class SafetyFusion:
    def __init__(self, persist_windows=2):
        self.persist_windows = persist_windows
        self.critical_count = 0
        self.warning_count = 0

    def decide(self, packet: SensorPacket, prediction: Prediction,
               symptoms: FastSymptoms | None = None) -> RiskDecision:
        reasons = list(prediction.reasons)
        sos = bool(packet.sos_pressed)
        fast_active, fast_reasons = evaluate(symptoms or FastSymptoms())
        reasons.extend(fast_reasons)

        if sos:
            return RiskDecision(RiskState.CRITICAL, 1.0, ["manual_sos"], True, True, True)

        if fast_active:
            return RiskDecision(RiskState.CRITICAL, 1.0, reasons, True, True, False)

        if packet.sensor_quality < 0.60:
            return RiskDecision(RiskState.SENSOR_ERROR, 0.0,
                                reasons + ["sensor_quality_below_minimum"],
                                False, False, False)

        if prediction.state == RiskState.CRITICAL:
            self.critical_count += 1
        else:
            self.critical_count = 0

        if prediction.state == RiskState.WARNING:
            self.warning_count += 1
        else:
            self.warning_count = 0

        if self.critical_count >= self.persist_windows:
            return RiskDecision(RiskState.CRITICAL, prediction.score,
                                reasons + ["persistent_model_critical"],
                                True, True, False)

        if self.warning_count >= self.persist_windows:
            return RiskDecision(RiskState.WARNING, prediction.score,
                                reasons + ["persistent_model_warning"],
                                False, True, False)

        return RiskDecision(RiskState.NORMAL, prediction.score, reasons, False, False, False)
