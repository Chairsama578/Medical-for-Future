"""Non-diagnostic physiological risk features and temporal decision logic."""

from dataclasses import dataclass, field
import math
import time
from typing import Iterable

import numpy as np

from strokeguard.core.domain import SensorPacket


@dataclass
class SensorQualityReport:
    score: float
    valid: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class PersonalBaseline:
    hr_baseline: float | None = None
    spo2_baseline: float | None = None
    sbp_baseline: float | None = None
    dbp_baseline: float | None = None
    valid_samples: int = 0
    initialized: bool = False

    def reset(self):
        self.hr_baseline = self.spo2_baseline = None
        self.sbp_baseline = self.dbp_baseline = None
        self.valid_samples = 0
        self.initialized = False

    def update(self, packets: Iterable[SensorPacket], min_samples: int = 5):
        values = list(packets)
        self.hr_baseline = _mean_optional([p.heart_rate_bpm for p in values])
        self.spo2_baseline = _mean_optional([p.spo2_pct for p in values])
        self.sbp_baseline = _mean_optional([p.systolic_bp_mmhg for p in values])
        self.dbp_baseline = _mean_optional([p.diastolic_bp_mmhg for p in values])
        self.valid_samples = sum(
            _finite(p.heart_rate_bpm) and _finite(p.spo2_pct) for p in values
        )
        self.initialized = self.valid_samples >= min_samples

    def deviations(self, features: dict[str, float]) -> dict[str, float]:
        if not self.initialized:
            return {}
        result = {}
        for feature, baseline_name in [
            ("hr_mean", "hr_baseline"),
            ("spo2_mean", "spo2_baseline"),
            ("sbp_mean", "sbp_baseline"),
            ("dbp_mean", "dbp_baseline"),
        ]:
            baseline = getattr(self, baseline_name)
            if baseline is not None and feature in features:
                result[f"{feature}_deviation"] = features[feature] - baseline
        return result


@dataclass
class PhysiologyRiskResult:
    score: float
    state: str
    reasons: list[str]
    confidence: float
    sensor_quality: float
    features: dict[str, float]
    timestamp: float = field(default_factory=time.time)


def _finite(value) -> bool:
    try:
        return value is not None and math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _mean_optional(values) -> float | None:
    valid = [float(value) for value in values if _finite(value)]
    return float(np.mean(valid)) if valid else None


def validate_packet(packet: SensorPacket, require_imu: bool = True) -> SensorQualityReport:
    reasons = []
    required = {
        "heart_rate_bpm": (packet.heart_rate_bpm, 30.0, 220.0),
        "spo2_pct": (packet.spo2_pct, 70.0, 100.0),
    }
    if require_imu:
        required.update({
            "accel_x_g": (packet.accel_x_g, -16.0, 16.0),
            "accel_y_g": (packet.accel_y_g, -16.0, 16.0),
            "accel_z_g": (packet.accel_z_g, -16.0, 16.0),
        })
    valid_count = 0
    for name, (value, low, high) in required.items():
        if not _finite(value):
            reasons.append(f"{name}_missing_or_nonfinite")
        elif not low <= float(value) <= high:
            reasons.append(f"{name}_out_of_range")
        else:
            valid_count += 1
    for name, value, low, high in [
        ("systolic_bp_mmhg", packet.systolic_bp_mmhg, 50.0, 300.0),
        ("diastolic_bp_mmhg", packet.diastolic_bp_mmhg, 20.0, 200.0),
    ]:
        if value is not None and (not _finite(value) or not low <= float(value) <= high):
            reasons.append(f"{name}_invalid")
    packet_quality = float(packet.sensor_quality) if _finite(packet.sensor_quality) else 0.0
    if packet_quality < 0.60:
        reasons.append("sensor_quality_low")
    score = max(0.0, min(1.0, min(valid_count / len(required), packet_quality)))
    return SensorQualityReport(score, not reasons, reasons)


def extract_physiology_features(packets: Iterable[SensorPacket]) -> dict[str, float]:
    values = list(packets)
    if not values:
        return {}

    def series(name):
        return np.asarray([
            float(getattr(packet, name)) for packet in values
            if _finite(getattr(packet, name))
        ])

    def add_stats(prefix, data):
        if len(data):
            features[f"{prefix}_mean"] = float(np.mean(data))
            features[f"{prefix}_std"] = float(np.std(data))
            features[f"{prefix}_min"] = float(np.min(data))
            features[f"{prefix}_max"] = float(np.max(data))
            features[f"{prefix}_delta"] = float(data[-1] - data[0])
            features[f"{prefix}_slope"] = float((data[-1] - data[0]) / max(1, len(data) - 1))

    features = {}
    hr = series("heart_rate_bpm")
    spo2 = series("spo2_pct")
    add_stats("hr", hr)
    add_stats("spo2", spo2)
    if len(hr) > 1:
        features["hr_range"] = float(np.ptp(hr))
        features["hr_variability"] = float(np.std(np.diff(hr)))
    if len(spo2) > 1:
        features["spo2_drop_rate"] = float(max(0.0, -features["spo2_slope"]))
    for prefix, name in [("sbp", "systolic_bp_mmhg"), ("dbp", "diastolic_bp_mmhg")]:
        add_stats(prefix, series(name))

    if all(all(_finite(getattr(packet, axis)) for axis in ("accel_x_g", "accel_y_g", "accel_z_g")) for packet in values):
        accel = np.asarray([
            [float(packet.accel_x_g), float(packet.accel_y_g), float(packet.accel_z_g)]
            for packet in values
        ])
        magnitude = np.linalg.norm(accel, axis=1)
        jerk = np.diff(magnitude)
        features["accel_mag_mean"] = float(np.mean(magnitude))
        features["accel_mag_std"] = float(np.std(magnitude))
        features["accel_mag_max"] = float(np.max(magnitude))
        features["jerk_std"] = float(np.std(jerk)) if len(jerk) else 0.0
        features["jerk_max"] = float(np.max(np.abs(jerk))) if len(jerk) else 0.0
    return features


class PhysiologyRiskEngine:
    """Engineering risk indicator, not a diagnostic or clinical model."""

    def __init__(self, persistence_windows: int = 2, baseline: PersonalBaseline | None = None):
        self.persistence_windows = persistence_windows
        self.baseline = baseline or PersonalBaseline()
        self.abnormal_windows = 0
        self.critical_windows = 0
        self.previous_features: dict[str, float] = {}

    def decide(self, packets: Iterable[SensorPacket], activity_result=None, require_imu: bool = True) -> PhysiologyRiskResult:
        values = list(packets)
        if not values:
            return PhysiologyRiskResult(0.0, "UNKNOWN", ["no_sensor_window"], 0.0, 0.0, {})
        reports = [validate_packet(packet, require_imu=require_imu) for packet in values]
        quality = min(report.score for report in reports)
        quality_reasons = sorted({reason for report in reports for reason in report.reasons})
        for previous, current in zip(values, values[1:]):
            if _finite(previous.heart_rate_bpm) and _finite(current.heart_rate_bpm):
                if abs(float(current.heart_rate_bpm) - float(previous.heart_rate_bpm)) > 80:
                    quality_reasons.append("heart_rate_sudden_unrealistic_jump")
            if _finite(previous.spo2_pct) and _finite(current.spo2_pct):
                if abs(float(current.spo2_pct) - float(previous.spo2_pct)) > 10:
                    quality_reasons.append("spo2_sudden_unrealistic_jump")
        if quality_reasons:
            return PhysiologyRiskResult(0.0, "SENSOR_ERROR", quality_reasons, quality, quality, {})

        features = extract_physiology_features(values)
        features.update(self.baseline.deviations(features))
        if "hr_mean" in features and "hr_mean" in self.previous_features:
            features["hr_window_delta"] = features["hr_mean"] - self.previous_features["hr_mean"]
        if "spo2_mean" in features and "spo2_mean" in self.previous_features:
            features["spo2_window_delta"] = features["spo2_mean"] - self.previous_features["spo2_mean"]
        reasons = []
        warning_signals = 0
        critical_signals = 0
        battery_values = [float(packet.battery_pct) for packet in values if _finite(packet.battery_pct)]
        if battery_values and min(battery_values) < 20:
            warning_signals += 1
            reasons.append("battery_low")
        if features.get("hr_mean", 0) < 45 or features.get("hr_mean", 0) > 120:
            warning_signals += 1
            reasons.append("persistent_hr_abnormality")
        if (
            features.get("hr_range", 0) > 25
            or abs(features.get("hr_delta", 0)) > 25
            or abs(features.get("hr_window_delta", 0)) > 25
        ):
            critical_signals += 1
            reasons.append("rapid_hr_change")
        if features.get("spo2_mean", 100) < 92 or features.get("spo2_min", 100) < 90:
            warning_signals += 1
            reasons.append("persistent_spo2_abnormality")
        if (
            features.get("spo2_drop_rate", 0) > 0.5
            or features.get("spo2_delta", 0) < -3
            or features.get("spo2_window_delta", 0) < -3
        ):
            critical_signals += 1
            reasons.append("rapid_spo2_decline")
        if "sbp_mean" in features and (
            features["sbp_mean"] < 90 or features["sbp_mean"] > 180
            or features.get("dbp_mean", 0) < 60 or features.get("dbp_mean", 0) > 120
        ):
            warning_signals += 1
            reasons.append("bp_abnormality")
        if "sbp_delta" in features and abs(features["sbp_delta"]) > 30:
            critical_signals += 1
            reasons.append("rapid_bp_change")
        if abs(features.get("hr_mean_deviation", 0)) > 25 or abs(features.get("spo2_mean_deviation", 0)) > 3:
            warning_signals += 1
            reasons.append("physiological_deterioration")
        if warning_signals >= 2:
            critical_signals += 1
            reasons.append("physiological_deterioration")
        if activity_result:
            label = activity_result.get("label") if isinstance(activity_result, dict) else getattr(activity_result, "label", None)
            if label:
                features["activity_context"] = str(label)

        abnormal = warning_signals > 0 or critical_signals > 0
        self.abnormal_windows = self.abnormal_windows + 1 if abnormal else 0
        self.critical_windows = (
            self.critical_windows + 1
            if critical_signals or (abnormal and self.critical_windows)
            else 0
        )
        score = min(1.0, 0.25 * warning_signals + 0.40 * critical_signals)
        if self.critical_windows >= self.persistence_windows or (
            self.abnormal_windows >= self.persistence_windows and critical_signals > 0
        ):
            state = "PHYSIO_CRITICAL"
            score = max(score, 0.80)
        elif abnormal:
            state = "PHYSIO_WARNING"
            score = max(score, 0.35)
        else:
            state = "NORMAL"
        confidence = quality * (1.0 if not abnormal else min(1.0, 0.5 + 0.25 * self.abnormal_windows))
        self.previous_features = {
            key: value for key, value in features.items() if isinstance(value, (int, float))
        }
        return PhysiologyRiskResult(score, state, reasons, confidence, quality, features)
