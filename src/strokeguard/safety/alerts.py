from strokeguard.core.domain import RiskDecision, RiskState
from strokeguard.bridge.uno_q import UnoQBridge

class AlertController:
    def __init__(self, bridge: UnoQBridge):
        self.bridge = bridge

    def apply(self, decision: RiskDecision):
        if decision.local_alert:
            self.bridge.set_local_alert(decision.state.value)
        elif decision.state == RiskState.NORMAL:
            self.bridge.set_local_alert("OFF")
        if decision.sos:
            self.bridge.manual_sos()
