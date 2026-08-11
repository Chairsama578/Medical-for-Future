import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from strokeguard.safety.fusion import SafetyFusion
from strokeguard.core.domain import *

def test_sos_overrides():
    d=SafetyFusion().decide(
        SensorPacket(timestamp=1,sos_pressed=True),
        Prediction(RiskState.NORMAL,0.1,{"NORMAL":.9})
    )
    assert d.emergency and d.sos and d.state == RiskState.CRITICAL

def test_fast_overrides():
    s=FastSymptoms(face_drooping=True)
    d=SafetyFusion().decide(
        SensorPacket(timestamp=1),
        Prediction(RiskState.NORMAL,0.1,{"NORMAL":.9}),
        s
    )
    assert d.emergency and d.state == RiskState.CRITICAL
