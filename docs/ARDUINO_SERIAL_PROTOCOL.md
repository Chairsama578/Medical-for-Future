# Arduino Serial Protocol

## Connection

```text
USB Serial
115200 baud
8 data bits, no parity, 1 stop bit
```

Arduino sends one compact JSON object followed by newline:

```json
{"timestamp":1723456789000,"heart_rate_bpm":82,"spo2_pct":98,"accel_x_g":0.02,"accel_y_g":0.98,"accel_z_g":0.05,"sensor_quality":1.0,"battery_pct":87,"sos_pressed":false}
```

Python responds with one compact JSON object followed by newline.

Normal response:

```json
{"risk_state":"NORMAL","risk_score":0.0,"activity":"STANDING","activity_confidence":0.82,"physiology_state":"NORMAL","physiology_score":0.0,"fall_detected":false,"fall_confidence":0.0,"fall_model_status":"NOT_AVAILABLE","trigger":null,"reasons":[],"timestamp":1723456789000}
```

Critical response:

```json
{"risk_state":"CRITICAL","risk_score":0.91,"activity":"LAYING","activity_confidence":0.84,"physiology_state":"PHYSIO_CRITICAL","physiology_score":0.91,"fall_detected":false,"fall_confidence":0.0,"fall_model_status":"NOT_AVAILABLE","trigger":"v4_risk","reasons":["persistent_physiological_risk"],"timestamp":1723456789000}
```

Manual SOS response:

```json
{"risk_state":"CRITICAL","risk_score":1.0,"trigger":"manual_sos"}
```

Malformed JSON or invalid fields return an error response with:

```json
{"risk_state":"SENSOR_ERROR","error":"invalid_json"}
```

The bridge continues reading after malformed input. It does not terminate the
whole process.
