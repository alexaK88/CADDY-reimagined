from schemas import ScenarioName
from simulator import DiverWearableSimulator, SimulatorConfig


def test_heading_is_always_in_valid_range():
    config = SimulatorConfig(initial_heading_deg=350.0, heading_sway_amplitude_deg=30.0,
        heading_noise_deg=5.0, random_seed=42, )

    simulator = DiverWearableSimulator(scenario=ScenarioName.NORMAL, config=config)

    for sample_index in range(200):
        packet = simulator.sample(sample_index)
        heading = packet.values.heading_deg

        assert 0.0 <= heading < 360.0


def test_heading_is_reproducible_with_same_seed():
    config = SimulatorConfig(random_seed=42)

    simulator_1 = DiverWearableSimulator(config=config)
    simulator_2 = DiverWearableSimulator(config=config)

    headings_1 = [simulator_1.sample(i).values.heading_deg for i in range(10)]
    headings_2 = [simulator_2.sample(i).values.heading_deg for i in range(10)]

    assert headings_1 == headings_2


def test_heading_can_be_constant_when_sway_and_noise_are_zero():
    config = SimulatorConfig(initial_heading_deg=130.0, heading_sway_amplitude_deg=0.0,
        heading_noise_deg=0.0, random_seed=42)

    simulator = DiverWearableSimulator(scenario=ScenarioName.NORMAL, config=config)
    headings = [simulator.sample(i).values.heading_deg for i in range(10)]

    assert headings == [130.0] * 10


def test_heading_wraps_above_360_degrees():
    config = SimulatorConfig(initial_heading_deg=370.0, heading_sway_amplitude_deg=0.0,
        heading_noise_deg=0.0, random_seed=42)

    simulator = DiverWearableSimulator(scenario=ScenarioName.NORMAL, config=config)
    packet = simulator.sample(0)

    assert packet.values.heading_deg == 10.0
