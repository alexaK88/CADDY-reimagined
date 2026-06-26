from autonomous_diver_companion.schemas import RobotMode
from autonomous_diver_companion.robot_system import RobotSystem
from autonomous_diver_companion.tracker import RobotTrackerConfig
from shared.shared_protocol import SafetyState
from shared.tests.helpers import make_safety_packet


def test_robot_system_returns_idle_when_no_packet_has_arrived():
    robot = RobotSystem()

    decision = robot.update(
        packet=None,
        robot_elapsed_time_s=0.0,
    )

    assert decision.track.latest_packet is None
    assert decision.action.mode == RobotMode.IDLE


def test_robot_system_monitors_ok_packet():
    robot = RobotSystem()

    packet = make_safety_packet(
        safety_state=SafetyState.OK,
        elapsed_time_s=10.0,
        sample_index=2,
    )

    decision = robot.update(
        packet=packet,
        robot_elapsed_time_s=10.0,
    )

    assert decision.track.latest_packet == packet
    assert decision.track.is_stale is False
    assert decision.action.mode == RobotMode.MONITORING


def test_robot_system_approaches_warning_packet():
    robot = RobotSystem()

    packet = make_safety_packet(
        safety_state=SafetyState.WARNING,
        alarm_code="LOW_GAS",
        elapsed_time_s=10.0,
        sample_index=2,
    )

    decision = robot.update(
        packet=packet,
        robot_elapsed_time_s=10.0,
    )

    assert decision.track.latest_packet == packet
    assert decision.action.mode == RobotMode.APPROACH_DIVER


def test_robot_system_enters_emergency_support_for_critical_packet():
    robot = RobotSystem()

    packet = make_safety_packet(
        safety_state=SafetyState.CRITICAL,
        alarm_code="FAST_ASCENT",
        elapsed_time_s=10.0,
        sample_index=2,
    )

    decision = robot.update(
        packet=packet,
        robot_elapsed_time_s=10.0,
    )

    assert decision.track.latest_packet == packet
    assert decision.action.mode == RobotMode.EMERGENCY_SUPPORT
    assert decision.action.notify_surface is True


def test_robot_system_enters_emergency_support_for_emergency_packet():
    robot = RobotSystem()

    packet = make_safety_packet(
        safety_state=SafetyState.EMERGENCY,
        alarm_code="DIVER_EMERGENCY_BUTTON",
        elapsed_time_s=10.0,
        sample_index=2,
    )

    decision = robot.update(
        packet=packet,
        robot_elapsed_time_s=10.0,
    )

    assert decision.track.latest_packet == packet
    assert decision.action.mode == RobotMode.EMERGENCY_SUPPORT
    assert decision.action.notify_surface is True


def test_robot_system_searches_last_known_when_packet_becomes_stale():
    robot = RobotSystem(
        tracker_config=RobotTrackerConfig(stale_packet_after_s=10.0)
    )

    packet = make_safety_packet(
        safety_state=SafetyState.OK,
        elapsed_time_s=10.0,
        sample_index=2,
    )

    robot.update(
        packet=packet,
        robot_elapsed_time_s=10.0,
    )

    decision = robot.update(
        packet=None,
        robot_elapsed_time_s=21.0,
    )

    assert decision.track.latest_packet == packet
    assert decision.track.is_stale is True
    assert decision.action.mode == RobotMode.SEARCH_LAST_KNOWN
    assert decision.action.notify_surface is True