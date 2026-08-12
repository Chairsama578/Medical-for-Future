# Physiology Dataset Comparison

## Current Local Status

```text
data/raw/physiology/: DEMO SUBSET INSTALLED
data/raw/physiology/bidmc/: BIDMC records 01-05 installed
data/raw/physiology/mimic3wdb/: NOT INSTALLED
data/raw/physiology/mimic3_ext_ppg/: NOT INSTALLED
```

Only five BIDMC records were acquired manually from the official directory. No
physiology ML model was trained. The existing rule-based `PhysiologyRiskEngine`
remains the primary demo branch.

## Candidate A: BIDMC PPG and Respiration Dataset

Official source:

```text
https://www.physionet.org/content/bidmc/1.0.0/
```

Dataset DOI:

```text
https://doi.org/10.13026/C2208R
```

Paper citation:

```text
https://doi.org/10.1109/TBME.2016.2613124
```

Access:

```text
Open access subject to Open Data Commons Attribution License v1.0
```

Official dataset facts:

```text
Recordings: 53
Duration: approximately 8 minutes per recording
Waveforms: PPG, ECG, impedance respiration
Waveform sampling: 125 Hz
Numerics sampling: 1 Hz
Numerics: HR, pulse rate, SpO2, respiratory rate
Files: WFDB, CSV, Matlab
Archive size: approximately 207.8 MB uncompressed/download package
```

Strengths:

- Public and manageable compared with MIMIC waveform collections.
- Explicit WFDB headers and sampling rates.
- Directly useful for HR, SpO2, PPG, ECG, and temporal physiology features.
- Existing repository dependency `wfdb` already supports the format.

Limitations:

- No StrokeGuard `NORMAL/ABNORMAL` or stroke labels should be assumed.
- The recordings are critically ill hospital data, not wearable data.
- BP is not a guaranteed signal in this dataset.
- Subject/record grouping is available, but clinical labels must not be invented.

Assessment:

```text
Best practical physiology signal-validation dataset.
Suitable for feature extraction and signal-quality validation.
Not sufficient by itself for a stroke-diagnosis model.
```

## Candidate B: MIMIC-III Waveform Database

Official source:

```text
https://www.physionet.org/content/mimic3wdb/1.0/
```

Dataset DOI:

```text
https://doi.org/10.13026/c2607m
```

Access/license:

```text
PhysioNet Open Data Commons Open Database License v1.0
```

Official dataset facts:

```text
Approximately 67,830 record sets
Approximately 30,000 ICU patients
Total uncompressed size: approximately 6.7 TB
Waveforms: typically ECG, ABP, respiration, PPG where available
Waveform sampling: typically 125 Hz
Numerics: commonly HR, SpO2, SBP/DBP and other monitor values
```

The full collection is impractical for the remaining demo window. A small,
documented record subset could be selected later, but no download or selection
was attempted.

Limitations:

- Very large and heterogeneous.
- Signal availability varies per record and segment.
- ICU monitor data is not wearable data.
- Clinical waveform presence does not create a stroke label.
- Patient/record grouping and de-identification metadata require care.

## Candidate C: MIMIC-III-Ext-PPG

Official source:

```text
https://www.physionet.org/content/mimic-iii-ext-ppg/
```

Dataset DOI:

```text
https://doi.org/10.13026/nmwb-6h34
```

Access:

```text
Credentialed PhysioNet access
CITI Data or Specimens Only Research training
Signed PhysioNet Data Use Agreement
PhysioNet Credentialed Health Data License 1.5.0
```

Official dataset facts:

```text
Approximately 4.9 million 30-second PPG segments
Approximately 6,131 critically ill patients for rhythm task
PPG with ECG, ABP, RESP where available
Waveform sampling: 125 Hz
Metadata includes derived HR and BP fields where available
```

Strengths:

- Strongest practical PPG/ECG/ABP metadata source.
- Quality metrics and signal annotations are available.

Limitations:

- Credentialed access makes it unsuitable for the two-day demo schedule.
- No stroke diagnosis labels should be inferred from ICU rhythm labels.
- Dataset scale is too large for an immediate local pipeline.

## Comparison

| Dataset | Local | Access | Signals | Sampling | Size | Labels | Demo suitability |
|---|---|---|---|---|---|---|---|
| BIDMC | No | Open, ODC Attribution | PPG, ECG, RESP, HR, SpO2 | 125 Hz waveforms, 1 Hz numerics | ~207.8 MB | No stroke labels | Best practical option |
| MIMIC-III WDB | No | Open ODbL, very large | ECG, ABP, PPG, RESP, numerics | Usually 125 Hz waveforms | ~6.7 TB | Clinical context, not stroke labels | Not practical now |
| MIMIC-III-Ext-PPG | No | Credentialed + DUA/training | PPG, ECG, ABP, RESP, HR/BP metadata | 125 Hz | Very large | Rhythm annotations, not stroke labels | Not practical now |

## Label Policy

No source currently provides a validated StrokeGuard stroke target in the local
repository. The safe initial physiology task is signal/measurement behavior and
engineering abnormality detection, not stroke diagnosis.

If BIDMC is acquired, source-derived numeric measurements may be used for
feature extraction and signal-quality validation. `physiology_state` must not
be assigned from arbitrary vital-sign thresholds as a clinical label.

## Exact Next Steps

1. Acquire BIDMC manually from the official PhysioNet page.
2. Place it under `data/raw/physiology/bidmc/`.
3. Run `python scripts/validate_physiology_raw.py`.
4. Record source version, license, file count, SHA256, records, signals, and sampling rates.
5. Define a transparent feature-only or source-annotation task.
6. Do not create stroke labels from HR, SpO2, or BP values.
7. Only then decide whether a small physiology baseline model is justified.

No download was performed and no physiology model is currently ready.
