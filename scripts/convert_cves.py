from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "raw" / "cves"
OUTPUT = PROJECT_ROOT / "data" / "unified"
OUTPUT.mkdir(parents=True, exist_ok=True)
source = ROOT / "subjects.csv"
if not source.exists():
    raise SystemExit("Put CVES subjects.csv under data/raw/cves/")
data = pd.read_csv(source)
data["source_dataset"] = "cves"
data.to_csv(OUTPUT / "cves_subjects.csv", index=False)
print("CVES subject metadata indexed; do not load the 173.9GB database into RAM.")
