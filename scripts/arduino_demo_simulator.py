import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from arduino_serial_bridge import default_runtime, process_json_line
from strokeguard_v4.runtime import V4RuntimeAdapter


SCENARIOS = {"normal", "high_hr", "low_spo2", "critical", "manual_sos", "motion"}


def packet(scenario, index):
    value = {
        "timestamp": int(time.time() * 1000),
        "heart_rate_bpm": 82,
        "spo2_pct": 98,
        "systolic_bp_mmhg": None,
        "diastolic_bp_mmhg": None,
        "accel_x_g": 0.02,
        "accel_y_g": 0.98,
        "accel_z_g": 0.05,
        "sensor_quality": 1.0,
        "battery_pct": 87,
        "sos_pressed": scenario == "manual_sos",
    }
    if scenario == "high_hr":
        value["heart_rate_bpm"] = 140
    elif scenario == "low_spo2":
        value["spo2_pct"] = 88
    elif scenario == "critical":
        value.update({"heart_rate_bpm": 145, "spo2_pct": 88, "systolic_bp_mmhg": 195, "diastolic_bp_mmhg": 125})
    elif scenario == "motion":
        value.update({"accel_x_g": 1.2, "accel_y_g": 0.4, "accel_z_g": 0.3})
    return value


def main():
    parser = argparse.ArgumentParser(description="Arduino protocol simulator")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="normal")
    args = parser.parse_args()
    runtime = default_runtime()
    for index in range(120):
        payload = packet(args.scenario, index)
        print("ARDUINO ->", json.dumps(payload, separators=(",", ":")))
        result = process_json_line(json.dumps(payload), runtime)
        if index % 40 == 39:
            print("AI       <-", json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
