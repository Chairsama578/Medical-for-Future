# StrokeGuard AI contract

## Required sensor fields

| Field | Unit | Required |
|---|---|---|
| heart_rate_bpm | bpm | yes for normal operation |
| spo2_pct | % | yes for normal operation |
| systolic_bp_mmhg | mmHg | optional until a validated BP module exists |
| diastolic_bp_mmhg | mmHg | optional until a validated BP module exists |
| accel_x_g | g | yes |
| accel_y_g | g | yes |
| accel_z_g | g | yes |
| sensor_quality | 0..1 | yes |
| battery_pct | % | optional |
| sos_pressed | boolean | yes |

## Feature vector

The model currently consumes:
`hr_mean, hr_std, spo2_mean, spo2_min, sbp_mean, dbp_mean, accel_mag_mean, accel_mag_std, accel_mag_max, accel_jerk_std`.

## Safety hierarchy

Priority:
1. Manual SOS
2. B.E. FAST symptom signal
3. Sensor integrity
4. Persistent ML risk
5. Normal state

The hierarchy prevents a low-confidence ML output from suppressing an explicit emergency signal.
