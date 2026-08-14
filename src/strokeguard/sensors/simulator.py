import math, random, time
from strokeguard.core.domain import SensorPacket

class SensorSimulator:
    def __init__(self, scenario="normal", seed=42):
        self.scenario = scenario
        self.rng = random.Random(seed)
        self.t = 0.0

    def next_packet(self):
        self.t += 0.2
        if self.scenario == "normal":
            hr, spo2, sbp, dbp = 72, 98, 120, 80
            ax, ay, az = 0.02, -0.01, 1.00
        elif self.scenario == "warning":
            hr, spo2, sbp, dbp = 108, 93, 158, 96
            ax, ay, az = 0.35, 0.12, 0.94
        else:
            hr, spo2, sbp, dbp = 142, 84, 190, 112
            ax, ay, az = 1.5, 0.8, 0.3
        return SensorPacket(
            timestamp=time.time(),
            heart_rate_bpm=hr + self.rng.gauss(0, 2),
            spo2_pct=spo2 + self.rng.gauss(0, 0.5),
            systolic_bp_mmhg=sbp + self.rng.gauss(0, 3),
            diastolic_bp_mmhg=dbp + self.rng.gauss(0, 2),
            accel_x_g=ax + self.rng.gauss(0, 0.04),
            accel_y_g=ay + self.rng.gauss(0, 0.04),
            accel_z_g=az + self.rng.gauss(0, 0.04),
            sensor_quality=0.98,
            battery_pct=85
        )
