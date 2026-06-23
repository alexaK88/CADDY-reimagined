from .schemas import ScenarioName
from .simulator import DiverWearableSimulator
from .preprocessing import SignalPreprocessor


simulator = DiverWearableSimulator(scenario=ScenarioName.NORMAL)
preprocessor = SignalPreprocessor()

for raw_packet in simulator.stream(samples=5):
    clean_packet = preprocessor.process(raw_packet)
    print(clean_packet.model_dump_json(indent=2))