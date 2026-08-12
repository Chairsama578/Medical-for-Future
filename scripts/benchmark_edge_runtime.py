import json
import statistics
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from arduino_demo_simulator import packet
from arduino_serial_bridge import default_runtime, process_json_line
from strokeguard_v4.runtime import V4RuntimeAdapter


def main():
    lines = [json.dumps(packet("normal", index)) for index in range(100)]
    samples = []
    runtime = default_runtime()
    for line in lines:
        started = time.perf_counter()
        process_json_line(line, runtime)
        samples.append((time.perf_counter() - started) * 1000)
    ordered = sorted(samples)
    print({
        "iterations": len(samples),
        "average_ms": statistics.mean(samples),
        "p95_ms": ordered[int(len(ordered) * 0.95) - 1],
        "note": "development workstation benchmark; not an Arduino UNO Q measurement",
    })


if __name__ == "__main__":
    main()
