import sys, time, argparse
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT_ROOT/"src"))
from strokeguard.sensors.simulator import SensorSimulator
from strokeguard.bridge.uno_q import SimulatorBridge
from strokeguard.ai.inference import EdgeInference
from strokeguard.safety.fusion import SafetyFusion
from strokeguard.core.config import settings

ap=argparse.ArgumentParser()
ap.add_argument("--scenario",choices=["normal","warning","critical"],default="normal")
ap.add_argument("--windows",type=int,default=2)
args=ap.parse_args()

sim=SensorSimulator(args.scenario)
bridge=SimulatorBridge(sim)
inf=EdgeInference(settings.model_path,window_size=40)
fusion=SafetyFusion(2)

for i in range(args.windows*40):
    p=bridge.get_sensor_packet()
    inf.push(p)
    pred=inf.predict()
    decision=fusion.decide(p,pred)
    if i%10==0:
        print({"state":decision.state.value,"score":round(decision.score,3),
               "hr":round(p.heart_rate_bpm,1),"spo2":round(p.spo2_pct,1),
               "reasons":decision.reasons})
    time.sleep(0.01)
