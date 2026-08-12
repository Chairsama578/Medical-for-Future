import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from strokeguard.core.domain import SensorPacket
from strokeguard_v4.contracts import EmergencyEvent, PlaceholderFallDetector
from strokeguard_v4.physiology import PersonalBaseline, PhysiologyRiskEngine, extract_physiology_features
from strokeguard_v4.physiology_simulator import SCENARIOS, PhysiologySimulator
from strokeguard_v4.safety import SafetyFusionV4


def packets(hr=72.0, spo2=98.0, quality=0.98, count=40):
    return [
        SensorPacket(
            timestamp=float(index), heart_rate_bpm=hr, spo2_pct=spo2,
            accel_x_g=0.0, accel_y_g=0.0, accel_z_g=1.0,
            sensor_quality=quality,
        )
        for index in range(count)
    ]


def test_normal_physiology_and_features():
    result = PhysiologyRiskEngine().decide(packets())
    assert result.state == "NORMAL"
    assert result.score == 0.0
    assert "hr_mean" in result.features
    assert "spo2_mean" in result.features


def test_persistent_abnormal_hr_and_spo2():
    hr_engine = PhysiologyRiskEngine(persistence_windows=2)
    assert hr_engine.decide(packets(hr=135)).state == "PHYSIO_WARNING"
    assert hr_engine.decide(packets(hr=135)).state == "PHYSIO_WARNING"
    spo2_engine = PhysiologyRiskEngine(persistence_windows=2)
    assert spo2_engine.decide(packets(spo2=88)).state == "PHYSIO_WARNING"
    assert spo2_engine.decide(packets(spo2=88)).state == "PHYSIO_WARNING"


def test_sensor_dropout_and_invalid_values_are_sensor_errors():
    assert PhysiologyRiskEngine().decide(packets(hr=None, spo2=None, quality=0.1)).state == "SENSOR_ERROR"
    invalid = packets()
    invalid[0].heart_rate_bpm = float("nan")
    assert PhysiologyRiskEngine().decide(invalid).state == "SENSOR_ERROR"
    jump = packets()
    jump[1].heart_rate_bpm = 220
    assert "heart_rate_sudden_unrealistic_jump" in PhysiologyRiskEngine().decide(jump).reasons


def test_baseline_initialization_reset_and_deviation():
    baseline = PersonalBaseline()
    normal = packets()
    baseline.update(normal)
    assert baseline.initialized
    features = extract_physiology_features(packets(hr=100))
    assert baseline.deviations(features)["hr_mean_deviation"] == 28.0
    baseline.reset()
    assert not baseline.initialized


def test_rapid_deterioration_persists_to_critical():
    engine = PhysiologyRiskEngine(persistence_windows=2)
    first = packets(hr=72)
    second = packets(hr=150)
    assert engine.decide(first).state == "NORMAL"
    assert engine.decide(second).state == "PHYSIO_WARNING"
    assert engine.decide(second).state == "PHYSIO_CRITICAL"


def test_safety_overrides_activity_and_fall_placeholder():
    fusion = SafetyFusionV4(persistence=2)
    assert fusion.decide(manual_sos=True)["state"] == "CRITICAL"
    assert fusion.decide(befast_positive=True)["state"] == "CRITICAL"
    fall = PlaceholderFallDetector().decide()
    assert not fall.fall_detected
    assert fusion.decide(physiology_result={"state": "PHYSIO_WARNING"}, fall_result={"fall_detected": True})["state"] == "CRITICAL"


def test_physiology_critical_requires_fusion_persistence():
    fusion = SafetyFusionV4(persistence=2)
    result = {"state": "PHYSIO_CRITICAL"}
    assert fusion.decide(physiology_result=result)["state"] == "NORMAL"
    assert fusion.decide(physiology_result=result)["state"] == "CRITICAL"


def test_emergency_event_serialization_and_scenarios():
    event = EmergencyEvent("CRITICAL", 0.9, "physiology", ["rapid_hr_change"])
    payload = event.to_dict()
    assert payload["event_id"]
    assert payload["latitude"] is None
    assert payload["risk_state"] == "CRITICAL"
    assert SCENARIOS == {
        "normal", "elevated_hr", "low_spo2", "rapid_spo2_decline", "rapid_hr_change",
        "sensor_dropout", "mixed_warning", "critical_physiology", "manual_sos",
        "fall_placeholder",
    }
    for scenario in SCENARIOS:
        assert PhysiologySimulator(scenario).next_packet() is not None
