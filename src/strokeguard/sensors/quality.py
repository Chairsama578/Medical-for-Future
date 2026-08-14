from dataclasses import dataclass
from typing import Optional
from strokeguard.core.domain import SensorPacket

@dataclass
class QualityResult:
    ok: bool
    score: float
    reasons: list[str]

def validate(packet: SensorPacket) -> QualityResult:
    reasons = []
    checks = []
    if packet.heart_rate_bpm is not None:
        checks.append(35 <= packet.heart_rate_bpm <= 220)
    if packet.spo2_pct is not None:
        checks.append(70 <= packet.spo2_pct <= 100)
    if packet.systolic_bp_mmhg is not None:
        checks.append(70 <= packet.systolic_bp_mmhg <= 260)
    if packet.diastolic_bp_mmhg is not None:
        checks.append(40 <= packet.diastolic_bp_mmhg <= 160)
    for a in (packet.accel_x_g, packet.accel_y_g, packet.accel_z_g):
        checks.append(-8 <= a <= 8)
    checks.append(0 <= packet.sensor_quality <= 1)

    if not all(checks):
        reasons.append("out_of_range_sensor_value")
    if packet.sensor_quality < 0.60:
        reasons.append("low_sensor_quality")
    if packet.heart_rate_bpm is None and packet.spo2_pct is None:
        reasons.append("no_primary_vitals")

    score = packet.sensor_quality
    if not all(checks):
        score *= 0.25
    return QualityResult(ok=(score >= 0.60 and not reasons), score=score, reasons=reasons)
