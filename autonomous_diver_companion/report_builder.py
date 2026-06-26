"""
Robot status report builder.

This module converts internal RobotDecision objects into RobotStatusPacket
objects that can be sent to the surface gateway.
"""

from __future__ import annotations

from datetime import datetime, timezone

from autonomous_diver_companion.schemas import RobotDecision
from shared.robot_protocol import RobotStatusPacket


class RobotReportBuilder:
    """
    Builds surface-facing robot status reports from internal robot decisions.
    """

    def __init__(self, robot_id: str = "robot_01"):
        """
        Initialize the report builder for one robot.
        """

        if not robot_id:
            raise ValueError("robot_id must not be empty")

        self.robot_id = robot_id

    def build(self, decision: RobotDecision, robot_elapsed_time_s: float, ) -> RobotStatusPacket:
        """
        Convert one RobotDecision into a RobotStatusPacket.
        """

        if robot_elapsed_time_s < 0:
            raise ValueError("robot_elapsed_time_s must be non-negative")

        latest_packet = decision.track.latest_packet

        diver_id = None
        diver_safety_state = None
        active_alarm_codes: list[str] = []

        if latest_packet is not None:
            diver_id = latest_packet.diver_id
            diver_safety_state = latest_packet.safety_state
            active_alarm_codes = [alarm.code for alarm in latest_packet.alarms]

        return RobotStatusPacket(robot_id=self.robot_id, produced_at_utc=datetime.now(timezone.utc),
            robot_elapsed_time_s=robot_elapsed_time_s,

            mode=decision.action.mode, reason=decision.action.reason, priority=decision.action.priority,
            notify_surface=decision.action.notify_surface,

            diver_id=diver_id, diver_safety_state=diver_safety_state, active_alarm_codes=active_alarm_codes,

            latest_diver_packet_age_s=decision.track.packet_age_s, is_diver_data_stale=decision.track.is_stale, )
