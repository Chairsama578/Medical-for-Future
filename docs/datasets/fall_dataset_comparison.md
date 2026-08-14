# Fall Dataset Comparison

## Scope

This document identifies a legally/publicly accessible research dataset that
could replace the unavailable original UP-Fall raw wearable dataset. No data
was downloaded, converted, or used for training.

The original UP-Fall Challenge page is no longer a download source. Its current
dataset section states that the competition files are no longer public there.
The Zenodo 3D Skeletons UP-Fall record is not a replacement: it contains pose/
joint coordinates rather than raw wearable IMU streams.

## Ranking

| Rank | Dataset | Recommendation | Main reason |
|---|---|---|---|
| A | UMAFall: Fall Detection Dataset (Universidad de Malaga) | Recommended replacement | Official university repository, direct sensor archive, explicit FALL/ADL labels, accelerometer + gyroscope, 19 subjects |
| B | SisFall: A Fall and Movement Dataset | Backup | Strong paper provenance, 38 subjects, explicit falls/ADLs, two accelerometers + gyroscope; current source access requires manual verification |
| C | UniMiB SHAR | Backup only | 30 subjects and explicit fall/ADL labels, but accelerometer-only and dataset access/package must be verified |

## A. UMAFall

### Provenance and Access

Official repository record:

```text
https://hdl.handle.net/10630/41001
```

Official sensor archive listed by the University of Malaga repository:

```text
https://riuma.uma.es/bitstreams/d87aa5f2-bf22-47c0-9a79-eae50cc874e0/download
```

Official metadata/readme:

```text
https://riuma.uma.es/bitstreams/213f5cea-5f4a-424a-a488-16502ffc3483/download
```

Paper:

```text
https://doi.org/10.1016/j.procs.2017.06.110
```

Additional dataset DOI:

```text
https://doi.org/10.6084/m9.figshare.4214283
```

Access is public through the institutional repository. The repository states
Creative Commons Attribution-NonCommercial 4.0 International:

```text
https://creativecommons.org/licenses/by-nc/4.0/
```

Use requires attribution and non-commercial compliance. Confirm the current
repository terms before redistribution.

### Dataset Details

```text
Official name: UMAFall: Fall Detection Dataset (Universidad de Malaga)
Subjects: 19 experimental subjects
Fall classes: lateral, frontal, backwards
Non-fall classes: 12 ADL typologies
Sensors: smartphone plus four SensorTag nodes
Accelerometer: tri-axis
Gyroscope: tri-axis
Other sensors: tri-axis magnetometer
Sampling rate: not specified in the repository readme; derive/verify from timestamps
File format: CSV text with semicolon-delimited measurement rows and '%' metadata headers
Sensor archive size: approximately 74.92 MB
Subject IDs: encoded in filenames and metadata
Trial IDs: included in filename/metadata
Explicit fall labels: Boolean fall field and movement type metadata
Explicit non-fall labels: ADL movement type metadata
```

Each measurement row contains time in milliseconds, sample number, three sensor
axes, sensor type, and sensing node. The readme defines sensor type values for
accelerometer, gyroscope, and magnetometer. This is directly compatible with a
wearable IMU conversion after parsing node/sensor streams.

```text
Suitable for Edge AI: Yes, after resampling/windowing and node selection
Suitable for StrokeGuard: Yes, best current candidate
Conversion difficulty: Medium/High; custom parser required
Main risks: emulated falls, multiple nodes, semicolon format, metadata headers,
            sampling rate must be confirmed, non-commercial license
```

The current `convert_upfall.py` is not compatible with UMAFall as-is. A new
dataset-specific converter should be created after acquisition and inspection.

## B. SisFall

### Provenance and Access

Paper:

```text
https://doi.org/10.3390/s17010198
https://www.mdpi.com/1424-8220/17/1/198
```

The paper cites the dataset source:

```text
http://sistemic.udea.edu.co/investigacion/proyectos/english-falls/?lang=en
```

The source endpoint was not reachable from this environment and no alternate
download mirror is treated as authoritative here. Manual source verification
is required before acquisition.

The paper is published under CC BY 4.0, but the dataset-specific redistribution
terms must be confirmed separately.

### Dataset Details

```text
Official name: SisFall: A Fall and Movement Dataset
Subjects: 38 total; 23 young adults, 15 older adults
Fall classes: 15 fall types
Non-fall classes: 19 ADLs for the young cohort and 15 ADLs for the older cohort
Sensors: wearable/self-developed device
Accelerometer: two tri-axis accelerometers
Gyroscope: tri-axis gyroscope
Other sensors: none required for the core IMU stream
Sampling rate: 200 Hz as reported in the dataset literature
File format: raw delimited text files
Subject IDs: available in source file organization
Trial IDs: available in source file organization
Explicit fall labels: source fall-type activities
Explicit non-fall labels: source ADL activities
Approximate size: not verified from an accessible official archive
```

```text
Suitable for Edge AI: Yes, after resampling/windowing
Suitable for StrokeGuard: Yes, strong IMU fallback
Conversion difficulty: Medium; raw text parsing and dual accelerometer selection
Main risks: source download currently unverified, dataset-specific license terms,
            simulated falls, multiple accelerometer channels
```

## C. UniMiB SHAR

### Provenance and Access

Paper and dataset description:

```text
https://arxiv.org/abs/1611.07688
https://doi.org/10.48550/arXiv.1611.07688
```

The project website is:

```text
https://www.sal.disco.unimib.it/technologies/unimib-shar/
```

The website/download package was not accessible for verification in this
environment. Manual access and license confirmation are required.

### Dataset Details

```text
Official name: UniMiB SHAR
Subjects: 30
Fall classes: 8 fall types
Non-fall classes: 9 ADL types
Sensors: smartphone
Accelerometer: tri-axis
Gyroscope: not included
Other sensors: none in the core dataset
Sampling rate: smartphone acceleration; confirm exact source package metadata
File format: dataset-specific packaged acceleration samples
Subject IDs: included for subject-independent evaluation
Trial IDs: source sample metadata must be confirmed
Explicit fall labels: 8 source fall classes
Explicit non-fall labels: 9 source ADL classes
Approximate size: 11,771 labeled samples reported by the paper
```

```text
Suitable for Edge AI: Yes
Suitable for StrokeGuard: Limited backup only
Conversion difficulty: Low/Medium after access is verified
Main risks: no gyroscope, smartphone-only acceleration, access/license package
            not verified, source samples are not raw multi-node wearable streams
```

## Compatibility Matrix

| Requirement | UMAFall | SisFall | UniMiB SHAR |
|---|---|---|---|
| Raw accelerometer X/Y/Z | Yes | Yes | Yes |
| Gyroscope X/Y/Z | Yes | Yes | No |
| Explicit FALL labels | Yes | Yes | Yes |
| Explicit ADL labels | Yes | Yes | Yes |
| Multiple subjects | 19 | 38 | 30 |
| Subject-group split | Yes | Yes | Yes |
| Trial metadata | Yes | Yes | Must verify |
| Public source verified | Yes, University of Malaga | Paper/source, download unavailable here | Paper/site, download unavailable here |
| Edge conversion | Medium/High | Medium | Low/Medium |
| Current converter compatible | No | No | No |

## Recommended Acquisition

UMAFall is the current recommended replacement because its official
institutional repository exposes the sensor archive and metadata, has explicit
fall/ADL labels, includes both accelerometer and gyroscope streams, and has a
manageable archive size.

Acquisition must still be manual. Do not download during repository setup.

Recommended target directory:

```text
data/raw/umafall/
```

Using a distinct directory prevents confusing UMAFall with the unavailable
original UP-Fall dataset.

## Exact Acquisition Steps

1. Open the official RIUMA record.
2. Read the repository license and metadata.
3. Download only the sensor archive, not the optional videos unless needed.
4. Record the archive SHA-256 locally.
5. Extract into `data/raw/umafall/`.
6. Preserve the original metadata headers and filenames.
7. Inspect sensor/node/timestamp fields before writing a converter.
8. Confirm fall and ADL mappings from the supplied metadata/readme.
9. Create a dataset-specific provenance manifest.
10. Create a dataset-specific validator report.
11. Implement a converter only after validation.
12. Create subject-grouped train/validation/test splits.
13. Train and evaluate the Fall branch only after the data audit passes.

## Required Validation Before Conversion

Validate:

- archive hash and provenance
- license and citation
- file count and total size
- metadata header format
- delimiter and row schema
- sensor type and node mapping
- accelerometer and gyroscope availability
- timestamp monotonicity
- sampling-rate distribution
- subject identifiers
- trial identifiers
- explicit fall labels
- explicit ADL labels
- missing and malformed values
- duplicate records
- subject-group split feasibility

Do not use `data/raw/upfall/` for UMAFall without an explicit decision. Do not
modify `convert_upfall.py` until the acquired data has been inspected.

No dataset was downloaded and no Fall model was trained for this comparison.
