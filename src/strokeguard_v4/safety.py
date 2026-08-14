"""Runtime-compatible multi-signal safety fusion for the v4 layer."""


class SafetyFusionV4:
    """Return only the runtime states NORMAL/WARNING/CRITICAL/SENSOR_ERROR."""

    def __init__(self, warning=0.55, critical=0.80, persistence=2):
        self.warning = warning
        self.critical = critical
        self.persistence = persistence
        self.warning_count = 0
        self.critical_count = 0

    def decide(
        self,
        risk_score=0.0,
        fall_state="NO_FALL",
        sensor_quality=1.0,
        manual_sos=False,
        befast_positive=False,
        activity_result=None,
        fall_result=None,
        physiology_result=None,
    ):
        if manual_sos or befast_positive:
            return {"state": "CRITICAL", "reasons": ["manual_sos_or_befast"]}
        if sensor_quality < 0.60:
            return {"state": "SENSOR_ERROR", "reasons": ["low_sensor_quality"]}

        physiology_state = _value(physiology_result, "state")
        if physiology_state == "SENSOR_ERROR":
            return {"state": "SENSOR_ERROR", "reasons": ["physiology_sensor_error"]}

        detected_fall = bool(_value(fall_result, "fall_detected")) or fall_state == "FALL"
        physiology_abnormal = physiology_state in {"PHYSIO_WARNING", "PHYSIO_CRITICAL"}
        if detected_fall and physiology_abnormal:
            return {"state": "CRITICAL", "reasons": ["fall_with_physiological_abnormality"]}

        critical_signal = physiology_state == "PHYSIO_CRITICAL" or risk_score >= self.critical
        warning_signal = physiology_state == "PHYSIO_WARNING" or risk_score >= self.warning
        if critical_signal:
            self.critical_count += 1
            self.warning_count = 0
            if self.critical_count >= self.persistence:
                return {"state": "CRITICAL", "reasons": ["persistent_physiological_risk"]}
        elif warning_signal:
            self.warning_count += 1
            self.critical_count = 0
            if self.warning_count >= self.persistence:
                return {"state": "WARNING", "reasons": ["persistent_physiological_risk"]}
        else:
            self.warning_count = 0
            self.critical_count = 0

        if detected_fall:
            self.warning_count += 1
            if self.warning_count >= self.persistence:
                return {"state": "WARNING", "reasons": ["persistent_fall"]}
            return {"state": "NORMAL", "reasons": ["fall_checking"]}

        activity = _value(activity_result, "label")
        reasons = [f"activity_context:{activity}"] if activity else []
        return {"state": "NORMAL", "reasons": reasons}


def _value(value, key):
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)
