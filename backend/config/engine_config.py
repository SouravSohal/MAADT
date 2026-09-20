"""
Typed configuration models for aero-piston engines, missions, and anomaly thresholds.
Reference: overview.md Sections 4.4, 19, 24, 52.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RPMOperatingLimits(BaseModel):
    min_idle: float = 1400.0
    nominal_cruise_min: float = 2200.0
    nominal_cruise_max: float = 2650.0
    max_continuous: float = 2800.0
    redline: float = 3200.0


class CHTOperatingLimits(BaseModel):
    min_operating: float = 60.0
    nominal_min: float = 135.0
    nominal_max: float = 185.0
    warning_threshold: float = 205.0
    redline: float = 230.0


class EGTOperatingLimits(BaseModel):
    nominal_min: float = 650.0
    nominal_max: float = 760.0
    warning_threshold: float = 820.0
    redline: float = 880.0


class OilPressureLimits(BaseModel):
    critical_low: float = 1.5
    warning_low: float = 2.5
    nominal_min: float = 3.8
    nominal_max: float = 5.2
    max_limit: float = 7.0


class OilTemperatureLimits(BaseModel):
    min_operating: float = 50.0
    nominal_min: float = 80.0
    nominal_max: float = 105.0
    warning_threshold: float = 120.0
    redline: float = 135.0


class FuelFlowLimits(BaseModel):
    min_idle: float = 3.5
    nominal_cruise: float = 18.5
    max_takeoff: float = 32.0


class VibrationLimits(BaseModel):
    nominal_max: float = 0.35
    warning_threshold: float = 0.65
    critical_limit: float = 1.20


class ElectricalLimits(BaseModel):
    min_limit: float = 24.0
    nominal: float = 28.0
    max_limit: float = 30.5


class AlternatorLimits(BaseModel):
    min_limit: float = 2.0
    nominal: float = 15.0
    max_limit: float = 45.0


class EngineOperatingLimits(BaseModel):
    rpm: RPMOperatingLimits = Field(default_factory=RPMOperatingLimits)
    cht: CHTOperatingLimits = Field(default_factory=CHTOperatingLimits)
    egt: EGTOperatingLimits = Field(default_factory=EGTOperatingLimits)
    oil_pressure: OilPressureLimits = Field(default_factory=OilPressureLimits)
    oil_temperature: OilTemperatureLimits = Field(default_factory=OilTemperatureLimits)
    fuel_flow: FuelFlowLimits = Field(default_factory=FuelFlowLimits)
    vibration: VibrationLimits = Field(default_factory=VibrationLimits)
    battery_voltage: ElectricalLimits = Field(default_factory=ElectricalLimits)
    alternator_current: AlternatorLimits = Field(default_factory=AlternatorLimits)


class PhysicsParameters(BaseModel):
    thermal_cht_time_constant_s: float = 45.0
    thermal_egt_time_constant_s: float = 6.0
    oil_thermal_time_constant_s: float = 90.0
    base_mechanical_efficiency: float = 0.38
    stoichiometric_afr: float = 14.7


class AnomalyWeights(BaseModel):
    physics: float = 0.40
    statistical: float = 0.15
    ml: float = 0.30
    trend: float = 0.15


class AnomalyThresholds(BaseModel):
    warning: float = 0.45
    critical: float = 0.70


class AnomalyConfig(BaseModel):
    weights: AnomalyWeights = Field(default_factory=AnomalyWeights)
    thresholds: AnomalyThresholds = Field(default_factory=AnomalyThresholds)


class SubsystemHealthWeights(BaseModel):
    combustion: float = 0.28
    thermal: float = 0.25
    lubrication: float = 0.22
    vibration: float = 0.15
    electrical: float = 0.10


class EngineConfig(BaseModel):
    name: str = "AeroPiston-4X"
    type: str = "aero-piston-turbocharged"
    cylinders: int = 4
    displacement_cc: float = 1352.0
    rated_power_hp: float = 115.0
    compression_ratio: float = 9.0
    operating_limits: EngineOperatingLimits = Field(default_factory=EngineOperatingLimits)
    physics_parameters: PhysicsParameters = Field(default_factory=PhysicsParameters)
    anomaly: AnomalyConfig = Field(default_factory=AnomalyConfig)
    subsystem_health_weights: SubsystemHealthWeights = Field(default_factory=SubsystemHealthWeights)


class MissionWaypoint(BaseModel):
    time_minutes: float
    target_altitude_m: float
    target_throttle_pct: float
    regime: str


class MissionConfig(BaseModel):
    id: str
    name: str
    description: str
    target_altitude_m: float
    duration_minutes: float
    ambient_temperature_c: float
    ambient_pressure_kpa: float
    waypoints: List[List] = Field(default_factory=list)
