from __future__ import annotations

from enum import Enum                    # -> for fixed scenario names
from typing import Optional              # -> for missing values
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator    #-> data validation


class ScenarioName(str, Enum):
    """
    Defines possible simulation scenarios.
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
    One raw packet produced by the simulated diver wearable.

    This should represent the data that a real diver wearable could provide
    before state estimation and alarm logic are applied.
    """

    # Diver's depth (in meters)
    depth_m: float = Field(ge=0)

    # Tank pressure
    tank_pressure_bar: Optional[float] = Field(default=None, ge=0)

    # Compass heading in degrees
    heading_deg: Optional[float] = Field(default=None, ge=0, le=360)

    # IMU/Motion data
    motion_intensity: Optional[float] = Field(default=None, ge=0, le=1)

    # Battery percentage
    battery_pct: Optional[float] = Field(default=None, ge=0, le=100)

    # Diver interaction with wearable unit
    # - emergency button -> Diver sends SOS signal
    # - acknowledged button -> Diver explicitly acknowledges receiving data
    emergency_button_pressed: bool = False
    ack_button_pressed: bool = False

    # Communication quality
    link_quality: Optional[float] = Field(default=None, ge=0, le=1)


class RawWearablePacket(BaseModel):
    # Message metadata
    diver_id: str = Field(min_length=1)
    sample_index: int = Field(ge=0)
    elapsed_time_s: float = Field(ge=0)
    produced_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    values: RawSensorValues

    @field_validator("produced_at_utc")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return value


class CleanSensorPacket(BaseModel):
    """
    Validated values and Calculated Rates
    """
    diver_id: str
    produced_at_utc: datetime
    sample_index: int
    elapsed_time_s: float

    depth_m: float
    tank_pressure_bar: float | None
    heading_deg: float | None
    motion_intensity: float | None
    battery_pct: float | None
    emergency_button_pressed: bool
    ack_button_pressed: bool
    link_quality: float | None

    ascent_rate_m_min: float | None
    gas_rate_bar_min: float | None
