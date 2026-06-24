"""
Signal preprocessing for the diver wearable simulator.

This module converts RawWearablePacket objects into CleanSensorPacket objects.
It keeps the latest previous sample so that time-based rates can be calculated, such as ascent/descent rate and gas
consumption rate.

The preprocessor does not interpret the diver's state and does not generate alarms. It only prepares cleaned numerical
signals for the estimator.
"""

from __future__ import annotations

from dataclasses import dataclass

from schemas import CleanSensorPacket, RawWearablePacket
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class PreviousSample:
    """
    Previous packet values needed to calculate rates.

    The preprocessor stores only the fields required to compare the current packet with the previous one: elapse time,
    depth, and tank pressure.
    """

    elapsed_time_s: float
    depth_m: float
    tank_pressure_bar: float | None


class SignalPreprocessor:
    """
    Converts RawWearablePacket objects into CleanSensorPacket objects.

    Responsibilities:
    - copy packet metadata forward
    - flatten packet metadata and raw values into CleanSensorPacket
    - calculate ascent/descent rate in meters/minute
    - calculate gas consumption rate in bar/minute
    - keep previous sample for rate calculation

    This class does NOT classify safety state or raise alarms.
    """

    def __init__(self):
        """
        Initialise an empty preprocessor with no previous sample.

        The first processed packet cannot produce rate values because there is no earlier packet to compare against.
        """
        self._previous: PreviousSample | None = None

    def process(self, packet: RawWearablePacket) -> CleanSensorPacket:
        """
        Convert one raw wearable packet into a clean sensor packet.

        The method copies packet metadata and raw sensor values, calculates available rates using the previous sample,
        and then stores the current packet as the new previous sample.

        For the first packet in a stream, rate values are None because no previous sample exists yet.
        """

        values = packet.values

        ascent_rate_m_min = self._calculate_ascent_rate(packet)
        gas_rate_bar_min = self._calculate_gas_rate(packet)

        clean_packet = CleanSensorPacket(diver_id=packet.diver_id, sample_index=packet.sample_index,
                                         elapsed_time_s=packet.elapsed_time_s, produced_at_utc=packet.produced_at_utc,

                                         depth_m=values.depth_m, tank_pressure_bar=values.tank_pressure_bar,
                                         heading_deg=values.heading_deg, motion_intensity=values.motion_intensity,
                                         battery_pct=values.battery_pct,
                                         emergency_button_pressed=values.emergency_button_pressed,
                                         ack_button_pressed=values.ack_button_pressed, link_quality=values.link_quality,

                                         ascent_rate_m_min=ascent_rate_m_min, gas_rate_bar_min=gas_rate_bar_min, )

        self._previous = PreviousSample(elapsed_time_s=packet.elapsed_time_s, depth_m=values.depth_m,
                                        tank_pressure_bar=values.tank_pressure_bar, )

        return clean_packet

    def reset(self) -> None:
        """
        Clear previous sample memory when starting a new simulated dive.

        This should be called before starting a new simulated dive or when a packet stream is restarted. Without reset,
        the first packet of a new run could be incorrectly compared with the last packet of the previous run.
        """

        logger.info("Signal preprocessor reset")
        self._previous = None

    def _calculate_ascent_rate(self, packet: RawWearablePacket) -> float | None:
        """
        Calculate ascent/descent rate in meters per minute.

        The rate is calculated by comparing the previous depth with the current depth over the elapsed time difference.

        Positive value means ascending.
        Negative value means descending.

        Returns None for the first packet, because no previous sample exists.
        """

        if self._previous is None:
            return None

        dt_s = packet.elapsed_time_s - self._previous.elapsed_time_s

        if dt_s <= 0:
            raise ValueError("Packet elapsed_time_s must increase between samples. "
                             f"previous={self._previous.elapsed_time_s}, current={packet.elapsed_time_s}")

        previous_depth_m = self._previous.depth_m
        current_depth_m = packet.values.depth_m

        return (previous_depth_m - current_depth_m) / dt_s * 60.0

    def _calculate_gas_rate(self, packet: RawWearablePacket) -> float | None:
        """
        Calculate gas consumption rate in bar per minute.

        The rate is calculated by comparing the previous tank pressure with the
        current tank pressure over the elapsed time difference.

        Positive value means gas is being consumed.
        Returns None if this is the first packet or if tank pressure is unavailable
        in either the previous or current sample.
        """

        if self._previous is None:
            return None

        previous_pressure = self._previous.tank_pressure_bar
        current_pressure = packet.values.tank_pressure_bar

        if previous_pressure is None or current_pressure is None:
            return None

        dt_s = packet.elapsed_time_s - self._previous.elapsed_time_s

        if dt_s <= 0:
            raise ValueError("Packet elapsed_time_s must increase between samples. "
                             f"previous={self._previous.elapsed_time_s}, current={packet.elapsed_time_s}")

        return (previous_pressure - current_pressure) / dt_s * 60.0
