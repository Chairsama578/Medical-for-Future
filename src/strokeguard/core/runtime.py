import time, logging
from dataclasses import asdict
from strokeguard.core.config import settings
from strokeguard.core.events import EventStore
from strokeguard.safety.fusion import SafetyFusion
from strokeguard.safety.alerts import AlertController
from strokeguard_v4.runtime import V4RuntimeAdapter, v4_decision_to_risk_decision

log=logging.getLogger("strokeguard")

class StrokeGuardEngine:
    def __init__(self, bridge, inference, event_store=None, symptoms=None, v4_enabled=None):
        self.bridge=bridge
        self.inference=inference
        self.fusion=SafetyFusion(settings.persist_windows)
        self.alerts=AlertController(bridge)
        self.events=event_store or EventStore()
        self.symptoms=symptoms
        self.last_packet=None
        self.last_prediction=None
        self.last_decision=None
        self.v4_enabled = settings.v4_enabled if v4_enabled is None else v4_enabled
        self.v4 = V4RuntimeAdapter(
            window_size=max(10, int(settings.poll_hz * settings.window_seconds)),
        ) if self.v4_enabled else None
        self.last_v4 = None
        self.last_emergency_event = None

    def step(self):
        packet=self.bridge.get_sensor_packet()
        self.last_packet=packet
        self.inference.push(packet)
        prediction=self.inference.predict()
        decision=self.fusion.decide(packet,prediction,self.symptoms)
        if self.v4 is not None:
            self.last_v4 = self.v4.step(packet, self.symptoms)
            decision = v4_decision_to_risk_decision(self.last_v4, decision)
            self.last_emergency_event = self.last_v4.emergency_event
        self.last_prediction=prediction
        self.last_decision=decision
        self.alerts.apply(decision)
        self.events.log("risk_decision", decision.state.value, decision.score, {
            "sensor":packet.to_dict(),
            "prediction":asdict(prediction),
            "decision":asdict(decision),
            "v4_enabled": self.v4_enabled,
            "v4": asdict(self.last_v4) if self.last_v4 else None,
        })
        if decision.emergency:
            self.events.log("emergency_signal", decision.state.value, decision.score, {
                "reasons":decision.reasons,
                "sos":decision.sos
            })
        return packet,prediction,decision

    def run_forever(self):
        period=1.0/settings.poll_hz
        while True:
            started=time.monotonic()
            try:
                self.step()
            except Exception:
                log.exception("engine step failed")
            elapsed=time.monotonic()-started
            time.sleep(max(0,period-elapsed))
