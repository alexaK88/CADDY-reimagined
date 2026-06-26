"""
Alarm evaluation for the diver wearable simulator.

This module contains the local wearable-side alarm engine. It receives an
interpreted DiverState and evaluates whether any safety-relevant conditions
are present, such as fast ascent, low gas, weak communication link, low
wearable battery, lack of motion, or an explicit emergency button press.

The alarm engine does not work with raw sensor values directly. It operates
after preprocessing and state estimation, and produces a DiverSafetyPacket
containing the overall safety state and a list of detected AlarmEvent objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from diver_wearable_unit_simulator.utils.logger import get_logger
from shared.shared_protocol import (
    AlarmEvent,
    AlarmSeverity,
    DiverSafetyPacket,
    DiverState,
    GasState,
    LinkState,
    MotionState,
    SafetyState,
)


logger = get_logger(__name__)


@dataclass(frozen=True)
class AlarmEngineConfig:
    """
    Thresholds used by the alarm engine to decide when a DiveState becomes safety-relevant.
    These values are intentionally kept separate from the alarm logic so that alarm sensitivity can
    be tuned without changing the implementation.
    """
    max_safe_ascent_rate_m_min: float = 9.0

    # Battery life thresholds
    low_battery_pct: float = 20.0
    critical_battery_pct: float = 10.0

    no_motion_min_depth_m: float = 1.0


class AlarmEngine:
    """
    Evaluates DiverState and produces a DiverSafetyPacket.

    The alarm engine receives a DiverState from the state estimator and checks it against a set of
    safety rules/ Each rule may produce zero or one AlarmEvent objects. The final output is a
    DiverSafetyPacket which contains the original diver state, all detected alarms, and the highest
    resulting SafetyState.

    This class is intentionally rules-based for now. It does not estimate diver state, simulate
    sensor data, or control the robot.

    Asks: Given DiverState, should we raise any alarm?
    """

    def __init__(self, config: AlarmEngineConfig | None = None):
        # loading incoming config or default one
        self.config = config or AlarmEngineConfig()

    def evaluate(self, state: DiverState) -> DiverSafetyPacket:
        """
        Evaluate one interpreted DiverState and produce a DiverSafetyPacket.

        The method runs all alarm checks, combines the generated AlarmEvent objects, calculates the
        overall SafetyState, and returns a DiverSafetyPacket.
        """
        alarms: list[AlarmEvent] = []

        alarms.extend(self._check_emergency_button(state))
        alarms.extend(self._check_fast_ascent(state))
        alarms.extend(self._check_gas(state))
        alarms.extend(self._check_link(state))
        alarms.extend(self._check_battery(state))
        alarms.extend(self._check_motion(state))

        safety_state = self._calculate_safety_state(alarms)

        return DiverSafetyPacket(diver_id=state.diver_id, sample_index=state.sample_index,
                                 elapsed_time_s=state.elapsed_time_s,
                                 produced_at_utc=state.produced_at_utc, safety_state=safety_state,
                                 alarms=alarms, diver_state=state)

    def _check_emergency_button(self, state: DiverState) -> list[AlarmEvent]:
        """
        Check if diver has pressed emergency button and send AlarmEvent state, or empty list if not.
        """
        if state.emergency_button_pressed:
            return [AlarmEvent(code="DIVER_EMERGENCY_BUTTON", severity=AlarmSeverity.EMERGENCY,
                               message="Diver pressed the emergency button.", recommended_action=(
                    "Robot should enter emergency support mode and notify "
                    "surface supervisor immediately."))]

        return []

    def _check_fast_ascent(self, state: DiverState) -> list[AlarmEvent]:
        """
        Return a critical alarm if the diver is ascending faster than the configured safe scent rate
        """
        if state.ascent_rate_m_min is None:
            return []

        if state.ascent_rate_m_min > self.config.max_safe_ascent_rate_m_min:
            return [AlarmEvent(code="FAST_ASCENT", severity=AlarmSeverity.CRITICAL,
                               message=(f"Diver is ascending too fast: "
                                        f"{state.ascent_rate_m_min:.1f} m/min"),
                               recommended_action="Slow ascent and notify robot/surface supervisor.")]

        return []

    def _check_gas(self, state: DiverState) -> list[AlarmEvent]:
        """
        Return gas-related alarms based on the interpreted gas state.
        Possible outputs include low gas, critical gas, or unusually fast gas pressure drop.
        """
        if state.gas_state == GasState.CRITICAL:
            return [AlarmEvent(code="CRITICAL_GAS", severity=AlarmSeverity.CRITICAL,
                               message="Tank pressure is critically low.",
                               recommended_action="Abort dive and guide diver to ascent/exit point.")]

        if state.gas_state == GasState.LOW:
            return [AlarmEvent(code="LOW_GAS", severity=AlarmSeverity.WARNING,
                               message="Tank pressure is low.",
                               recommended_action="Recommend return-to-buoy or ascent planning.")]

        if state.gas_state == GasState.DROPPING_FAST:
            return [AlarmEvent(code="GAS_DROPPING_FAST", severity=AlarmSeverity.CRITICAL,
                               message="Tank pressure is dropping unusually fast.",
                               recommended_action="Check for leak or abnormal gas consumption.")]

        return []

    def _check_link(self, state: DiverState) -> list[AlarmEvent]:
        """
        Return communication-link alarms based on the interpreted link state.
        """
        if state.link_state == LinkState.LINK_LOST:
            return [AlarmEvent(code="LINK_LOST", severity=AlarmSeverity.CRITICAL,
                               message="Communication link with diver wearable is lost.",
                               recommended_action="Robot should use last known state and prepare search behavior.")]

        if state.link_state == LinkState.LINK_WEAK:
            return [AlarmEvent(code="WEAK_LINK", severity=AlarmSeverity.WARNING,
                               message="Communication link with diver wearable is weak.",
                               recommended_action="Robot should move closer or improve communication geometry.")]

        return []

    def _check_battery(self, state: DiverState) -> list[AlarmEvent]:
        """
        Return battery alarms (wearable unit) if the level is low or critical.
        """
        if state.battery_pct is None:
            return []

        if state.battery_pct <= self.config.critical_battery_pct:
            return [AlarmEvent(code="WEARABLE_BATTERY_CRITICAL", severity=AlarmSeverity.CRITICAL,
                               message="Wearable battery is critically low.",
                               recommended_action="Abort mission or switch to backup tracking method.")]

        if state.battery_pct <= self.config.low_battery_pct:
            return [AlarmEvent(code="WEARABLE_BATTERY_LOW", severity=AlarmSeverity.WARNING,
                               message="Wearable battery is low.",
                               recommended_action="Monitor battery and prepare to end dive.")]

        return []

    def _check_motion(self, state: DiverState) -> list[AlarmEvent]:
        """
        Return motion-related alarms when the diver appears still underwater or motionless.
        """
        if (state.motion_state == MotionState.STILL and state.depth_m > self.config.no_motion_min_depth_m):
            return [AlarmEvent(code="DIVER_STILL_UNDERWATER", severity=AlarmSeverity.WARNING,
                               message="Diver appears still underwater.",
                               recommended_action="Robot should observe more closely and notify supervisor if prolonged.")]

        if (state.motion_state == MotionState.NO_MOTION and state.depth_m > self.config.no_motion_min_depth_m):
            return [AlarmEvent(code="NO_MOTION_DETECTED", severity=AlarmSeverity.CRITICAL,
                               message="No diver motion detected underwater.",
                               recommended_action="Robot should move closer carefully and notify supervisor.")]

        return []

    def _calculate_safety_state(self, alarms: list[AlarmEvent]) -> SafetyState:
        """
        Calculate the overall safety state from all detected alarms.
        The highest severity alarm determines the final SafetyState.
        Priority: EMERGENCY > CRITICAL > WARNING > OK
        """
        if any(alarm.severity == AlarmSeverity.EMERGENCY for alarm in alarms):
            return SafetyState.EMERGENCY

        if any(alarm.severity == AlarmSeverity.CRITICAL for alarm in alarms):
            return SafetyState.CRITICAL

        if any(alarm.severity == AlarmSeverity.WARNING for alarm in alarms):
            return SafetyState.WARNING

        return SafetyState.OK
