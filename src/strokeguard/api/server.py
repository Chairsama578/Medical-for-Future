from dataclasses import asdict
from fastapi import FastAPI
from pydantic import BaseModel
from strokeguard.core.domain import FastSymptoms
from strokeguard.core.config import settings
from strokeguard.bridge.uno_q import UnoQBridge, SimulatorBridge
from strokeguard.sensors.simulator import SensorSimulator
from strokeguard.ai.inference import EdgeInference
from strokeguard.safety.fusion import SafetyFusion
from strokeguard.core.runtime import StrokeGuardEngine

app=FastAPI(title="StrokeGuard AI",version="3.0.0")
if settings.mode=="simulator":
    bridge=SimulatorBridge(SensorSimulator("normal"))
else:
    bridge=UnoQBridge(settings.bridge_socket,settings.mode)
inference=EdgeInference(settings.model_path,window_size=max(10,int(settings.poll_hz*settings.window_seconds)))
fusion=SafetyFusion(settings.persist_windows)
engine=StrokeGuardEngine(bridge, inference)

class Symptoms(BaseModel):
    balance_loss: bool=False
    eye_changes: bool=False
    face_drooping: bool=False
    arm_weakness: bool=False
    speech_difficulty: bool=False
    onset_timestamp: float|None=None

@app.get("/health")
def health(): return {"status":"ok","mode":settings.mode,"ai_local":True,"v4_enabled":engine.v4_enabled}

@app.get("/device")
def device(): return bridge.get_status()

@app.get("/sensor")
def sensor():
    p,pred,decision=engine.step()
    v4=engine.last_v4
    payload={"sensor":p.to_dict(),
            "prediction":{"state":pred.state.value,"score":pred.score,"probabilities":pred.probabilities,
                          "reasons":pred.reasons,"model_version":pred.model_version},
            "decision":{"state":decision.state.value,"score":decision.score,"reasons":decision.reasons,
                         "emergency":decision.emergency,"local_alert":decision.local_alert,
                         "sos":decision.sos,"timestamp":decision.timestamp}}
    if v4:
        physiology_payload=asdict(v4.physiology)
        physiology_payload.update({
            "heart_rate": p.heart_rate_bpm,
            "spo2": p.spo2_pct,
            "sbp": p.systolic_bp_mmhg,
            "dbp": p.diastolic_bp_mmhg,
            "battery": p.battery_pct,
        })
        payload.update({
            "activity": v4.activity.to_dict(),
            "physiology": physiology_payload,
            "fall": asdict(v4.fall),
            "risk": {
                "state": decision.state.value,
                "score": decision.score,
                "reasons": decision.reasons,
            },
            "emergency_event": v4.emergency_event.to_dict() if v4.emergency_event else None,
        })
    return payload

@app.post("/sos")
def sos():
    bridge.manual_sos()
    return {
        "emergency":True,
        "medical_emergency_number":settings.emergency_number,
        "message":"SOS latched locally. Contact emergency medical services immediately."
    }

@app.post("/symptoms")
def symptoms(s:Symptoms):
    fs=FastSymptoms(**s.model_dump())
    return {
        "fast_active":fs.any_active(),
        "active_count":fs.active_count(),
        "emergency":fs.any_active(),
        "message":"Suspected stroke symptoms require immediate emergency medical help and symptom-onset time should be recorded."
    }
