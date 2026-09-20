"""
MAADT Telemetry & Digital Twin Schemas (v1.0)
Defines standardized data contracts for engine sensors, data quality states,
operating regimes, digital twin state vectors, fault diagnostics, and advisories.
Reference: overview.md Sections 7, 8, 9, 13, 20, 21, 24, 29, 39, 40.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SensorQuality(str, Enum):
    """Quality classification for each sensor signal (overview.md §9)."""
    VALID = "VALID"
    STALE = "STALE"
    MISSING = "MISSING"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    NOISY = "NOISY"
    SUSPECT = "SUSPECT"


class OperatingRegime(str, Enum):
    """Flight and engine operational regimes (overview.md §13)."""
    START = "START"
    WARM_UP = "WARM_UP"
    IDLE = "IDLE"
    TAXI = "TAXI"
    TAKEOFF = "TAKEOFF"
    CLIMB = "CLIMB"
    CRUISE = "CRUISE"
    LOITER = "LOITER"
    THROTTLE_TRANSIENT = "THROTTLE_TRANSIENT"
    DESCENT = "DESCENT"
    LANDING = "LANDING"
    SHUTDOWN = "SHUTDOWN"


class AlertSeverity(str, Enum):
    """Alert and diagnosis severity tiers (overview.md §40)."""
    INFO = "INFO"
    ADVISORY = "ADVISORY"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FaultType(str, Enum):
    """Supported fault classes for aero-piston engine (overview.md §20)."""
    MISFIRE = "misfire"
    INJECTOR_ABNORMALITY = "injector_abnormality"
    IGNITION_DEGRADATION = "ignition_degradation"
    LUBRICATION_ISSUE = "lubrication_issue"
    SENSOR_DRIFT = "sensor_drift"
    SENSOR_FAILURE = "sensor_failure"
    COMBUSTION_INSTABILITY = "combustion_instability"
    OVERHEATING = "overheating"
    ABNORMAL_VIBRATION = "abnormal_vibration"
    ELECTRICAL_ABNORMALITY = "electrical_abnormality"
    HEALTHY = "healthy"


class TelemetryPacket(BaseModel):
    """
    Standardized Telemetry Schema v1 (overview.md §7, §8).
    Captures primary engine, environmental, control, and data quality fields.
    """
    schema_version: str = Field(default="v1.0", description="Schema specification version")
    timestamp: float = Field(..., description="UNIX epoch timestamp in seconds")
    engine_id: str = Field(default="ENG-001", description="Unique propulsion unit identifier")
    mission_id: Optional[str] = Field(default="MIS-001", description="Active mission identifier")
    sequence_id: Optional[int] = Field(default=0, description="Monotonically increasing sequence number")

    # Primary Propulsion Parameters (§8)
    rpm: float = Field(..., description="Engine speed in Revolutions Per Minute")
    cht: float = Field(..., description="Cylinder Head Temperature in degrees Celsius")
    egt: float = Field(..., description="Exhaust Gas Temperature in degrees Celsius")
    oil_pressure: float = Field(..., description="Engine oil pressure in bar")
    oil_temperature: float = Field(..., description="Engine oil temperature in degrees Celsius")
    fuel_flow: float = Field(..., description="Instantaneous fuel flow in liters/hour")
    vibration: float = Field(..., description="Overall vibration amplitude in g (RMS)")
    battery_voltage: float = Field(default=28.0, description="Electrical bus voltage in Volts")
    alternator_current: float = Field(default=12.0, description="Alternator current output in Amperes")
    injection_timing: float = Field(default=22.0, description="Injection/ignition advance timing in degrees BTDC")

    # Environmental Parameters (§8, §15)
    altitude: float = Field(..., description="Barometric pressure altitude in meters")
    ambient_temperature: float = Field(default=25.0, description="Ambient air temperature in degrees Celsius")
    ambient_pressure: float = Field(default=101.3, description="Ambient barometric pressure in kPa")
    humidity: Optional[float] = Field(default=50.0, description="Relative humidity in percent")

    # Control Parameters (§8)
    throttle: float = Field(..., description="Commanded throttle position in percent (0.0 - 100.0)")
    mixture: Optional[float] = Field(default=1.0, description="Air-fuel mixture command ratio (lambda)")
    ecu_status: Optional[str] = Field(default="NORMAL", description="FADEC / ECU operational health code")

    # Data Quality Layer (§9)
    sensor_quality: Dict[str, SensorQuality] = Field(
        default_factory=dict,
        description="Per-sensor data quality classification"
    )
    sensor_trust: Dict[str, float] = Field(
        default_factory=dict,
        description="Dynamic trust score per sensor [0.0 - 1.0]"
    )


class PhysicsResiduals(BaseModel):
    """Discrepancy between physics-expected baseline and sensor observations (§17)."""
    egt_residual: float = Field(0.0, description="Observed EGT minus Expected EGT (°C)")
    cht_residual: float = Field(0.0, description="Observed CHT minus Expected CHT (°C)")
    rpm_residual: float = Field(0.0, description="Observed RPM minus Expected RPM")
    fuel_flow_residual: float = Field(0.0, description="Observed minus Expected Fuel Flow (L/h)")
    oil_temp_residual: float = Field(0.0, description="Observed minus Expected Oil Temperature (°C)")
    oil_pressure_residual: float = Field(0.0, description="Observed minus Expected Oil Pressure (bar)")


class AnomalyScoreDetails(BaseModel):
    """Composite and component anomaly metrics (§18, §19)."""
    composite_score: float = Field(0.0, description="Weighted composite anomaly score [0.0 - 1.0]")
    physics_score: float = Field(0.0, description="Physics residual contribution")
    statistical_score: float = Field(0.0, description="Z-score / rolling statistical deviation")
    ml_score: float = Field(0.0, description="Isolation forest / ML anomaly score")
    trend_score: float = Field(0.0, description="Temporal trajectory divergence score")
    is_out_of_distribution: bool = Field(False, description="Whether operating outside training distribution (§99)")


class SubsystemHealth(BaseModel):
    """Decomposed health status across engine subsystems (§23, §24)."""
    overall: float = Field(100.0, ge=0.0, le=100.0, description="Overall engine health index [0 - 100]")
    thermal: float = Field(100.0, ge=0.0, le=100.0, description="Thermal management health index")
    combustion: float = Field(100.0, ge=0.0, le=100.0, description="Combustion / injection health index")
    lubrication: float = Field(100.0, ge=0.0, le=100.0, description="Lubrication & oil circuit health index")
    vibration: float = Field(100.0, ge=0.0, le=100.0, description="Mechanical & vibration health index")
    electrical: float = Field(100.0, ge=0.0, le=100.0, description="Electrical & alternator health index")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in health estimation")


class RULPrediction(BaseModel):
    """Probabilistic Remaining Useful Life prediction (§26)."""
    estimate_hours: float = Field(..., description="Point estimate of RUL in operating hours")
    lower_bound: float = Field(..., description="10th percentile lower uncertainty bound")
    upper_bound: float = Field(..., description="90th percentile upper uncertainty bound")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Estimation confidence score")
    degradation_trend: str = Field(default="STABLE", description="STABLE | LINEAR | ACCELERATING | SUDDEN")


class DigitalTwinState(BaseModel):
    """
    Synchronized Virtual Engine State (overview.md §29, §101).
    Full internal state vector exposed to analytics, mission simulation, and HMI.
    """
    engine_id: str = Field(..., description="Target engine identifier")
    timestamp: float = Field(..., description="Timestamp of twin synchronization")
    operating_regime: OperatingRegime = Field(default=OperatingRegime.CRUISE)
    system_operational_state: str = Field(default="MONITORING", description="INITIALIZING|READY|MONITORING|DIAGNOSING")

    # Estimated True Mechanical State
    estimated_rpm: float = Field(...)
    estimated_load: float = Field(...)
    estimated_thermal_stress: float = Field(0.0)

    # Physics Residuals & Anomalies
    residuals: PhysicsResiduals = Field(default_factory=PhysicsResiduals)
    anomaly: AnomalyScoreDetails = Field(default_factory=AnomalyScoreDetails)

    # Health & Prognostics
    health: SubsystemHealth = Field(default_factory=SubsystemHealth)
    rul: Optional[RULPrediction] = Field(None)

    # Mission Survival Metric (§35)
    mission_margin: float = Field(100.0, ge=-100.0, le=100.0, description="Mission Survival Margin %")
    twin_confidence: float = Field(1.0, ge=0.0, le=1.0, description="Overall digital twin state confidence")


class FaultEvent(BaseModel):
    """Diagnostic fault event with physical evidence aggregation (overview.md §21, §22)."""
    timestamp: float = Field(...)
    engine_id: str = Field(...)
    fault_type: FaultType = Field(...)
    probability: float = Field(..., ge=0.0, le=1.0)
    severity: AlertSeverity = Field(...)
    subsystem: str = Field(...)
    evidence: List[str] = Field(default_factory=list, description="Physical explanations and deviations")
    sensor_trust_verified: bool = Field(True, description="True if verified not to be a pure sensor electrical fault")


class Advisory(BaseModel):
    """Explainable maintenance and operational advisory (overview.md §39)."""
    id: str = Field(...)
    timestamp: float = Field(...)
    severity: AlertSeverity = Field(...)
    subsystem: str = Field(...)
    potential_issue: str = Field(...)
    evidence: List[str] = Field(default_factory=list)
    current_health: float = Field(...)
    estimated_rul: Optional[str] = Field(None)
    recommended_action: str = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
