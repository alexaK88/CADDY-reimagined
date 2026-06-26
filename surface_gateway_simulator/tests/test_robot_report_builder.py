from autonomous_diver_companion.report_builder import RobotReportBuilder
from autonomous_diver_companion.schemas import DiverTrack, RobotActionIntent, RobotDecision
from shared.shared_protocol import SafetyState
from shared.robot_protocol import RobotMode

from shared.tests.helpers import make_safety_packet


def test_report_builder_creates_report_without_diver_packet():
    builder = RobotReportBuilder(robot_id="robot_01")

    decision = RobotDecision(
        track=DiverTrack(latest_packet=None, packets_received=0, last_packet_elapsed_time_s=None, packet_age_s=None,
            is_stale=True, ),
        action=RobotActionIntent(mode=RobotMode.IDLE, reason="No diver packet has been received yet.", priority=0,
            notify_surface=False, ), )

    report = builder.build(decision=decision, robot_elapsed_time_s=0.0, )

    assert report.robot_id == "robot_01"
    assert report.robot_elapsed_time_s == 0.0
    assert report.mode == RobotMode.IDLE
    assert report.reason == "No diver packet has been received yet."
    assert report.priority == 0
    assert report.notify_surface is False

    assert report.diver_id is None
    assert report.diver_safety_state is None
    assert report.active_alarm_codes == []
    assert report.latest_diver_packet_age_s is None
    assert report.is_diver_data_stale is True


def test_report_builder_creates_report_with_normal_diver_packet():
    builder = RobotReportBuilder(robot_id="robot_01")

    packet = make_safety_packet(safety_state=SafetyState.OK, elapsed_time_s=10.0, sample_index=2, )

    decision = RobotDecision(
        track=DiverTrack(latest_packet=packet, packets_received=1, last_packet_elapsed_time_s=10.0, packet_age_s=0.0,
            is_stale=False, ),
        action=RobotActionIntent(mode=RobotMode.MONITORING, reason="Diver safety state is OK.", priority=10,
            notify_surface=False, ), )

    report = builder.build(decision=decision, robot_elapsed_time_s=10.0, )

    assert report.robot_id == "robot_01"
    assert report.robot_elapsed_time_s == 10.0
    assert report.mode == RobotMode.MONITORING
    assert report.reason == "Diver safety state is OK."
    assert report.priority == 10
    assert report.notify_surface is False

    assert report.diver_id == "diver_01"
    assert report.diver_safety_state == SafetyState.OK
    assert report.active_alarm_codes == []
    assert report.latest_diver_packet_age_s == 0.0
    assert report.is_diver_data_stale is False


def test_report_builder_includes_alarm_codes():
    builder = RobotReportBuilder(robot_id="robot_01")

    packet = make_safety_packet(safety_state=SafetyState.CRITICAL, alarm_code="FAST_ASCENT", elapsed_time_s=20.0,
        sample_index=4, )

    decision = RobotDecision(
        track=DiverTrack(latest_packet=packet, packets_received=1, last_packet_elapsed_time_s=20.0, packet_age_s=0.0,
            is_stale=False, ),
        action=RobotActionIntent(mode=RobotMode.EMERGENCY_SUPPORT, reason="Diver is ascending too fast.", priority=90,
            notify_surface=True, ), )

    report = builder.build(decision=decision, robot_elapsed_time_s=20.0, )

    assert report.mode == RobotMode.EMERGENCY_SUPPORT
    assert report.diver_safety_state == SafetyState.CRITICAL
    assert report.active_alarm_codes == ["FAST_ASCENT"]
    assert report.notify_surface is True
    assert report.priority == 90


def test_report_builder_rejects_empty_robot_id():
    try:
        RobotReportBuilder(robot_id="")
    except ValueError as exc:
        assert "robot_id must not be empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty robot_id")


def test_report_builder_rejects_negative_robot_elapsed_time():
    builder = RobotReportBuilder(robot_id="robot_01")

    decision = RobotDecision(
        track=DiverTrack(latest_packet=None, packets_received=0, last_packet_elapsed_time_s=None, packet_age_s=None,
            is_stale=True, ),
        action=RobotActionIntent(mode=RobotMode.IDLE, reason="No diver packet has been received yet.", priority=0,
            notify_surface=False, ), )

    try:
        builder.build(decision=decision, robot_elapsed_time_s=-1.0, )
    except ValueError as exc:
        assert "robot_elapsed_time_s must be non-negative" in str(exc)
    else:
        raise AssertionError("Expected ValueError for negative robot_elapsed_time_s")
