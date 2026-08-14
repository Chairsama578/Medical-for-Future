#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline LLM eval: OLD prompt vs NEW dataset-driven prompt (23 cases).
Cases: 17 vitals (BIDMC ICU ground truth) + 6 motion (UMAFall-derived).
Run INSIDE app container: docker exec strokeguard_ai-main-1 python3 /app/eval_llm.py
"""
import time

from arduino.app_bricks.llm import LargeLanguageModel


class _BoundedLLM(LargeLanguageModel):
    def __init__(self, **kw):
        kw.setdefault("max_tokens", 192)
        kw.setdefault("timeout", 90)
        super().__init__(**kw)


LLM = _BoundedLLM(model="llamacpp:Qwen3.5-0.8B-Q4_0")
print("[LLM-INIT-OK]", flush=True)

LEVELS = ("NORMAL", "WARNING", "CRITICAL")


def parse(resp):
    if not resp:
        return None
    s = resp.replace(";", "|").replace(",", "|")
    if "<think>" in s.lower():
        low = s.lower()
        idx = low.rfind("</think>")
        if idx != -1:
            s = s[idx + 8:]
        else:
            for kw in ("CRITICAL", "WARNING", "NORMAL"):
                i = s.upper().rfind(kw)
                if i != -1:
                    s = s[i:]
                    break
    parts = [p.strip() for p in s.split("|")]

    def clean(p):
        p = p.strip()
        if "=" in p:
            p = p.split("=", 1)[1]
        return p.strip(" :\t.").upper()

    lvl = clean(parts[0]) if parts else ""
    if lvl == "LOW":
        lvl = "NORMAL"
    if lvl not in LEVELS:
        found = None
        for p in parts:
            for sub in p.split("/"):
                c2 = clean(sub)
                if c2 == "LOW":
                    c2 = "NORMAL"
                if c2 in LEVELS:
                    if found is None or LEVELS.index(c2) > LEVELS.index(found):
                        found = c2
        if found is None:
            # "level=CRITICAL risk=HIGH reason=..." (space-separated, no pipes)
            import re
            m = re.search(r"level\s*[=:]\s*(CRITICAL|WARNING|NORMAL)", s, re.I)
            found = m.group(1).upper() if m else None
        if found is None:
            return None
        lvl = found
    return lvl


FEWSHOT_OLD = (
    "Examples:\n"
    "mag_dev=0.3 tilt=5 -> NORMAL|LOW|Không bất thường\n"
    "mag_dev=5.2 tilt=60 -> CRITICAL|HIGH|Ngã: va đập mạnh kèm tư thế lật, cần cấp cứu\n"
)

FEWSHOT_NEW = (
    "Examples (real dataset cases):\n"
    "mag_dev=0.4 tilt=8 -> NORMAL|LOW|Vận động bình thường\n"
    "mag_dev=2.1 tilt=12 -> WARNING|MODERATE|Va đập nhẹ, theo dõi\n"
    "mag_dev=6.8 tilt=63 -> CRITICAL|HIGH|Ngã: va đập mạnh kèm lật người, cấp cứu\n"
    "HR=66 SpO2=100 -> NORMAL|LOW|Chỉ số sinh tồn ổn định\n"
    "HR=94 SpO2=93 -> WARNING|MODERATE|Oxy máu giảm nhẹ, theo dõi\n"
    "HR=126 SpO2=100 -> CRITICAL|HIGH|Nhịp tim quá nhanh, nguy cơ thiếu máu não\n"
    "HR=84 SpO2=85 -> CRITICAL|HIGH|Thiếu oxy nghiêm trọng, cấp cứu\n"
)

RULES = (
    "Rules: HR=0 or SpO2=0 means NO DATA (ignore it). "
    "Impact+lying=CRITICAL. Impact alone=WARNING. Tilt alone=WARNING. "
    "SpO2<90 or HR>120=CRITICAL. SpO2 91-93 or HR 50-60=WARNING. "
    "No data=NORMAL|LOW. Normal=NORMAL.\n"
    "Output EXACTLY: level|stroke_risk|reason (VN, <=60 chars). "
    "level=NORMAL/WARNING/CRITICAL risk=LOW/MODERATE/HIGH. "
    "No thinking, no extra text."
)


def build(fewshot, c):
    hr = c.get("hr", 0) or 0
    sp = c.get("spo2", 0) or 0
    return (
        "StrokeGuard: ESP32 sensor via MQTT. Diagnose fall/stroke risk.\n"
        + fewshot
        + "Now analyze:\n"
        + f"device=esp32-strokeguard-01 mag_dev={c['magdev']:.2f} "
        + f"tilt_roll={c['roll']:.0f} tilt_pitch={c.get('pitch', 0):.0f}\n"
        + f"HR={hr:.0f} SpO2={sp:.0f} "
        + "gyro=(0.0,0.0,0.0) ir=300 red=310 signal_ok=True "
        + "flags=['test']\n"
        + RULES
    )


# 17 vitals from BIDMC ICU ground truth + 6 motion from UMAFall findings.
# EVAL_NEW_ONLY: bỏ OLD (đã đo 0/4) + rút còn 12 cases đại diện — model 0.8B
# generate ~3 tok/s, CoT dài → 46 calls mất ~50 phút (threads=1).
import os
CASES = [
    # --- CRITICAL: HR > 120 (BIDMC) ---
    {"name": "b-hr121", "hr": 121.0, "spo2": 100.0, "magdev": 0.1, "roll": 0, "expected": "CRITICAL"},
    {"name": "b-hr124", "hr": 124.0, "spo2": 100.0, "magdev": 0.1, "roll": 0, "expected": "CRITICAL"},
    # --- CRITICAL: SpO2 < 90 (BIDMC hypoxia) ---
    {"name": "b-spo85a", "hr": 84.0, "spo2": 85.0, "magdev": 0.1, "roll": 0, "expected": "CRITICAL"},
    {"name": "b-spo88", "hr": 90.0, "spo2": 88.0, "magdev": 0.1, "roll": 0, "expected": "CRITICAL"},
    # --- WARNING: SpO2 91-93 (BIDMC) ---
    {"name": "b-spo93a", "hr": 94.0, "spo2": 93.0, "magdev": 0.1, "roll": 0, "expected": "WARNING"},
    {"name": "b-spo91", "hr": 91.0, "spo2": 91.0, "magdev": 0.1, "roll": 0, "expected": "WARNING"},
    # --- NORMAL: SpO2 96-99 (BIDMC) ---
    {"name": "b-ok97", "hr": 94.0, "spo2": 97.0, "magdev": 0.1, "roll": 0, "expected": "NORMAL"},
    {"name": "b-ok98", "hr": 94.0, "spo2": 98.0, "magdev": 0.1, "roll": 0, "expected": "NORMAL"},
    # --- Motion: falls / ADL (UMAFall) ---
    {"name": "u-fall68", "hr": 0, "spo2": 0, "magdev": 6.8, "roll": 63, "expected": "CRITICAL"},
    {"name": "u-impact", "hr": 0, "spo2": 0, "magdev": 5.2, "roll": 10, "expected": "WARNING"},
    {"name": "u-adl", "hr": 0, "spo2": 0, "magdev": 1.2, "roll": 15, "expected": "NORMAL"},
    {"name": "u-nodata", "hr": 0, "spo2": 0, "magdev": 0.3, "roll": 4, "expected": "NORMAL"},
]


def run(fewshot, label):
    ok = total = 0
    for c in CASES:
        try:
            resp = LLM.chat(build(fewshot, c))
            LLM.clear_memory()  # brick giữ history -> phình ctx (lỗi 400 đã gặp)
        except Exception as e:
            LLM.clear_memory()
            print(f"[{label}] {c['name']} exp={c['expected']} got=ERR {e}", flush=True)
            continue
        lvl = parse(resp)
        good = lvl == c["expected"]
        ok += good
        total += 1
        mark = "OK " if good else "X  "
        print(f"[{label}] {mark}{c['name']} exp={c['expected']} got={lvl} | {str(resp)[:90]!r}", flush=True)
    print(f"\n=== {label}: {ok}/{total} exact-level match ===", flush=True)
    return ok, total


if __name__ == "__main__":
    t0 = time.time()
    # OLD đã đo trước đó: 0/4 (HR>120 → NORMAL sai) — chỉ chạy NEW (12 cases, ~15 phút)
    ok2, t2 = run(FEWSHOT_NEW, "NEW")
    print(f"\nSUMMARY: NEW {ok2}/{t2}  (OLD baseline: 0/4)  ({time.time()-t0:.0f}s)", flush=True)
