"""
Robot-side schemas for the automation diver companion prototype.

These models describe the robot's internal decision state. The robot consumers shared DiverSafetyPacket
messages from the wearable module, tracks the latest known diver information, and selects high-level
action intents.

The models in this file do not represent raw wearable data and do not control motors, thrusters,
or navigation.
"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field

from shared.shared_protocol import DiverSafetyPacket


class RobotMode(str, Enum):
    """
    High-level behaviour mode selected by the robot.
    """

    IDLE = "IDLE"
    MONITORING = "MONITORING"
    APPROACH_DIVER = "APPROACH_DIVER"
    GUIDE_DIVER = "GUIDE_DIVER"
    EMERGENCY_SUPPORT = "EMERGENCY_SUPPORT"
    SEARCH_LAST_KNOWN = "SEARCH_LAST_KNOWN"


class DiverTrack(BaseModel):
    """
    Robot-side memory of the latest known diver packet.

    The robot may not receive a fresh wearable packet at every update cycle. This model stores the latest known packet
    and marks whether that information is stale.
    """
    latest_packet: DiverSafetyPacket | None = None

    packets_received: int = Field(default=0, ge=0)
    last_packet_elapsed_time_s: float | None = Field(default=None, ge=0)
    packet_age_s: float | None = Field(default=None, ge=0)

    is_stale: bool = False


class RobotActionIntent(BaseModel):
    """
    High-level action selected by the robot.

    This does not directly command thrusters or motors. It describes the robot's intended
    behaviour at mission level.
    """
    mode: RobotMode
    reason: str = Field(min_length=1)

    priority: int = Field(ge=0, le=100)
    notify_surface: bool = False


class RobotDecision(BaseModel):
    """Full robot-side decision for one update cycle."""
    track: DiverTrack
    action: RobotActionIntent