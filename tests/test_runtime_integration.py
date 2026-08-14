import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from strokeguard.ai.inference import EdgeInference
from strokeguard.bridge.uno_q import SimulatorBridge
from strokeguard.core.domain import FastSymptoms, RiskState, SensorPacket
from strokeguard.core.runtime import StrokeGuardEngine
from strokeguard.sensors.simulator import SensorSimulator
from strokeguard_v4.contracts import PlaceholderFallDetector
from strokeguard_v4.physiology_simulator import PhysiologySimulator
from strokeguard_v4.runtime import V4RuntimeAdapter, sensor_packet_to_v4


def packet(hr=72, spo2=98, quality=0.98, sos=False):
    return SensorPacket(
        timestamp=1.0, heart_rate_bpm=hr, spo2_pct=spo2,
        systolic_bp_mmhg=None, diastolic_bp_mmhg=None,
        accel_x_g=0.01, accel_y_g=0.02, accel_z_g=0.98,
        sensor_quality=quality, battery_pct=88, sos_pressed=sos,
    )


def run_window(adapter, packets, symptoms=None):
    result = None
    for value in packets:
        result = adapter.step(value, symptoms)
    return result


def test_sensor_packet_adapter_preserves_explicit_mapping_and_missing_bp():
    value = sensor_packet_to_v4(packet())
    assert value["heart_rate"] == 72
    assert value["spo2"] == 98
    assert value["sbp"] is None
    assert value["dbp"] is None
    assert value["accel_x"] == 0.01
    assert value["battery"] == 88


def test_activity_inference_and_activity_alone_are_noncritical():
    adapter = V4RuntimeAdapter()
    result = run_window(adapter, [packet() for _ in range(40)])
    assert result.activity.activity in result.activity.probabilities
    assert 0.0 <= result.activity.confidence <= 1.0
    assert result.decision["state"] == "NORMAL"


def test_physiology_and_sensor_dropout():
    adapter = V4RuntimeAdapter()
    result = run_window(adapter, [packet(hr=135) for _ in range(40)])
    assert result.physiology.state == "PHYSIO_WARNING"
    dropout = V4RuntimeAdapter()
    result = run_window(dropout, [packet(hr=None, spo2=None, quality=0.1) for _ in range(40)])
    assert result.physiology.state == "SENSOR_ERROR"
    assert result.decision["state"] == "SENSOR_ERROR"


def test_manual_sos_and_befast_are_immediate():
    sos = V4RuntimeAdapter().step(packet(sos=True))
    assert sos.decision["state"] == "CRITICAL"
    assert sos.emergency_event is not None
    assert sos.emergency_event.trigger == "manual_sos"
    befast = V4RuntimeAdapter().step(packet(), FastSymptoms(face_drooping=True))
    assert befast.decision["state"] == "CRITICAL"
    assert befast.emergency_event.trigger == "befast"


def test_critical_physiology_persistence_and_placeholder_fall():
    adapter = V4RuntimeAdapter()
    simulator = PhysiologySimulator("critical_physiology")
    results = [run_window(adapter, [simulator.next_packet() for _ in range(40)]) for _ in range(3)]
    assert results[-1].physiology.state == "PHYSIO_CRITICAL"
    assert results[-1].decision["state"] == "CRITICAL"
    fall = PlaceholderFallDetector().decide()
    assert fall.fall_model_status == "NOT_AVAILABLE"
    assert not fall.fall_detected


def test_v3_engine_v4_enabled_and_disabled():
    class MemoryEvents:
        def log(self, *args, **kwargs):
            pass

    events = MemoryEvents()
    bridge = SimulatorBridge(SensorSimulator("normal"))
    legacy = StrokeGuardEngine(
        bridge, EdgeInference("models/strokeguard_edge.json"),
        event_store=events, v4_enabled=False,
    )
    legacy.step()
    assert legacy.v4 is None
    enabled = StrokeGuardEngine(
        SimulatorBridge(SensorSimulator("normal")), EdgeInference("models/strokeguard_edge.json"),
        event_store=events, v4_enabled=True,
    )
    enabled.step()
    assert enabled.v4 is not None
    assert enabled.last_v4 is not None


def test_emergency_event_serialization_and_gps_are_empty():
    result = V4RuntimeAdapter().step(packet(sos=True))
    payload = result.emergency_event.to_dict()
    assert payload["event_id"]
    assert payload["risk_state"] == "CRITICAL"
    assert payload["latitude"] is None
    assert payload["longitude"] is None
