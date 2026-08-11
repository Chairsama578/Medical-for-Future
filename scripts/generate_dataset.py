import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT/"src"))
import numpy as np, pandas as pd
from pathlib import Path
from strokeguard.ai.features import FEATURE_NAMES

rng = np.random.default_rng(42)
rows=[]
for state, n, base in [
    ("NORMAL", 1200, [72,1.5,98,97,120,80,1.0,.03,1.05,.03]),
    ("WARNING", 1200, [105,5,93,90,155,95,1.15,.20,1.6,.15]),
    ("CRITICAL", 1200, [145,10,84,78,190,112,1.70,.12,1.85,.10])
]:
    for _ in range(n):
        noise=np.array([3,1,0.7,0.8,5,4,.08,.08,.15,.06])
        x=np.array(base)+rng.normal(0,noise)
        rows.append(dict(zip(FEATURE_NAMES,x),risk_state=state))
df=pd.DataFrame(rows)
out=PROJECT_ROOT/"data/generated/strokeguard_windows.csv"
out.parent.mkdir(parents=True,exist_ok=True)
df.to_csv(out,index=False)
print(out, len(df))
