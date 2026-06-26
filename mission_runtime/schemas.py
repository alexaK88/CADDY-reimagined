"""
Mission runtime schemas.

The runtime layer controls live mission execution from the API/UI.
It is responsible for starting and stopping the simulation loop.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class MissionRuntimeState(str, Enum):
    """
    Current execution state of the live mission runner.
    """

    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StartRuntimeRequest(BaseModel):
    """
    Request body for starting a live mission runtime.
    """

    scenario: str = Field(min_length=1)
    mission_id: str | None = Field(default=None, min_length=1)
    tick_interval_s: float = Field(default=1.0, gt=0)


class StopRuntimeRequest(BaseModel):
    """
    Request body for stopping a live mission runtime.
    """

    reason: str = "Operator ended the mission."


class MissionRuntimeStatus(BaseModel):
    """
    Current runtime status returned to the UI.
    """

    state: MissionRuntimeState
    mission_id: str | None = None
    scenario: str | None = None

    started_at_utc: datetime | None = None
    stopped_at_utc: datetime | None = None

    events_processed: int = Field(default=0, ge=0)
    log_path: str | None = None
    last_error: str | None = None

    @field_validator("started_at_utc", "stopped_at_utc")
    @classmethod
    def timestamps_must_be_timezone_aware(cls, value: datetime | None, ) -> datetime | None:
        if value is None:
            return value

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("runtime timestamps must be timezone-aware")

        return value
