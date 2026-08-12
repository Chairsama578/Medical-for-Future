"""JSON-lines USB serial bridge for Member 2 hardware integration."""

import argparse
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from strokeguard.core.domain import SensorPacket
from strokeguard_v4.runtime import V4RuntimeAdapter


REQUIRED = ["timestamp", "accel_x_g", "accel_y_g", "accel_z_g"]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "v4" / "activity.joblib"


def default_runtime():
    return V4RuntimeAdapter(model_path=DEFAULT_MODEL_PATH)


def _number(value, name, low=None, high=None):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    if low is not None and not low <= number <= high:
        raise ValueError(f"{name} outside range {low}..{high}")
    return number


def packet_from_json(payload):
    missing = [name for name in REQUIRED if name not in payload]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    timestamp = _number(payload["timestamp"], "timestamp")
    return SensorPacket(
        timestamp=timestamp,
        heart_rate_bpm=_number(payload.get("heart_rate_bpm"), "heart_rate_bpm", 30, 220),
        spo2_pct=_number(payload.get("spo2_pct"), "spo2_pct", 50, 100),
        systolic_bp_mmhg=_number(payload.get("systolic_bp_mmhg"), "systolic_bp_mmhg", 50, 300),
        diastolic_bp_mmhg=_number(payload.get("diastolic_bp_mmhg"), "diastolic_bp_mmhg", 20, 200),
        accel_x_g=_number(payload["accel_x_g"], "accel_x_g", -16, 16),
        accel_y_g=_number(payload["accel_y_g"], "accel_y_g", -16, 16),
        accel_z_g=_number(payload["accel_z_g"], "accel_z_g", -16, 16),
        sensor_quality=_number(payload.get("sensor_quality", 1.0), "sensor_quality", 0, 1),
        battery_pct=_number(payload.get("battery_pct"), "battery_pct", 0, 100),
        sos_pressed=bool(payload.get("sos_pressed", False)),
    )


def compact_result(result):
    event = result.emergency_event
    return {
        "risk_state": result.decision["state"],
        "risk_score": result.physiology.score,
        "activity": result.activity.activity,
        "activity_confidence": result.activity.confidence,
        "physiology_state": result.physiology.state,
        "physiology_score": result.physiology.score,
        "fall_detected": result.fall.fall_detected,
        "fall_confidence": result.fall.confidence,
        "fall_model_status": result.fall.fall_model_status,
        "trigger": event.trigger if event else None,
        "reasons": result.decision["reasons"] + result.physiology.reasons,
        "timestamp": result.physiology.timestamp,
    }


def process_json_line(line, runtime=None):
    runtime = runtime or default_runtime()
    try:
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError("JSON packet must be an object")
        result = runtime.step(packet_from_json(payload))
        return compact_result(result)
    except json.JSONDecodeError:
        return {"risk_state": "SENSOR_ERROR", "error": "invalid_json"}
    except (TypeError, ValueError) as error:
        return {"risk_state": "SENSOR_ERROR", "error": str(error)}


def main():
    parser = argparse.ArgumentParser(description="StrokeGuard Arduino JSON-lines bridge")
    parser.add_argument("--port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()
    try:
        import serial
    except ImportError as error:
        raise SystemExit("pyserial is required: python -m pip install pyserial") from error
    runtime = default_runtime()
    print(f"StrokeGuard serial bridge listening on {args.port} @ {args.baud}")
    with serial.Serial(args.port, args.baud, timeout=1) as connection:
        while True:
            raw = connection.readline()
            if not raw:
                continue
            response = process_json_line(raw.decode("utf-8", errors="replace"), runtime)
            encoded = (json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8")
            connection.write(encoded)
            print(response, flush=True)


if __name__ == "__main__":
    main()
