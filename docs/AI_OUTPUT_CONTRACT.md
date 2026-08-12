# AI Output Contract

The compact bridge response contains:

```text
risk_state
risk_score
activity
activity_confidence
physiology_state
physiology_score
fall_detected
fall_confidence
fall_model_status
trigger
reasons
```

Allowed `risk_state` values:

```text
NORMAL
WARNING
CRITICAL
SENSOR_ERROR
```

Physiology values:

```text
NORMAL
PHYSIO_WARNING
PHYSIO_CRITICAL
SENSOR_ERROR
UNKNOWN
```

Current Fall values:

```text
fall_detected: false
fall_confidence: 0.0
fall_model_status: NOT_AVAILABLE
```

The Fall placeholder cannot trigger a critical decision. A future trained Fall
model can replace the placeholder without changing the serial input/output
shape.

These outputs represent engineering risk and safety states. They do not claim
stroke detection or stroke diagnosis.
