"""
Acoustic communication link simulator.

This module approximates an underwater acoustic link between the diver wearable
and companion robot. It does not simulate acoustic wave physics. Instead, it
models communication-level effects that matter for robot decisions:
packet loss, latency, jitter, missing updates, and message sequencing.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from uuid import uuid4

from communication.schemas import (
    CommunicationResult,
    CommunicationStats,
    CommunicationStatus,
)
from shared.shared_protocol import DiverSafetyPacket, LinkState


@dataclass(frozen=True)
class AcousticLinkConfig:
    """
    Configuration for the acoustic communication simulator.
    """

    sender_id: str = "wearable_01"
    receiver_id: str = "robot_01"

    base_latency_s: float = 1.0
    jitter_s: float = 2.0

    base_drop_probability: float = 0.05
    weak_link_drop_probability: float = 0.35
    lost_link_drop_probability: float = 0.95

    random_seed: int | None = 42


@dataclass
class _ScheduledPacket:
    """
    Internal packet scheduled for future delivery.
    """

    packet: DiverSafetyPacket
    message_id: str
    sequence_number: int
    sender_id: str
    receiver_id: str
    sent_at_s: float
    delivered_at_s: float


class AcousticLinkSimulator:
    """
    Simulates packet delivery over an underwater acoustic link.

    Packets can be dropped immediately or scheduled for delayed delivery.
    The robot calls receive() at its current time to retrieve the next packet
    whose delivery time has arrived.
    """

    def __init__(self, config: AcousticLinkConfig | None = None):
        self.config = config or AcousticLinkConfig()
        self._random = random.Random(self.config.random_seed)
        self._queue: list[_ScheduledPacket] = []

        self._next_sequence_number = 0
        self._transmitted_count = 0
        self._delivered_count = 0
        self._dropped_count = 0

        self._validate_config()

    def transmit(
        self,
        packet: DiverSafetyPacket,
        transmit_time_s: float,
    ) -> CommunicationResult:
        """
        Attempt to transmit one wearable safety packet.

        If the packet is dropped, it is not added to the delivery queue.
        If it is not dropped, it is scheduled for future delivery.
        """

        if transmit_time_s < 0:
            raise ValueError("transmit_time_s must be non-negative")

        sequence_number = self._next_sequence_number
        self._next_sequence_number += 1
        self._transmitted_count += 1

        message_id = str(uuid4())

        drop_probability = self._drop_probability_for_packet(packet)

        if self._random.random() < drop_probability:
            self._dropped_count += 1

            return CommunicationResult(
                status=CommunicationStatus.DROPPED,
                packet=None,
                message_id=message_id,
                sequence_number=sequence_number,
                sender_id=self.config.sender_id,
                receiver_id=self.config.receiver_id,
                sent_at_s=transmit_time_s,
                delivered_at_s=None,
                latency_s=None,
                reason="Packet dropped by simulated acoustic link.",
            )

        latency_s = self._calculate_latency_s()
        delivered_at_s = transmit_time_s + latency_s

        self._queue.append(
            _ScheduledPacket(
                packet=packet,
                message_id=message_id,
                sequence_number=sequence_number,
                sender_id=self.config.sender_id,
                receiver_id=self.config.receiver_id,
                sent_at_s=transmit_time_s,
                delivered_at_s=delivered_at_s,
            )
        )

        self._queue.sort(key=lambda item: item.delivered_at_s)

        return CommunicationResult(
            status=CommunicationStatus.NO_PACKET_AVAILABLE,
            packet=None,
            message_id=message_id,
            sequence_number=sequence_number,
            sender_id=self.config.sender_id,
            receiver_id=self.config.receiver_id,
            sent_at_s=transmit_time_s,
            delivered_at_s=delivered_at_s,
            latency_s=latency_s,
            reason="Packet scheduled for delayed acoustic delivery.",
        )

    def receive(self, robot_elapsed_time_s: float) -> CommunicationResult:
        """
        Receive the next packet that has arrived by robot_elapsed_time_s.

        Returns NO_PACKET_AVAILABLE if no scheduled packet is ready yet.
        """

        if robot_elapsed_time_s < 0:
            raise ValueError("robot_elapsed_time_s must be non-negative")

        if not self._queue:
            return CommunicationResult(
                status=CommunicationStatus.NO_PACKET_AVAILABLE,
                packet=None,
                reason="No packets are currently queued.",
            )

        next_packet = self._queue[0]

        if next_packet.delivered_at_s > robot_elapsed_time_s:
            return CommunicationResult(
                status=CommunicationStatus.NO_PACKET_AVAILABLE,
                packet=None,
                message_id=next_packet.message_id,
                sequence_number=next_packet.sequence_number,
                sender_id=next_packet.sender_id,
                receiver_id=next_packet.receiver_id,
                sent_at_s=next_packet.sent_at_s,
                delivered_at_s=next_packet.delivered_at_s,
                latency_s=next_packet.delivered_at_s - next_packet.sent_at_s,
                reason="Next packet has not arrived yet.",
            )

        delivered = self._queue.pop(0)
        self._delivered_count += 1

        return CommunicationResult(
            status=CommunicationStatus.DELIVERED,
            packet=delivered.packet,
            message_id=delivered.message_id,
            sequence_number=delivered.sequence_number,
            sender_id=delivered.sender_id,
            receiver_id=delivered.receiver_id,
            sent_at_s=delivered.sent_at_s,
            delivered_at_s=delivered.delivered_at_s,
            latency_s=delivered.delivered_at_s - delivered.sent_at_s,
            reason="Packet delivered by simulated acoustic link.",
        )

    def get_stats(self) -> CommunicationStats:
        """
        Return cumulative communication statistics for this link.
        """

        if self._transmitted_count == 0:
            delivery_ratio = 0.0
            drop_ratio = 0.0
            last_sequence_number = None
        else:
            delivery_ratio = self._delivered_count / self._transmitted_count
            drop_ratio = self._dropped_count / self._transmitted_count
            last_sequence_number = self._next_sequence_number - 1

        return CommunicationStats(
            transmitted_count=self._transmitted_count,
            delivered_count=self._delivered_count,
            dropped_count=self._dropped_count,
            queued_count=len(self._queue),
            last_sequence_number=last_sequence_number,
            delivery_ratio=delivery_ratio,
            drop_ratio=drop_ratio,
        )

    def reset(self) -> None:
        """
        Clear queued packets and reset communication counters.
        """

        self._queue.clear()
        self._next_sequence_number = 0
        self._transmitted_count = 0
        self._delivered_count = 0
        self._dropped_count = 0

    def _calculate_latency_s(self) -> float:
        """
        Calculate simulated acoustic latency.
        """

        return self.config.base_latency_s + self._random.uniform(
            0.0,
            self.config.jitter_s,
        )

    def _drop_probability_for_packet(self, packet: DiverSafetyPacket) -> float:
        """
        Choose packet drop probability from the wearable-reported link state.
        """

        link_state = packet.diver_state.link_state

        if link_state == LinkState.LINK_LOST:
            return self.config.lost_link_drop_probability

        if link_state == LinkState.LINK_WEAK:
            return self.config.weak_link_drop_probability

        return self.config.base_drop_probability

    def _validate_config(self) -> None:
        """
        Validate acoustic link configuration.
        """

        if not self.config.sender_id:
            raise ValueError("sender_id must not be empty")

        if not self.config.receiver_id:
            raise ValueError("receiver_id must not be empty")

        if self.config.base_latency_s < 0:
            raise ValueError("base_latency_s must be non-negative")

        if self.config.jitter_s < 0:
            raise ValueError("jitter_s must be non-negative")

        for name, value in (
            ("base_drop_probability", self.config.base_drop_probability),
            ("weak_link_drop_probability", self.config.weak_link_drop_probability),
            ("lost_link_drop_probability", self.config.lost_link_drop_probability),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")