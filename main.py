"""
Demo runner for the autonomous diver companion prototype.

This script connects the wearable-side simulator pipeline with the robot-side
decision system.

Flow:
    DiverWearableSimulator
        -> SignalPreprocessor
        -> DiverStateEstimator
        -> AlarmEngine
        -> DiverSafetyPacket
        -> RobotSystem
        -> RobotDecision
"""

from __future__ import annotations

from pathlib import Path

from mission_logging.mission_logger import MissionLogger

from diver_wearable_unit_simulator.alarm_engine import AlarmEngine
from diver_wearable_unit_simulator.preprocessing import SignalPreprocessor
from autonomous_diver_companion.robot_system import RobotSystem
from autonomous_diver_companion.tracker import RobotTrackerConfig
from diver_wearable_unit_simulator.schemas import ScenarioName
from diver_wearable_unit_simulator.simulator import DiverWearableSimulator, SimulatorConfig
from diver_wearable_unit_simulator.state_estimator import DiverStateEstimator
from diver_wearable_unit_simulator.utils.logger import setup_logging

from communication.acoustic_link import AcousticLinkConfig, AcousticLinkSimulator

from autonomous_diver_companion.report_builder import RobotReportBuilder
from surface_gateway_simulator.gateway import SurfaceGatewaySimulator
from mission_api_client import (MissionApiClient, MissionApiClientConfig, MissionApiClientError, )


def format_alarm_codes(alarm_codes: list[str]) -> str:
    """
    Format alarm codes for compact console output.
    """

    if not alarm_codes:
        return "-"

    return ", ".join(alarm_codes)


def run_demo(scenario: ScenarioName, samples: int = 80, ) -> None:
    """
    Run one end-to-end wearable-to-robot demo scenario.

    The wearable side produces DiverSafetyPacket objects. The robot side
    consumes those packets and chooses high-level RobotDecision outputs.
    """
    mission_logger = MissionLogger()
    mission_started = False

    mission_api_client = MissionApiClient(
        config=MissionApiClientConfig(base_url="http://127.0.0.1:8000", timeout_s=5.0, ))

    try:
        mission_api_client.health_check()

        mission_api_client.start_mission(scenario=scenario.value, mission_id=f"{scenario.value}_demo", )

        config = SimulatorConfig(sample_interval_s=5.0, descent_duration_s=60.0, bottom_duration_s=120.0,
                                 normal_ascent_rate_m_min=6.0, fast_ascent_rate_m_min=18.0, random_seed=42, )

        wearable_simulator = DiverWearableSimulator(scenario=scenario, config=config, )

        preprocessor = SignalPreprocessor()
        state_estimator = DiverStateEstimator()
        alarm_engine = AlarmEngine()

        robot = RobotSystem(tracker_config=RobotTrackerConfig(stale_packet_after_s=10.0, ))

        link = AcousticLinkSimulator(config=AcousticLinkConfig(base_latency_s=1.0, jitter_s=2.0, base_drop_probability=0.05,
                                                               weak_link_drop_probability=0.35,
                                                               lost_link_drop_probability=0.95, random_seed=42, ))

        report_builder = RobotReportBuilder(robot_id="robot_01")
        surface_gateway = SurfaceGatewaySimulator()

        print()
        print("=" * 90)
        print(f"Running scenario: {scenario.value}")
        print("=" * 90)
        print(f"{'t[s]':>6} | "
              f"{'safety':>10} | "
              f"{'alarms':<35} | "
              f"{'robot_mode':<20} | "
              f"reason")
        print("-" * 90)

        last_robot_time_s = 0.0

        for raw_packet in wearable_simulator.stream(samples=samples):
            clean_packet = preprocessor.process(raw_packet)
            diver_state = state_estimator.estimate(clean_packet)
            safety_packet = alarm_engine.evaluate(diver_state)

            transmit_result = link.transmit(packet=safety_packet, transmit_time_s=safety_packet.elapsed_time_s)
            received = link.receive(robot_elapsed_time_s=safety_packet.elapsed_time_s, )

            robot_decision = robot.update(packet=received.packet, robot_elapsed_time_s=safety_packet.elapsed_time_s, )

            robot_report = report_builder.build(decision=robot_decision,
                                                robot_elapsed_time_s=safety_packet.elapsed_time_s, )

            surface_state = surface_gateway.update(robot_report)

            alarm_codes = [alarm.code for alarm in safety_packet.alarms]

            mission_event = mission_logger.record_step(scenario=scenario.value, elapsed_time_s=safety_packet.elapsed_time_s,
                                                       wearable_packet=safety_packet, transmit_result=transmit_result,
                                                       receive_result=received, robot_decision=robot_decision,
                                                       surface_state=surface_state, )

            mission_api_client.publish_event(mission_event)

            mission_logger.record_step(scenario=scenario.value, elapsed_time_s=safety_packet.elapsed_time_s,
                                       wearable_packet=safety_packet, transmit_result=transmit_result,
                                       receive_result=received, robot_decision=robot_decision,
                                       surface_state=surface_state, )

            print(f"{safety_packet.elapsed_time_s:6.1f} | "
                  f"{safety_packet.safety_state.value:>10} | "
                  f"{format_alarm_codes(alarm_codes):<35} | "
                  f"{robot_decision.action.mode.value:<20} | "
                  f"{robot_decision.action.reason} |"
                  f"{surface_state.mission_state.value}")

            last_robot_time_s = safety_packet.elapsed_time_s

        print("-" * 90)
        print("Simulating missing wearable packets...")

        stale_decision = robot.update(packet=None, robot_elapsed_time_s=last_robot_time_s + 15.0, )

        robot_report = report_builder.build(decision=stale_decision, robot_elapsed_time_s=last_robot_time_s + 15.0, )

        surface_state = surface_gateway.update(robot_report)

        missing_packet_time_s = last_robot_time_s + 15.0

        mission_event = mission_logger.record_step(scenario=scenario.value, elapsed_time_s=missing_packet_time_s,
                                                   wearable_packet=None, transmit_result=None, receive_result=None,
                                                   robot_decision=stale_decision, surface_state=surface_state, )

        mission_api_client.publish_event(mission_event)

        mission_logger.record_step(scenario=scenario.value, elapsed_time_s=missing_packet_time_s, wearable_packet=None,
                                   transmit_result=None, receive_result=None, robot_decision=stale_decision,
                                   surface_state=surface_state, )

        print(f"{last_robot_time_s + 15.0:6.1f} | "
              f"{'NO PACKET':>10} | "
              f"{'-':<35} | "
              f"{stale_decision.action.mode.value:<20} | "
              f"{stale_decision.action.reason} |"
              f"{surface_state.mission_state.value}")

        print("=" * 90)
        print()

        log_path = mission_logger.export_text_log(Path("../mission_logs") / f"{scenario.value}_mission_log.log")
        print(f"Mission log saved to: {log_path}")

        mission_api_client.finish_mission()
    except Exception:
        if mission_started:
            try:
                mission_api_client.abort_mission()
            except MissionApiClientError:
                pass
        raise

    finally:
        mission_api_client.close()

    mission_summary_response = mission_api_client.get_summary()
    mission_summary = mission_summary_response["summary"]


if __name__ == "__main__":
    setup_logging()

    run_demo(scenario=ScenarioName.NORMAL, samples=80, )
    run_demo(scenario=ScenarioName.FAST_ASCENT, samples=80, )
    run_demo(scenario=ScenarioName.EMERGENCY_BUTTON, samples=40, )
