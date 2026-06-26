"""
Robot decision system for the autonomous diver companion prototype.

This module connects the robot-side tracker and behaviour planner into one
update loop. It receives optional DiverSafetyPacket objects from the wearable
side, updates the robot's latest known diver track, and produces a high-level
RobotDecision.

The robot system does not perform physical navigation, motor control, or
underwater communication. It only coordinates the current robot-side decision
logic.
"""

from __future__ import annotations

from autonomous_diver_companion.behaviour_planner import RobotBehaviorPlanner
from autonomous_diver_companion.schemas import RobotDecision
from autonomous_diver_companion.tracker import RobotDiverTracker, RobotTrackerConfig
from shared.shared_protocol import DiverSafetyPacket


class RobotSystem:
    """
    High-level robot-side decision coordinator.

    The system combines:
    - RobotDiverTracker: stores latest diver packet and checks freshness
    - RobotBehaviorPlanner: chooses the robot's high-level action

    This class represents one robot-side decision cycle.
    """

    def __init__(
        self,
        tracker_config: RobotTrackerConfig | None = None,
        tracker: RobotDiverTracker | None = None,
        behavior_planner: RobotBehaviorPlanner | None = None,
    ):
        """
        Initialize the robot decision system.

        Args:
            tracker_config: Optional configuration for packet freshness checks.
            tracker: Optional pre-built tracker instance, useful for tests.
            behavior_planner: Optional pre-built behaviour planner instance,
                useful for tests.
        """

        self.tracker = tracker or RobotDiverTracker(config=tracker_config)
        self.behavior_planner = behavior_planner or RobotBehaviorPlanner()

    def update(
        self,
        packet: DiverSafetyPacket | None,
        robot_elapsed_time_s: float,
    ) -> RobotDecision:
        """
        Run one robot-side decision cycle.

        Args:
            packet: Latest wearable safety packet, or None if no new packet
                arrived during this update cycle.
            robot_elapsed_time_s: Current robot simulation time in seconds.

        Returns:
            RobotDecision containing the updated diver track and selected
            high-level robot action.
        """

        track = self.tracker.update(
            packet=packet,
            robot_elapsed_time_s=robot_elapsed_time_s,
        )

        action = self.behavior_planner.plan(track)

        return RobotDecision(
            track=track,
            action=action,
        )

    def reset(self) -> None:
        """
        Reset robot-side memory.

        This should be called before starting a new robot simulation run.
        """

        self.tracker.reset()