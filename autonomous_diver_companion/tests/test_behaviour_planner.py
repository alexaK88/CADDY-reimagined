from autonomous_diver_companion.behaviour_planner import RobotBehaviorPlanner
from autonomous_diver_companion.schemas import DiverTrack, RobotMode
from shared.shared_protocol import SafetyState
from shared.tests.helpers import make_safety_packet


def test_planner_returns_idle_when_no_packet_exists():
    planner = RobotBehaviorPlanner()

    track = DiverTrack(
        latest_packet=None,
        packets_received=0,
        last_packet_elapsed_time_s=None,
        packet_age_s=None,
        is_stale=True,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.IDLE
    assert action.priority == 0
    assert action.notify_surface is False


def test_planner_searches_when_packet_is_stale():
    planner = RobotBehaviorPlanner()

    packet = make_safety_packet(
        safety_state=SafetyState.OK,
        elapsed_time_s=10.0,
    )

    track = DiverTrack(
        latest_packet=packet,
        packets_received=1,
        last_packet_elapsed_time_s=10.0,
        packet_age_s=20.0,
        is_stale=True,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.SEARCH_LAST_KNOWN
    assert action.priority == 90
    assert action.notify_surface is True


def test_planner_monitors_when_safety_state_is_ok():
    planner = RobotBehaviorPlanner()

    packet = make_safety_packet(
        safety_state=SafetyState.OK,
        elapsed_time_s=10.0,
    )

    track = DiverTrack(
        latest_packet=packet,
        packets_received=1,
        last_packet_elapsed_time_s=10.0,
        packet_age_s=0.0,
        is_stale=False,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.MONITORING
    assert action.priority == 10
    assert action.notify_surface is False


def test_planner_approaches_when_safety_state_is_warning_without_specific_alarm():
    planner = RobotBehaviorPlanner()

    packet = make_safety_packet(
        safety_state=SafetyState.WARNING,
        alarm_code=None,
        elapsed_time_s=10.0,
    )

    track = DiverTrack(
        latest_packet=packet,
        packets_received=1,
        last_packet_elapsed_time_s=10.0,
        packet_age_s=0.0,
        is_stale=False,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.APPROACH_DIVER
    assert action.priority == 50
    assert action.notify_surface is False


def test_planner_enters_emergency_support_when_safety_state_is_critical():
    planner = RobotBehaviorPlanner()

    packet = make_safety_packet(
        safety_state=SafetyState.CRITICAL,
        alarm_code="FAST_ASCENT",
        elapsed_time_s=10.0,
    )

    track = DiverTrack(
        latest_packet=packet,
        packets_received=1,
        last_packet_elapsed_time_s=10.0,
        packet_age_s=0.0,
        is_stale=False,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.EMERGENCY_SUPPORT
    assert action.priority == 90
    assert action.notify_surface is True


def test_planner_enters_emergency_support_when_safety_state_is_emergency():
    planner = RobotBehaviorPlanner()

    packet = make_safety_packet(
        safety_state=SafetyState.EMERGENCY,
        alarm_code="DIVER_EMERGENCY_BUTTON",
        elapsed_time_s=10.0,
    )

    track = DiverTrack(
        latest_packet=packet,
        packets_received=1,
        last_packet_elapsed_time_s=10.0,
        packet_age_s=0.0,
        is_stale=False,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.EMERGENCY_SUPPORT
    assert action.priority == 100
    assert action.notify_surface is True

def test_planner_guides_diver_when_low_gas_alarm_is_present():
    planner = RobotBehaviorPlanner()

    packet = make_safety_packet(
        safety_state=SafetyState.WARNING,
        alarm_code="LOW_GAS",
        elapsed_time_s=10.0,
    )

    track = DiverTrack(
        latest_packet=packet,
        packets_received=1,
        last_packet_elapsed_time_s=10.0,
        packet_age_s=0.0,
        is_stale=False,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.GUIDE_DIVER
    assert action.priority == 70
    assert action.notify_surface is False


def test_planner_searches_when_link_lost_alarm_is_present():
    planner = RobotBehaviorPlanner()

    packet = make_safety_packet(
        safety_state=SafetyState.CRITICAL,
        alarm_code="LINK_LOST",
        elapsed_time_s=10.0,
    )

    track = DiverTrack(
        latest_packet=packet,
        packets_received=1,
        last_packet_elapsed_time_s=10.0,
        packet_age_s=0.0,
        is_stale=False,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.SEARCH_LAST_KNOWN
    assert action.priority == 90
    assert action.notify_surface is True


def test_planner_approaches_when_weak_link_alarm_is_present():
    planner = RobotBehaviorPlanner()

    packet = make_safety_packet(
        safety_state=SafetyState.WARNING,
        alarm_code="WEAK_LINK",
        elapsed_time_s=10.0,
    )

    track = DiverTrack(
        latest_packet=packet,
        packets_received=1,
        last_packet_elapsed_time_s=10.0,
        packet_age_s=0.0,
        is_stale=False,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.APPROACH_DIVER
    assert action.priority == 50
    assert action.notify_surface is False


def test_planner_prioritizes_emergency_button_alarm():
    planner = RobotBehaviorPlanner()

    packet = make_safety_packet(
        safety_state=SafetyState.EMERGENCY,
        alarm_code="DIVER_EMERGENCY_BUTTON",
        elapsed_time_s=10.0,
    )

    track = DiverTrack(
        latest_packet=packet,
        packets_received=1,
        last_packet_elapsed_time_s=10.0,
        packet_age_s=0.0,
        is_stale=False,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.EMERGENCY_SUPPORT
    assert action.priority == 100
    assert action.notify_surface is True


def test_planner_falls_back_to_safety_state_when_alarm_code_is_unknown():
    planner = RobotBehaviorPlanner()

    packet = make_safety_packet(
        safety_state=SafetyState.CRITICAL,
        alarm_code="UNKNOWN_TEST_ALARM",
        elapsed_time_s=10.0,
    )

    track = DiverTrack(
        latest_packet=packet,
        packets_received=1,
        last_packet_elapsed_time_s=10.0,
        packet_age_s=0.0,
        is_stale=False,
    )

    action = planner.plan(track)

    assert action.mode == RobotMode.EMERGENCY_SUPPORT
    assert action.priority == 90
    assert action.notify_surface is True