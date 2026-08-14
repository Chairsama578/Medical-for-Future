import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from strokeguard.ai.features import extract, FEATURE_NAMES
from strokeguard.core.domain import SensorPacket

def test_feature_count():
    p=[SensorPacket(timestamp=i,heart_rate_bpm=70,spo2_pct=98,systolic_bp_mmhg=120,diastolic_bp_mmhg=80) for i in range(10)]
    x=extract(p)
    assert len(x)==len(FEATURE_NAMES)
