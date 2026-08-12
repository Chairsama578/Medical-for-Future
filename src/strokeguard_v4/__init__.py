"""Drop-in v4 branches for the StrokeGuard v3 runtime."""

from .features import make_windows, window_features
from .inference import MultiBranchInference
from .contracts import EmergencyEvent, FallResult, PlaceholderFallDetector
from .physiology import (
    PersonalBaseline,
    PhysiologyRiskEngine,
    PhysiologyRiskResult,
    extract_physiology_features,
    validate_packet,
)
from .safety import SafetyFusionV4
from .runtime import ActivityResult, V4RuntimeAdapter, sensor_packet_to_v4

__all__ = [
    "make_windows", "window_features", "MultiBranchInference", "SafetyFusionV4",
    "EmergencyEvent", "FallResult", "PlaceholderFallDetector", "PersonalBaseline",
    "PhysiologyRiskEngine", "PhysiologyRiskResult", "extract_physiology_features",
    "validate_packet",
    "ActivityResult", "V4RuntimeAdapter", "sensor_packet_to_v4",
]
