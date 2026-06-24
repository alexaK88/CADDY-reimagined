"""
Contract file of the simulator.

Shared data models for the diver wearable simulator.

This module defines the schemas used by all parts of the simulation pipeline.
The models describe the data as it moves from raw simulated sensor readings, through preprocessing
and state estimation, to the final safety packet produced by the alarm engine.

Schemas are implemented with Pydantic so that packet fields are validated when objects are created.
This helps us catch invalid simulator values early, such as negative depth, invalid battery
percentage, or timestamps without timezone information.
"""

from __future__ import annotations

from enum import Enum                    # -> for fixed scenario names
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator    #-> data validation


class ScenarioName(str, Enum):
    """
    Defines possible simulation scenarios.

    A scenario controls how the simulator generates raw wearable data. It is used only to drive
    simulated behaviour, such as low gas, weak link, fast ascent, or emergency button activation.
    It is not part of the final safety classification.

    Input to the simulator.
    """
    NORMAL = "normal"
    LOW_GAS = "low_gas"
    FAST_ASCENT = "fast_ascent"
    EMERGENCY_BUTTON = "emergency_button"
    NO_MOTION = "no_motion"
    WEAK_LINK = "weak_link"
    LOST_LINK = "lost_link"
    BATTERY_LOW = "battery_low"


class RawSensorValues(BaseModel):
    """
    Raw sensor and interaction values produced by the simulated wearable.

    This model contains only values that a diver wearable could directly measure or receive from
    the diver, such as depth, tank pressure, heading, motion intensity, battery level, button
    presses, and local communication quality.

    It does not contain metadata, calculated rates, interpreted diver states, or alarms.
    """
    depth_m: float = Field(ge=0, description="Diver depth in meters. Zero means surface level.")
    tank_pressure_bar: float = Field(default=None, ge=0, description="Pressure in the tank.")
    heading_deg: float | None = Field(default=None, ge=0, lt=360, description="Compass heading in degrees.")
    motion_intensity: float = Field(default=None, ge=0, le=1, description="IMU motion data.")
    battery_pct: float = Field(default=None, ge=0, le=100, description="Battery percentage.")
    link_quality: float = Field(default=None, ge=0, le=1, description="Communication quality.")

    # Diver interaction with wearable unit
    # - emergency button -> Diver sends SOS signal
    # - acknowledged button -> Diver explicitly acknowledges receiving data
    emergency_button_pressed: bool = False
    ack_button_pressed: bool = False


class RawWearablePacket(BaseModel):
    """
    Full raw packet produced by the simulated diver wearable.

    This model combines packet metadata with the raw sensor values. It is the first complete message
    in the wearable-side pipeline and represents the data before preprocessing, rate calculation,
    state estimation, or alarm evaluation.

    RawWearablePacket
    ├── metadata
    │   ├── diver_id
    │   ├── sample_index
    │   ├── elapsed_time_s
    │   └── produced_at_utc
    └── values
        └── RawSensorValues
    """
    # Message metadata
    diver_id: str = Field(min_length=1)
    sample_index: int = Field(ge=0)
    elapsed_time_s: float = Field(ge=0)
    produced_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    values: RawSensorValues

    @field_validator("produced_at_utc")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        """
        Ensure packet timestamps include timezone information.

        The simulator uses UTC timestamps so that generated packets can later be logged,
        replayed, or compared across modules without ambiguous  local time.
        """
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("produced_at_utc must be timezone-aware")
        return value


class CleanSensorPacket(BaseModel):
    """
    Preprocessed wearable packet.

    This model is produced from a RawWearablePacket by the SignalPreprocessor.
    It contains the current sensor values in a flattened form and adds derived rates that require
    comparison with the previous sample.

    The preprocessor does not interpret the diver's condition and does not create alarms.
    It only prepares clean numerical signals for the state estimator.
    """
    produced_at_utc: datetime

    diver_id: str = Field(min_length=1)
    sample_index: int = Field(ge=0)
    elapsed_time_s: float = Field(ge=0)

    depth_m: float = Field(ge=0)
    tank_pressure_bar: float | None = Field(default=None, ge=0)
    heading_deg: float | None = Field(default=None, ge=0, lt=360)
    motion_intensity: float | None = Field(default=None, ge=0, le=1)
    battery_pct: float | None = Field(default=None, ge=0, le=100)
    link_quality: float | None = Field(default=None, ge=0, le=1)

    emergency_button_pressed: bool
    ack_button_pressed: bool

    ascent_rate_m_min: float | None
    gas_rate_bar_min: float | None

#-------------------------------------------------
# State Enums
#-------------------------------------------------

class DivePhase(str, Enum):
    """
    Interpreted vertical phase of the dive.

    This value is estimated from depth and ascent/descent rate. It describes what the diver appears
    to be doing vertically, but it does not by itself indicate whether the situation is safe
    or unsafe.
    """
    AT_SURFACE = "AT_SURFACE"
    DESCENDING = "DESCENDING"
    AT_DEPTH = "AT_DEPTH"
    ASCENDING = "ASCENDING"
    SAFETY_STOP = "SAFETY_STOP"
    UNKNOWN = "UNKNOWN"


class MotionState(str, Enum):
    """
    Interpreted motion state of the diver based on wearable motion intensity.
    """
    STILL = "STILL"                    # very low movement, but not impossible/no signal
    SWIMMING = "SWIMMING"
    FAST_SWIMMING = "FAST_SWIMMING"
    NO_MOTION = "NO_MOTION"            # prolonged or scenario-level abscence of motion
    UNKNOWN = "UNKNOWN"


class GasState(str, Enum):
    """
    Interpreted gas state based on tank pressure and has consumption rate.
    """
    NORMAL = "NORMAL"
    LOW = "LOW"
    CRITICAL = "CRITICAL"
    DROPPING_FAST = "DROPPING_FAST"
    UNKNOWN = "UNKNOWN"


class LinkState(str, Enum):
    """
    Interpreted quality of the communication link with the diver wearable.
    """
    LINK_OK = "LINK_OK"
    LINK_WEAK = "LINK_WEAK"
    LINK_LOST = "LINK_LOST"
    UNKNOWN = "UNKNOWN"

#-------------------------------------------------

class DiverState(BaseModel):
    """
    Interpreted local state of the diver after preprocessing.

    This model is produced by the DiverStateEstimator from a CleanSensorPacket.
    It keeps selected numerical values, such as depth and rates, and adds interpreted state
    categories such as dive phase, motion state, gas state, and link state.

    This is not yet a full alarm packet. It says what condition the diver appears to be in based on
    clean sensor data. The AlarmEngine decides whether that condition is safety-relevant.
    """

    diver_id: str
    sample_index: int
    elapsed_time_s: float
    produced_at_utc: datetime

    depth_m: float
    tank_pressure_bar: float | None
    battery_pct: float | None

    ascent_rate_m_min: float | None
    gas_rate_bar_min: float | None

    emergency_button_pressed: bool
    ack_button_pressed: bool

    dive_phase: DivePhase
    motion_state: MotionState
    gas_state: GasState
    link_state: LinkState

    heading_deg: float | None
    link_quality: float | None


class AlarmSeverity(str, Enum):
    """
    Severity level of a single alarm event.
    """
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class SafetyState(str, Enum):
    """
    Overall safety state of the full safety packet.

    This value is calculated from all AlarmEvent severities. It represents the highest
    severity in the packet.

    Output from the alarm engine.

    Example:
        alarms = [LOW_GAS WARNING, FAST_ASCENT CRITICAL]
        safety_state = CRITICAL
    """
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class AlarmEvent(BaseModel):
    """
    One safety-relevant event detected by the alarm engine.

    The code identifies the alarm type, while severity describes its impact.
    The message is intended for human-readable logs or dashboards, and the recommended action
    provides a first suggested response for downstream systems.
    """

    code: str
    severity: AlarmSeverity
    message: str
    recommended_action: str | None = None


class DiverSafetyPacket(BaseModel):
    """
    Final wearable-side safety output.
    This combines interpreted diver state with warnings/alarms.

    This model is produced by the AlarmEngine. It combines packet metadata, the interpreted
    DiverState, the overall SafetyState, and all AlarmEvent objects detected from the current sample.

    This packet is the current output boundary of the wearable module and can later be transmitted
    to the companion robot, surface gateway, backend, or dashboard.
    """

    diver_id: str
    sample_index: int
    elapsed_time_s: float
    produced_at_utc: datetime

    safety_state: SafetyState
    alarms: list[AlarmEvent]

    # Keep the full interpreted state attached for downstream modules.
    diver_state: DiverState
