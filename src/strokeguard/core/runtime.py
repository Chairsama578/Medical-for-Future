import time, logging
from dataclasses import asdict
from strokeguard.core.config import settings
from strokeguard.core.events import EventStore
from strokeguard.safety.fusion import SafetyFusion
from strokeguard.safety.alerts import AlertController

log=logging.getLogger("strokeguard")

class StrokeGuardEngine:
    def __init__(self, bridge, inference, event_store=None, symptoms=None):
        self.bridge=bridge
        self.inference=inference
        self.fusion=SafetyFusion(settings.persist_windows)
        self.alerts=AlertController(bridge)
        self.events=event_store or EventStore()
        self.symptoms=symptoms
        self.last_packet=None
        self.last_prediction=None
        self.last_decision=None

    def step(self):
        packet=self.bridge.get_sensor_packet()
        self.last_packet=packet
        self.inference.push(packet)
        prediction=self.inference.predict()
        decision=self.fusion.decide(packet,prediction,self.symptoms)
        self.last_prediction=prediction
        self.last_decision=decision
        self.alerts.apply(decision)
        self.events.log("risk_decision", decision.state.value, decision.score, {
            "sensor":packet.to_dict(),
            "prediction":asdict(prediction),
            "decision":asdict(decision)
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
