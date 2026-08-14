"""Convert validated UMAFall node-0 streams without modifying raw files."""

from collections import Counter, defaultdict
from pathlib import Path
import csv
import json
import math
import re
import statistics


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "data" / "raw" / "umafall"
OUTPUT = PROJECT_ROOT / "data" / "unified" / "umafall.csv"
REPORT = PROJECT_ROOT / "data" / "unified" / "umafall_conversion_report.json"
PROVENANCE = ROOT / "provenance.json"
TARGET_RATE_HZ = 20.0
PRIMARY_NODE_ID = 2
NODE_PRIORITY = (2, 1, 3, 4)
PAIR_TOLERANCE_MS = 50.0
LINE_PATTERN = re.compile(
    r"UMAFall_Subject_(?P<subject>\d+)_(?P<kind>ADL|Fall)_(?P<activity>[^_]+(?:_[^_]+)*)_(?P<trial>\d+)_"
)


def load_policy():
    if not PROVENANCE.exists():
        raise SystemExit("provenance.json is required before UMAFall conversion")
    metadata = json.loads(PROVENANCE.read_text(encoding="utf-8"))
    required = [
        "activity_mapping_verified", "fall_mapping_verified", "sensor_mapping_verified",
        "timestamp_policy_verified", "malformed_row_policy", "primary_node_id",
        "accelerometer_node_id", "gyroscope_node_id", "timestamp_alignment_method",
        "resampling_method", "maximum_allowed_gap_seconds",
    ]
    missing = [field for field in required if field not in metadata]
    if missing:
        raise SystemExit(f"provenance.json missing policy fields: {missing}")
    if not all(metadata[field] is True for field in [
        "activity_mapping_verified", "fall_mapping_verified", "sensor_mapping_verified",
        "timestamp_policy_verified",
    ]):
        raise SystemExit("Verified UMAFall mapping/timestamp policy is required")
    if metadata["primary_node_id"] != PRIMARY_NODE_ID:
        raise SystemExit("Unexpected primary node policy")
    if tuple(metadata.get("primary_node_candidates", [])) != NODE_PRIORITY:
        raise SystemExit("Primary node priority policy does not match converter")
    return metadata


def parse_file(path):
    match = LINE_PATTERN.search(path.name)
    if not match:
        raise ValueError(f"Filename metadata is ambiguous: {path.name}")
    subject = match.group("subject")
    kind = match.group("kind").upper()
    activity = match.group("activity")
    trial = match.group("trial")
    fall_state = "FALL" if kind == "FALL" else "NO_FALL"
    fall_type = activity if fall_state == "FALL" else ""
    streams = defaultdict(dict)
    raw_rows = 0
    excluded = 0
    excluded_reasons = Counter()
    source_timestamps = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for raw in handle:
            line = raw.rstrip("\r\n")
            if line.startswith("%") or not line.strip():
                continue
            parts = line.split(";")
            if len(parts) == 8 and not parts[-1].strip():
                parts = parts[:-1]
            if not any(value.strip() for value in parts):
                continue
            if parts[0].strip().lower() == "timestamp":
                continue
            raw_rows += 1
            if len(parts) != 7:
                excluded += 1
                excluded_reasons["malformed_structure"] += 1
                continue
            try:
                timestamp = float(parts[0])
                sample = int(parts[1])
                axes = [float(value) for value in parts[2:5]]
                sensor_type = int(parts[5])
                sensor_id = int(parts[6])
                if not all(math.isfinite(value) for value in [timestamp, *axes]):
                    raise ValueError("nonfinite")
            except (TypeError, ValueError):
                excluded += 1
                excluded_reasons["malformed_numeric_sensor_row"] += 1
                continue
            source_timestamps.append(timestamp)
            if sensor_type in (0, 1) and sensor_id in NODE_PRIORITY:
                if sample in streams[(sensor_type, sensor_id)]:
                    raise ValueError(f"Duplicate primary-node sample: {path.name} {sensor_type} {sample}")
                streams[(sensor_type, sensor_id)][sample] = (timestamp, *axes)
    selected_node = next(
        (node for node in NODE_PRIORITY if streams[(0, node)] and streams[(1, node)]),
        None,
    )
    if selected_node is None:
        raise ValueError(f"No node has paired accelerometer/gyroscope samples: {path.name}")
    accel_samples = sorted(streams[(0, selected_node)].items(), key=lambda item: item[1][0])
    gyro_samples = sorted(streams[(1, selected_node)].items(), key=lambda item: item[1][0])
    pairs = []
    gyro_index = 0
    used_gyro = set()
    for accel_sample, accel in accel_samples:
        while gyro_index + 1 < len(gyro_samples) and gyro_samples[gyro_index + 1][1][0] <= accel[0]:
            gyro_index += 1
        candidates = [gyro_index]
        if gyro_index + 1 < len(gyro_samples):
            candidates.append(gyro_index + 1)
        best = min(candidates, key=lambda index: abs(gyro_samples[index][1][0] - accel[0])) if candidates else None
        if best is None or best in used_gyro or abs(gyro_samples[best][1][0] - accel[0]) > PAIR_TOLERANCE_MS:
            continue
        used_gyro.add(best)
        pairs.append((accel_sample, gyro_samples[best][0], accel, gyro_samples[best][1]))
    if not pairs:
        raise ValueError(f"No paired accelerometer/gyroscope samples: {path.name}")
    rows = []
    paired_timestamps = []
    for accel_sample, gyro_sample, accel, gyro in pairs:
        timestamp_ms = (accel[0] + gyro[0]) / 2.0
        paired_timestamps.append(timestamp_ms)
        rows.append({
            "timestamp": timestamp_ms / 1000.0,
            "subject_id": subject,
            "trial_id": path.stem,
            "activity": activity,
            "fall_state": fall_state,
            "fall_type": fall_type,
            "accel_x_g": accel[1], "accel_y_g": accel[2], "accel_z_g": accel[3],
            "gyro_x_dps": gyro[1], "gyro_y_dps": gyro[2], "gyro_z_dps": gyro[3],
            "sensor_id": selected_node,
            "accel_sample_no": accel_sample,
            "gyro_sample_no": gyro_sample,
            "source_dataset": "umafall",
            "source_sample_rate_hz": None,
        })
    observed_rate = None
    if len(paired_timestamps) > 1 and paired_timestamps[-1] > paired_timestamps[0]:
        observed_rate = (len(paired_timestamps) - 1) / ((paired_timestamps[-1] - paired_timestamps[0]) / 1000.0)
    for row in rows:
        row["source_sample_rate_hz"] = observed_rate
    return rows, {
        "raw_rows": raw_rows,
        "valid_primary_pairs": len(rows),
        "excluded_rows": excluded,
        "excluded_reasons": dict(excluded_reasons),
        "unpaired_primary_samples": len(set(streams[0]) ^ set(streams[1])),
        "subject": subject,
        "kind": kind,
        "activity": activity,
        "path": str(path.relative_to(PROJECT_ROOT)),
        "selected_node": selected_node,
        "source_timestamp_min": min(paired_timestamps) if paired_timestamps else None,
        "source_timestamp_max": max(paired_timestamps) if paired_timestamps else None,
        "source_sample_rate_hz": observed_rate,
    }


def main():
    policy = load_policy()
    files = sorted(ROOT.glob("UMAFall_Dataset/*.csv"))
    if not files:
        raise SystemExit("No UMAFall CSV files found")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp", "subject_id", "trial_id", "activity", "fall_state", "fall_type",
        "accel_x_g", "accel_y_g", "accel_z_g", "gyro_x_dps", "gyro_y_dps", "gyro_z_dps",
        "sensor_id", "accel_sample_no", "gyro_sample_no", "source_dataset", "source_sample_rate_hz",
    ]
    totals = Counter()
    class_rows = Counter()
    selected_nodes = Counter()
    subjects = set()
    trials = set()
    rates = []
    rate_unknown_records = 0
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for path in files:
            rows, report = parse_file(path)
            writer.writerows(rows)
            totals["raw_rows"] += report["raw_rows"]
            totals["valid_rows"] += report["valid_primary_pairs"]
            totals["excluded_rows"] += report["excluded_rows"]
            totals["unpaired_primary_samples"] += report["unpaired_primary_samples"]
            class_rows[report["kind"]] += len(rows)
            selected_nodes[report["selected_node"]] += len(rows)
            subjects.add(report["subject"])
            trials.add((report["subject"], report["path"]))
            if report["source_timestamp_min"] is not None and report["source_timestamp_max"] > report["source_timestamp_min"]:
                rates.append(report["valid_primary_pairs"] / ((report["source_timestamp_max"] - report["source_timestamp_min"]) / 1000.0))
            elif report["valid_primary_pairs"]:
                rate_unknown_records += report["valid_primary_pairs"]
    conversion_report = {
        "dataset": "UMAFall",
        "policy": policy,
        "raw_rows": totals["raw_rows"],
        "raw_valid_rows": totals["raw_rows"] - totals["excluded_rows"],
        "valid_rows": totals["valid_rows"],
        "raw_valid_rows_not_emitted_by_node_policy": totals["raw_rows"] - totals["excluded_rows"] - totals["valid_rows"],
        "excluded_rows": totals["excluded_rows"],
        "excluded_percentage": totals["excluded_rows"] / totals["raw_rows"] * 100,
        "unpaired_primary_samples": totals["unpaired_primary_samples"],
        "rate_unknown_records": rate_unknown_records,
        "fall_rows": class_rows["FALL"],
        "no_fall_rows": class_rows["ADL"],
        "selected_node_rows": dict(selected_nodes),
        "subjects": sorted(subjects),
        "trials": len(trials),
        "sampling_rate_before_median_hz": statistics.median(rates) if rates else None,
        "sampling_rate_after_hz": TARGET_RATE_HZ,
        "resampling_applied": False,
        "output": str(OUTPUT.relative_to(PROJECT_ROOT)),
    }
    REPORT.write_text(json.dumps(conversion_report, indent=2), encoding="utf-8")
    print(json.dumps(conversion_report, indent=2))


if __name__ == "__main__":
    main()
