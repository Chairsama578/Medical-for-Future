import math
import numpy as np
from strokeguard.core.domain import SensorPacket

FEATURE_NAMES = [
    "hr_mean","hr_std","spo2_mean","spo2_min",
    "sbp_mean","dbp_mean",
    "accel_mag_mean","accel_mag_std","accel_mag_max","accel_jerk_std"
]

def extract(packets: list[SensorPacket]) -> np.ndarray:
    if not packets:
        return np.zeros(len(FEATURE_NAMES), dtype=np.float32)
    hr = np.array([p.heart_rate_bpm for p in packets if p.heart_rate_bpm is not None], dtype=float)
    sp = np.array([p.spo2_pct for p in packets if p.spo2_pct is not None], dtype=float)
    sbp = np.array([p.systolic_bp_mmhg for p in packets if p.systolic_bp_mmhg is not None], dtype=float)
    dbp = np.array([p.diastolic_bp_mmhg for p in packets if p.diastolic_bp_mmhg is not None], dtype=float)
    acc = np.array([[p.accel_x_g,p.accel_y_g,p.accel_z_g] for p in packets], dtype=float)
    mag = np.linalg.norm(acc, axis=1)
    jerk = np.diff(mag) if len(mag) > 1 else np.array([0.0])

    def mean(x, default=0.0): return float(np.mean(x)) if len(x) else default
    def std(x, default=0.0): return float(np.std(x)) if len(x) else default
    def minv(x, default=0.0): return float(np.min(x)) if len(x) else default

    return np.array([
        mean(hr), std(hr), mean(sp, 98.0), minv(sp, 98.0),
        mean(sbp, 120.0), mean(dbp, 80.0),
        mean(mag), std(mag), float(np.max(mag)),
        std(jerk)
    ], dtype=np.float32)
