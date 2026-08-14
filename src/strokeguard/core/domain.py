from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Optional
import time

class RiskState(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    SENSOR_ERROR = "SENSOR_ERROR"

@dataclass
class SensorPacket:
    timestamp: float
    heart_rate_bpm: Optional[float] = None
    spo2_pct: Optional[float] = None
    systolic_bp_mmhg: Optional[float] = None
    diastolic_bp_mmhg: Optional[float] = None
    accel_x_g: float = 0.0
    accel_y_g: float = 0.0
    accel_z_g: float = 1.0
    sensor_quality: float = 1.0
    battery_pct: Optional[float] = None
    sos_pressed: bool = False

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(
            timestamp=float(d.get("timestamp", time.time())),
            heart_rate_bpm=_opt(d.get("heart_rate_bpm")),
            spo2_pct=_opt(d.get("spo2_pct")),
            systolic_bp_mmhg=_opt(d.get("systolic_bp_mmhg")),
            diastolic_bp_mmhg=_opt(d.get("diastolic_bp_mmhg")),
            accel_x_g=float(d.get("accel_x_g", 0.0)),
            accel_y_g=float(d.get("accel_y_g", 0.0)),
            accel_z_g=float(d.get("accel_z_g", 1.0)),
            sensor_quality=float(d.get("sensor_quality", 1.0)),
            battery_pct=_opt(d.get("battery_pct")),
            sos_pressed=bool(d.get("sos_pressed", False)),
        )

@dataclass
class FastSymptoms:
    balance_loss: bool = False
    eye_changes: bool = False
    face_drooping: bool = False
    arm_weakness: bool = False
    speech_difficulty: bool = False
    onset_timestamp: Optional[float] = None

    def active_count(self):
        return sum([
            self.balance_loss, self.eye_changes, self.face_drooping,
            self.arm_weakness, self.speech_difficulty
        ])

    def any_active(self):
        return self.active_count() > 0

@dataclass
class Prediction:
    state: RiskState
    score: float
    probabilities: dict
    reasons: list[str] = field(default_factory=list)
    model_version: str = "unknown"

@dataclass
class RiskDecision:
    state: RiskState
    score: float
    reasons: list[str]
    emergency: bool
    local_alert: bool
    sos: bool
    timestamp: float = field(default_factory=time.time)

def _opt(x):
    return None if x is None else float(x)
