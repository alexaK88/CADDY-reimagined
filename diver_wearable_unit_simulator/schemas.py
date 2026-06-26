"""
Wearable-side data models for the diver wearable simulator.

This module defines schemas used internally by the wearable simulation
pipeline. These models represent raw simulated sensor values and preprocessed
sensor packets before they become shared safety protocol messages.

Shared output models such as DiverState and DiverSafetyPacket are defined in
shared.protocol because they are consumed by the robot module.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ScenarioName(str, Enum):
    """
    Supported wearable simulation scenarios.
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

    This model contains only values that a diver wearable could directly
    measure or receive from the diver. It does not contain metadata,
    calculated rates, interpreted states, or alarms.
    """

    depth_m: float = Field(ge=0)
    tank_pressure_bar: float | None = Field(default=None, ge=0)
    heading_deg: float | None = Field(default=None, ge=0, lt=360)
    motion_intensity: float | None = Field(default=None, ge=0, le=1)
    battery_pct: float | None = Field(default=None, ge=0, le=100)

    emergency_button_pressed: bool = False
    ack_button_pressed: bool = False

    link_quality: float | None = Field(default=None, ge=0, le=1)


class RawWearablePacket(BaseModel):
    """
    Full raw packet produced by the simulated diver wearable.

    This model combines packet metadata with raw sensor values before
    preprocessing, state estimation, or alarm evaluation.
    """

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
        """

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("produced_at_utc must be timezone-aware")

        return value


class CleanSensorPacket(BaseModel):
    """
    Preprocessed wearable packet.

    This model is produced from a RawWearablePacket by the SignalPreprocessor.
    It contains flattened sensor values and derived rates used by the state
    estimator.
    """

    diver_id: str = Field(min_length=1)
    produced_at_utc: datetime
    sample_index: int = Field(ge=0)
    elapsed_time_s: float = Field(ge=0)

    depth_m: float = Field(ge=0)
    tank_pressure_bar: float | None = Field(default=None, ge=0)
    heading_deg: float | None = Field(default=None, ge=0, lt=360)
    motion_intensity: float | None = Field(default=None, ge=0, le=1)
    battery_pct: float | None = Field(default=None, ge=0, le=100)

    emergency_button_pressed: bool
    ack_button_pressed: bool
    link_quality: float | None = Field(default=None, ge=0, le=1)

    ascent_rate_m_min: float | None
    gas_rate_bar_min: float | None

