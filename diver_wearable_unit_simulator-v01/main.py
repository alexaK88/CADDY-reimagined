from schemas import ScenarioName
from simulator import DiverWearableSimulator
from preprocessing import SignalPreprocessor
from state_estimator import DiverStateEstimator
from alarm_engine import AlarmEngine


simulator = DiverWearableSimulator(scenario=ScenarioName.WEAK_LINK)
preprocessor = SignalPreprocessor()
state_estimator = DiverStateEstimator()
alarm_engine = AlarmEngine()

for raw_packet in simulator.stream(samples=80):
    clean_packet = preprocessor.process(raw_packet)
    diver_state = state_estimator.estimate(clean_packet)
    safety_packet = alarm_engine.evaluate(diver_state)

    print(safety_packet.model_dump_json(indent=2))