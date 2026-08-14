# UMAFall Conversion Policy

## Status

The acquired UMAFall files are genuine and explicitly labeled, but 47,067
measurement rows contain malformed sensor-axis tokens. The raw files are
read-only and are never rewritten.

## 1. Malformed Rows

The malformed rows are concentrated in 20 ADL files for subject 13. They affect
sensor-axis fields across sensor types 0, 1, and 2. Examples include tokens
with multiple decimal separators such as:

```text
1.012.598.156.929.010
```

Repeated metadata/header and separator rows are parser records, not sensor
measurements, and are ignored by the validator/converter. The remaining
malformed measurement rows are genuine non-parseable numeric records.

Cleaning policy:

```text
Policy A: exclude only malformed measurement rows.
```

No value repair, interpolation, replacement, clipping, or fabricated sample is
performed. The conversion report records the exact excluded count and files.

## 2. Timestamp Policy

Source timestamps are milliseconds. The observed median stream rate is about
20.10 Hz, with irregular per-stream rates and millisecond timestamp collisions.

```text
target_sample_rate_hz: 20
timestamp_alignment_method: pair by sensor_id + sample_no
output_timestamp: mean of paired accelerometer/gyroscope source timestamps
maximum_allowed_gap_seconds: 0.25, for reporting/quality gating
```

The converter does not resample or interpolate. It preserves cleaned source
observations and records `source_sample_rate_hz`. A later windowing stage may
resample to a 20 Hz grid after reviewing gap statistics. No interpolation is
allowed across gaps larger than 0.25 seconds.

Records with insufficient timestamp span to calculate a source rate retain a
missing source-rate value and are reported as conversion blockers; no global
rate is substituted for them.

## 3. Duplicate Timestamps

Timestamp collisions are expected because timestamps have millisecond
resolution and distinct samples can share a timestamp. They are not duplicate
measurements when `sample_no` differs.

Policy:

```text
pair and preserve distinct sample_no records
never deduplicate by timestamp alone
```

## 4. Sensor Node Policy

Metadata consistently identifies:

```text
Sensor ID 0: RIGHTPOCKET smartphone
Sensor ID 1: CHEST SensorTag
Sensor ID 2: WAIST SensorTag
Sensor ID 3: WRIST SensorTag
Sensor ID 4: ANKLE SensorTag
```

The smartphone node 0 contains accelerometer data but does not provide the
paired gyroscope stream required by the initial Fall schema. SensorTag node 2
is selected because it is the WAIST node and contains the paired accelerometer
and gyroscope streams.

Initial Fall schema policy:

```text
PRIMARY_NODE_PREFERENCE: sensor ID 2 (WAIST)
FALLBACK_NODES: sensor ID 1 (CHEST), 3 (WRIST), 4 (ANKLE)
NODE_SELECTION: first preferred node with paired accelerometer + gyroscope
MAGNETOMETER: ignored in initial Fall schema
```

Accelerometer and gyroscope are paired only within the selected node by nearest
source timestamp, with a maximum 50 ms pairing tolerance. Sample
numbers are preserved as source metadata but are not used as cross-sensor keys
because their streams have observed offsets. Other nodes are not silently
merged or discarded from the raw source; they are excluded from this first
normalized branch by documented policy. The selected `sensor_id` is preserved
per output row and the node-selection distribution is written to the report.

## 5. Label Policy

Only explicit metadata is used:

```text
forwardFall  -> FALL
backwardFall -> FALL
lateralFall  -> FALL
all official ADL movement types -> NO_FALL
```

`fall_type` preserves the exact fall subtype for FALL rows. No fall label is
inferred from lying, inactivity, acceleration peaks, or filenames alone.

## 6. Subject Split Policy

The deterministic subject-grouped split policy is:

```text
TRAIN:      subjects 01-11
VALIDATION: subjects 12-15
TEST:       subjects 16-19
```

No subject may occur in more than one split. Class counts must be checked after
conversion before any training begins.

## 7. Fall Window Policy

The Fall branch has its own window configuration and does not change Activity
AI:

```text
source_rate: approximately 20 Hz
target_rate: 20 Hz
window_seconds: 2
window_size: 40 samples
stride: 10 samples
```

This preserves short impact/post-impact behavior better than the Activity
branch's 8-second window. The converter does not create windows.

## 8. Unified Schema

The planned output is:

```text
data/unified/umafall.csv
```

Required fields:

```text
timestamp
subject_id
trial_id
activity
fall_state
fall_type
accel_x_g
accel_y_g
accel_z_g
sensor_id
source_dataset
source_sample_rate_hz
```

No physiological fields are fabricated.

## 9. Provenance

`data/raw/umafall/provenance.json` records:

```text
archive_sha256: null because the archive is not present locally
extracted_tree_hash: available
file_count: 746
```

The extracted tree hash is a deterministic hash of sorted relative paths and
per-file SHA-256 values.

## 10. Remaining Risks

- The original archive hash cannot be independently verified locally.
- Some sensor-axis values are malformed and will be excluded.
- Source timestamps are irregular and collide at millisecond resolution.
- Node 0 is a documented first policy, not a claim that other nodes are useless.
- UMAFall contains emulated falls, not clinical real-world falls.
- No Fall model or clinical validation is authorized yet.
