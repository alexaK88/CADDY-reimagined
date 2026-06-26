"""
Mission event logger.

The MissionLogger records a structured timeline of the simulation. It does not
make safety decisions, robot decisions, or surface gateway decisions.

Its role is similar to a lightweight mission black box:
- what the wearable produced
- what the communication layer delivered
- what the robot decided
- what the surface gateway reported
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from communication.schemas import CommunicationResult
from mission_logging.schemas import MissionEvent
from autonomous_diver_companion.schemas import RobotDecision
from shared.shared_protocol import DiverSafetyPacket
from surface_gateway_simulator.gateway import SurfaceGatewayState


class MissionLogger:
    """
    Records structured mission events and exports them to disk.
    """

    def __init__(self):
        """
        Initialize an empty mission logger.
        """

        self._events: list[MissionEvent] = []

    @property
    def events(self) -> list[MissionEvent]:
        """
        Return a copy of recorded mission events.
        """

        return list(self._events)

    def record_step(self,
                    scenario: str,
                    elapsed_time_s: float,
                    wearable_packet: DiverSafetyPacket | None,
                    transmit_result: CommunicationResult | None,
                    receive_result: CommunicationResult | None,
                    robot_decision: RobotDecision,
                    surface_state: SurfaceGatewayState, ) -> MissionEvent:
        """
        Record one simulation step.

        Args:
            scenario: Current scenario name.
            elapsed_time_s: Current simulation time in seconds.
            wearable_packet: Current safety packet produced by the wearable, or
                None if no wearable packet was produced for this step.
            transmit_result: Result returned by the communication layer when
                transmitting the wearable packet, or None if no transmission
                occurred.
            receive_result: Result returned by the communication layer when
                receiving at the robot side, or None if no receive attempt
                occurred.
            robot_decision: Robot-side decision for this step.
            surface_state: Surface gateway state for this step.

        Returns:
            The MissionEvent that was recorded.
        """

        if not scenario:
            raise ValueError("scenario must not be empty")

        if elapsed_time_s < 0:
            raise ValueError("elapsed_time_s must be non-negative")

        wearable_safety_state = "NO_PACKET"
        wearable_alarm_codes: list[str] = []

        if wearable_packet is not None:
            wearable_safety_state = wearable_packet.safety_state.value
            wearable_alarm_codes = [alarm.code for alarm in wearable_packet.alarms]

        received_packet = None

        if receive_result is not None:
            received_packet = receive_result.packet

        received_safety_state = None
        received_alarm_codes: list[str] = []

        if received_packet is not None:
            received_safety_state = received_packet.safety_state.value
            received_alarm_codes = [alarm.code for alarm in received_packet.alarms]

        event = MissionEvent(event_index=len(self._events), recorded_at_utc=datetime.now(timezone.utc),

                             scenario=scenario, elapsed_time_s=elapsed_time_s,

                             wearable_safety_state=wearable_safety_state, wearable_alarm_codes=wearable_alarm_codes,

                             communication_transmit_status=(
                                 transmit_result.status.value if transmit_result is not None else None),
                             communication_receive_status=(
                                 receive_result.status.value if receive_result is not None else None),
                             communication_latency_s=(receive_result.latency_s if receive_result is not None else None),
                             communication_reason=(receive_result.reason if receive_result is not None else None),
                             communication_tx_sequence_number=(
                                 transmit_result.sequence_number if transmit_result is not None else None),
                             communication_rx_sequence_number=(
                                 receive_result.sequence_number if receive_result is not None else None),
                             communication_tx_message_id=(
                                 transmit_result.message_id if transmit_result is not None else None),
                             communication_rx_message_id=(
                                 receive_result.message_id if receive_result is not None else None),
                             communication_sender_id=(transmit_result.sender_id if transmit_result is not None else (
                                 receive_result.sender_id if receive_result is not None else None)),
                             communication_receiver_id=(
                                 transmit_result.receiver_id if transmit_result is not None else (
                                     receive_result.receiver_id if receive_result is not None else None)),
                             received_safety_state=received_safety_state, received_alarm_codes=received_alarm_codes,

                             robot_mode=robot_decision.action.mode.value, robot_reason=robot_decision.action.reason,
                             robot_priority=robot_decision.action.priority,
                             robot_notify_surface=robot_decision.action.notify_surface,

                             latest_diver_packet_age_s=robot_decision.track.packet_age_s,
                             diver_data_stale=robot_decision.track.is_stale,

                             surface_mission_state=surface_state.mission_state.value,
                             surface_alert_codes=[alert.code for alert in surface_state.alerts], )

        self._events.append(event)

        return event

    def export_jsonl(self, output_path: str | Path) -> Path:
        """
        Export recorded mission events as JSON Lines.

        JSONL is useful because each line is one complete event and list fields
        such as alarm codes and surface alerts are preserved cleanly.
        """

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            for event in self._events:
                file.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, ))
                file.write("\n")

        return path

    def export_pipe_log(self, output_path: str | Path) -> Path:
        """
        Export recorded mission events as a pipe-separated text log.

        This format is human-readable and compact. It is useful for quick mission
        inspection, demos, and simple timeline debugging.
        """

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        header = ("event_index | "
                  "time_s | "
                  "scenario | "
                  "wearable_safety | "
                  "wearable_alarms | "
                  "tx_status | "
                  "rx_status | "
                  "rx_safety | "
                  "rx_alarms | "
                  "robot_mode | "
                  "robot_priority | "
                  "notify_surface | "
                  "diver_data_stale | "
                  "surface_state | "
                  "surface_alerts | "
                  "robot_reason")

        with path.open("w", encoding="utf-8") as file:
            file.write(header)
            file.write("\n")

            for event in self._events:
                file.write(self._format_event_as_pipe_row(event))
                file.write("\n")

        return path

    def export_text_log(self, output_path: str | Path) -> Path:
        """
        Export recorded mission events as a human-readable text log.

        The format follows a standard operational logging style:

            YYYY-MM-DD HH:MM:SS,mmm - LEVEL - [component] message

        This is useful for mission review, debugging, and demo output.
        """

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            for event in self._events:
                file.write(self._format_event_as_log_line(event))
                file.write("\n")

        return path

    def _format_event_as_log_line(self, event: MissionEvent) -> str:
        """
        Convert one MissionEvent into one operational log line.
        """

        timestamp = self._format_timestamp(event.recorded_at_utc)
        level = self._level_for_event(event)

        message = (f"[{event.scenario}] "
                   f"t={event.elapsed_time_s:.1f}s "
                   f"wearable={event.wearable_safety_state} "
                   f"alarms={self._format_list(event.wearable_alarm_codes)} "
                   f"tx={self._safe_text(event.communication_transmit_status)} "
                   f"rx={self._safe_text(event.communication_receive_status)} "
                   f"tx_seq={self._safe_text(event.communication_tx_sequence_number)} "
                    f"rx_seq={self._safe_text(event.communication_rx_sequence_number)} "
                    f"sender={self._safe_text(event.communication_sender_id)} "
                    f"receiver={self._safe_text(event.communication_receiver_id)} "
                   f"received={self._safe_text(event.received_safety_state)} "
                   f"received_alarms={self._format_list(event.received_alarm_codes)} "
                   f"robot={event.robot_mode} "
                   f"priority={event.robot_priority} "
                   f"notify_surface={event.robot_notify_surface} "
                   f"diver_data_stale={event.diver_data_stale} "
                   f"surface={event.surface_mission_state} "
                   f"surface_alerts={self._format_list(event.surface_alert_codes)} "
                   f"reason={event.robot_reason}")

        return f"{timestamp} - {level} - [mission_logger] {message}"

    @staticmethod
    def _format_timestamp(value: datetime) -> str:
        """
        Format timestamp like standard Python logging output.

        Example:
            2026-06-25 16:13:40,158
        """

        return value.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

    @staticmethod
    def _level_for_event(event: MissionEvent) -> str:
        """
        Choose a log level based on mission severity.
        """

        if event.surface_mission_state == "EMERGENCY":
            return "ERROR"

        if event.surface_mission_state in {"DIVER_DATA_STALE", "ATTENTION_REQUIRED", }:
            return "WARNING"

        if event.communication_receive_status == "DROPPED":
            return "WARNING"

        if event.communication_transmit_status == "DROPPED":
            return "WARNING"

        return "INFO"

    @staticmethod
    def _format_list(values: list[str]) -> str:
        """
        Format list values compactly for log output.
        """

        if not values:
            return "-"

        return ",".join(values)

    @staticmethod
    def _safe_text(value: object) -> str:
        """
        Convert optional values into readable log-safe text.
        """

        if value is None:
            return "-"

        return str(value).replace("\n", " ")

    def _format_event_as_pipe_row(self, event: MissionEvent) -> str:
        """
        Convert one MissionEvent into a pipe-separated text row.
        """

        return " | ".join([str(event.event_index), f"{event.elapsed_time_s:.1f}", self._safe_text(event.scenario),
                           self._safe_text(event.wearable_safety_state), self._format_list(event.wearable_alarm_codes),
                           self._safe_text(event.communication_transmit_status),
                           self._safe_text(event.communication_receive_status),
                           self._safe_text(event.received_safety_state), self._format_list(event.received_alarm_codes),
                           self._safe_text(event.robot_mode), str(event.robot_priority),
                           str(event.robot_notify_surface), str(event.diver_data_stale),
                           self._safe_text(event.surface_mission_state), self._format_list(event.surface_alert_codes),
                           self._safe_text(event.robot_reason), ])

    def clear(self) -> None:
        """
        Clear all recorded events.
        """

        self._events.clear()
