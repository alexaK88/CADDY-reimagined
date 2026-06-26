from datetime import datetime, timezone

from shared.shared_protocol import (AlarmEvent, AlarmSeverity, DivePhase, DiverSafetyPacket, DiverState, GasState, LinkState,
                             MotionState, SafetyState, )


def make_diver_state(elapsed_time_s: float = 0.0, sample_index: int = 0, ) -> DiverState:
    """
    Create a minimal valid DiverState for robot-side tests.
    """

    return DiverState(diver_id="diver_01", sample_index=sample_index, elapsed_time_s=elapsed_time_s,
        produced_at_utc=datetime.now(timezone.utc),

        depth_m=10.0, tank_pressure_bar=180.0, battery_pct=90.0,

        ascent_rate_m_min=0.0, gas_rate_bar_min=1.2,

        emergency_button_pressed=False, ack_button_pressed=False,

        dive_phase=DivePhase.AT_DEPTH, motion_state=MotionState.SWIMMING, gas_state=GasState.NORMAL,
        link_state=LinkState.LINK_OK, )


def make_safety_packet(safety_state: SafetyState = SafetyState.OK,
        elapsed_time_s: float = 0.0,
        sample_index: int = 0,
        alarm_code: str | None = None, ) -> DiverSafetyPacket:
    """
    Create a minimal valid DiverSafetyPacket for robot-side tests.
    """

    alarms = []

    if alarm_code is not None:
        alarms.append(AlarmEvent(code=alarm_code, severity=_severity_from_safety_state(safety_state),
            message=f"Test alarm: {alarm_code}", recommended_action="Test recommended action.", ))

    return DiverSafetyPacket(diver_id="diver_01", sample_index=sample_index, elapsed_time_s=elapsed_time_s,
        produced_at_utc=datetime.now(timezone.utc), safety_state=safety_state, alarms=alarms,
        diver_state=make_diver_state(elapsed_time_s=elapsed_time_s, sample_index=sample_index, ), )


def _severity_from_safety_state(safety_state: SafetyState) -> AlarmSeverity:
    """
    Convert packet-level SafetyState into a matching AlarmSeverity for tests.
    """

    if safety_state == SafetyState.EMERGENCY:
        return AlarmSeverity.EMERGENCY

    if safety_state == SafetyState.CRITICAL:
        return AlarmSeverity.CRITICAL

    if safety_state == SafetyState.WARNING:
        return AlarmSeverity.WARNING

    return AlarmSeverity.INFO
