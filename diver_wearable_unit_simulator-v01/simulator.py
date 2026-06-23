from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Iterator

from .schemas import RawSensorValues, RawWearablePacket, ScenarioName
from .utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SimulatorConfig:
    """
    Configuration for the diver wearable simulator.
    """

    diver_id: str = "diver_01"
    sample_interval_s: float = 1.0

    cruise_depth_m: float = 22.0

    initial_tank_pressure_bar: float = 200.0
    initial_battery_pct: float = 96.0

    random_seed: int | None = 42


class DiverWearableSimulator:
    """
    Generates raw wearable packets for one simulated diver.

    The simulator behaves like a future physical wearable:
    it produces raw measurements but does not interpret them.
    """

    def __init__(self,
                 scenario: ScenarioName = ScenarioName.NORMAL,
                 config: SimulatorConfig | None = None,
                 start_time: datetime | None = None, ):
        self.scenario = scenario
        self.config = config or SimulatorConfig()

        if self.config.sample_interval_s <= 0:
            raise ValueError("sample_interval_s must be positive")

        self.start_time = start_time or datetime.now(timezone.utc)
        self._random = random.Random(self.config.random_seed)

        logger.info("Diver wearable simulator initialized: diver_id=%s, scenario=%s",
                    self.config.diver_id, self.scenario.value, )

    def stream(self, samples: int) -> Iterator[RawWearablePacket]:
        """
        Generate a sequence of raw wearable packets.
        """

        if samples < 0:
            raise ValueError("samples must be non-negative")

        logger.info("Starting packet stream: samples=%s, scenario=%s", samples,
                    self.scenario.value, )

        for sample_index in range(samples):
            yield self.sample(sample_index)

        logger.info("Packet stream finished")

    def sample(self, sample_index: int) -> RawWearablePacket:
        """
        Generate one raw wearable packet for a given sample index.
        """

        if sample_index < 0:
            raise ValueError("sample_index must be non-negative")

        elapsed_time_s = sample_index * self.config.sample_interval_s
        produced_at_utc = self.start_time + timedelta(seconds=elapsed_time_s)

        values = RawSensorValues(depth_m=round(self._depth(sample_index), 2),
                                 tank_pressure_bar=round(self._tank_pressure(sample_index), 1),
                                 heading_deg=round(self._heading(sample_index), 1),
                                 motion_intensity=round(self._motion_intensity(sample_index), 3),
                                 battery_pct=round(self._battery(sample_index), 1),
                                 emergency_button_pressed=self._emergency_button(sample_index),
                                 ack_button_pressed=self._ack_button(sample_index),
                                 link_quality=round(self._link_quality(sample_index), 2), )

        return RawWearablePacket(diver_id=self.config.diver_id, sample_index=sample_index,
                                 elapsed_time_s=elapsed_time_s, produced_at_utc=produced_at_utc,
                                 values=values, )

    def _depth(self, sample_index: int) -> float:
        """
        Simulate diver depth.

        Basic profile:
        - 0-20 samples: descent
        - 20-70 samples: stable working depth
        - 70+ samples: slow ascent

        FAST_ASCENT overrides this after sample 45.
        """

        cruise_depth = self.config.cruise_depth_m

        if sample_index < 20:
            depth = sample_index * (cruise_depth / 20)

        elif sample_index < 70:
            depth = cruise_depth + math.sin(sample_index / 8) * 0.5

        else:
            depth = max(0.0, cruise_depth - (sample_index - 70) * 0.25)

        if self.scenario == ScenarioName.FAST_ASCENT and sample_index >= 45:
            depth = max(0.0, cruise_depth - (sample_index - 45) * 0.65)

        depth += self._random.uniform(-0.05, 0.05)

        return max(0.0, depth)

    def _tank_pressure(self, sample_index: int) -> float:
        """
        Simulate tank pressure in bar.
        """

        if self.scenario == ScenarioName.LOW_GAS:
            pressure = 105.0 - sample_index * 0.85
        else:
            pressure = self.config.initial_tank_pressure_bar - sample_index * 0.45

        return max(25.0, pressure)

    def _heading(self, sample_index: int) -> float:
        """
        Simulate compass heading in degrees.
        """

        heading = 130.0
        heading += math.sin(sample_index / 12) * 25.0
        heading += self._random.uniform(-2.0, 2.0)

        return heading % 360

    def _motion_intensity(self, sample_index: int) -> float:
        """
        Simulate simplified IMU/motion intensity.

        0.0 = no movement
        1.0 = strong movement
        """

        if self.scenario == ScenarioName.NO_MOTION and sample_index >= 30:
            motion = 0.02 + self._random.uniform(-0.01, 0.01)
            return max(0.0, min(1.0, motion))

        motion = 0.38
        motion += math.sin(sample_index / 6) * 0.08
        motion += self._random.uniform(-0.08, 0.08)

        return max(0.0, min(1.0, motion))

    def _battery(self, sample_index: int) -> float:
        """
        Simulate wearable battery percentage.
        """

        if self.scenario == ScenarioName.BATTERY_LOW:
            battery = 24.0 - sample_index * 0.25
        else:
            battery = self.config.initial_battery_pct - sample_index * 0.025

        return max(3.0, battery)

    def _emergency_button(self, sample_index: int) -> bool:
        """
        Simulate emergency button press.
        """

        return self.scenario == ScenarioName.EMERGENCY_BUTTON and sample_index >= 25

    def _ack_button(self, sample_index: int) -> bool:
        """
        Simulate acknowledge button.

        For v0.1 this is always false.
        Later, it can respond to incoming robot messages.
        """

        return False

    def _link_quality(self, sample_index: int) -> float:
        """
        Simulate communication link quality.

        0.0 = no link
        1.0 = excellent link
        """

        if self.scenario == ScenarioName.LOST_LINK and sample_index >= 35:
            link_quality = 0.03 + self._random.uniform(-0.02, 0.02)
            return max(0.0, min(1.0, link_quality))

        if self.scenario == ScenarioName.WEAK_LINK and sample_index >= 25:
            link_quality = 0.28 + self._random.uniform(-0.08, 0.08)
            return max(0.0, min(1.0, link_quality))

        link_quality = 0.88 + self._random.uniform(-0.06, 0.06)
        return max(0.0, min(1.0, link_quality))
