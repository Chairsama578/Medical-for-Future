"""Read-only structural and quality audit for an acquired UMAFall dataset."""

from collections import Counter, defaultdict
from pathlib import Path
import csv
import math
import re
import statistics


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "raw" / "umafall"
FILE_PATTERN = re.compile(
    r"UMAFall_Subject_(?P<subject>\d+)_(?P<kind>ADL|Fall)_(?P<activity>[^_]+(?:_[^_]+)*)_(?P<trial>\d+)_"
)


def metadata_value(lines, prefix):
    for line in lines:
        if line.lower().startswith(prefix.lower()):
            return line.split(":", 1)[1].strip()
    return None


def audit_file(path):
    header = []
    data_rows = 0
    malformed = 0
    missing = 0
    nonfinite = 0
    malformed_fields = Counter()
    malformed_sensor_types = Counter()
    malformed_sensor_ids = Counter()
    malformed_axis_patterns = Counter()
    duplicate_samples = 0
    duplicate_timestamps = 0
    sensor_types = Counter()
    sensor_ids = Counter()
    node_positions = set()
    stream_last = {}
    stream_first = {}
    stream_counts = Counter()
    stream_diffs = defaultdict(list)
    samples_seen = set()
    timestamps_seen = set()
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for raw in handle:
            line = raw.rstrip("\r\n")
            if line.startswith("%") or not line.strip():
                if line.startswith("%"):
                    header.append(line)
                    node_match = re.search(r";\s*(\d+);\s*([^;]+);\s*(.+?)\s*$", line)
                    if node_match:
                        node_positions.add(
                            (node_match.group(1), node_match.group(2).strip(), node_match.group(3).strip())
                        )
                continue
            parts = line.split(";")
            if len(parts) == 8 and not parts[-1].strip():
                parts = parts[:-1]
            if not any(value.strip() for value in parts):
                continue
            if parts[0].strip().lower() in {"timestamp", "timestamp"}:
                continue
            if len(parts) != 7:
                if len(parts) >= 7:
                    malformed_sensor_types[parts[5].strip()] += 1
                    malformed_sensor_ids[parts[6].strip()] += 1
                malformed += 1
                continue
            data_rows += 1
            if any(not value.strip() for value in parts):
                missing += 1
            try:
                timestamp = float(parts[0])
            except ValueError:
                if len(parts) >= 7:
                    malformed_sensor_types[parts[5].strip()] += 1
                    malformed_sensor_ids[parts[6].strip()] += 1
                malformed_fields["timestamp"] += 1
                malformed += 1
                continue
            try:
                sample = int(parts[1])
            except ValueError:
                malformed_sensor_types[parts[5].strip()] += 1
                malformed_sensor_ids[parts[6].strip()] += 1
                malformed_fields["sample"] += 1
                malformed += 1
                continue
            try:
                axes = [float(value) for value in parts[2:5]]
            except ValueError:
                malformed_sensor_types[parts[5].strip()] += 1
                malformed_sensor_ids[parts[6].strip()] += 1
                malformed_fields["sensor_axes"] += 1
                for value in parts[2:5]:
                    try:
                        float(value)
                    except ValueError:
                        malformed_axis_patterns[
                            "grouped_decimal" if re.fullmatch(r"-?\d(?:\.\d{3})+", value.strip()) else "other"
                        ] += 1
                malformed += 1
                continue
            try:
                sensor_type = int(parts[5])
                sensor_id = int(parts[6])
            except ValueError:
                malformed_sensor_types[parts[5].strip()] += 1
                malformed_sensor_ids[parts[6].strip()] += 1
                malformed_fields["sensor_metadata"] += 1
                malformed += 1
                continue
            if not all(math.isfinite(value) for value in [timestamp, *axes]):
                nonfinite += 1
            sensor_types[sensor_type] += 1
            sensor_ids[sensor_id] += 1
            sample_key = (sensor_type, sensor_id, sample)
            timestamp_key = (sensor_type, sensor_id, timestamp)
            if sample_key in samples_seen:
                duplicate_samples += 1
            if timestamp_key in timestamps_seen:
                duplicate_timestamps += 1
            samples_seen.add(sample_key)
            timestamps_seen.add(timestamp_key)
            stream = (sensor_type, sensor_id)
            stream_first.setdefault(stream, timestamp)
            stream_counts[stream] += 1
            if stream in stream_last:
                delta = timestamp - stream_last[stream]
                if delta > 0:
                    stream_diffs[stream].append(delta)
            stream_last[stream] = timestamp

    match = FILE_PATTERN.search(path.name)
    subject = match.group("subject") if match else None
    kind = match.group("kind").upper() if match else None
    activity = match.group("activity") if match else None
    trial = match.group("trial") if match else None
    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "rows": data_rows,
        "malformed": malformed,
        "missing": missing,
        "nonfinite": nonfinite,
        "malformed_fields": malformed_fields,
        "malformed_sensor_types": malformed_sensor_types,
        "malformed_sensor_ids": malformed_sensor_ids,
        "malformed_axis_patterns": malformed_axis_patterns,
        "duplicate_samples": duplicate_samples,
        "duplicate_timestamps": duplicate_timestamps,
        "sensor_types": sensor_types,
        "sensor_ids": sensor_ids,
        "node_positions": node_positions,
        "subject": subject,
        "kind": kind,
        "activity": activity,
        "trial": trial,
        "header": header,
        "stream_diffs": stream_diffs,
        "stream_first": stream_first,
        "stream_last": stream_last,
        "stream_counts": stream_counts,
    }


def main():
    files = sorted(ROOT.rglob("*.csv")) if ROOT.exists() else []
    if not files:
        print("UMAFALL RAW DATA NOT INSTALLED")
        return 2
    results = [audit_file(path) for path in files]
    total_rows = sum(item["rows"] for item in results)
    total_malformed = sum(item["malformed"] for item in results)
    total_missing = sum(item["missing"] for item in results)
    total_nonfinite = sum(item["nonfinite"] for item in results)
    malformed_fields = Counter()
    malformed_sensor_types = Counter()
    malformed_sensor_ids = Counter()
    malformed_axis_patterns = Counter()
    total_duplicate_samples = sum(item["duplicate_samples"] for item in results)
    total_duplicate_timestamps = sum(item["duplicate_timestamps"] for item in results)
    subjects = sorted({item["subject"] for item in results if item["subject"]})
    trials = sorted({(item["subject"], item["trial"]) for item in results if item["subject"] and item["trial"]})
    kinds = Counter(item["kind"] or "UNKNOWN" for item in results)
    activities = Counter(item["activity"] or "UNKNOWN" for item in results)
    kind_rows = Counter()
    activity_rows = Counter()
    sensor_types = Counter()
    sensor_ids = Counter()
    node_positions = set()
    all_diffs = []
    rates = []
    rates_by_type = defaultdict(list)
    for item in results:
        sensor_types.update(item["sensor_types"])
        sensor_ids.update(item["sensor_ids"])
        node_positions.update(item["node_positions"])
        kind_rows[item["kind"] or "UNKNOWN"] += item["rows"]
        activity_rows[item["activity"] or "UNKNOWN"] += item["rows"]
        malformed_fields.update(item["malformed_fields"])
        malformed_sensor_types.update(item["malformed_sensor_types"])
        malformed_sensor_ids.update(item["malformed_sensor_ids"])
        malformed_axis_patterns.update(item["malformed_axis_patterns"])
        for diffs in item["stream_diffs"].values():
            all_diffs.extend(diffs)
        for stream, count in item["stream_counts"].items():
            elapsed_ms = item["stream_last"][stream] - item["stream_first"][stream]
            if count > 1 and elapsed_ms > 0:
                rate = (count - 1) / (elapsed_ms / 1000.0)
                rates.append(rate)
                rates_by_type[stream[0]].append(rate)
    header_counts = Counter(tuple(item["header"][-1:]) for item in results)
    print(f"FILES={len(files)}")
    print(f"TOTAL_ROWS={total_rows}")
    print(f"TOTAL_BYTES={sum(path.stat().st_size for path in files)}")
    print(f"SUBJECTS={len(subjects)}:{subjects}")
    print(f"TRIALS={len(trials)}")
    print(f"MOVEMENT_KINDS={dict(kinds)}")
    print(f"MOVEMENT_KIND_ROWS={dict(kind_rows)}")
    print(f"ACTIVITY_TOKENS={dict(activities)}")
    print(f"ACTIVITY_TOKEN_ROWS={dict(activity_rows)}")
    print(f"SENSOR_TYPES={dict(sensor_types)}")
    print(f"SENSOR_IDS={dict(sensor_ids)}")
    print(f"NODE_POSITIONS={sorted(node_positions)}")
    print(f"HEADERS={dict(header_counts)}")
    print(f"MALFORMED_ROWS={total_malformed}")
    print(f"MALFORMED_FIELDS={dict(malformed_fields)}")
    print(f"MALFORMED_BY_SENSOR_TYPE={dict(malformed_sensor_types)}")
    print(f"MALFORMED_BY_SENSOR_ID={dict(malformed_sensor_ids)}")
    print(f"MALFORMED_AXIS_PATTERNS={dict(malformed_axis_patterns)}")
    malformed_by_subject = Counter()
    malformed_by_activity = Counter()
    malformed_by_fall_state = Counter()
    for item in results:
        if item["malformed"]:
            malformed_by_subject[item["subject"] or "UNKNOWN"] += item["malformed"]
            malformed_by_activity[item["activity"] or "UNKNOWN"] += item["malformed"]
            malformed_by_fall_state[item["kind"] or "UNKNOWN"] += item["malformed"]
    malformed_by_file = {
        item["path"]: item["malformed"] for item in results if item["malformed"]
    }
    print(f"MALFORMED_BY_SUBJECT={dict(malformed_by_subject)}")
    print(f"MALFORMED_BY_ACTIVITY={dict(malformed_by_activity)}")
    print(f"MALFORMED_BY_FALL_STATE={dict(malformed_by_fall_state)}")
    print(f"MALFORMED_FILE_COUNT={len(malformed_by_file)}")
    print(f"MALFORMED_BY_FILE={malformed_by_file}")
    print(f"MISSING_VALUES={total_missing}")
    print(f"NONFINITE_VALUES={total_nonfinite}")
    print(f"DUPLICATE_SAMPLES={total_duplicate_samples}")
    print(f"DUPLICATE_TIMESTAMPS_PER_STREAM={total_duplicate_timestamps}")
    print(f"TIMESTAMP_RESOLUTION_MS_MIN={min(all_diffs) if all_diffs else 'UNKNOWN'}")
    print(
        "TIMESTAMP_RATE_HZ_MEDIAN="
        f"{statistics.median(rates) if rates else 'UNKNOWN'}"
    )
    print(
        "TIMESTAMP_RATE_HZ_RANGE="
        f"{(min(rates), max(rates)) if rates else 'UNKNOWN'}"
    )
    print(
        "TIMESTAMP_RATE_HZ_MEDIAN_BY_SENSOR_TYPE="
        f"{ {sensor_type: statistics.median(values) for sensor_type, values in rates_by_type.items()} }"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
