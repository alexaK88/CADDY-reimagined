from alarm_engine import AlarmEngine
from preprocessing import SignalPreprocessor
from schemas import ScenarioName, SafetyState
from simulator import DiverWearableSimulator, SimulatorConfig
from state_estimator import DiverStateEstimator


def run_pipeline(scenario: ScenarioName,
        samples: int = 120,
        config: SimulatorConfig | None = None):
    simulator = DiverWearableSimulator(scenario=scenario, config=config)

    preprocessor = SignalPreprocessor()
    state_estimator = DiverStateEstimator()
    alarm_engine = AlarmEngine()

    safety_packets = []

    for raw_packet in simulator.stream(samples=samples):
        clean_packet = preprocessor.process(raw_packet)
        diver_state = state_estimator.estimate(clean_packet)
        safety_packet = alarm_engine.evaluate(diver_state)
        safety_packets.append(safety_packet)

    return safety_packets


def get_alarm_codes(safety_packets):
    return {alarm.code for packet in safety_packets for alarm in packet.alarms}


def test_normal_scenario_has_no_critical_alarms():
    config = SimulatorConfig(sample_interval_s=5.0, descent_duration_s=60.0,
        bottom_duration_s=120.0, normal_ascent_rate_m_min=6.0, normal_gas_rate_bar_min=1.2,
        random_seed=42)

    packets = run_pipeline(scenario=ScenarioName.NORMAL, samples=80, config=config)
    alarm_codes = get_alarm_codes(packets)

    assert "GAS_DROPPING_FAST" not in alarm_codes
    assert "FAST_ASCENT" not in alarm_codes
    assert all(packet.safety_state != SafetyState.CRITICAL for packet in packets)


def test_fast_ascent_scenario_triggers_fast_ascent_alarm():
    config = SimulatorConfig(sample_interval_s=5.0, descent_duration_s=60.0,
        bottom_duration_s=120.0, fast_ascent_rate_m_min=18.0, random_seed=42)

    packets = run_pipeline(scenario=ScenarioName.FAST_ASCENT, samples=80, config=config)
    alarm_codes = get_alarm_codes(packets)

    assert "FAST_ASCENT" in alarm_codes


def test_low_gas_scenario_triggers_gas_alarm():
    config = SimulatorConfig(sample_interval_s=10.0, descent_duration_s=60.0,
        bottom_duration_s=120.0, low_gas_start_pressure_bar=72.0, low_gas_rate_bar_min=2.5,
        random_seed=42)

    packets = run_pipeline(scenario=ScenarioName.LOW_GAS, samples=80, config=config)
    alarm_codes = get_alarm_codes(packets)

    assert "LOW_GAS" in alarm_codes or "CRITICAL_GAS" in alarm_codes


def test_weak_link_scenario_triggers_weak_link_alarm():
    packets = run_pipeline(scenario=ScenarioName.WEAK_LINK, samples=40)
    alarm_codes = get_alarm_codes(packets)

    assert "WEAK_LINK" in alarm_codes


def test_lost_link_scenario_triggers_lost_link_alarm():
    packets = run_pipeline(scenario=ScenarioName.LOST_LINK, samples=50)
    alarm_codes = get_alarm_codes(packets)

    assert "LINK_LOST" in alarm_codes


def test_emergency_button_scenario_triggers_emergency_alarm():
    packets = run_pipeline(scenario=ScenarioName.EMERGENCY_BUTTON, samples=40)
    alarm_codes = get_alarm_codes(packets)

    assert "DIVER_EMERGENCY_BUTTON" in alarm_codes
    assert any(packet.safety_state == SafetyState.EMERGENCY for packet in packets)
