from robot_tracker import RobotDiverTracker, RobotTrackerConfig
from tests.helpers import make_safety_packet


def test_tracker_starts_without_latest_packet():
    tracker = RobotDiverTracker()

    track = tracker.update(packet=None, robot_elapsed_time_s=0.0, )

    assert track.latest_packet is None
    assert track.packets_received == 0
    assert track.last_packet_elapsed_time_s is None
    assert track.packet_age_s is None
    assert track.is_stale is True


def test_tracker_stores_new_packet():
    tracker = RobotDiverTracker()

    packet = make_safety_packet(elapsed_time_s=10.0, sample_index=2, )

    track = tracker.update(packet=packet, robot_elapsed_time_s=10.0, )

    assert track.latest_packet == packet
    assert track.packets_received == 1
    assert track.last_packet_elapsed_time_s == 10.0
    assert track.packet_age_s == 0.0
    assert track.is_stale is False


def test_tracker_keeps_latest_packet_when_no_new_packet_arrives():
    tracker = RobotDiverTracker(config=RobotTrackerConfig(stale_packet_after_s=10.0))

    packet = make_safety_packet(elapsed_time_s=20.0, sample_index=4, )

    tracker.update(packet=packet, robot_elapsed_time_s=20.0, )

    track = tracker.update(packet=None, robot_elapsed_time_s=25.0, )

    assert track.latest_packet == packet
    assert track.packets_received == 1
    assert track.packet_age_s == 5.0
    assert track.is_stale is False


def test_tracker_marks_packet_as_stale_when_age_exceeds_threshold():
    tracker = RobotDiverTracker(config=RobotTrackerConfig(stale_packet_after_s=10.0))

    packet = make_safety_packet(elapsed_time_s=20.0, sample_index=4, )

    tracker.update(packet=packet, robot_elapsed_time_s=20.0, )

    track = tracker.update(packet=None, robot_elapsed_time_s=31.0, )

    assert track.latest_packet == packet
    assert track.packet_age_s == 11.0
    assert track.is_stale is True


def test_tracker_reset_clears_memory():
    tracker = RobotDiverTracker()

    packet = make_safety_packet(elapsed_time_s=10.0, sample_index=2, )

    tracker.update(packet=packet, robot_elapsed_time_s=10.0, )

    tracker.reset()

    track = tracker.update(packet=None, robot_elapsed_time_s=12.0, )

    assert track.latest_packet is None
    assert track.packets_received == 0
    assert track.is_stale is True
