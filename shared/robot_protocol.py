"""
Shared robot-to-surface protocol models.

These models describe the compact status reports that the robot can send to a
surface gateway, backend, or operator dashboard.

The robot module produces RobotStatusPacket objects. The surface gateway
consumes them. This keeps the surface layer independent from the robot's
internal decision objects.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from shared.shared_protocol import SafetyState


class RobotMode(str, Enum):
    """
    High-level robot behaviour mode.

    This is part of the robot-to-surface protocol because the surface gateway
    and operator dashboard need to know what the robot is currently trying to
    do.
    """

    IDLE = "IDLE"
    MONITORING = "MONITORING"
    APPROACH_DIVER = "APPROACH_DIVER"
    GUIDE_DIVER = "GUIDE_DIVER"
    EMERGENCY_SUPPORT = "EMERGENCY_SUPPORT"
    SEARCH_LAST_KNOWN = "SEARCH_LAST_KNOWN"


class RobotStatusPacket(BaseModel):
    """
    Compact robot status report sent to the surface gateway.

    This packet summarizes the robot's latest decision and the diver safety
    information that influenced it. It does not expose the full internal
    RobotDecision object.
    """

    robot_id: str = Field(min_length=1)
    produced_at_utc: datetime

    robot_elapsed_time_s: float = Field(ge=0)

    mode: RobotMode
    reason: str = Field(min_length=1)
    priority: int = Field(ge=0, le=100)
    notify_surface: bool

    diver_id: str | None = None
    diver_safety_state: SafetyState | None = None
    active_alarm_codes: list[str] = Field(default_factory=list)

    latest_diver_packet_age_s: float | None = Field(default=None, ge=0)
    is_diver_data_stale: bool = False

    @field_validator("produced_at_utc")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        """
        Ensure report timestamps include timezone information.
        """

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("produced_at_utc must be timezone-aware")

        return value