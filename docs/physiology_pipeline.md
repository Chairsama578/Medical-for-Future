# Physiological Risk Pipeline

The v4 physiological layer is an assistive engineering risk indicator. It is
not a stroke detector, diagnostic model, or probability of stroke.

## Inputs

The existing v3 `SensorPacket` contract is preserved:

```text
timestamp
heart_rate_bpm
spo2_pct
systolic_bp_mmhg
diastolic_bp_mmhg
accel_x_g / accel_y_g / accel_z_g
sensor_quality
battery_pct
sos_pressed
```

Heart rate, SpO2, and IMU values must be finite and within engineering input
ranges. Blood pressure is optional and is used only when an actual measured
value is present. Missing values are not converted into abnormal physiology.

## Features

`strokeguard_v4.physiology.extract_physiology_features` computes windowed
means, standard deviations, extrema, deltas, slopes, variability, acceleration
magnitude, and jerk. BP features are omitted when BP is unavailable.

The runtime demo uses 5 Hz and 8-second windows, but the physiology module
accepts any packet window and does not resample data implicitly.

## Baseline

`PersonalBaseline` is optional and resettable. It learns from explicitly
provided normal measurements only. Population averages are not treated as a
personal baseline.

## Risk States

The physiology engine returns:

```text
NORMAL
PHYSIO_WARNING
PHYSIO_CRITICAL
SENSOR_ERROR
UNKNOWN
```

The score is an engineering indicator in the range 0.0 to 1.0. It is not a
clinical probability and must not be described as stroke risk probability.

Abnormal signals persist across windows before becoming critical. Manual SOS
and B.E. FAST remain immediate safety overrides in the fusion layer.

## Fusion

`SafetyFusionV4` maps physiology and future fall results to the existing
runtime-compatible states:

```text
NORMAL
WARNING
CRITICAL
SENSOR_ERROR
```

It does not emit the incompatible `EMERGENCY` state. Manual SOS and B.E. FAST
map to `CRITICAL` for compatibility with the current v3 runtime contract.

## Sensor Availability

The replaceable sensor contracts in `strokeguard_v4.contracts` return
`available=false` when a physical sensor is not connected. They do not return
fake measurements. GPS fields in `EmergencyEvent` remain null unless a future
GPS implementation provides real values.

The fall detector is currently a safe placeholder and never fabricates a fall.

## Arduino UNO Q

The Arduino firmware and `SensorPacket` JSON contract were not modified by
this layer. Real sensor adapters remain hardware-dependent and must be added
only after the sensor BOM is confirmed.

## Clinical Dataset Status

BIDMC is the planned open physiology signal-validation dataset:

```text
https://www.physionet.org/content/bidmc/1.0.0/
```

It is not installed locally in this repository. No physiology ML model has
been trained from BIDMC. BIDMC does not provide a StrokeGuard stroke target;
HR/SpO2/BP abnormalities must not be relabeled as stroke. The current demo
therefore uses the rule-based engine and its temporal safety policy.

StrokeGuard is an assistive early-warning prototype. It does not diagnose
stroke.
