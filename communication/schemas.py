"""
Communication-layer schemas for the autonomous diver companion prototype.

These models describe the result of transmitting wearable safety packets
through a simulated underwater communication link.

The communication layer does not inspect how the wearable produced the packet
and does not decide robot behaviour. It only models whether a packet was
delivered, dropped, delayed, or unavailable during a robot update cycle.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from shared.shared_protocol import DiverSafetyPacket


class CommunicationStatus(str, Enum):
    """
    Result status for one communication operation.
    """

    DELIVERED = "DELIVERED"
    DROPPED = "DROPPED"
    NO_PACKET_AVAILABLE = "NO_PACKET_AVAILABLE"


class CommunicationResult(BaseModel):
    """
    Result returned by the communication simulator.

    If status is DELIVERED, packet contains the delivered DiverSafetyPacket.
    If status is DROPPED or NO_PACKET_AVAILABLE, packet is None.

    Message metadata is included so delayed, dropped, duplicated, and
    out-of-order communication can be inspected and logged.
    """

    status: CommunicationStatus
    packet: DiverSafetyPacket | None = None

    message_id: str | None = None
    sequence_number: int | None = Field(default=None, ge=0)
    sender_id: str | None = None
    receiver_id: str | None = None

    sent_at_s: float | None = Field(default=None, ge=0)
    delivered_at_s: float | None = Field(default=None, ge=0)
    latency_s: float | None = Field(default=None, ge=0)

    reason: str


class CommunicationStats(BaseModel):
    """
    Cumulative communication statistics for one simulated link.
    """

    transmitted_count: int = Field(ge=0)
    delivered_count: int = Field(ge=0)
    dropped_count: int = Field(ge=0)
    queued_count: int = Field(ge=0)

    last_sequence_number: int | None = Field(default=None, ge=0)

    delivery_ratio: float = Field(ge=0, le=1)
    drop_ratio: float = Field(ge=0, le=1)