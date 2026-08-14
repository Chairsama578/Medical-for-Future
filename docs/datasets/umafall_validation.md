# UMAFall Raw Validation

## Result

```text
UMAFALL ACQUISITION: PASS
PROVENANCE: PASS
LICENSE: PASS
RAW SCHEMA: PASS
TIMESTAMP: PASS
SAMPLING RATE: 20.10 Hz median observed per sensor stream
ACCELEROMETER: PASS
GYROSCOPE: PASS
SUBJECT IDS: PASS
TRIAL IDS: PASS
FALL LABELS: PASS
NO_FALL LABELS: PASS
LABEL MAPPING: PASS
DATA QUALITY: FAIL
STROKEGUARD COMPATIBILITY: FAIL
```

Fall training readiness:

```text
NOT READY
```

The raw dataset is present and identifiable as UMAFall, but conversion is
blocked by malformed sensor-axis values and irregular timestamp behavior.

## Provenance

The extracted files are under:

```text
data/raw/umafall/UMAFall_Dataset/
```

The file metadata identifies:

```text
Universidad de Malaga - ETSI de Telecomunicacion (Spain)
```

The observed file naming, metadata headers, movement names, sensor types, and
five-node structure match the official UMAFall repository documentation.

Official record:

```text
https://hdl.handle.net/10630/41001
```

Sensor archive source:

```text
https://riuma.uma.es/bitstreams/d87aa5f2-bf22-47c0-9a79-eae50cc874e0/download
```

Paper:

```text
https://doi.org/10.1016/j.procs.2017.06.110
```

No archive remains locally, so an archive SHA-256 cannot be reported. The
current audit covers the extracted files only.

## License

The official RIUMA record identifies the dataset as Creative Commons
Attribution-NonCommercial 4.0 International:

```text
https://creativecommons.org/licenses/by-nc/4.0/
```

Attribution and non-commercial research restrictions apply. No local license
file was included in the extracted directory.

## Raw Structure

```text
CSV files: 746
TXT files: 0
README files: 0
License files: 0
Archive files: 0
Total extracted bytes: 287,768,818
Total measurement rows: 4,688,254
```

Every CSV uses metadata lines beginning with `%`, followed by measurement rows.
The common data header is:

```text
TimeStamp; Sample No; X-Axis; Y-Axis; Z-Axis; Sensor Type; Sensor ID;
```

Data rows use semicolon delimiters and contain a trailing semicolon. The
metadata identifies sensor types:

```text
0 = Accelerometer
1 = Gyroscope
2 = Magnetometer
```

Sensor units in the metadata are:

```text
Accelerometer: G
Gyroscope: degrees/second
Magnetometer: microtesla
```

## Labels

The labels are explicit in both filenames and metadata headers:

```text
Type of Movement: ADL
Type of Movement: FALSE
```

or:

```text
Type of Movement: FALL
Type of Movement: TRUE
```

Observed file/row counts:

| Original movement kind | Files | Rows | StrokeGuard state |
|---|---:|---:|---|
| ADL | 538 | 3,385,365 | NO_FALL |
| FALL | 208 | 1,302,889 | FALL |

Explicit fall labels:

| Original label | Evidence | StrokeGuard state |
|---|---|---|
| `forwardFall` | `Type of Movement: FALL`, `TRUE` | FALL |
| `backwardFall` | `Type of Movement: FALL`, `TRUE` | FALL |
| `lateralFall` | `Type of Movement: FALL`, `TRUE` | FALL |

Explicit ADL labels:

| Original label | Evidence | StrokeGuard state |
|---|---|---|
| `Walking` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `Jogging` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `Bending` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `Hopping` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `GoUpstairs` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `GoDownstairs` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `LyingDown_OnABed` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `Sitting_GettingUpOnAChair` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `Aplausing` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `HandsUp` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `MakingACall` | `Type of Movement: ADL`, `FALSE` | NO_FALL |
| `OpeningDoor` | `Type of Movement: ADL`, `FALSE` | NO_FALL |

No fall label was inferred from lying, transitions, acceleration magnitude, or
filename alone. The FALL/ADL mapping is supported by the source metadata.

## Subjects and Trials

```text
Subjects: 19
Subject IDs: 01 through 19
Unique (subject, trial) pairs: 97
```

The filename and metadata provide subject, movement subtype, trial, and date/
time. Trial numbers repeat across activities and dates, so a future converter
must preserve a composite record identifier rather than using trial number
alone.

Subject-grouped splitting is feasible. Windows from one subject must remain in
one of train, validation, or test.

## Sensor and Timestamp Audit

Observed sensor row counts:

```text
Accelerometer: 3,039,728
Gyroscope:       800,927
Magnetometer:    800,532
```

Observed sensor IDs:

```text
0, 1, 2, 3, 4
```

Timestamp characteristics:

```text
Timestamp present: yes
Timestamp unit: milliseconds since experiment start
Minimum observed positive resolution: 1 ms
Median observed stream rate: approximately 20.10 Hz
Median by sensor type:
  accelerometer: approximately 20.12 Hz
  gyroscope:     approximately 20.10 Hz
  magnetometer:  approximately 20.10 Hz
```

The observed per-stream rate range is broad because streams have irregular
timing, startup/termination gaps, and millisecond timestamp quantization. The
rate must be revalidated per node/record before resampling to StrokeGuard's
canonical representation.

## Data Quality

```text
Malformed sensor-axis rows: 47,067
Missing values: 0
Non-finite numeric values: 0
Duplicate sample keys: 0
Duplicate timestamps within a sensor stream: 393,766
```

The malformed rows contain non-numeric axis values such as:

```text
1.012.598.156.929.010
```

These rows were not repaired, dropped, or interpreted. Duplicate timestamps
are possible because timestamps have millisecond resolution while sensor
streams contain multiple observations; they still require explicit handling in
the future converter.

## StrokeGuard Compatibility

The source contains the required physical signals and metadata to support a
future conversion:

```text
timestamp       -> source timestamp in milliseconds
accel_x_g/y_g/z_g -> sensor type 0, selected Sensor ID
gyro_x_dps/y_dps/z_dps -> sensor type 1, selected Sensor ID
subject_id      -> metadata and filename
trial_id        -> metadata and filename
activity        -> movement subtype
fall_state      -> explicit FALL/ADL metadata
```

The magnetometer is available but not required by the current Fall contract.
Multiple sensor nodes must be selected or represented explicitly; combining
nodes without a documented policy would create leakage or duplicate windows.

Compatibility is currently `FAIL` because malformed axis values and irregular
timing must be resolved by a documented conversion policy first.

After applying the documented read-only cleaning/node policy, the initial
conversion produced 215,964 paired WAIST/CHEST accelerometer-gyroscope rows:

```text
FALL: 61,922
NO_FALL: 154,042
selected nodes: sensor 2 = 184,024 rows; sensor 1 = 31,940 rows
```

Two records have only enough valid paired data for a row but not enough
timestamp span to calculate a source sampling rate. They remain explicitly
reported as unknown rather than being assigned a population rate.

## Remaining Blockers

1. Decide whether to preserve all five nodes or select one canonical node.
2. Define handling for the 47,067 malformed axis rows without silent repair.
3. Define timestamp gap/duplicate policy per node and sensor type.
4. Confirm per-record sampling and resampling policy.
5. Create a provenance manifest with archive hash if the original archive is still available.
6. Only after those decisions create `scripts/convert_umafall.py`.
7. Only after conversion validate windows and subject-grouped splits.

No Fall model was trained. No existing Activity or Physiology component was
modified.
