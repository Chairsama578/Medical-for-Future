import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from strokeguard_v4.physiology import PhysiologyRiskEngine
from strokeguard_v4.physiology_simulator import SCENARIOS, PhysiologySimulator
from strokeguard_v4.safety import SafetyFusionV4


parser = argparse.ArgumentParser(description="Synthetic physiology risk demo")
parser.add_argument("--scenario", choices=sorted(set(SCENARIOS) | {"critical"}), default="normal")
parser.add_argument("--windows", type=int, default=3)
args = parser.parse_args()

simulator = PhysiologySimulator("critical_physiology" if args.scenario == "critical" else args.scenario)
engine = PhysiologyRiskEngine()
fusion = SafetyFusionV4()
for index in range(args.windows):
    packets = [simulator.next_packet() for _ in range(40)]
    result = engine.decide(packets)
    decision = fusion.decide(
        physiology_result=result,
        manual_sos=args.scenario == "manual_sos",
    )
    print({
        "synthetic": simulator.synthetic,
        "scenario": args.scenario,
        "window": index + 1,
        "physiology_state": result.state,
        "score": round(result.score, 3),
        "confidence": round(result.confidence, 3),
        "sensor_quality": round(result.sensor_quality, 3),
        "safety_state": decision["state"],
        "reasons": result.reasons + decision["reasons"],
    })
