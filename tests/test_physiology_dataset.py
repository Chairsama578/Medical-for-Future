import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_physiology_raw
import pandas as pd
from strokeguard.core.domain import SensorPacket
from strokeguard_v4.physiology import PhysiologyRiskEngine


def test_bidmc_demo_subset_is_detected():
    assert validate_physiology_raw.main() == 0


def test_bidmc_schema_and_offline_engine_mode():
    data = pd.read_csv("data/unified/bidmc_physiology.csv")
    assert set(["record_id", "heart_rate_bpm", "spo2_pct", "respiration_rate"]).issubset(data)
    rows = data.dropna(subset=["heart_rate_bpm", "spo2_pct"]).iloc[:40]
    packets = [SensorPacket(
        timestamp=float(row.timestamp),
        heart_rate_bpm=float(row.heart_rate_bpm),
        spo2_pct=float(row.spo2_pct),
        accel_x_g=None, accel_y_g=None, accel_z_g=None,
        sensor_quality=1.0,
    ) for row in rows.itertuples()]
    result = PhysiologyRiskEngine().decide(packets, require_imu=False)
    assert result.state in {"NORMAL", "PHYSIO_WARNING", "PHYSIO_CRITICAL"}
