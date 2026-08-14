import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from arduino_demo_simulator import packet
from arduino_serial_bridge import default_runtime, process_json_line
from strokeguard_v4.runtime import V4RuntimeAdapter


SCENARIOS = {"normal", "high_hr", "low_spo2", "critical", "manual_sos", "motion"}


parser = argparse.ArgumentParser(description="StrokeGuard live edge demo")
parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="normal")
args = parser.parse_args()
runtime = default_runtime()
result = None
last_packet = None
for index in range(120):
    last_packet = packet(args.scenario, index)
    result = process_json_line(json.dumps(last_packet), runtime)

print("--------------------------------")
print("STROKEGUARD AI - EDGE DEMO")
print("--------------------------------")
print("Sensor: Simulator (Arduino JSON protocol)")
print(f"Activity: {result.get('activity', 'UNKNOWN')}")
print(f"Heart Rate: {last_packet.get('heart_rate_bpm')} BPM")
print(f"SpO2: {last_packet.get('spo2_pct')} %")
print(f"Fall: {'YES' if result.get('fall_detected') else 'NO'}")
print(f"Fall model: {result.get('fall_model_status')}")
print(f"Physiology: {result.get('physiology_state')}")
print(f"AI Risk: {result.get('risk_state')}")
print(f"Risk score: {result.get('risk_score')}")
print(f"Trigger: {result.get('trigger')}")
print(f"Reasons: {', '.join(result.get('reasons', []))}")
print("--------------------------------")
