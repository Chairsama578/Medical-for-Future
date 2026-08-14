import sys, logging
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT_ROOT/"src"))
from strokeguard.core.config import settings
from strokeguard.bridge.uno_q import UnoQBridge, SimulatorBridge
from strokeguard.sensors.simulator import SensorSimulator
from strokeguard.ai.inference import EdgeInference
from strokeguard.core.runtime import StrokeGuardEngine

logging.basicConfig(level=logging.INFO)
if settings.mode=="simulator":
    bridge=SimulatorBridge(SensorSimulator("critical"))
else:
    bridge=UnoQBridge(settings.bridge_socket,settings.mode)

engine=StrokeGuardEngine(
    bridge,
    EdgeInference(settings.model_path,max(10,int(settings.poll_hz*settings.window_seconds)))
)
engine.run_forever()
