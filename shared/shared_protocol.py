"""
Shared protocol models between the wearable and robot prototypes.

In the current Python prototype, these Pydantic models act as the shared
message contract between modules. The wearable module produces these messages,
and the robot module consumes them.

In a real distributed system, this layer would likely be replaced by generated
message definitions such as ROS 2 messages, Protocol Buffers, or another
versioned communication schema.

Important dependency rule:
    shared.protocol must not import wearable modules or robot modules.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class DivePhase(str, Enum):
    """
    Interpreted vertical phase of the dive.
    """

    AT_SURFACE = "AT_SURFACE"
    DESCENDING = "DESCENDING"
    AT_DEPTH = "AT_DEPTH"
    ASCENDING = "ASCENDING"
    SAFETY_STOP = "SAFETY_STOP"
    UNKNOWN = "UNKNOWN"


class MotionState(str, Enum):
    """
    Interpreted motion state of the diver.
    """

    STILL = "STILL"
    SWIMMING = "SWIMMING"
    FAST_SWIMMING = "FAST_SWIMMING"
    NO_MOTION = "NO_MOTION"
    UNKNOWN = "UNKNOWN"


class GasState(str, Enum):
    """
    Interpreted gas state based on tank pressure and pressure drop rate.
    """

    NORMAL = "NORMAL"
    LOW = "LOW"
    CRITICAL = "CRITICAL"
    DROPPING_FAST = "DROPPING_FAST"
    UNKNOWN = "UNKNOWN"


class LinkState(str, Enum):
    """
    Interpreted quality of the communication link with the diver wearable.
    """

    LINK_OK = "LINK_OK"
    LINK_WEAK = "LINK_WEAK"
    LINK_LOST = "LINK_LOST"
    UNKNOWN = "UNKNOWN"


class DiverState(BaseModel):
    """
    Interpreted local state of the diver.

    This model is part of the shared protocol because it is included in the
    DiverSafetyPacket produced by the wearable and consumed by the robot.

    It does not contain raw wearable sensor packets or preprocessing-only
    fields. It represents the interpreted condition of the diver at one sample.
    """

    diver_id: str = Field(min_length=1)
    sample_index: int = Field(ge=0)
    elapsed_time_s: float = Field(ge=0)
    produced_at_utc: datetime

    depth_m: float = Field(ge=0)
    tank_pressure_bar: float | None = Field(default=None, ge=0)
    battery_pct: float | None = Field(default=None, ge=0, le=100)

    ascent_rate_m_min: float | None = None
    gas_rate_bar_min: float | None = None

    emergency_button_pressed: bool
    ack_button_pressed: bool

    dive_phase: DivePhase
    motion_state: MotionState
    gas_state: GasState
    link_state: LinkState

    @field_validator("produced_at_utc")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        """
        Ensure protocol timestamps include timezone information.
        """

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("produced_at_utc must be timezone-aware")

        return value


class AlarmSeverity(str, Enum):
    """
    Severity level of a single alarm event.
    """

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class SafetyState(str, Enum):
    """
    Overall safety state of a DiverSafetyPacket.

    This value is calculated from all AlarmEvent severities by the wearable
    alarm engine.
    """

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class AlarmEvent(BaseModel):
    """
    One safety-relevant event detected by the wearable alarm engine.

    The code identifies the alarm type, severity describes its importance,
    message is human-readable, and recommended_action gives downstream systems
    a suggested response.
    """

    code: str = Field(min_length=1)
    severity: AlarmSeverity
    message: str = Field(min_length=1)
    recommended_action: str | None = None


class DiverSafetyPacket(BaseModel):
    """
    Final wearable-side safety output consumed by downstream modules.

    This packet is the communication boundary between the wearable module and
    robot-side decision logic. The wearable produces it after preprocessing,
    state estimation, and alarm evaluation. The robot consumes it to update
    diver tracking and choose high-level behaviour.
    """

    diver_id: str = Field(min_length=1)
    sample_index: int = Field(ge=0)
    elapsed_time_s: float = Field(ge=0)
    produced_at_utc: datetime

    # sequence_numer: int
    # sender_id: str
    # received_id: str
    # message_id: str

    safety_state: SafetyState
    alarms: list[AlarmEvent]

    diver_state: DiverState

    @field_validator("produced_at_utc")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        """
        Ensure protocol timestamps include timezone information.
        """

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("produced_at_utc must be timezone-aware")

        return value