from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from mission_logging.schemas import MissionEvent


@pytest.fixture()
def client():
    """
    Create a fresh API client for each test.

    Using create_app() here gives every test an isolated in-memory
    MissionBackend.
    """

    with TestClient(create_app()) as test_client:
        yield test_client


def make_mission_event_payload(event_index: int = 0,
        scenario: str = "normal",
        elapsed_time_s: float = 0.0,
        wearable_safety_state: str = "OK",
        wearable_alarm_codes: list[str] | None = None,
        communication_transmit_status: str | None = "NO_PACKET_AVAILABLE",
        communication_receive_status: str | None = "DELIVERED",
        communication_tx_sequence_number: int | None = 0,
        communication_rx_sequence_number: int | None = 0,
        communication_tx_message_id: str | None = "tx-message-0",
        communication_rx_message_id: str | None = "rx-message-0",
        communication_sender_id: str | None = "wearable_01",
        communication_receiver_id: str | None = "robot_01",
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
        surface_alert_codes: list[str] | None = None, ) -> dict:
    """
    Create a JSON-serializable MissionEvent payload for API tests.
    """

    event = MissionEvent(event_index=event_index, recorded_at_utc=datetime.now(timezone.utc),

        scenario=scenario, elapsed_time_s=elapsed_time_s,

        wearable_safety_state=wearable_safety_state, wearable_alarm_codes=wearable_alarm_codes or [],

        communication_transmit_status=communication_transmit_status,
        communication_receive_status=communication_receive_status,

        communication_tx_sequence_number=communication_tx_sequence_number,
        communication_rx_sequence_number=communication_rx_sequence_number,
        communication_tx_message_id=communication_tx_message_id,
        communication_rx_message_id=communication_rx_message_id, communication_sender_id=communication_sender_id,
        communication_receiver_id=communication_receiver_id,

        communication_latency_s=communication_latency_s, communication_reason=communication_reason,

        received_safety_state=received_safety_state, received_alarm_codes=received_alarm_codes or [],

        robot_mode=robot_mode, robot_reason=robot_reason, robot_priority=robot_priority,
        robot_notify_surface=robot_notify_surface,

        latest_diver_packet_age_s=latest_diver_packet_age_s, diver_data_stale=diver_data_stale,

        surface_mission_state=surface_mission_state, surface_alert_codes=surface_alert_codes or [], )

    return event.model_dump(mode="json")


def test_get_snapshot_before_start_returns_404(client):
    response = client.get("/missions/snapshot")

    assert response.status_code == 404
    assert response.json()["detail"] == "mission has not been started"


def test_start_mission_returns_running_snapshot(client):
    response = client.post("/missions/start", json={
        "scenario": "normal",
        "mission_id": "mission_01", }, )

    assert response.status_code == 200

    body = response.json()
    snapshot = body["snapshot"]

    assert snapshot["mission_id"] == "mission_01"
    assert snapshot["scenario"] == "normal"
    assert snapshot["status"] == "RUNNING"
    assert snapshot["events_received"] == 0
    assert snapshot["latest_event"] is None


def test_start_mission_rejects_empty_scenario(client):
    response = client.post("/missions/start", json={
        "scenario": "",
        "mission_id": "mission_01", }, )

    assert response.status_code == 422


def test_ingest_event_updates_snapshot(client):
    client.post("/missions/start", json={
        "scenario": "fast_ascent",
        "mission_id": "mission_01", }, )

    event_payload = make_mission_event_payload(event_index=0, scenario="fast_ascent", elapsed_time_s=190.0,
        wearable_safety_state="CRITICAL", wearable_alarm_codes=["FAST_ASCENT"], received_safety_state="CRITICAL",
        received_alarm_codes=["FAST_ASCENT"], robot_mode="EMERGENCY_SUPPORT",
        robot_reason="Diver is ascending too fast.", robot_priority=90, robot_notify_surface=True,
        surface_mission_state="EMERGENCY", surface_alert_codes=["DIVER_CRITICAL", "DIVER_ALARM_FAST_ASCENT"], )

    response = client.post("/missions/events", json=event_payload, )

    assert response.status_code == 200

    snapshot = response.json()["snapshot"]

    assert snapshot["events_received"] == 1
    assert snapshot["last_event_time_s"] == 190.0
    assert snapshot["current_wearable_safety_state"] == "CRITICAL"
    assert snapshot["current_received_safety_state"] == "CRITICAL"
    assert snapshot["current_robot_mode"] == "EMERGENCY_SUPPORT"
    assert snapshot["current_surface_mission_state"] == "EMERGENCY"
    assert snapshot["active_wearable_alarm_codes"] == ["FAST_ASCENT"]
    assert snapshot["active_surface_alert_codes"] == ["DIVER_CRITICAL", "DIVER_ALARM_FAST_ASCENT", ]
    assert snapshot["emergency_event_count"] == 1


def test_ingest_event_before_start_returns_409(client):
    event_payload = make_mission_event_payload(scenario="normal", )

    response = client.post("/missions/events", json=event_payload, )

    assert response.status_code == 409
    assert response.json()["detail"] == "mission has not been started"


def test_ingest_event_with_wrong_scenario_returns_400(client):
    client.post("/missions/start", json={
        "scenario": "normal",
        "mission_id": "mission_01", }, )

    event_payload = make_mission_event_payload(scenario="fast_ascent", )

    response = client.post("/missions/events", json=event_payload, )

    assert response.status_code == 400
    assert "event scenario does not match" in response.json()["detail"]


def test_get_summary_returns_compact_summary(client):
    client.post("/missions/start", json={
        "scenario": "emergency_button",
        "mission_id": "mission_01", }, )

    event_payload = make_mission_event_payload(event_index=0, scenario="emergency_button", elapsed_time_s=130.0,
        wearable_safety_state="EMERGENCY", wearable_alarm_codes=["DIVER_EMERGENCY_BUTTON"],
        received_safety_state="EMERGENCY", received_alarm_codes=["DIVER_EMERGENCY_BUTTON"],
        robot_mode="EMERGENCY_SUPPORT", robot_reason="Diver pressed the emergency button.", robot_priority=100,
        robot_notify_surface=True, surface_mission_state="EMERGENCY",
        surface_alert_codes=["DIVER_EMERGENCY", "DIVER_ALARM_DIVER_EMERGENCY_BUTTON", ], )

    client.post("/missions/events", json=event_payload, )

    response = client.get("/missions/summary")

    assert response.status_code == 200

    summary = response.json()["summary"]

    assert summary["mission_id"] == "mission_01"
    assert summary["scenario"] == "emergency_button"
    assert summary["status"] == "RUNNING"
    assert summary["events_received"] == 1
    assert summary["current_surface_mission_state"] == "EMERGENCY"
    assert summary["current_robot_mode"] == "EMERGENCY_SUPPORT"
    assert summary["emergency_event_count"] == 1


def test_get_events_returns_all_events(client):
    client.post("/missions/start", json={
        "scenario": "normal",
        "mission_id": "mission_01", }, )

    event_1 = make_mission_event_payload(event_index=0, scenario="normal", elapsed_time_s=0.0, )
    event_2 = make_mission_event_payload(event_index=1, scenario="normal", elapsed_time_s=5.0, )

    client.post("/missions/events", json=event_1)
    client.post("/missions/events", json=event_2)

    response = client.get("/missions/events")

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 2
    assert events[0]["event_index"] == 0
    assert events[1]["event_index"] == 1


def test_get_recent_events_returns_limited_events(client):
    client.post("/missions/start", json={
        "scenario": "normal",
        "mission_id": "mission_01", }, )

    for index in range(3):
        event_payload = make_mission_event_payload(event_index=index, scenario="normal",
            elapsed_time_s=float(index * 5), )
        client.post("/missions/events", json=event_payload)

    response = client.get("/missions/events/recent?limit=2")

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 2
    assert events[0]["event_index"] == 1
    assert events[1]["event_index"] == 2


def test_get_recent_events_rejects_invalid_limit(client):
    client.post("/missions/start", json={
        "scenario": "normal",
        "mission_id": "mission_01", }, )

    response = client.get("/missions/events/recent?limit=0")

    assert response.status_code == 422


def test_finish_mission_marks_mission_completed(client):
    client.post("/missions/start", json={
        "scenario": "normal",
        "mission_id": "mission_01", }, )

    response = client.post("/missions/finish")

    assert response.status_code == 200

    snapshot = response.json()["snapshot"]

    assert snapshot["status"] == "COMPLETED"
    assert snapshot["ended_at_utc"] is not None


def test_ingest_after_finish_returns_409(client):
    client.post("/missions/start", json={
        "scenario": "normal",
        "mission_id": "mission_01", }, )

    client.post("/missions/finish")

    event_payload = make_mission_event_payload(scenario="normal", )

    response = client.post("/missions/events", json=event_payload, )

    assert response.status_code == 409
    assert "mission is not running" in response.json()["detail"]


def test_abort_mission_marks_mission_aborted(client):
    client.post("/missions/start", json={
        "scenario": "normal",
        "mission_id": "mission_01", }, )

    response = client.post("/missions/abort")

    assert response.status_code == 200

    snapshot = response.json()["snapshot"]

    assert snapshot["status"] == "ABORTED"
    assert snapshot["ended_at_utc"] is not None


def test_reset_clears_backend_state(client):
    client.post("/missions/start", json={
        "scenario": "normal",
        "mission_id": "mission_01", }, )

    reset_response = client.post("/missions/reset")

    assert reset_response.status_code == 200
    assert reset_response.json() == {
        "message": "Mission backend reset."}

    snapshot_response = client.get("/missions/snapshot")

    assert snapshot_response.status_code == 404
    assert snapshot_response.json()["detail"] == "mission has not been started"
