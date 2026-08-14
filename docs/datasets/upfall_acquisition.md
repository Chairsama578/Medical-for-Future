# UP-Fall Acquisition Guide

## Current Status

```text
UP-FALL RAW SENSOR DATA: NOT INSTALLED
ACQUISITION: MANUAL / EXTERNAL SOURCE REQUIRED
DIRECT CHALLENGE UP DOWNLOAD: UNAVAILABLE
AUTOMATIC DOWNLOAD: DISABLED
```

The local directory is currently empty:

```text
data/raw/upfall/
```

## Provenance References

The following references are retained as provenance and research references:

- Historical official Challenge UP page: https://sites.google.com/up.edu.mx/challenge-up-2019/data
- Original UP-Fall paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC6539235/
- Sensors publication: https://www.mdpi.com/1424-8220/19/9/1988

The Challenge UP page is a historical official competition/provenance page.
Its current dataset section states that the competition dataset files are no
longer publicly downloadable there. It must not be presented as a direct
download endpoint.

No replacement download URL is recorded or invented by this repository.

## Dataset Distinction

### Original UP-Fall Detection Dataset

This is the target dataset for the StrokeGuard Fall AI branch. It is the
original research dataset containing wearable, ambient, and vision modalities,
with 17 healthy young subjects, 11 activities, and 3 trials per activity. The
original consolidated wearable/sensor data must be acquired from a verified or

### Challenge UP

The Challenge UP page is retained only for historical provenance and source
context. Its current page explicitly says that the dataset files are no longer
public there.

### 3D Skeletons UP-Fall Dataset

https://zenodo.org/records/12773013 is a separate later 3D skeleton/impact
dataset. Its `joint_*` coordinate and `LABEL` schema is not the original raw
wearable sensor dataset expected by this repository.

Do not download the Zenodo skeleton dataset into `data/raw/upfall/`. Do not
modify `convert_upfall.py` to consume skeleton data. Do not treat it as an
automatic replacement for the original UP-Fall sensor dataset.

## Manual Acquisition Checklist

1. Obtain the original UP-Fall raw sensor dataset from a verified/authorized source.
2. Verify provenance and license.
3. Verify archive checksum if available.
4. Extract into:

```text
data/raw/upfall/
```

5. Run:

```powershell
$env:PYTHONPATH="src"
python scripts/validate_upfall_raw.py
```

6. Review validator output.
7. Only then revise/run:

```text
scripts/convert_upfall.py
```

8. Build:

```text
data/unified/upfall.csv
```

9. Verify `FALL` / `NO_FALL` labels against source metadata.
10. Create subject-grouped train/validation/test split.
11. Train Fall AI.
12. Validate false-positive and false-negative behavior.
13. Only after validation integrate with `StrokeGuardEngine`.
14. Only after software integration benchmark on Arduino UNO Q.

## Provisional Raw Schema

The actual acquired source must be inspected before these assumptions are
accepted. The current converter looks for CSV columns matching:

```text
accel_x / acc_x / x
accel_y / acc_y / y
accel_z / acc_z / z
gyro_x / gyr_x
```

Timestamp, subject, activity, trial, sampling rate, units, and label columns
remain unknown until the raw source is installed.

## Conversion Guard

`convert_upfall.py` now refuses to run without a manually created
`data/raw/upfall/provenance.json` containing verified provenance and activity/
fall mapping fields. The converter must never map activity IDs to `FALL` based
on an unverified assumption.

No raw data, provenance manifest, generated windows, or Fall model is present.

The Fall AI branch is not a stroke detector and has no clinical validation.
