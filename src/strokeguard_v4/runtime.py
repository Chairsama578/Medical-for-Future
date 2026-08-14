"""Optional runtime adapter joining Activity, Physiology, and Fall contracts."""

from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
import time

import joblib
import pandas as pd

from strokeguard.core.domain import FastSymptoms, RiskDecision, RiskState, SensorPacket
from .contracts import EmergencyEvent, FallResult, PlaceholderFallDetector
from .features import window_features
from .physiology import PhysiologyRiskEngine, PhysiologyRiskResult
from .safety import SafetyFusionV4


@dataclass
class ActivityResult:
    activity: str = "UNKNOWN"
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)
    window_samples: int = 0
    probabilities: dict = field(default_factory=dict)
    model_version: str = "unavailable"

    def to_dict(self):
        return asdict(self)


@dataclass
class V4RuntimeResult:
    ready: bool
    activity: ActivityResult
    physiology: PhysiologyRiskResult
    fall: FallResult
    decision: dict
    emergency_event: EmergencyEvent | None = None


def sensor_packet_to_v4(packet: SensorPacket) -> dict:
    """Explicitly map the v3 wire contract to v4 internal names."""
    return {
        "timestamp": packet.timestamp,
        "heart_rate": packet.heart_rate_bpm,
        "spo2": packet.spo2_pct,
        "sbp": packet.systolic_bp_mmhg,
        "dbp": packet.diastolic_bp_mmhg,
        "accel_x": packet.accel_x_g,
        "accel_y": packet.accel_y_g,
        "accel_z": packet.accel_z_g,
        "sensor_quality": packet.sensor_quality,
        "battery": packet.battery_pct,
        "sos_pressed": packet.sos_pressed,
    }


class ActivityInferenceAdapter:
    def __init__(self, model_path="models/v4/activity.joblib"):
        self.model_path = Path(model_path)
        self.bundle = joblib.load(self.model_path) if self.model_path.exists() else None

    def predict(self, packets) -> ActivityResult:
        timestamp = packets[-1].timestamp if packets else time.time()
        if not packets or self.bundle is None:
            return ActivityResult(timestamp=timestamp, window_samples=len(packets))
        frame = pd.DataFrame([sensor_packet_to_v4(packet) for packet in packets])
        features = window_features(frame)
        names = list(self.bundle["features"])
        values = pd.DataFrame([{name: features.get(name, 0.0) for name in names}])
        if values.isna().any().any():
            raise ValueError("NaN entered Activity inference")
        probabilities = self.bundle["model"].predict_proba(values)[0]
        classes = [str(value) for value in self.bundle["model"].classes_]
        index = int(probabilities.argmax())
        return ActivityResult(
            activity=classes[index],
            confidence=float(probabilities[index]),
            timestamp=timestamp,
            window_samples=len(packets),
            probabilities={name: float(value) for name, value in zip(classes, probabilities)},
            model_version=self.bundle.get("version", "activity-model"),
        )


class V4RuntimeAdapter:
    def __init__(self, model_path="models/v4/activity.joblib", window_size=40, persistence=2):
        self.window_size = window_size
        self.window = deque(maxlen=window_size)
        self.activity = ActivityInferenceAdapter(model_path)
        self.physiology = PhysiologyRiskEngine(persistence_windows=persistence)
        self.fall = PlaceholderFallDetector()
        self.fusion = SafetyFusionV4(persistence=persistence)

    def step(self, packet: SensorPacket, symptoms: FastSymptoms | None = None) -> V4RuntimeResult:
        self.window.append(packet)
        packets = list(self.window)
        ready = len(packets) >= self.window_size
        timestamp = packet.timestamp
        if not ready:
            activity = ActivityResult(timestamp=timestamp, window_samples=len(packets))
            physiology = PhysiologyRiskResult(0.0, "UNKNOWN", ["warming_up"], 0.0, 0.0, {}, timestamp)
        else:
            activity = self.activity.predict(packets)
            physiology = self.physiology.decide(packets, activity.to_dict())
        fall = self.fall.decide(timestamp)
        decision = self.fusion.decide(
            risk_score=physiology.score,
            sensor_quality=physiology.sensor_quality if ready else packet.sensor_quality,
            manual_sos=packet.sos_pressed,
            befast_positive=bool(symptoms and symptoms.any_active()),
            activity_result=activity.to_dict(),
            fall_result=fall,
            physiology_result=physiology,
        )
        event = None
        if decision["state"] == "CRITICAL":
            trigger = "manual_sos" if packet.sos_pressed else "befast" if symptoms and symptoms.any_active() else "v4_risk"
            event = EmergencyEvent(
                risk_state=decision["state"],
                risk_score=max(physiology.score, 1.0 if packet.sos_pressed or symptoms and symptoms.any_active() else 0.0),
                trigger=trigger,
                reasons=decision["reasons"] + physiology.reasons,
                heart_rate=packet.heart_rate_bpm,
                spo2=packet.spo2_pct,
                systolic_bp=packet.systolic_bp_mmhg,
                diastolic_bp=packet.diastolic_bp_mmhg,
                activity=activity.activity,
                fall_detected=fall.fall_detected,
                sensor_quality=packet.sensor_quality,
                battery=packet.battery_pct,
                sos_pressed=packet.sos_pressed,
                timestamp=timestamp,
            )
        return V4RuntimeResult(ready, activity, physiology, fall, decision, event)


def v4_decision_to_risk_decision(result: V4RuntimeResult, fallback: RiskDecision) -> RiskDecision:
    v4_state = result.decision["state"]
    if v4_state == "NORMAL":
        return fallback
    if fallback.state == RiskState.CRITICAL and v4_state != "CRITICAL":
        return fallback
    state = RiskState(v4_state)
    emergency = state == RiskState.CRITICAL
    return RiskDecision(
        state=state,
        score=result.physiology.score,
        reasons=result.decision["reasons"] + result.physiology.reasons,
        emergency=emergency,
        local_alert=state in {RiskState.WARNING, RiskState.CRITICAL},
        sos=result.decision["state"] == "CRITICAL" and result.emergency_event is not None and result.emergency_event.sos_pressed,
        timestamp=result.physiology.timestamp,
    )
