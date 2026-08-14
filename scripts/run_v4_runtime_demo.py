import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from strokeguard.core.domain import FastSymptoms
from strokeguard_v4.physiology_simulator import PhysiologySimulator
from strokeguard_v4.runtime import V4RuntimeAdapter


SCENARIOS = {
    "normal": "normal",
    "high_hr": "elevated_hr",
    "low_spo2": "low_spo2",
    "critical_physiology": "critical_physiology",
    "manual_sos": "manual_sos",
    "be_fast": "normal",
    "sensor_error": "sensor_dropout",
    "fall_placeholder": "fall_placeholder",
}


parser = argparse.ArgumentParser(description="StrokeGuard v4 runtime demo")
parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="normal")
parser.add_argument("--windows", type=int, default=3)
args = parser.parse_args()

simulator = PhysiologySimulator(SCENARIOS[args.scenario])
adapter = V4RuntimeAdapter()
symptoms = FastSymptoms(face_drooping=True) if args.scenario == "be_fast" else None

for _ in range(args.windows):
    packet_window = [simulator.next_packet() for _ in range(40)]
    result = None
    for packet in packet_window:
        result = adapter.step(packet, symptoms)
    packet = packet_window[-1]
    physiology = result.physiology
    print({
        "timestamp": packet.timestamp,
        "activity": result.activity.activity,
        "activity_confidence": round(result.activity.confidence, 4),
        "hr": packet.heart_rate_bpm,
        "spo2": packet.spo2_pct,
        "bp": [packet.systolic_bp_mmhg, packet.diastolic_bp_mmhg],
        "physiology_state": physiology.state,
        "physiology_score": round(physiology.score, 4),
        "fall_status": result.fall.fall_model_status,
        "fall_detected": result.fall.fall_detected,
        "risk_state": result.decision["state"],
        "risk_score": round(physiology.score, 4),
        "reasons": result.decision["reasons"] + physiology.reasons,
        "emergency_event": result.emergency_event.to_dict() if result.emergency_event else None,
    })
