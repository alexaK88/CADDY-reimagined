"""
Mission logging schemas.

These models describe one recorded mission timeline event. The logger is an
observability layer: it records what happened, but it does not influence
wearable, communication, robot, or surface gateway decisions.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MissionEvent(BaseModel):
    """
    One recorded mission timeline event.

    A MissionEvent captures the state of the system at one simulation step:
    wearable output, communication result, robot decision, and surface gateway
    interpretation.
    """

    event_index: int = Field(ge=0)
    recorded_at_utc: datetime

    scenario: str = Field(min_length=1)
    elapsed_time_s: float = Field(ge=0)

    wearable_safety_state: str
    wearable_alarm_codes: list[str] = Field(default_factory=list)

    communication_transmit_status: str | None = None
    communication_receive_status: str | None = None
    communication_latency_s: float | None = Field(default=None, ge=0)
    communication_reason: str | None = None

    received_safety_state: str | None = None
    received_alarm_codes: list[str] = Field(default_factory=list)

    robot_mode: str
    robot_reason: str
    robot_priority: int = Field(ge=0, le=100)
    robot_notify_surface: bool

    latest_diver_packet_age_s: float | None = Field(default=None, ge=0)
    diver_data_stale: bool

    surface_mission_state: str
    surface_alert_codes: list[str] = Field(default_factory=list)

    communication_tx_sequence_number: int | None = Field(default=None, ge=0)
    communication_rx_sequence_number: int | None = Field(default=None, ge=0)

    communication_tx_message_id: str | None = None
    communication_rx_message_id: str | None = None

    communication_sender_id: str | None = None
    communication_receiver_id: str | None = None

    @field_validator("recorded_at_utc")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        """
        Ensure mission log timestamps include timezone information.
        """

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("recorded_at_utc must be timezone-aware")

        return value
