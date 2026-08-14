"""StrokeGuard ML fallback — ML-centric phán đoán khi LLM không trả lời/chết.

- P(fall): RandomForest 150 cây (UMA-FALL, mag_dev log1p + tilt, AUC 0.756)
- class: fall | flip | lying | adl — luật vật lý làm feature, ML cross-check
- stroke_fall: ngã/nằm + vitals CRITICAL (HR>=130 hoặc SpO2<90) = nghi đột quỵ
- vitals CRITICAL luôn CRITICAL (BIDMC, đã verify — không hạ cấp)

Pure python, KHÔNG sklearn — chạy trên board. fall_model.json cạnh script.
"""
import json
import math
import os

# ---- ngưỡng đồng bộ CFG main.py ----
VITALS_HR_CRIT = 130
VITALS_HR_HIGH = 120
VITALS_HR_LOW = 50
VITALS_SPO2_CRIT = 90
VITALS_SPO2_WARN = 94
MAG_DEV_FALL = 4.0
TILT_FALL_DEG = 55

ML_FALL_STRONG = 0.45   # P(fall) 2-class
ML_FALL_HINT = 0.22
ML_FALL_MIN_MAG = 1.5   # m/s² — P(fall) chỉ tin cậy khi có chuyển động thật
                        # (dataset UMA-FALL peak 4-8; magdev thấp+tilt cao là
                        #  ngoài phân phối -> không dùng ML, để rule lying lo)
GYRO_FAST = 150         # °/s — xoay/lật nhanh
GYRO_MOVE = 60          # °/s — chuyển động xoay/lật
TILT_CLEAR = 40         # ° — gyro chỉ báo khi nghiêng RÕ (>40°); nghiêng nhẹ
                        #     (<40°) dù xoay nhanh = sinh hoạt thường, không báo

_MODEL = None
_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "fall_model.json")


def _load_model():
    global _MODEL
    if _MODEL is None:
        with open(_MODEL_PATH) as f:
            _MODEL = json.load(f)
    return _MODEL


def _features(magdev, tilt):
    m = float(magdev or 0)
    t = float(tilt or 0)
    return [math.log1p(max(m, 0.0))] * 3 + [t, t]


def predict_fall_prob(magdev, tilt):
    """P(fall) — average votes 150 trees, 2-class [adl, fall]."""
    model = _load_model()
    x = _features(magdev, tilt)
    votes = [0.0, 0.0]
    for tree in model["trees"]:
        i = 0
        while True:
            n = tree[i]
            if n["l"] == -1:
                votes[0] += n["v"][0]
                votes[1] += n["v"][1]
                break
            i = n["r"] if x[n["f"]] <= n["t"] else n["l"]
    s = sum(votes) or 1.0
    return votes[1] / s


def classify(magdev, roll, pitch, gyro=0.0):
    """Phân biệt: fall | flip (lật nhanh) | lying | adl.
    Luật vật lý (tilt/impact/gyro) làm feature + ML P(fall) cross-check."""
    tilt = max(abs(roll), abs(pitch)) if (roll is not None and pitch is not None) else 0.0
    impact = magdev > MAG_DEV_FALL
    lying = tilt > TILT_FALL_DEG
    gyro = float(gyro or 0)
    p = predict_fall_prob(magdev, tilt)

    if impact and (lying or p >= ML_FALL_STRONG):
        return "fall", p
    if gyro > GYRO_FAST and tilt > TILT_CLEAR:
        return "flip", p
    if lying and not impact and gyro < GYRO_MOVE:
        return "lying", p
    return "adl", p


def vitals_level(hr, spo2):
    """Level từ vitals (BIDMC evalcases). Trả (level, reason).
    hr/spo2 <= 0 = không có data."""
    hr = float(hr or 0)
    spo2 = float(spo2 or 0)
    if hr <= 0 and spo2 <= 0:
        return None, ""
    reasons = []
    if hr > 0:
        if hr >= VITALS_HR_CRIT:
            reasons.append(f"Nhịp tim rất cao ({hr:.0f} BPM)")
        elif hr >= VITALS_HR_HIGH:
            reasons.append(f"Nhịp tim cao ({hr:.0f} BPM)")
        elif hr < VITALS_HR_LOW:
            reasons.append(f"Nhịp tim thấp ({hr:.0f} BPM)")
    if spo2 > 0:
        if spo2 < VITALS_SPO2_CRIT:
            reasons.append(f"Thiếu oxy nghiêm trọng (SpO2 {spo2:.0f}%)")
        elif spo2 < VITALS_SPO2_WARN:
            reasons.append(f"SpO2 thấp ({spo2:.0f}%)")
    if not reasons:
        return "NORMAL", ""
    if hr >= VITALS_HR_CRIT or (spo2 > 0 and spo2 < VITALS_SPO2_CRIT):
        return "CRITICAL", ", ".join(reasons)
    return "WARNING", ", ".join(reasons)


def physics_signals(magdev, roll, pitch, gyro=0.0):
    """Tín hiệu vật lý (feature cho ML/LLM — không tự quyết định)."""
    tilt = max(abs(roll), abs(pitch)) if (roll is not None and pitch is not None) else 0.0
    impact = magdev > MAG_DEV_FALL
    lying = tilt > TILT_FALL_DEG
    gyro = float(gyro or 0)
    if impact and lying:
        return 0.8, f"Ngã: va đập {magdev:.1f} m/s² + tư thế lật {tilt:.0f}°"
    if impact:
        return 0.45, f"Va đập / chuyển động mạnh ({magdev:.1f} m/s² lệch)"
    if gyro > GYRO_FAST and tilt > TILT_CLEAR:
        return 0.45, f"Xoay/lật nhanh (gyro {gyro:.0f}°/s)"
    if gyro > GYRO_MOVE and tilt > TILT_CLEAR:
        return 0.35, f"Chuyển động xoay/lật ({gyro:.0f}°/s)"
    if lying:
        return 0.4, f"Tư thế bất thường: nghiêng/lật {tilt:.0f}°"
    return 0.0, ""


def analyze(magdev, roll, pitch, hr, spo2, gyro=0.0):
    """Phán đoán đầy đủ khi LLM chết. Trả dict tương thích LLM analysis:
    {level, risk, reason, source, class, prob}."""
    tilt = max(abs(roll), abs(pitch)) if (roll is not None and pitch is not None) else 0.0
    try:
        cls, p_fall = classify(magdev, roll, pitch, gyro)
    except Exception:
        cls, p_fall = "adl", 0.0
    v_level, v_reason = vitals_level(hr, spo2)
    p_score, p_reason = physics_signals(magdev, roll, pitch, gyro)

    # ---- stroke-fall: ngã/nằm/lật + vitals CRITICAL = nghi đột quỵ ----
    if cls in ("fall", "flip", "lying") and v_level == "CRITICAL":
        reason = (f"Nghi té ngã do đột quỵ: {p_reason or cls}; {v_reason}. "
                  f"[ML] {cls} {p_fall * 100:.0f}%")
        return {"level": "CRITICAL", "risk": "HIGH", "reason": reason,
                "source": "ML", "class": "stroke_fall", "prob": p_fall,
                "score": 1.0}

    # vitals CRITICAL luôn CRITICAL (BIDMC — không hạ cấp)
    if v_level == "CRITICAL":
        return {"level": "CRITICAL", "risk": "HIGH", "reason": v_reason,
                "source": "ML", "class": cls, "prob": p_fall, "score": 0.9}

    score = 0.0
    parts = []
    if p_score:
        score += p_score
        parts.append(p_reason)
    if magdev >= ML_FALL_MIN_MAG and p_fall >= ML_FALL_HINT:
        score += 0.2 if p_fall < ML_FALL_STRONG else 0.4
        parts.append(f"[ML] chuyển động bất thường ({p_fall * 100:.0f}%)")
    if v_level == "WARNING":
        score += 0.25
        parts.append(v_reason)

    if score >= 0.75:
        level, risk = "CRITICAL", "HIGH"
    elif score >= 0.35:
        level, risk = "WARNING", "MEDIUM"
    elif score >= 0.15:
        level, risk = "LOW", "LOW"
    else:
        level, risk = "NORMAL", "LOW"

    reason = "; ".join(parts) if parts else "Dữ liệu bình thường (ML fallback)"
    return {"level": level, "risk": risk, "reason": reason, "source": "ML",
            "class": cls, "prob": p_fall, "score": score}


if __name__ == "__main__":
    import sys
    a = [float(x) for x in sys.argv[1:6]] + [float(sys.argv[6]) if len(sys.argv) > 6 else 0.0]
    print(json.dumps(analyze(*a), ensure_ascii=False, indent=1))
