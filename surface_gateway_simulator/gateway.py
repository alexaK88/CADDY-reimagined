"""
Surface gateway simulator.

The surface gateway receives robot status reports and converts them into
operator-facing mission state and alerts. It does not control the robot
directly and does not process raw diver sensor data.
"""

from __future__ import annotations

from surface_gateway_simulator.schemas import (SurfaceAlert, SurfaceGatewayState, SurfaceMissionState, )
from shared.robot_protocol import RobotMode, RobotStatusPacket
from shared.shared_protocol import SafetyState


class SurfaceGatewaySimulator:
    """
    Simulates the surface-side gateway or operator supervision layer.
    """

    def __init__(self):
        """
        Initialize an empty surface gateway.
        """

        self._latest_robot_report: RobotStatusPacket | None = None
        self._reports_received: int = 0

    def update(self, robot_report: RobotStatusPacket | None, ) -> SurfaceGatewayState:
        """
        Update the surface gateway with an optional robot status report.

        Args:
            robot_report: Latest robot report, or None if no report arrived.

        Returns:
            SurfaceGatewayState containing mission status and alerts.
        """

        if robot_report is not None:
            self._latest_robot_report = robot_report
            self._reports_received += 1

        if self._latest_robot_report is None:
            return SurfaceGatewayState(latest_robot_report=None, reports_received=self._reports_received,
                mission_state=SurfaceMissionState.NO_ROBOT_REPORT, alerts=[
                    SurfaceAlert(code="NO_ROBOT_REPORT", message="No robot status report has been received yet.",
                        priority=50, )], )

        mission_state = self._estimate_mission_state(self._latest_robot_report)
        alerts = self._build_alerts(self._latest_robot_report, mission_state)

        return SurfaceGatewayState(latest_robot_report=self._latest_robot_report,
            reports_received=self._reports_received, mission_state=mission_state, alerts=alerts, )

    def reset(self) -> None:
        """
        Clear surface gateway memory.
        """

        self._latest_robot_report = None
        self._reports_received = 0

    def _estimate_mission_state(self, report: RobotStatusPacket, ) -> SurfaceMissionState:
        """
        Estimate surface-side mission state from the latest robot report.
        """

        if report.diver_id is None:
            return SurfaceMissionState.AWAITING_DIVER_DATA

        if report.is_diver_data_stale:
            return SurfaceMissionState.DIVER_DATA_STALE

        if report.diver_safety_state == SafetyState.EMERGENCY:
            return SurfaceMissionState.EMERGENCY

        if report.diver_safety_state == SafetyState.CRITICAL:
            return SurfaceMissionState.EMERGENCY

        if report.notify_surface:
            return SurfaceMissionState.ATTENTION_REQUIRED

        if report.mode in {RobotMode.APPROACH_DIVER, RobotMode.GUIDE_DIVER, RobotMode.SEARCH_LAST_KNOWN, }:
            return SurfaceMissionState.ATTENTION_REQUIRED

        return SurfaceMissionState.NORMAL
    def _build_alerts(self, report: RobotStatusPacket, mission_state: SurfaceMissionState, ) -> list[SurfaceAlert]:
        """
        Build operator-facing alerts from the latest robot report.
        """

        alerts: list[SurfaceAlert] = []

        if mission_state == SurfaceMissionState.DIVER_DATA_STALE:
            alerts.append(
                SurfaceAlert(code="DIVER_DATA_STALE", message="Robot is working with stale diver data.", priority=90, ))

        if report.mode == RobotMode.SEARCH_LAST_KNOWN:
            alerts.append(
                SurfaceAlert(code="SEARCH_LAST_KNOWN", message="Robot is searching from the last known diver state.",
                    priority=90, ))

        if report.diver_safety_state == SafetyState.EMERGENCY:
            alerts.append(
                SurfaceAlert(code="DIVER_EMERGENCY", message="Diver emergency reported by robot.", priority=100, ))

        if report.diver_safety_state == SafetyState.CRITICAL:
            alerts.append(
                SurfaceAlert(code="DIVER_CRITICAL", message="Critical diver safety condition reported by robot.",
                    priority=95, ))

        for alarm_code in report.active_alarm_codes:
            alerts.append(SurfaceAlert(code=f"DIVER_ALARM_{alarm_code}", message=f"Active diver alarm: {alarm_code}",
                priority=report.priority, ))

        return alerts
