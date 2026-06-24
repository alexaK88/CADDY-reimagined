"""
Diver state estimator for wearable simulator.

This module converts preprocessed numerical signals into interpreted diver states. It receives CleanSensorPacket objects
from the preprocessing layer and classifies the diver's local condition, including dive phase, motion state, gas state,
and communication link state.

The estimator does not generate alarms and does not decide the final safety state. It only describes what the diver
appears to be doing. The AlarmEngine uses this interpreted DiverState to decide whether any condition is safety-relevant.
"""

from __future__ import annotations

from dataclasses import dataclass

from schemas import (CleanSensorPacket, DivePhase, DiverState, GasState, LinkState, MotionState, )


@dataclass(frozen=True)
class StateEstimatorConfig:
    """
    Thresholds used to convert clean sensor values into diver states.

    These thresholds control how numerical values such as depth, ascent rate, motion intensity, tank pressure,
    gas pressure drop rate, and link quality are converted into discrete state labels.
    """

    surface_depth_m: float = 0.5

    safety_stop_min_depth_m: float = 3.0
    safety_stop_max_depth_m: float = 6.0
    stable_vertical_rate_m_min: float = 1.0

    still_motion_threshold: float = 0.08
    fast_motion_threshold: float = 0.75

    low_gas_bar: float = 70.0
    critical_gas_bar: float = 50.0
    fast_gas_drop_bar_min: float = 20.0

    weak_link_quality: float = 0.4
    lost_link_quality: float = 0.1


class DiverStateEstimator:
    """
    Converts CleanSensorPacket into DiverState.

    The estimator receives CleanSensorPacket objects from the preprocessing layer and classifies the diver's local
    condition into discrete state categories:
    - dive phase
    - motion state
    - gas state
    - link state

    It does not raise alarms yet. It only describes the current diver state.
    """

    def __init__(self, config: StateEstimatorConfig | None = None):
        """
        Initialise the estimator with optional classification thresholds. If no config is provided, default thresholds
        are used.
        """

        self.config = config or StateEstimatorConfig()

    def estimate(self, packet: CleanSensorPacket) -> DiverState:
        """
        Estimate diver state from one clean sensor packet.

        The method classifies the packet into diver phase, motion state, gas state, and link state, while also carrying
        forward numerical values and diver interaction flags.

        :param packet: preprocessed sensor packet produced by preprocessor

        :return DiverState containing both selected numerical values and interpreted state labels.
        """

        dive_phase = self._estimate_dive_phase(packet)
        motion_state = self._estimate_motion_state(packet)
        gas_state = self._estimate_gas_state(packet)
        link_state = self._estimate_link_state(packet)

        return DiverState(diver_id=packet.diver_id, sample_index=packet.sample_index,
                          elapsed_time_s=packet.elapsed_time_s, produced_at_utc=packet.produced_at_utc,

                          depth_m=packet.depth_m, tank_pressure_bar=packet.tank_pressure_bar,
                          battery_pct=packet.battery_pct,

                          ascent_rate_m_min=packet.ascent_rate_m_min, gas_rate_bar_min=packet.gas_rate_bar_min,

                          emergency_button_pressed=packet.emergency_button_pressed,
                          ack_button_pressed=packet.ack_button_pressed,

                          dive_phase=dive_phase, motion_state=motion_state, gas_state=gas_state, link_state=link_state,

                          heading_deg=None, link_quality=None)

    def _estimate_dive_phase(self, packet: CleanSensorPacket) -> DivePhase:
        """
        Estimate whether the diver is at surface, descending, at depth, ascending, or doing a safety stop.

        The phase is estimated from current depth and ascent/descent rate.

        Classification order:
        - near the surface -> AT_SURFACE
        - missing rate -> UNKNOWN
        - stable between safety-stop depths -> SAFETY_STOP
        - positive vertical rate above threshold -> ASCENDING
        - negative vertical rate below threshold -> DESCENDING
        - otherwise -> AT_DEPTH

        A positive ascent_rate_m_min means the diver is moving upward.
        A negative ascent_rate_m_min means the diver is moving downward.
        """

        if packet.depth_m <= self.config.surface_depth_m:
            return DivePhase.AT_SURFACE

        if packet.ascent_rate_m_min is None:
            return DivePhase.UNKNOWN

        if (self.config.safety_stop_min_depth_m <= packet.depth_m <= self.config.safety_stop_max_depth_m and abs(
                packet.ascent_rate_m_min) <= self.config.stable_vertical_rate_m_min):
            return DivePhase.SAFETY_STOP

        if packet.ascent_rate_m_min > self.config.stable_vertical_rate_m_min:
            return DivePhase.ASCENDING

        if packet.ascent_rate_m_min < -self.config.stable_vertical_rate_m_min:
            return DivePhase.DESCENDING

        return DivePhase.AT_DEPTH

    def _estimate_motion_state(self, packet: CleanSensorPacket) -> MotionState:
        """
        Estimate diver movement state from normalised motion intensity.

        motion_intensity is expected to be between 0 and 1:
        - missing value -> UNKNOWN
        - value below still threshold -> STILL
        - value above fast threshold -> FAST_SWIMMING
        - otherwise -> SWIMMING
        """

        #TODO: add time-based no-motionn detection so the estimator can distinguish STILL from prolonged NO_MOTION.

        if packet.motion_intensity is None:
            return MotionState.UNKNOWN

        if packet.motion_intensity <= self.config.still_motion_threshold:
            return MotionState.STILL

        if packet.motion_intensity >= self.config.fast_motion_threshold:
            return MotionState.FAST_SWIMMING

        return MotionState.SWIMMING

    def _estimate_gas_state(self, packet: CleanSensorPacket) -> GasState:
        """
        Estimate gas state from tank pressure and gas consumption rate.

        Classification order:
            - missing tank pressure -> UNKNOWN
            - pressure dropping faster than threshold -> DROPPING_FAST
            - tank pressure below critical threshold -> CRITICAL
            - tank pressure below low threshold -> LOW
            - otherwise -> NORMAL
        """

        if packet.tank_pressure_bar is None:
            return GasState.UNKNOWN

        if packet.tank_pressure_bar <= self.config.critical_gas_bar:
            return GasState.CRITICAL

        if packet.gas_rate_bar_min is not None and packet.gas_rate_bar_min >= self.config.fast_gas_drop_bar_min:
            return GasState.DROPPING_FAST

        if packet.tank_pressure_bar <= self.config.low_gas_bar:
            return GasState.LOW

        return GasState.NORMAL

    def _estimate_link_state(self, packet: CleanSensorPacket) -> LinkState:
        """
        Estimate communication link state.

        link_quality is expected to be between 0 and 1:
        - missing value -> UNKNOWN
        - value below lost threshold -> LINK_LOST
        - value below weak threshold -> LINK_WEAK
        - otherwise -> LINK_OK
        """

        if packet.link_quality is None:
            return LinkState.UNKNOWN

        if packet.link_quality <= self.config.lost_link_quality:
            return LinkState.LINK_LOST

        if packet.link_quality <= self.config.weak_link_quality:
            return LinkState.LINK_WEAK

        return LinkState.LINK_OK
