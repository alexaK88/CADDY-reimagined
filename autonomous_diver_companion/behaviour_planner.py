"""
Robot high-level behaviour planning.

The planner converts the current DiverTrack into a RobotActionIntent. It does
not perform path planning, motor control, or physical navigation.

The planner first reacts to specific wearable alarm codes when available. If no
specific alarm rule matches, it falls back to the packet-level SafetyState.
"""

from __future__ import annotations

from autonomous_diver_companion.schemas import DiverTrack, RobotActionIntent, RobotMode
from shared.shared_protocol import SafetyState


class RobotBehaviorPlanner:
    """
    Selects the robot's high-level behaviour from the latest diver track.
    """

    def plan(self, track: DiverTrack) -> RobotActionIntent:
        """
        Choose the next robot action from packet freshness, alarm codes, and
        diver safety state.

        Decision order:
        - no packet -> IDLE
        - stale packet -> SEARCH_LAST_KNOWN
        - specific alarm code rules
        - fallback SafetyState rules
        """

        if track.latest_packet is None:
            return RobotActionIntent(mode=RobotMode.IDLE, reason="No diver packet has been received yet.", priority=0,
                notify_surface=False, )

        if track.is_stale:
            return RobotActionIntent(mode=RobotMode.SEARCH_LAST_KNOWN, reason="Latest diver packet is stale.",
                priority=90, notify_surface=True, )

        alarm_codes = self._get_alarm_codes(track)

        alarm_action = self._plan_from_alarm_codes(alarm_codes)
        if alarm_action is not None:
            return alarm_action

        return self._plan_from_safety_state(track)

    def _get_alarm_codes(self, track: DiverTrack) -> set[str]:
        """
        Return all alarm codes from the latest diver packet.
        """

        if track.latest_packet is None:
            return set()

        return {alarm.code for alarm in track.latest_packet.alarms}

    def _plan_from_alarm_codes(self, alarm_codes: set[str], ) -> RobotActionIntent | None:
        """
        Choose a robot action from specific wearable alarm codes.

        Higher-priority conditions are checked first so that, if multiple
        alarms are present, the robot chooses the safest response.
        """

        if "DIVER_EMERGENCY_BUTTON" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.EMERGENCY_SUPPORT, reason="Diver pressed the emergency button.",
                priority=100, notify_surface=True, )

        if "NO_MOTION_DETECTED" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.EMERGENCY_SUPPORT, reason="No diver motion detected underwater.",
                priority=95, notify_surface=True, )

        if "FAST_ASCENT" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.EMERGENCY_SUPPORT, reason="Diver is ascending too fast.",
                priority=90, notify_surface=True, )

        if "CRITICAL_GAS" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.EMERGENCY_SUPPORT, reason="Diver tank pressure is critically low.",
                priority=90, notify_surface=True, )

        if "GAS_DROPPING_FAST" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.EMERGENCY_SUPPORT,
                reason="Diver tank pressure is dropping unusually fast.", priority=90, notify_surface=True, )

        if "LINK_LOST" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.SEARCH_LAST_KNOWN,
                reason="Communication link with diver wearable is lost.", priority=90, notify_surface=True, )

        if "LOW_GAS" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.GUIDE_DIVER, reason="Diver tank pressure is low.", priority=70,
                notify_surface=False, )

        if "WEAK_LINK" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.APPROACH_DIVER,
                reason="Communication link with diver wearable is weak.", priority=50, notify_surface=False, )

        if "DIVER_STILL_UNDERWATER" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.APPROACH_DIVER, reason="Diver appears still underwater.",
                priority=50, notify_surface=False, )

        if "WEARABLE_BATTERY_CRITICAL" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.EMERGENCY_SUPPORT, reason="Wearable battery is critically low.",
                priority=80, notify_surface=True, )

        if "WEARABLE_BATTERY_LOW" in alarm_codes:
            return RobotActionIntent(mode=RobotMode.APPROACH_DIVER, reason="Wearable battery is low.", priority=40,
                notify_surface=False, )

        return None

    def _plan_from_safety_state(self, track: DiverTrack) -> RobotActionIntent:
        """
        Fallback behaviour when no specific alarm-code rule matches.
        """

        if track.latest_packet is None:
            return RobotActionIntent(mode=RobotMode.IDLE, reason="No diver packet has been received yet.", priority=0,
                notify_surface=False, )

        safety_state = track.latest_packet.safety_state

        if safety_state == SafetyState.EMERGENCY:
            return RobotActionIntent(mode=RobotMode.EMERGENCY_SUPPORT, reason="Diver safety state is EMERGENCY.",
                priority=100, notify_surface=True, )

        if safety_state == SafetyState.CRITICAL:
            return RobotActionIntent(mode=RobotMode.EMERGENCY_SUPPORT, reason="Diver safety state is CRITICAL.",
                priority=90, notify_surface=True, )

        if safety_state == SafetyState.WARNING:
            return RobotActionIntent(mode=RobotMode.APPROACH_DIVER, reason="Diver safety state is WARNING.",
                priority=50, notify_surface=False, )

        return RobotActionIntent(mode=RobotMode.MONITORING, reason="Diver safety state is OK.", priority=10,
            notify_surface=False, )
