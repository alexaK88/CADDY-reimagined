"""
Mission backend.

The MissionBackend stores mission events and maintains a current mission
snapshot. It does not make robot decisions, surface decisions, or communication
decisions.

For now this is an in-memory backend. Later, this layer can be connected to:
- FastAPI endpoints
- SQLite/PostgreSQL storage
- WebSocket dashboard updates
- mission replay tools
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from mission_backend.schemas import (MissionBackendSummary, MissionRunStatus, MissionSnapshot, )
from mission_logging.schemas import MissionEvent


class MissionBackend:
    """
    In-memory mission backend for one mission run.
    """

    def __init__(self):
        """
        Initialize an empty backend.
        """

        self._mission_id: str | None = None
        self._scenario: str | None = None
        self._status: MissionRunStatus = MissionRunStatus.NOT_STARTED

        self._started_at_utc: datetime | None = None
        self._ended_at_utc: datetime | None = None

        self._events: list[MissionEvent] = []

    def start_mission(self, scenario: str, mission_id: str | None = None, ) -> MissionSnapshot:
        """
        Start a new mission run.

        Args:
            scenario: Scenario name for this mission run.
            mission_id: Optional external mission identifier. If omitted, one
                is generated automatically.

        Returns:
            Initial MissionSnapshot.
        """

        if not scenario:
            raise ValueError("scenario must not be empty")

        self._mission_id = mission_id or str(uuid4())
        self._scenario = scenario
        self._status = MissionRunStatus.RUNNING
        self._started_at_utc = datetime.now(timezone.utc)
        self._ended_at_utc = None
        self._events.clear()

        return self.get_snapshot()

    def ingest_event(self, event: MissionEvent) -> MissionSnapshot:
        """
        Store one mission event and update the mission snapshot.

        Args:
            event: MissionEvent produced by the mission logging layer.

        Returns:
            Updated MissionSnapshot.
        """

        self._raise_if_not_running()

        if event.scenario != self._scenario:
            raise ValueError("event scenario does not match active mission scenario. "
                             f"event.scenario={event.scenario}, active_scenario={self._scenario}")

        self._events.append(event)

        return self.get_snapshot()

    def finish_mission(self) -> MissionSnapshot:
        """
        Mark the mission as completed.
        """

        self._raise_if_not_started()

        self._status = MissionRunStatus.COMPLETED
        self._ended_at_utc = datetime.now(timezone.utc)

        return self.get_snapshot()

    def abort_mission(self) -> MissionSnapshot:
        """
        Mark the mission as aborted.
        """

        self._raise_if_not_started()

        self._status = MissionRunStatus.ABORTED
        self._ended_at_utc = datetime.now(timezone.utc)

        return self.get_snapshot()

    def get_events(self) -> list[MissionEvent]:
        """
        Return a copy of all stored mission events.
        """

        return list(self._events)

    def get_recent_events(self, limit: int = 10) -> list[MissionEvent]:
        """
        Return the latest mission events.

        Args:
            limit: Maximum number of events to return.
        """

        if limit <= 0:
            raise ValueError("limit must be positive")

        return self._events[-limit:]

    def get_snapshot(self) -> MissionSnapshot:
        """
        Return the current mission snapshot.
        """

        self._raise_if_not_started()

        latest_event = self._events[-1] if self._events else None

        return MissionSnapshot(mission_id=self._mission_id or "unknown", scenario=self._scenario or "unknown",
            status=self._status,

            started_at_utc=self._started_at_utc, ended_at_utc=self._ended_at_utc,

            events_received=len(self._events),

            last_event_time_s=(latest_event.elapsed_time_s if latest_event is not None else None),
            current_wearable_safety_state=(latest_event.wearable_safety_state if latest_event is not None else None),
            current_received_safety_state=(latest_event.received_safety_state if latest_event is not None else None),
            current_robot_mode=(latest_event.robot_mode if latest_event is not None else None),
            current_surface_mission_state=(latest_event.surface_mission_state if latest_event is not None else None),

            active_wearable_alarm_codes=(latest_event.wearable_alarm_codes if latest_event is not None else []),
            active_surface_alert_codes=(latest_event.surface_alert_codes if latest_event is not None else []),

            emergency_event_count=self._count_emergency_events(), warning_event_count=self._count_warning_events(),
            stale_data_event_count=self._count_stale_data_events(),

            latest_event=latest_event, )

    def get_summary(self) -> MissionBackendSummary:
        """
        Return a compact backend summary.
        """

        snapshot = self.get_snapshot()

        return MissionBackendSummary(mission_id=snapshot.mission_id, scenario=snapshot.scenario, status=snapshot.status,
            events_received=snapshot.events_received,
            current_surface_mission_state=snapshot.current_surface_mission_state,
            current_robot_mode=snapshot.current_robot_mode, emergency_event_count=snapshot.emergency_event_count,
            warning_event_count=snapshot.warning_event_count, stale_data_event_count=snapshot.stale_data_event_count, )

    def reset(self) -> None:
        """
        Clear the backend state.
        """

        self._mission_id = None
        self._scenario = None
        self._status = MissionRunStatus.NOT_STARTED
        self._started_at_utc = None
        self._ended_at_utc = None
        self._events.clear()

    def _count_emergency_events(self) -> int:
        """
        Count events where the surface mission state was emergency.
        """

        return sum(1 for event in self._events if event.surface_mission_state == "EMERGENCY")

    def _count_warning_events(self) -> int:
        """
        Count events that required attention but were not full emergencies.
        """

        return sum(
            1 for event in self._events if event.surface_mission_state in {"ATTENTION_REQUIRED", "DIVER_DATA_STALE", })

    def _count_stale_data_events(self) -> int:
        """
        Count events where diver data was stale.
        """

        return sum(1 for event in self._events if event.diver_data_stale)

    def _raise_if_not_started(self) -> None:
        """
        Raise if no mission has been started.
        """

        if self._status == MissionRunStatus.NOT_STARTED:
            raise RuntimeError("mission has not been started")

    def _raise_if_not_running(self) -> None:
        """
        Raise if the mission is not currently running.
        """

        self._raise_if_not_started()

        if self._status != MissionRunStatus.RUNNING:
            raise RuntimeError(f"mission is not running. Current status={self._status.value}")
