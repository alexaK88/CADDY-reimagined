from datetime import datetime, timezone

from shared.shared_protocol import SafetyState
from shared.robot_protocol import RobotMode, RobotStatusPacket
from surface_gateway_simulator.gateway import SurfaceGatewaySimulator
from surface_gateway_simulator.schemas import SurfaceMissionState


def make_robot_report(mode: RobotMode = RobotMode.MONITORING,
        reason: str = "Test robot report.",
        priority: int = 10,
        notify_surface: bool = False,
        diver_id: str | None = "diver_01",
        diver_safety_state: SafetyState | None = SafetyState.OK,
        active_alarm_codes: list[str] | None = None,
        latest_diver_packet_age_s: float | None = 0.0,
        is_diver_data_stale: bool = False, ) -> RobotStatusPacket:
    """
    Create a minimal valid RobotStatusPacket for surface gateway tests.
    """

    return RobotStatusPacket(robot_id="robot_01", produced_at_utc=datetime.now(timezone.utc), robot_elapsed_time_s=10.0,
        mode=mode, reason=reason, priority=priority, notify_surface=notify_surface, diver_id=diver_id,
        diver_safety_state=diver_safety_state, active_alarm_codes=active_alarm_codes or [],
        latest_diver_packet_age_s=latest_diver_packet_age_s, is_diver_data_stale=is_diver_data_stale, )


def test_surface_gateway_returns_no_robot_report_initially():
    gateway = SurfaceGatewaySimulator()

    state = gateway.update(robot_report=None)

    assert state.latest_robot_report is None
    assert state.reports_received == 0
    assert state.mission_state == SurfaceMissionState.NO_ROBOT_REPORT
    assert len(state.alerts) == 1
    assert state.alerts[0].code == "NO_ROBOT_REPORT"


def test_surface_gateway_reports_awaiting_diver_data_when_robot_has_no_diver_packet():
    gateway = SurfaceGatewaySimulator()

    report = make_robot_report(mode=RobotMode.IDLE, reason="No diver packet has been received yet.", priority=0,
        notify_surface=False, diver_id=None, diver_safety_state=None, active_alarm_codes=[],
        latest_diver_packet_age_s=None, is_diver_data_stale=True, )

    state = gateway.update(robot_report=report)

    assert state.latest_robot_report == report
    assert state.reports_received == 1
    assert state.mission_state == SurfaceMissionState.AWAITING_DIVER_DATA


def test_surface_gateway_reports_normal_for_ok_monitoring_report():
    gateway = SurfaceGatewaySimulator()

    report = make_robot_report(mode=RobotMode.MONITORING, diver_safety_state=SafetyState.OK,
        is_diver_data_stale=False, )

    state = gateway.update(robot_report=report)

    assert state.latest_robot_report == report
    assert state.reports_received == 1
    assert state.mission_state == SurfaceMissionState.NORMAL
    assert state.alerts == []


def test_surface_gateway_reports_diver_data_stale():
    gateway = SurfaceGatewaySimulator()

    report = make_robot_report(mode=RobotMode.SEARCH_LAST_KNOWN, reason="Latest diver packet is stale.", priority=90,
        notify_surface=True, diver_safety_state=SafetyState.OK, latest_diver_packet_age_s=15.0,
        is_diver_data_stale=True, )

    state = gateway.update(robot_report=report)

    assert state.mission_state == SurfaceMissionState.DIVER_DATA_STALE
    assert any(alert.code == "DIVER_DATA_STALE" for alert in state.alerts)
    assert any(alert.code == "SEARCH_LAST_KNOWN" for alert in state.alerts)


def test_surface_gateway_reports_emergency_for_emergency_safety_state():
    gateway = SurfaceGatewaySimulator()

    report = make_robot_report(mode=RobotMode.EMERGENCY_SUPPORT, reason="Diver pressed the emergency button.",
        priority=100, notify_surface=True, diver_safety_state=SafetyState.EMERGENCY,
        active_alarm_codes=["DIVER_EMERGENCY_BUTTON"], is_diver_data_stale=False, )

    state = gateway.update(robot_report=report)

    assert state.mission_state == SurfaceMissionState.EMERGENCY
    assert any(alert.code == "DIVER_EMERGENCY" for alert in state.alerts)
    assert any(alert.code == "DIVER_ALARM_DIVER_EMERGENCY_BUTTON" for alert in state.alerts)


def test_surface_gateway_reports_emergency_for_critical_safety_state():
    gateway = SurfaceGatewaySimulator()

    report = make_robot_report(mode=RobotMode.EMERGENCY_SUPPORT, reason="Diver is ascending too fast.", priority=90,
        notify_surface=True, diver_safety_state=SafetyState.CRITICAL, active_alarm_codes=["FAST_ASCENT"],
        is_diver_data_stale=False, )

    state = gateway.update(robot_report=report)

    assert state.mission_state == SurfaceMissionState.EMERGENCY
    assert any(alert.code == "DIVER_CRITICAL" for alert in state.alerts)
    assert any(alert.code == "DIVER_ALARM_FAST_ASCENT" for alert in state.alerts)


def test_surface_gateway_reports_attention_required_when_notify_surface_is_true():
    gateway = SurfaceGatewaySimulator()

    report = make_robot_report(mode=RobotMode.MONITORING, reason="Robot requests surface attention.", priority=60,
        notify_surface=True, diver_safety_state=SafetyState.OK, is_diver_data_stale=False, )

    state = gateway.update(robot_report=report)

    assert state.mission_state == SurfaceMissionState.ATTENTION_REQUIRED


def test_surface_gateway_reports_attention_required_for_guide_diver_mode():
    gateway = SurfaceGatewaySimulator()

    report = make_robot_report(mode=RobotMode.GUIDE_DIVER, reason="Diver tank pressure is low.", priority=70,
        notify_surface=False, diver_safety_state=SafetyState.WARNING, active_alarm_codes=["LOW_GAS"],
        is_diver_data_stale=False, )

    state = gateway.update(robot_report=report)

    assert state.mission_state == SurfaceMissionState.ATTENTION_REQUIRED
    assert any(alert.code == "DIVER_ALARM_LOW_GAS" for alert in state.alerts)


def test_surface_gateway_keeps_latest_report_when_no_new_report_arrives():
    gateway = SurfaceGatewaySimulator()

    report = make_robot_report(mode=RobotMode.MONITORING, diver_safety_state=SafetyState.OK, )

    first_state = gateway.update(robot_report=report)
    second_state = gateway.update(robot_report=None)

    assert first_state.latest_robot_report == report
    assert second_state.latest_robot_report == report
    assert second_state.reports_received == 1
    assert second_state.mission_state == SurfaceMissionState.NORMAL


def test_surface_gateway_reset_clears_memory():
    gateway = SurfaceGatewaySimulator()

    report = make_robot_report(mode=RobotMode.MONITORING, diver_safety_state=SafetyState.OK, )

    gateway.update(robot_report=report)
    gateway.reset()

    state = gateway.update(robot_report=None)

    assert state.latest_robot_report is None
    assert state.reports_received == 0
    assert state.mission_state == SurfaceMissionState.NO_ROBOT_REPORT
