"""Explicitly synthetic physiological packet scenarios for offline testing."""

import random
import time

from strokeguard.core.domain import SensorPacket


SCENARIOS = {
    "normal", "elevated_hr", "low_spo2", "rapid_spo2_decline", "rapid_hr_change",
    "sensor_dropout", "mixed_warning", "critical_physiology", "manual_sos",
    "fall_placeholder",
}


class PhysiologySimulator:
    synthetic = True

    def __init__(self, scenario="normal", seed=42):
        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")
        self.scenario = scenario
        self.rng = random.Random(seed)
        self.index = 0

    def next_packet(self) -> SensorPacket:
        self.index += 1
        hr, spo2, sbp, dbp, quality = 72.0, 98.0, 120.0, 80.0, 0.98
        if self.scenario == "elevated_hr":
            hr = 135.0
        elif self.scenario == "low_spo2":
            spo2 = 88.0
        elif self.scenario == "rapid_spo2_decline":
            spo2 = max(84.0, 99.0 - self.index * 1.0)
        elif self.scenario == "rapid_hr_change":
            hr = 72.0 if self.index <= 3 else 150.0
        elif self.scenario == "sensor_dropout":
            hr, spo2, quality = None, None, 0.1
        elif self.scenario == "mixed_warning":
            hr, spo2 = 125.0, 93.0
        elif self.scenario == "critical_physiology":
            hr, spo2, sbp, dbp = 150.0, 84.0, 195.0, 125.0
        return SensorPacket(
            timestamp=time.time(),
            heart_rate_bpm=None if hr is None else hr + self.rng.gauss(0, 1.0),
            spo2_pct=None if spo2 is None else spo2 + self.rng.gauss(0, 0.2),
            systolic_bp_mmhg=sbp,
            diastolic_bp_mmhg=dbp,
            accel_x_g=0.02,
            accel_y_g=-0.01,
            accel_z_g=1.0,
            sensor_quality=quality,
            battery_pct=88.0,
            sos_pressed=self.scenario == "manual_sos",
        )
