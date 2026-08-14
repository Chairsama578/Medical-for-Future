# BIDMC Physiology Dataset Validation

## Current Status

```text
BIDMC: DEMO SUBSET INSTALLED
Records: bidmc_01 through bidmc_05
Physiology ML model: NOT TRAINED
Unified physiology table: CREATED
```

Expected local path after manual acquisition:

```text
data/raw/physiology/bidmc/
```

The official source is:

```text
https://www.physionet.org/content/bidmc/1.0.0/
```

The source is open access under the Open Data Commons Attribution License
v1.0. It contains 53 recordings of approximately 8 minutes each. Waveforms
include PPG, ECG, and impedance respiration at 125 Hz; numerics include HR,
SpO2, pulse rate, and respiratory rate at 1 Hz. CSV, WFDB, and MATLAB formats
are provided.

## Safe Acquisition

Acquire manually from the official PhysioNet page. Do not use an invented mirror
or automatic download command. After acquisition, place the files under:

```text
data/raw/physiology/bidmc/
```

Then run:

```powershell
$env:PYTHONPATH="src"
python scripts/validate_physiology_raw.py
```

The validator is read-only and returns exit code `2` when the directory is not
installed.

## Label Policy

BIDMC has no validated StrokeGuard stroke target. It must not be converted into
`stroke=0/1` or used to claim stroke diagnosis. Its legitimate uses here are:

- HR/SpO2/PPG/ECG signal processing
- physiology feature validation
- signal-quality and anomaly engineering
- testing missing-value and temporal handling

`NORMAL`, `PHYSIO_WARNING`, and `PHYSIO_CRITICAL` remain engineering states,
not clinical labels. Any supervised task must use source-documented labels only
and must be explicitly named as a signal/physiology task.

## Demo Subset Validation

Downloaded manually from the official directory:

```text
https://physionet.org/files/bidmc/1.0.0/bidmc_csv/
```

The subset contains 20 raw files: Numerics, Signals, Breaths, and Fix files
for records `01` through `05`. The unified Numerics table contains 2,405 rows.
HR, SpO2, and respiration rate are available. BP is not present in the
Numerics files and remains null. An ABP waveform is present in the raw Signals
file for record 04, but it has not been converted into SBP/DBP and therefore
the unified table still keeps BP null. PPG/ECG remain available in the raw
Signals files but are not copied into the Numerics unified table.

Observed Numerics quality:

```text
Records: 5
Rows: 2405
Numeric sampling: 1 Hz
HR: available
SpO2: available with some missing values
Respiration rate: available
BP: unavailable
Stroke labels: unavailable
```

Output:

```text
data/unified/bidmc_physiology.csv
```

## Current Blocker

No clinical stroke target exists, so no supervised stroke/physiology diagnosis
model was trained. The existing rule-based `PhysiologyRiskEngine` remains the
primary demo physiology branch. BIDMC is used for offline signal/feature
validation only.
