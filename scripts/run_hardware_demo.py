"""Human-readable Arduino hardware/simulation demo using the existing bridge."""

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from arduino_demo_simulator import packet as simulator_packet
from arduino_serial_bridge import default_runtime, process_json_line


def simulation_payload(scenario, index):
    if scenario == "sos":
        return simulator_packet("manual_sos", index)
    if scenario == "sensor_error":
        return simulator_packet("normal", index) | {
            "heart_rate_bpm": None,
            "spo2_pct": None,
            "sensor_quality": 0.1,
        }
    return simulator_packet(scenario, index)


def format_result(payload, result):
    lines = [
        f"[{time.strftime('%H:%M:%S')}]",
        f"HR: {payload.get('heart_rate_bpm')} BPM",
        f"SpO2: {payload.get('spo2_pct')} %",
        f"Activity: {result.get('activity', 'UNKNOWN')}",
        f"Physiology: {result.get('physiology_state', 'UNKNOWN')}",
        f"Fall: {'YES' if result.get('fall_detected') else 'NO'}",
        f"Fall model: {result.get('fall_model_status', 'NOT_AVAILABLE')}",
        f"Risk: {result.get('risk_state', 'UNKNOWN')}",
    ]
    if payload.get("sos_pressed"):
        lines.insert(1, "SOS BUTTON: PRESSED")
    if result.get("trigger"):
        lines.append(f"Trigger: {result['trigger']}")
    return "\n".join(lines)


def run_simulation(scenario):
    runtime = default_runtime()
    result = None
    payload = None
    for index in range(120):
        payload = simulation_payload(scenario, index)
        result = process_json_line(json.dumps(payload), runtime)
    print(format_result(payload, result))
    return 0


def run_serial(port, baud):
    try:
        import serial
    except ImportError as error:
        print("pyserial is required: python -m pip install pyserial", file=sys.stderr)
        return 2
    runtime = default_runtime()
    print(f"Opening {port} at {baud} baud. Press Ctrl+C to stop.")
    try:
        with serial.Serial(port, baud, timeout=1) as connection:
            while True:
                raw = connection.readline()
                if not raw:
                    continue
                text = raw.decode("utf-8", errors="replace").strip()
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    print("SERIAL ERROR: invalid JSON line", flush=True)
                    continue
                result = process_json_line(text, runtime)
                connection.write((json.dumps(result, separators=(",", ":")) + "\n").encode("utf-8"))
                print(format_result(payload, result), flush=True)
    except KeyboardInterrupt:
        print("\nSerial demo stopped.")
    except (OSError, serial.SerialException) as error:
        print(f"SERIAL ERROR: {error}", file=sys.stderr)
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="StrokeGuard Arduino hardware demo")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--port", help="Serial port, for example COM5")
    source.add_argument("--simulate", choices=["normal", "critical", "sos", "sensor_error"])
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()
    if args.simulate:
        return run_simulation(args.simulate)
    return run_serial(args.port, args.baud)


if __name__ == "__main__":
    raise SystemExit(main())
