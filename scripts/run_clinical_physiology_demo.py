"""Offline BIDMC physiology validation; never used by Arduino live mode."""

import argparse
from dataclasses import asdict
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from strokeguard.core.domain import SensorPacket
from strokeguard_v4.contracts import EmergencyEvent, PlaceholderFallDetector
from strokeguard_v4.physiology import PhysiologyRiskEngine, extract_physiology_features
from strokeguard_v4.safety import SafetyFusionV4


DATASET = PROJECT_ROOT / "data" / "unified" / "bidmc_physiology.csv"


def packets_for(data):
    return [
        SensorPacket(
            timestamp=float(row.timestamp),
            heart_rate_bpm=float(row.heart_rate_bpm) if pd.notna(row.heart_rate_bpm) else None,
            spo2_pct=float(row.spo2_pct) if pd.notna(row.spo2_pct) else None,
            systolic_bp_mmhg=None,
            diastolic_bp_mmhg=None,
            accel_x_g=None,
            accel_y_g=None,
            accel_z_g=None,
            sensor_quality=1.0,
            battery_pct=None,
        )
        for row in data.itertuples()
    ]


def run(mode, record):
    if not DATASET.exists():
        raise SystemExit(f"BIDMC unified table not found: {DATASET}")
    data = pd.read_csv(DATASET)
    data = data[data.record_id == record].dropna(subset=["heart_rate_bpm", "spo2_pct"])
    if len(data) < 40:
        raise SystemExit(f"Not enough valid BIDMC rows for {record}")
    data = data.iloc[:40].copy()
    source = "REAL BIDMC" if mode == "real" else "ENGINEERING STRESS TEST / NOT CLINICAL DATA"
    if mode == "stress":
        data["heart_rate_bpm"] = 145.0
        data["spo2_pct"] = 85.0
    packets = packets_for(data)
    engine = PhysiologyRiskEngine(persistence_windows=2)
    fusion = SafetyFusionV4(persistence=2)
    fall = PlaceholderFallDetector().decide()
    result = None
    decision = None
    for _ in range(3):
        result = engine.decide(packets, require_imu=False)
        decision = fusion.decide(
            risk_score=result.score,
            physiology_result=result,
            fall_result=fall,
            sensor_quality=result.sensor_quality,
        )
    features = extract_physiology_features(packets)
    print(f"=== BIDMC {source} ===")
    print(f"Record: {record}")
    print(f"Data source: {source}")
    print(f"HR: {features.get('hr_mean')} BPM")
    print(f"SpO2: {features.get('spo2_mean')} %")
    print(f"RR: {data.respiration_rate.mean()} BPM")
    print(f"Physiology: {result.state}")
    print(f"Risk: {decision['state']}")
    print(f"Reasons: {result.reasons}")
    if decision["state"] == "CRITICAL":
        event = EmergencyEvent(
            risk_state="CRITICAL", risk_score=result.score, trigger="v4_risk",
            reasons=result.reasons, heart_rate=features.get("hr_mean"),
            spo2=features.get("spo2_mean"), sensor_quality=result.sensor_quality,
            fall_detected=False, timestamp=time.time(),
        )
        print(f"EmergencyEvent: {event.to_dict()}")


parser = argparse.ArgumentParser(description="BIDMC offline physiology demo")
parser.add_argument("--mode", choices=["real", "stress"], default="real")
parser.add_argument("--record", default="bidmc_01")
args = parser.parse_args()
run(args.mode, args.record)
