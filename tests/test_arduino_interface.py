import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from arduino_serial_bridge import packet_from_json, process_json_line
from strokeguard_v4.runtime import V4RuntimeAdapter


def payload(**overrides):
    value = {
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
    value.update(overrides)
    return value


def send(runtime, value, count=1):
    result = None
    for _ in range(count):
        result = process_json_line(json.dumps(value), runtime)
    return result


def test_normal_packet_and_output_schema():
    runtime = V4RuntimeAdapter()
    result = send(runtime, payload(), 40)
    assert result["risk_state"] == "NORMAL"
    assert result["fall_model_status"] == "NOT_AVAILABLE"
    assert {"risk_state", "risk_score", "activity", "physiology_state", "fall_detected", "trigger"} <= set(result)


def test_invalid_json_and_missing_accelerometer():
    assert process_json_line("not-json")["risk_state"] == "SENSOR_ERROR"
    result = process_json_line(json.dumps({"timestamp": 1}))
    assert result["risk_state"] == "SENSOR_ERROR"


def test_missing_and_invalid_physiology_values():
    missing_spo2 = V4RuntimeAdapter()
    result = send(missing_spo2, payload(spo2_pct=None), 40)
    assert result["risk_state"] == "SENSOR_ERROR"
    assert process_json_line(json.dumps(payload(spo2_pct=120)))["risk_state"] == "SENSOR_ERROR"
    assert process_json_line(json.dumps(payload(heart_rate_bpm=500)))["risk_state"] == "SENSOR_ERROR"


def test_manual_sos_and_persistent_warning():
    sos = process_json_line(json.dumps(payload(sos_pressed=True)))
    assert sos["risk_state"] == "CRITICAL"
    assert sos["trigger"] == "manual_sos"
    runtime = V4RuntimeAdapter()
    result = send(runtime, payload(heart_rate_bpm=140), 80)
    assert result["risk_state"] == "WARNING"
    assert result["physiology_state"] == "PHYSIO_WARNING"


def test_activity_and_sensor_dropout():
    activity_runtime = V4RuntimeAdapter()
    result = send(activity_runtime, payload(), 40)
    assert result["activity"] != "UNKNOWN"
    dropout_runtime = V4RuntimeAdapter()
    result = send(dropout_runtime, payload(heart_rate_bpm=None, spo2_pct=None, sensor_quality=0.1), 40)
    assert result["risk_state"] == "SENSOR_ERROR"


def test_packet_field_mapping():
    packet = packet_from_json(payload())
    assert packet.heart_rate_bpm == 82
    assert packet.spo2_pct == 98
    assert packet.accel_x_g == 0.02
    assert packet.systolic_bp_mmhg is None
