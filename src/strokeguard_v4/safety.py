class SafetyFusionV4:
    def __init__(self, warning=0.55, critical=0.80, persistence=2):
        self.warning = warning
        self.critical = critical
        self.persistence = persistence
        self.warning_count = 0
        self.critical_count = 0

    def decide(
        self,
        risk_score,
        fall_state="NO_FALL",
        sensor_quality=1.0,
        manual_sos=False,
        befast_positive=False,
    ):
        if manual_sos or befast_positive:
            return {"state": "EMERGENCY", "reasons": ["manual_sos_or_befast"]}
        if sensor_quality < 0.60:
            return {"state": "WARNING", "reasons": ["low_sensor_quality"]}
        if fall_state == "FALL":
            self.warning_count += 1
            if self.warning_count >= self.persistence:
                return {"state": "WARNING", "reasons": ["persistent_fall"]}
            return {"state": "NORMAL", "reasons": ["fall_checking"]}
        if risk_score >= self.critical:
            self.critical_count += 1
            if self.critical_count >= self.persistence:
                return {
                    "state": "CRITICAL",
                    "reasons": ["persistent_physiological_risk"],
                }
        elif risk_score >= self.warning:
            self.warning_count += 1
            if self.warning_count >= self.persistence:
                return {
                    "state": "WARNING",
                    "reasons": ["persistent_physiological_risk"],
                }
        else:
            self.warning_count = 0
            self.critical_count = 0
        return {"state": "NORMAL", "reasons": []}
