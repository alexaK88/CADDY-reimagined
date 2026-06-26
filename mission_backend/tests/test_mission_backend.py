from datetime import datetime, timezone

import pytest

from mission_backend.mission_backend import MissionBackend
from mission_backend.schemas import MissionRunStatus
from mission_logging.schemas import MissionEvent


def make_mission_event(event_index: int = 0,
        scenario: str = "normal",
        elapsed_time_s: float = 0.0,
        wearable_safety_state: str = "OK",
        wearable_alarm_codes: list[str] | None = None,
        communication_transmit_status: str | None = "NO_PACKET_AVAILABLE",
        communication_receive_status: str | None = "DELIVERED",
        communication_latency_s: float | None = 1.0,
        communication_reason: str | None = "Packet delivered by simulated acoustic link.",
        received_safety_state: str | None = "OK",
        received_alarm_codes: list[str] | None = None,
        robot_mode: str = "MONITORING",
        robot_reason: str = "Diver safety state is OK.",
        robot_priority: int = 10,
        robot_notify_surface: bool = False,
        latest_diver_packet_age_s: float | None = 0.0,
        diver_data_stale: bool = False,
        surface_mission_state: str = "NORMAL",
        surface_alert_codes: list[str] | None = None, ) -> MissionEvent:
    """
    Create a minimal valid MissionEvent for backend tests.
    """

    return MissionEvent(event_index=event_index, recorded_at_utc=datetime.now(timezone.utc),

        scenario=scenario, elapsed_time_s=elapsed_time_s,

        wearable_safety_state=wearable_safety_state, wearable_alarm_codes=wearable_alarm_codes or [],

        communication_transmit_status=communication_transmit_status,
        communication_receive_status=communication_receive_status, communication_latency_s=communication_latency_s,
        communication_reason=communication_reason,

        received_safety_state=received_safety_state, received_alarm_codes=received_alarm_codes or [],

        robot_mode=robot_mode, robot_reason=robot_reason, robot_priority=robot_priority,
        robot_notify_surface=robot_notify_surface,

        latest_diver_packet_age_s=latest_diver_packet_age_s, diver_data_stale=diver_data_stale,

        surface_mission_state=surface_mission_state, surface_alert_codes=surface_alert_codes or [], )


def test_backend_cannot_return_snapshot_before_mission_starts():
    backend = MissionBackend()

    with pytest.raises(RuntimeError, match="mission has not been started"):
        backend.get_snapshot()


def test_backend_starts_mission():
    backend = MissionBackend()

    snapshot = backend.start_mission(scenario="normal", mission_id="mission_01", )

    assert snapshot.mission_id == "mission_01"
    assert snapshot.scenario == "normal"
    assert snapshot.status == MissionRunStatus.RUNNING
    assert snapshot.started_at_utc is not None
    assert snapshot.ended_at_utc is None
    assert snapshot.events_received == 0
    assert snapshot.latest_event is None


def test_backend_ingests_normal_event_and_updates_snapshot():
    backend = MissionBackend()
    backend.start_mission(scenario="normal", mission_id="mission_01", )

    event = make_mission_event(event_index=0, scenario="normal", elapsed_time_s=5.0, wearable_safety_state="OK",
        received_safety_state="OK", robot_mode="MONITORING", surface_mission_state="NORMAL", )

    snapshot = backend.ingest_event(event)

    assert snapshot.events_received == 1
    assert snapshot.latest_event == event
    assert snapshot.last_event_time_s == 5.0
    assert snapshot.current_wearable_safety_state == "OK"
    assert snapshot.current_received_safety_state == "OK"
    assert snapshot.current_robot_mode == "MONITORING"
    assert snapshot.current_surface_mission_state == "NORMAL"
    assert snapshot.active_wearable_alarm_codes == []
    assert snapshot.active_surface_alert_codes == []
    assert snapshot.emergency_event_count == 0
    assert snapshot.warning_event_count == 0
    assert snapshot.stale_data_event_count == 0


def test_backend_counts_emergency_events():
    backend = MissionBackend()
    backend.start_mission(scenario="fast_ascent", mission_id="mission_01", )

    normal_event = make_mission_event(event_index=0, scenario="fast_ascent", elapsed_time_s=180.0,
        surface_mission_state="NORMAL", )

    emergency_event = make_mission_event(event_index=1, scenario="fast_ascent", elapsed_time_s=190.0,
        wearable_safety_state="CRITICAL", wearable_alarm_codes=["FAST_ASCENT"], received_safety_state="CRITICAL",
        received_alarm_codes=["FAST_ASCENT"], robot_mode="EMERGENCY_SUPPORT",
        robot_reason="Diver is ascending too fast.", robot_priority=90, robot_notify_surface=True,
        surface_mission_state="EMERGENCY", surface_alert_codes=["DIVER_CRITICAL", "DIVER_ALARM_FAST_ASCENT"], )

    backend.ingest_event(normal_event)
    snapshot = backend.ingest_event(emergency_event)

    assert snapshot.events_received == 2
    assert snapshot.current_surface_mission_state == "EMERGENCY"
    assert snapshot.current_robot_mode == "EMERGENCY_SUPPORT"
    assert snapshot.active_wearable_alarm_codes == ["FAST_ASCENT"]
    assert snapshot.active_surface_alert_codes == ["DIVER_CRITICAL", "DIVER_ALARM_FAST_ASCENT", ]
    assert snapshot.emergency_event_count == 1
    assert snapshot.warning_event_count == 0
    assert snapshot.stale_data_event_count == 0


def test_backend_counts_warning_and_stale_data_events():
    backend = MissionBackend()
    backend.start_mission(scenario="normal", mission_id="mission_01", )

    warning_event = make_mission_event(event_index=0, scenario="normal", elapsed_time_s=20.0,
        wearable_safety_state="WARNING", wearable_alarm_codes=["LOW_GAS"], received_safety_state="WARNING",
        received_alarm_codes=["LOW_GAS"], robot_mode="GUIDE_DIVER", robot_reason="Diver tank pressure is low.",
        robot_priority=70, surface_mission_state="ATTENTION_REQUIRED", surface_alert_codes=["DIVER_ALARM_LOW_GAS"], )

    stale_event = make_mission_event(event_index=1, scenario="normal", elapsed_time_s=410.0,
        wearable_safety_state="NO_PACKET", communication_transmit_status=None, communication_receive_status=None,
        communication_latency_s=None, communication_reason=None, received_safety_state=None,
        robot_mode="SEARCH_LAST_KNOWN", robot_reason="Latest diver packet is stale.", robot_priority=90,
        robot_notify_surface=True, latest_diver_packet_age_s=15.0, diver_data_stale=True,
        surface_mission_state="DIVER_DATA_STALE", surface_alert_codes=["DIVER_DATA_STALE", "SEARCH_LAST_KNOWN"], )

    backend.ingest_event(warning_event)
    snapshot = backend.ingest_event(stale_event)

    assert snapshot.events_received == 2
    assert snapshot.warning_event_count == 2
    assert snapshot.stale_data_event_count == 1
    assert snapshot.emergency_event_count == 0
    assert snapshot.current_surface_mission_state == "DIVER_DATA_STALE"
    assert snapshot.current_robot_mode == "SEARCH_LAST_KNOWN"


def test_backend_rejects_event_with_different_scenario():
    backend = MissionBackend()
    backend.start_mission(scenario="normal", mission_id="mission_01", )

    event = make_mission_event(scenario="fast_ascent", )

    with pytest.raises(ValueError, match="event scenario does not match"):
        backend.ingest_event(event)


def test_backend_returns_all_events_as_copy():
    backend = MissionBackend()
    backend.start_mission(scenario="normal", mission_id="mission_01", )

    event_1 = make_mission_event(event_index=0, scenario="normal", elapsed_time_s=0.0, )
    event_2 = make_mission_event(event_index=1, scenario="normal", elapsed_time_s=5.0, )

    backend.ingest_event(event_1)
    backend.ingest_event(event_2)

    events = backend.get_events()

    assert events == [event_1, event_2]

    events.clear()

    assert backend.get_events() == [event_1, event_2]


def test_backend_returns_recent_events():
    backend = MissionBackend()
    backend.start_mission(scenario="normal", mission_id="mission_01", )

    event_1 = make_mission_event(event_index=0, scenario="normal", elapsed_time_s=0.0, )
    event_2 = make_mission_event(event_index=1, scenario="normal", elapsed_time_s=5.0, )
    event_3 = make_mission_event(event_index=2, scenario="normal", elapsed_time_s=10.0, )

    backend.ingest_event(event_1)
    backend.ingest_event(event_2)
    backend.ingest_event(event_3)

    assert backend.get_recent_events(limit=2) == [event_2, event_3]


def test_backend_rejects_invalid_recent_event_limit():
    backend = MissionBackend()
    backend.start_mission(scenario="normal", mission_id="mission_01", )

    with pytest.raises(ValueError, match="limit must be positive"):
        backend.get_recent_events(limit=0)


def test_backend_finishes_mission():
    backend = MissionBackend()
    backend.start_mission(scenario="normal", mission_id="mission_01", )

    event = make_mission_event(scenario="normal", )

    backend.ingest_event(event)

    snapshot = backend.finish_mission()

    assert snapshot.status == MissionRunStatus.COMPLETED
    assert snapshot.ended_at_utc is not None
    assert snapshot.events_received == 1


def test_backend_rejects_ingest_after_finish():
    backend = MissionBackend()
    backend.start_mission(scenario="normal", mission_id="mission_01", )

    backend.finish_mission()

    event = make_mission_event(scenario="normal", )

    with pytest.raises(RuntimeError, match="mission is not running"):
        backend.ingest_event(event)


def test_backend_aborts_mission():
    backend = MissionBackend()
    backend.start_mission(scenario="normal", mission_id="mission_01", )

    snapshot = backend.abort_mission()

    assert snapshot.status == MissionRunStatus.ABORTED
    assert snapshot.ended_at_utc is not None


def test_backend_summary_reflects_latest_snapshot():
    backend = MissionBackend()
    backend.start_mission(scenario="fast_ascent", mission_id="mission_01", )

    event = make_mission_event(event_index=0, scenario="fast_ascent", elapsed_time_s=190.0,
        wearable_safety_state="CRITICAL", wearable_alarm_codes=["FAST_ASCENT"], received_safety_state="CRITICAL",
        received_alarm_codes=["FAST_ASCENT"], robot_mode="EMERGENCY_SUPPORT",
        robot_reason="Diver is ascending too fast.", robot_priority=90, robot_notify_surface=True,
        surface_mission_state="EMERGENCY", surface_alert_codes=["DIVER_CRITICAL", "DIVER_ALARM_FAST_ASCENT"], )

    backend.ingest_event(event)

    summary = backend.get_summary()

    assert summary.mission_id == "mission_01"
    assert summary.scenario == "fast_ascent"
    assert summary.status == MissionRunStatus.RUNNING
    assert summary.events_received == 1
    assert summary.current_surface_mission_state == "EMERGENCY"
    assert summary.current_robot_mode == "EMERGENCY_SUPPORT"
    assert summary.emergency_event_count == 1
    assert summary.warning_event_count == 0
    assert summary.stale_data_event_count == 0


def test_backend_reset_clears_state():
    backend = MissionBackend()
    backend.start_mission(scenario="normal", mission_id="mission_01", )

    event = make_mission_event(scenario="normal", )

    backend.ingest_event(event)
    backend.reset()

    with pytest.raises(RuntimeError, match="mission has not been started"):
        backend.get_snapshot()
