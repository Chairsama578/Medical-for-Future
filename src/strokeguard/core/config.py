from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Settings:
    mode: str = os.getenv("STROKEGUARD_MODE", "simulator")
    bridge_socket: str = os.getenv("STROKEGUARD_BRIDGE_SOCKET", "/var/run/arduino-router.sock")
    poll_hz: float = float(os.getenv("STROKEGUARD_POLL_HZ", "5"))
    window_seconds: float = float(os.getenv("STROKEGUARD_WINDOW_SECONDS", "8"))
    model_path: Path = Path(os.getenv("STROKEGUARD_MODEL_PATH", "models/strokeguard_edge.json"))
    emergency_number: str = os.getenv("STROKEGUARD_EMERGENCY_NUMBER", "112")
    persist_windows: int = int(os.getenv("STROKEGUARD_ALERT_PERSIST_WINDOWS", "2"))
    sensor_quality_min: float = 0.60

settings = Settings()
