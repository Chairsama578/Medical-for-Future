"""Replaceable sensor, fall, and emergency contracts for UNO Q integration."""

from dataclasses import asdict, dataclass, field
import time
import uuid


@dataclass
class SensorValue:
    value: float | None = None
    available: bool = False
    valid: bool = False
    timestamp: float = field(default_factory=time.time)


class UnavailableSensor:
    def read(self) -> SensorValue:
        return SensorValue()


class HeartRateSensor(UnavailableSensor):
    pass


class SpO2Sensor(UnavailableSensor):
    pass


class BloodPressureSensor(UnavailableSensor):
    pass


class IMUSensor(UnavailableSensor):
    pass


class BatterySensor(UnavailableSensor):
    pass


class GPSSensor(UnavailableSensor):
    pass


class SOSButton(UnavailableSensor):
    pass


@dataclass
class FallResult:
    fall_detected: bool = False
    confidence: float = 0.0
    impact_score: float = 0.0
    recovery_detected: bool = False
    fall_model_status: str = "NOT_AVAILABLE"
    timestamp: float = field(default_factory=time.time)


class PlaceholderFallDetector:
    """Safe placeholder; it never fabricates a fall detection."""

    def decide(self, timestamp: float | None = None) -> FallResult:
        return FallResult(timestamp=timestamp or time.time())


@dataclass
class EmergencyEvent:
    risk_state: str
    risk_score: float
    trigger: str
    reasons: list[str]
    heart_rate: float | None = None
    spo2: float | None = None
    systolic_bp: float | None = None
    diastolic_bp: float | None = None
    activity: str | None = None
    fall_detected: bool = False
    sensor_quality: float = 0.0
    battery: float | None = None
    sos_pressed: bool = False
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    latitude: float | None = None
    longitude: float | None = None
    location_accuracy: float | None = None
    location_timestamp: float | None = None

    def to_dict(self):
        return asdict(self)
