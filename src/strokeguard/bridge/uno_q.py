import json
import time
from strokeguard.bridge.msgpack_rpc import MessagePackRPCClient
from strokeguard.core.domain import SensorPacket

class UnoQBridge:
    def __init__(self, socket_path="/var/run/arduino-router.sock", mode="simulator"):
        self.mode = mode
        self.client = None if mode == "simulator" else MessagePackRPCClient(socket_path)

    def get_sensor_packet(self) -> SensorPacket:
        if self.mode == "simulator":
            raise RuntimeError("Use SimulatorBridge in simulator mode")
        raw = self.client.call("get_sensor_snapshot")
        if isinstance(raw, bytes):
            raw = raw.decode()
        return SensorPacket.from_dict(json.loads(raw))

    def set_local_alert(self, state: str):
        if self.client:
            return self.client.call("set_local_alert", state)
        return True

    def clear_local_alert(self):
        if self.client:
            return self.client.call("clear_local_alert")
        return True

    def set_sensor_mode(self, mode: str):
        if self.client:
            return self.client.call("set_sensor_mode", mode)
        return True

    def get_status(self):
        if self.client:
            raw = self.client.call("get_device_status")
            if isinstance(raw, bytes): raw = raw.decode()
            return json.loads(raw)
        return {"mode": self.mode, "connected": True}

    def manual_sos(self):
        if self.client:
            return self.client.call("manual_sos")
        return True

class SimulatorBridge(UnoQBridge):
    def __init__(self, simulator):
        super().__init__(mode="simulator")
        self.simulator = simulator

    def get_sensor_packet(self):
        return self.simulator.next_packet()
