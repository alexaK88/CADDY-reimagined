"""
API request/response schemas.

These models are specific to the HTTP API layer. They do not replace the core
mission backend schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from mission_backend.schemas import MissionBackendSummary, MissionSnapshot


class StartMissionRequest(BaseModel):
    """
    Request body for starting a mission.
    """

    scenario: str = Field(min_length=1)
    mission_id: str | None = Field(default=None, min_length=1)


class ApiMessage(BaseModel):
    """
    Simple API message response.
    """

    message: str


class MissionSnapshotResponse(BaseModel):
    """
    Response wrapper for the current mission snapshot.
    """

    snapshot: MissionSnapshot


class MissionSummaryResponse(BaseModel):
    """
    Response wrapper for compact mission summary.
    """

    summary: MissionBackendSummary
