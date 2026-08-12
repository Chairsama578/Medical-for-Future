# v4 Runtime Integration

The v4 runtime layer is now available behind `v4_enabled`. It does not change
the v3 `SensorPacket` contract, Arduino firmware, or Activity model.

```text
SensorPacket
    -> explicit v3-to-v4 field adapter
    -> 40-sample rolling window
    -> ActivityInferenceAdapter
    -> PhysiologyRiskEngine
    -> PlaceholderFallDetector
    -> SafetyFusionV4
    -> v3 RiskDecision / AlertController
    -> optional EmergencyEvent
```

## Configuration

`config/config.example.yaml` contains:

```yaml
v4_enabled: true
```

The runtime setting is controlled by:

```text
STROKEGUARD_V4_ENABLED=true|false
```

Set `STROKEGUARD_V4_ENABLED=false` to use the existing v3 decision path.

## Field Mapping

The adapter maps explicitly:

```text
heart_rate_bpm      -> heart_rate
spo2_pct            -> spo2
systolic_bp_mmhg   -> sbp
diastolic_bp_mmhg  -> dbp
accel_x_g           -> accel_x
accel_y_g           -> accel_y
accel_z_g           -> accel_z
sensor_quality      -> sensor_quality
battery_pct         -> battery
sos_pressed         -> sos_pressed
```

Missing BP remains unavailable. It is not replaced with zero or a fabricated
measurement.

## Safety Priority

The runtime priority is:

1. Manual SOS
2. B.E. FAST
3. Sensor error
4. Persistent physiological critical state
5. Future confirmed fall with context
6. Physiological warning
7. Activity context
8. Normal

Activity alone cannot create a critical decision. `LAYING`, `STANDING`, and
`WALKING` are activity context only.

## Fall Status

The current fall result is explicitly:

```text
fall_model_status = NOT_AVAILABLE
fall_detected = false
confidence = 0
impact_score = 0
recovery_detected = false
```

It cannot trigger an emergency. The future UP-Fall branch can replace the
placeholder through the same `FallResult` contract.

## Emergency Events

`EmergencyEvent` is emitted only for a CRITICAL v4 decision. GPS fields remain
null because no GPS hardware is connected. The event describes an engineering
emergency condition; it does not diagnose stroke.

## Limitations

- Activity is a posture/activity model, not a medical model.
- Physiology is a rule-based engineering risk indicator, not a clinical model.
- Fall AI is unavailable and remains a non-triggering placeholder.
- Arduino real sensors are not connected.
- GPS and external family/emergency notifications are not connected.
- Latencies are workstation measurements, not UNO Q measurements.

StrokeGuard is an assistive early-warning prototype. It does not diagnose
stroke.
