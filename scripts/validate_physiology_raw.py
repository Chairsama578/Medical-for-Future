"""Read-only validator for manually acquired PhysioNet physiology data."""

from pathlib import Path
import re
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "raw" / "physiology"
SIGNAL_TOKENS = {
    "hr": ("hr", "heart", "pulse"),
    "spo2": ("spo2", "oxygen", "saturation"),
    "bp": ("sbp", "dbp", "abp", "blood"),
    "ppg": ("ppg", "pleth"),
    "ecg": ("ecg", "ekg", "ii", "avr"),
    "resp": ("resp", "respiration"),
}


def detect_signals(names):
    result = {}
    for signal, tokens in SIGNAL_TOKENS.items():
        result[signal] = sorted({
            str(name) for name in names
            if any(token in str(name).lower() for token in tokens)
        })
    return result


def inspect_csv(path):
    header = pd.read_csv(path, nrows=0)
    rows = 0
    missing = 0
    malformed = 0
    time_values = []
    time_columns = [column for column in header.columns if "time" in str(column).lower()]
    for chunk in pd.read_csv(path, chunksize=100000):
        rows += len(chunk)
        missing += int(chunk.isna().sum().sum())
        for column in chunk.columns:
            if any(token in str(column).lower() for values in SIGNAL_TOKENS.values() for token in values):
                malformed += int(pd.to_numeric(chunk[column], errors="coerce").isna().sum() - chunk[column].isna().sum())
        if time_columns:
            time_values.extend(pd.to_numeric(chunk[time_columns[0]], errors="coerce").dropna().tolist())
    print(f"FILE={path.relative_to(PROJECT_ROOT)}")
    print(f"ROWS={rows}")
    print(f"COLUMNS={list(header.columns)}")
    print(f"SIGNALS={detect_signals(header.columns)}")
    print(f"TIME_COLUMNS={time_columns}")
    print(f"DURATION_SECONDS={(max(time_values) - min(time_values)) if time_values else 'UNKNOWN'}")
    print(f"SAMPLING_RATE_HZ={(len(time_values) - 1) / (max(time_values) - min(time_values)) if len(time_values) > 1 and max(time_values) > min(time_values) else 'UNKNOWN'}")
    print(f"MISSING_VALUES={missing}")
    print(f"MALFORMED_NUMERIC_VALUES={malformed}")
    return rows


def inspect_wfdb_headers(files):
    headers = sorted(files.rglob("*.hea"))
    for path in headers:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        first = lines[0] if lines else ""
        signals = [line for line in lines[1:] if line and not line.startswith("#")]
        print(f"WFDB={path.relative_to(PROJECT_ROOT)}")
        print(f"HEADER={first}")
        print(f"SIGNAL_LINES={signals[:8]}")
    return len(headers)


def main():
    if not ROOT.exists():
        print("PHYSIOLOGY DATA NOT INSTALLED")
        return 2
    files = sorted(path for path in ROOT.rglob("*") if path.is_file())
    if not files:
        print("PHYSIOLOGY DATA NOT INSTALLED")
        return 2
    csv_files = [path for path in files if path.suffix.lower() == ".csv"]
    print(f"ROOT={ROOT}")
    print(f"FILES={len(files)}")
    print(f"CSV_FILES={len(csv_files)}")
    record_ids = sorted({match.group(1) for path in files if (match := re.search(r"bidmc[_-]?(\d+)", path.name, re.I))})
    print(f"RECORD_IDS={record_ids}")
    print(f"DATASET_STATUS={'FULL DATASET' if len(record_ids) == 53 else 'DEMO SUBSET INSTALLED'}")
    print(f"WFDB_HEADERS={inspect_wfdb_headers(ROOT)}")
    total_rows = sum(inspect_csv(path) for path in csv_files)
    print(f"TOTAL_CSV_ROWS={total_rows}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
