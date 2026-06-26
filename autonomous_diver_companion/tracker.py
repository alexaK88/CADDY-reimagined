"""
Robot-side diver tracking.

The tracker stores the latest DiverSafetyPacket received from teh wearable and checks whether that information is still
fresh from the robot's point of view.
"""

from __future__ import annotations
from dataclasses import dataclass

from autonomous_diver_companion.schemas import DiverTrack
from shared.shared_protocol import DiverSafetyPacket


@dataclass(frozen=True)
class RobotTrackerConfig:
    """
    Configuration for robot-side packet freshness checks.
    """
    stale_packet_after_s: float = 10.0


class RobotDiverTracker:
    """
    Maintains robot's latest known information about the diver.

    The tracker accepts new wearable safety packets when available. If no new packet arrives, it keeps the latest known
    packet and updates its age. This allows the robot to detect stale diver information and switch to search
    or fallback behaviour.
    """

    def __init__(self, config: RobotTrackerConfig | None = None):
        """
        Initialise an empty diver tracker.
        """
        self.config = config or RobotTrackerConfig()
        self._latest_packet: DiverSafetyPacket | None = None
        self._packets_received: int = 0

        if self.config.stale_packet_after_s <= 0:
            raise ValueError("stale_packet_after_s must be positive")

    def update(self, packet: DiverSafetyPacket | None, robot_elapsed_time_s: float, ) -> DiverTrack:
        """
        Update the diver track with an optional new packet.

        Args:
            packet: New wearable safety packet, or None if no packet arrived
                during this robot update cycle.
            robot_elapsed_time_s: Current robot simulation time in seconds.

        Returns:
            DiverTrack containing the latest known packet and freshness status.
        """

        if robot_elapsed_time_s < 0:
            raise ValueError("robot_elapsed_time_s must be non-negative")

        if (
                packet is not None and self._latest_packet is not None and packet.elapsed_time_s <= self._latest_packet.elapsed_time_s):
            packet = None

        if packet is not None:
            self._latest_packet = packet
            self._packets_received += 1

        if self._latest_packet is None:
            return DiverTrack(latest_packet=None, packets_received=self._packets_received,
                last_packet_elapsed_time_s=None, packet_age_s=None, is_stale=True, )

        packet_age_s = robot_elapsed_time_s - self._latest_packet.elapsed_time_s

        if packet_age_s < 0:
            raise ValueError("robot_elapsed_time_s cannot be earlier than latest packet elapsed_time_s. "
                             f"robot_elapsed_time_s={robot_elapsed_time_s}, "
                             f"packet_elapsed_time_s={self._latest_packet.elapsed_time_s}")

        return DiverTrack(latest_packet=self._latest_packet, packets_received=self._packets_received,
            last_packet_elapsed_time_s=self._latest_packet.elapsed_time_s, packet_age_s=packet_age_s,
            is_stale=packet_age_s > self.config.stale_packet_after_s, )

    def reset(self) -> None:
        """
        Clear the latest known diver packet.

        This should be called before starting a new robot simulation run.
        """

        self._latest_packet = None
        self._packets_received = 0
