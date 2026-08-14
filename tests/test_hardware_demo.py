import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arduino_serial_bridge import process_json_line
from run_hardware_demo import simulation_payload
from strokeguard_v4.runtime import V4RuntimeAdapter


def base_packet():
    return {
        "timestamp": 1723456789000,
        "heart_rate_bpm": 82,
        "spo2_pct": 98,
        "systolic_bp_mmhg": None,
        "diastolic_bp_mmhg": None,
        "accel_x_g": 0.02,
        "accel_y_g": 0.98,
        "accel_z_g": 0.05,
        "sensor_quality": 1.0,
        "battery_pct": 87,
        "sos_pressed": False,
    }


def run(runtime, payload, count=40):
    result = None
    for _ in range(count):
        result = process_json_line(json.dumps(payload), runtime)
    return result


def test_valid_packet_and_missing_bp():
    payload = base_packet()
    result = run(V4RuntimeAdapter(), payload)
    assert result["risk_state"] == "NORMAL"
    assert process_json_line(json.dumps(payload))["fall_model_status"] == "NOT_AVAILABLE"


def test_invalid_values_and_sensor_dropout():
    assert process_json_line(json.dumps(base_packet() | {"heart_rate_bpm": 500}))["risk_state"] == "SENSOR_ERROR"
    assert process_json_line(json.dumps(base_packet() | {"spo2_pct": 120}))["risk_state"] == "SENSOR_ERROR"
    dropout = base_packet() | {"heart_rate_bpm": None, "spo2_pct": None, "sensor_quality": 0.1}
    assert run(V4RuntimeAdapter(), dropout)["risk_state"] == "SENSOR_ERROR"


def test_sos_critical_and_malformed_json():
    result = process_json_line(json.dumps(base_packet() | {"sos_pressed": True}))
    assert result["risk_state"] == "CRITICAL"
    assert result["trigger"] == "manual_sos"
    assert process_json_line("{")["risk_state"] == "SENSOR_ERROR"


def test_simulator_modes():
    for scenario in ["normal", "critical", "sos", "sensor_error"]:
        payload = simulation_payload(scenario, 0)
        assert isinstance(payload, dict)
        assert process_json_line(json.dumps(payload))["risk_state"] in {
            "NORMAL", "CRITICAL", "SENSOR_ERROR"
        }
