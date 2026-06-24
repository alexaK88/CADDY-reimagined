"""
Raw wearable data simulation for the diver wearable unit.

This module simulates the sensor output of a diver-worn device. It generates RawWearablePacket
objects containing raw measurements such as depth, tank pressure, compasse heading, motion intensity,
battery level, button states, and communication link quality.

The simulator is scenario-driven. Different ScenarioName values modify the generates raw measurements
to represent situations such as low gas, fast ascent, lost communication link, no motion,
low battery, or an emergency button press.

This module does not process signals, estimate diver state, or raise alarms. It only produces
raw simulated wearable packets for the rest of the pipeline.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Iterator

from schemas import RawSensorValues, RawWearablePacket, ScenarioName
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SimulatorConfig:
    """
    Configuration for one diver wearable simulation run.

    The config controls both the sampling behaviour and the physical profile of the simulated
    dive. Values such as gas consumption, battery drain, ascent rate, and heading variation are
    expressed in time-based units so that the simulation remains consistent when
    sample_interval_s changes.
    """
    # identity and sampling
    diver_id: str = "diver_01"
    sample_interval_s: float = 1.0

    # depth profile
    cruise_depth_m: float = 22.0
    descent_duration_s: float = 180.0
    bottom_duration_s: float = 300.0
    normal_ascent_rate_m_min: float = 6.0
    fast_ascent_rate_m_min: float = 18.0

    # tank pressure profile
    initial_tank_pressure_bar: float = 200.0
    normal_gas_rate_bar_min: float = 1.2
    low_gas_start_pressure_bar: float = 75.0
    low_gas_rate_bar_min: float = 2.5

    # battery profile
    initial_battery_pct: float = 96.0
    battery_drain_pct_per_min: float = 0.05
    low_battery_start_pct: float = 24.0
    low_battery_drain_pct_per_min: float = 1.0

    # compass profile
    initial_heading_deg: float = 130.0
    heading_sway_amplitude_deg: float = 20.0
    heading_sway_period_s: float = 90.0
    heading_noise_deg: float = 2.0

    # emergency button profile
    emergency_button_trigger_s: float = 25.0

    # randomness
    random_seed: int | None = 42


class DiverWearableSimulator:
    """
    Generates raw wearable packets for one simulated diver.

    The simulator behaves like a sensor layer of a future physical wearable.
    For each sample index, it calculates the corresponding elapsed simulation time and
    generates raw sensor values for that moment.

    The simulator is intentionally limited to raw data generation. It does not calculate derived
    rates, classify diver state, or produce safety alarms.
    """

    def __init__(self,
                 scenario: ScenarioName = ScenarioName.NORMAL,
                 config: SimulatorConfig | None = None,
                 start_time: datetime | None = None, ):
        """
        Initialize a simulator for one diver and one scenario.


        :param scenario: Simulation scenario used to modify generates raw values.
        :param config: optional simulator configuration. If omitted, default values are used.
        :param start_time: Optional UTC start time for generated packets. If omitted, the current
        UTC time is used.
        """
        self.scenario = scenario
        self.config = config or SimulatorConfig()

        if self.config.sample_interval_s <= 0:
            raise ValueError("sample_interval_s must be positive")

        if self.config.heading_sway_period_s <= 0:
            raise ValueError("heading_sway_period_s must be positive")

        if self.config.descent_duration_s <= 0:
            raise ValueError("descent_duration_s must be positive")

        if self.config.bottom_duration_s < 0:
            raise ValueError("bottom_duration_s must be non-negative")

        self.start_time = start_time or datetime.now(timezone.utc)
        self._random = random.Random(self.config.random_seed)

        logger.info("Diver wearable simulator initialized: diver_id=%s, scenario=%s", self.config.diver_id,
                    self.scenario.value, )

    def stream(self, samples: int) -> Iterator[RawWearablePacket]:
        """
        Generate a sequence of raw wearable packets.

        The method yields one RawWearablePacket per sample index, starting at sample 0 and ending
        at samples - 1. It does not store packets internally, so callers can process the stream one
        packet at a time.
        """

        if samples < 0:
            raise ValueError("samples must be non-negative")

        logger.info("Starting packet stream: samples=%s, scenario=%s", samples, self.scenario.value, )

        for sample_index in range(samples):
            yield self.sample(sample_index)

        logger.info("Packet stream finished")

    def sample(self, sample_index: int) -> RawWearablePacket:
        """
        Generate one raw wearable packet for a given sample index.

        The sample index is converted into elapsed simulation time using
        sample_interval_s. The method then generates all raw sensor values for
        that time point and wraps them in a RawWearablePacket with metadata.
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
                                 elapsed_time_s=elapsed_time_s, produced_at_utc=produced_at_utc, values=values, )

    # -----------------------------------------------------------------
    # Sensor model methods
    # -----------------------------------------------------------------
    def _depth(self, sample_index: int) -> float:
        """
        Simulate diver depth using time-based dive phases.

        Basic NORMAL profile:
        - descent from surface to cruise depth
        - stable bottom phase
        - controlled ascent

        FAST_ASCENT uses a faster ascent rate after the bottom phase.

        This method only returns depth.
        """

        elapsed_time_s = sample_index * self.config.sample_interval_s

        descent_end_s = self.config.descent_duration_s
        bottom_end_s = self.config.descent_duration_s + self.config.bottom_duration_s

        cruise_depth = self.config.cruise_depth_m

        if elapsed_time_s < descent_end_s:
            descent_progress = elapsed_time_s / self.config.descent_duration_s
            depth = cruise_depth * descent_progress

        elif elapsed_time_s < bottom_end_s:
            bottom_time_s = elapsed_time_s - descent_end_s
            depth = cruise_depth + math.sin(bottom_time_s / 20.0) * 0.3

        else:
            elapsed_ascent_s = elapsed_time_s - bottom_end_s
            elapsed_ascent_min = elapsed_ascent_s / 60.0

            if self.scenario == ScenarioName.FAST_ASCENT:
                ascent_rate_m_min = self.config.fast_ascent_rate_m_min
            else:
                ascent_rate_m_min = self.config.normal_ascent_rate_m_min

            depth = max(0.0, cruise_depth - elapsed_ascent_min * ascent_rate_m_min, )

        depth += self._random.uniform(-0.03, 0.03)

        return max(0.0, depth)

    def _tank_pressure(self, sample_index: int) -> float:
        """
        Simulate tank pressure in bar.

        In NORMAL and most scenarios, pressure starts from initial_tank_pressure_bar_min. In LOW_GAS
        scenario, pressure starts from a lower configured value and decreases according to
        low_gas_rate_bar_min.

        The returned pressure is clamped to a minimum value to avoid physically impossible negative
        pressure.
        """

        elapsed_time_s = sample_index * self.config.sample_interval_s
        elapsed_time_min = elapsed_time_s / 60.0

        if self.scenario == ScenarioName.LOW_GAS:
            pressure = (self.config.low_gas_start_pressure_bar - elapsed_time_min * self.config.low_gas_rate_bar_min)
        else:
            pressure = (self.config.initial_tank_pressure_bar - elapsed_time_min * self.config.normal_gas_rate_bar_min)

        return max(25.0, pressure)

    def _heading(self, sample_index: int) -> float:
        """
        Simulate compass heading in degrees.

        The heading slowly oscillates around initial_heading_deg to represent natural diver
        movement. A small random noise component is added to imitate sensor variation.

        Returned value is always normalized to:
            0 <= heading < 360
        """

        elapsed_time_s = sample_index * self.config.sample_interval_s

        if self.config.heading_sway_period_s <= 0:
            raise ValueError("heading_sway_period_s must be positive")

        sway_angle = (2.0 * math.pi * elapsed_time_s) / self.config.heading_sway_period_s

        heading = self.config.initial_heading_deg
        heading += math.sin(sway_angle) * self.config.heading_sway_amplitude_deg
        heading += self._random.uniform(-self.config.heading_noise_deg, self.config.heading_noise_deg, )

        return self._normalize_heading_deg(heading)

    def _motion_intensity(self, sample_index: int) -> float:
        """
        Simulate simplified IMU/motion intensity.

        0.0 = no movement
        1.0 = strong movement

        In the NO_MOTION scenario, the signal dropos to a near-zero value after the configured
        trigger point. In normal behaviour, the signal varies around a moderate swimming-like motion
        level with random noise.
        """
        # TODO: Move NO_MOTION trigger and motion oscillation to time-based config values.
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

        In normal scenarios, battery decreases slowly according to
        battery_drain_pct_per_min. In BATTERY_LOW scenario, the battery starts at
        a lower level and drains faster.

        The returned value is clamped to avoid reaching zero in the current
        simulation.
        """

        elapsed_time_s = sample_index * self.config.sample_interval_s
        elapsed_time_min = elapsed_time_s / 60.0

        if self.scenario == ScenarioName.BATTERY_LOW:
            battery = self.config.low_battery_start_pct - elapsed_time_min * self.config.low_battery_drain_pct_per_min
        else:
            battery = (self.config.initial_battery_pct - elapsed_time_min * self.config.battery_drain_pct_per_min)

        return max(3.0, battery)

    def _emergency_button(self, sample_index: int) -> bool:
        """
        Simulate emergency button press.

        In EMERGENCY_BUTTON scenario, the button becomes pressed after the
        configured trigger point. In all other scenarios, it remains false.
        """
        return self.scenario == ScenarioName.EMERGENCY_BUTTON and sample_index >= self.config.emergency_button_trigger_s

    def _ack_button(self, sample_index: int) -> bool:
        """
        Simulate acknowledge button.

        In the current version, this always returns false because the wearable
        does not yet receive messages from a robot or surface system. Later, this
        can be connected to incoming command or notification messages.
        """

        return False

    def _link_quality(self, sample_index: int) -> float:
        """
        Simulate communication link quality.

        0.0 = no link
        1.0 = excellent link

        In WEAK_LINK scenario, link quality drops to a weak but nonzero level.
        In LOST_LINK scenario, link quality drops close to zero. In normal
        operation, link quality stays high with small random variation.
        """

        if self.scenario == ScenarioName.LOST_LINK and sample_index >= 35:
            link_quality = 0.03 + self._random.uniform(-0.02, 0.02)
            return max(0.0, min(1.0, link_quality))

        if self.scenario == ScenarioName.WEAK_LINK and sample_index >= 25:
            link_quality = 0.28 + self._random.uniform(-0.08, 0.08)
            return max(0.0, min(1.0, link_quality))

        link_quality = 0.88 + self._random.uniform(-0.06, 0.06)
        return max(0.0, min(1.0, link_quality))

    @staticmethod
    def _normalize_heading_deg(heading_deg: float) -> float:
        """
        Normalize a heading angle to the range:
            0 <= heading < 360
        """

        return heading_deg % 360.0
