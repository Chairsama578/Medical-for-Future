import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from strokeguard.core.domain import SensorPacket
from strokeguard_v4.physiology import PhysiologyRiskEngine, extract_physiology_features
from strokeguard_v4.safety import SafetyFusionV4


def main():
    packets = [
        SensorPacket(
            timestamp=index, heart_rate_bpm=72, spo2_pct=98,
            accel_x_g=0, accel_y_g=0, accel_z_g=1, sensor_quality=0.98,
        )
        for index in range(40)
    ]
    iterations = 1000
    started = time.perf_counter()
    for _ in range(iterations):
        extract_physiology_features(packets)
    feature_ms = (time.perf_counter() - started) * 1000 / iterations

    engine = PhysiologyRiskEngine()
    started = time.perf_counter()
    for _ in range(iterations):
        result = engine.decide(packets)
    physiology_ms = (time.perf_counter() - started) * 1000 / iterations

    fusion = SafetyFusionV4()
    started = time.perf_counter()
    for _ in range(iterations):
        fusion.decide(physiology_result=result)
    fusion_ms = (time.perf_counter() - started) * 1000 / iterations
    print({
        "iterations": iterations,
        "feature_extraction_ms": feature_ms,
        "physiology_decision_ms": physiology_ms,
        "safety_fusion_ms": fusion_ms,
        "combined_ms": feature_ms + physiology_ms + fusion_ms,
        "note": "Python workstation benchmark; not an UNO Q measurement",
    })


if __name__ == "__main__":
    main()
