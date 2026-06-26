"""
Mission backend schemas.

These models describe the backend-facing mission state. The backend consumes
MissionEvent objects produced by the mission logging layer and maintains a
current snapshot of the mission.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from mission_logging.schemas import MissionEvent


class MissionRunStatus(str, Enum):
    """
    Lifecycle state of one mission run.
    """

    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


class MissionSnapshot(BaseModel):
    """
    Current backend snapshot of one mission run.

    This is the object a future dashboard/API would read to show current mission
    state without scanning the whole event history every time.
    """

    mission_id: str = Field(min_length=1)
    scenario: str = Field(min_length=1)
    status: MissionRunStatus

    started_at_utc: datetime | None = None
    ended_at_utc: datetime | None = None

    events_received: int = Field(ge=0)

    last_event_time_s: float | None = Field(default=None, ge=0)
    current_wearable_safety_state: str | None = None
    current_received_safety_state: str | None = None
    current_robot_mode: str | None = None
    current_surface_mission_state: str | None = None

    active_wearable_alarm_codes: list[str] = Field(default_factory=list)
    active_surface_alert_codes: list[str] = Field(default_factory=list)

    emergency_event_count: int = Field(default=0, ge=0)
    warning_event_count: int = Field(default=0, ge=0)
    stale_data_event_count: int = Field(default=0, ge=0)

    latest_event: MissionEvent | None = None

    @field_validator("started_at_utc", "ended_at_utc")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime | None, ) -> datetime | None:
        """
        Ensure backend timestamps include timezone information.
        """

        if value is None:
            return value

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("mission backend timestamps must be timezone-aware")

        return value


class MissionBackendSummary(BaseModel):
    """
    Compact mission summary useful for console output or future API responses.
    """

    mission_id: str
    scenario: str
    status: MissionRunStatus
    events_received: int
    current_surface_mission_state: str | None
    current_robot_mode: str | None
    emergency_event_count: int
    warning_event_count: int
    stale_data_event_count: int
