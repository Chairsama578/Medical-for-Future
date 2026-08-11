import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from strokeguard_v4.features import make_windows
from strokeguard_v4.safety import SafetyFusionV4


def test_v4_window_features_and_metadata():
    data = pd.DataFrame({
        "accel_x": [0.0] * 40,
        "accel_y": [0.0] * 40,
        "accel_z": [1.0] * 40,
        "heart_rate": [70.0] * 40,
        "activity": ["SITTING"] * 40,
        "fall_state": ["NO_FALL"] * 40,
        "physiology_state": ["NORMAL"] * 40,
        "subject_id": ["subject-1"] * 40,
    })
    features, metadata = make_windows(data)
    assert len(features) == 1
    assert features.iloc[0]["accel_mag_mean"] == 1.0
    assert metadata.iloc[0]["activity"] == "SITTING"


def test_v4_safety_persistence_and_override():
    fusion = SafetyFusionV4(persistence=2)
    assert fusion.decide(0.9)["state"] == "NORMAL"
    assert fusion.decide(0.9)["state"] == "CRITICAL"
    assert fusion.decide(0.1, manual_sos=True)["state"] == "EMERGENCY"
