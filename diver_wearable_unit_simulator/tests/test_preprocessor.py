from datetime import datetime, timezone

import pytest

from preprocessing import SignalPreprocessor
from schemas import RawSensorValues, RawWearablePacket


def make_packet(sample_index: int,
        elapsed_time_s: float,
        depth_m: float,
        tank_pressure_bar: float | None = 150.0) -> RawWearablePacket:
    return RawWearablePacket(diver_id="diver_01", sample_index=sample_index,
        elapsed_time_s=elapsed_time_s, produced_at_utc=datetime.now(timezone.utc),
        values=RawSensorValues(depth_m=depth_m, tank_pressure_bar=tank_pressure_bar,
            heading_deg=120.0, motion_intensity=0.4, battery_pct=90.0, link_quality=0.9))


def test_first_packet_has_no_rates():
    preprocessor = SignalPreprocessor()
    packet = make_packet(sample_index=0, elapsed_time_s=0.0, depth_m=10.0,
        tank_pressure_bar=150.0)
    clean = preprocessor.process(packet)

    assert clean.ascent_rate_m_min is None
    assert clean.gas_rate_bar_min is None


def test_ascent_rate_is_positive_when_depth_decreases():
    preprocessor = SignalPreprocessor()
    preprocessor.process(make_packet(0, 0.0, depth_m=20.0))
    clean = preprocessor.process(make_packet(1, 60.0, depth_m=15.0))

    assert clean.ascent_rate_m_min == 5.0


def test_gas_rate_is_positive_when_pressure_decreases():
    preprocessor = SignalPreprocessor()
    preprocessor.process(make_packet(0, 0.0, depth_m=10.0, tank_pressure_bar=150.0))
    clean = preprocessor.process(make_packet(1, 60.0, depth_m=10.0, tank_pressure_bar=145.0))

    assert clean.gas_rate_bar_min == 5.0


def test_elapsed_time_must_increase():
    preprocessor = SignalPreprocessor()
    preprocessor.process(make_packet(0, 10.0, depth_m=10.0))

    with pytest.raises(ValueError):
        preprocessor.process(make_packet(1, 10.0, depth_m=9.0))
