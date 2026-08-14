from strokeguard.core.domain import FastSymptoms

def evaluate(symptoms: FastSymptoms) -> tuple[bool, list[str]]:
    reasons = []
    if symptoms.balance_loss: reasons.append("B: sudden balance loss")
    if symptoms.eye_changes: reasons.append("E: sudden vision change")
    if symptoms.face_drooping: reasons.append("F: face drooping")
    if symptoms.arm_weakness: reasons.append("A: arm weakness")
    if symptoms.speech_difficulty: reasons.append("S: speech difficulty")
    return bool(reasons), reasons
