import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from strokeguard.ai.model import EdgeLinearModel

def test_edge_model_loads():
    m=EdgeLinearModel(Path(__file__).resolve().parents[1]/"models/strokeguard_edge.json")
    assert len(m.classes)==3
    assert len(m.feature_names)==10
