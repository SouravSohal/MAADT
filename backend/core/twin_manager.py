"""
Digital Twin State Manager.
Orchestrates Physics Model, EKF State Estimator, Residual Generation,
Subsystem Health Decomposition, and History Synchronization.
Reference: overview.md Sections 29, 30, 93, 101.
"""

from collections import deque
import time
from typing import Deque, Dict, List, Optional

from config.engine_config import EngineConfig
from schemas.telemetry import (
    AnomalyScoreDetails,
    DigitalTwinState,
    OperatingRegime,
    PhysicsResiduals,
    RULPrediction,
    SubsystemHealth,
    TelemetryPacket,
)
from .ekf import ExtendedKalmanFilter
from .physics_model import AeroPistonPhysicsModel, ExpectedEngineState


class DigitalTwinManager:
    """
    Maintains the synchronized virtual engine representation (§29, §30).
    Integrates physics-expected models with EKF sensor fusion and retains
    a rolling window of historical twin states for trend and replay analysis.
    """

    def __init__(
        self,
        config: EngineConfig,
        engine_id: str = "ENG-001",
        history_maxlen: int = 1000
    ):
        self.config = config
        self.engine_id = engine_id
        self.physics = AeroPistonPhysicsModel(config=config)
        self.ekf = ExtendedKalmanFilter(dt=0.5)

        # Active Twin State
        self.current_state: Optional[DigitalTwinState] = None
        self.current_expected: Optional[ExpectedEngineState] = None
        self.current_residuals: Optional[PhysicsResiduals] = None

        # Rolling state history (§30)
        self.history: Deque[DigitalTwinState] = deque(maxlen=history_maxlen)

        # Baseline health tracking parameters
        self.overall_health: float = 100.0
        self.degradation_rate: float = 0.001

    def synchronize(
        self,
        telemetry: TelemetryPacket,
        operating_regime: OperatingRegime = OperatingRegime.CRUISE,
        anomaly_score: float = 0.0,
        mission_margin: float = 100.0,
        rul: Optional[RULPrediction] = None,
        dt: float = 0.5
    ) -> DigitalTwinState:
        """
        Main synchronization loop (§30):
        1. Calculates expected thermodynamic state from reduced-order physics.
        2. Steps EKF with physics prediction and sensor-trust-gated innovation.
        3. Generates physics residuals (Delta = Obs - Exp).
        4. Decomposes subsystem health (Thermal, Combustion, Lubrication, Vibration, Electrical).
        5. Builds and archives synchronized DigitalTwinState.
        """
        # 1. Physics Expected Baseline
        self.current_expected = self.physics.calculate_expected_state(
            throttle_pct=telemetry.throttle,
            altitude_m=telemetry.altitude,
            ambient_temp_c=telemetry.ambient_temperature
        )

        # 2. Physics Residuals (§17)
        self.current_residuals = self.physics.calculate_residuals(
            telemetry=telemetry,
            expected=self.current_expected
        )

        # 3. Extended Kalman Filter Estimation (§12)
        self.ekf.predict(expected=self.current_expected)
        estimated_vec, ekf_confidence = self.ekf.update(
            packet=telemetry,
            sensor_trust=telemetry.sensor_trust
        )
        est = self.ekf.get_estimated_state_dict()

        # 4. Decompose Subsystem Health Index (§23, §24)
        weights = self.config.subsystem_health_weights
        
        # Subsystem stress penalties based on residuals and operational limits
        thermal_penalty = max(0.0, self.current_residuals.cht_residual * 0.45) + max(0.0, self.current_residuals.egt_residual * 0.25)
        combustion_penalty = abs(self.current_residuals.fuel_flow_residual) * 2.2 + abs(self.current_residuals.rpm_residual) * 0.04
        lubrication_penalty = max(0.0, -self.current_residuals.oil_pressure_residual) * 18.0 + max(0.0, self.current_residuals.oil_temp_residual) * 0.5
        vibration_penalty = max(0.0, telemetry.vibration - self.config.operating_limits.vibration.nominal_max) * 75.0
        electrical_penalty = max(0.0, 26.0 - telemetry.battery_voltage) * 15.0

        thermal_health = round(max(0.0, min(100.0, 100.0 - thermal_penalty)), 1)
        combustion_health = round(max(0.0, min(100.0, 100.0 - combustion_penalty)), 1)
        lubrication_health = round(max(0.0, min(100.0, 100.0 - lubrication_penalty)), 1)
        vibration_health = round(max(0.0, min(100.0, 100.0 - vibration_penalty)), 1)
        electrical_health = round(max(0.0, min(100.0, 100.0 - electrical_penalty)), 1)

        # Weighted aggregate health
        overall_health = round(
            weights.thermal * thermal_health +
            weights.combustion * combustion_health +
            weights.lubrication * lubrication_health +
            weights.vibration * vibration_health +
            weights.electrical * electrical_health,
            1
        )
        self.overall_health = overall_health

        # Average sensor trust as component of state confidence
        avg_sensor_trust = 1.0
        if telemetry.sensor_trust:
            avg_sensor_trust = sum(telemetry.sensor_trust.values()) / len(telemetry.sensor_trust)
        overall_confidence = round(0.5 * ekf_confidence + 0.5 * avg_sensor_trust, 2)

        # 5. Build DigitalTwinState (§29)
        twin_state = DigitalTwinState(
            engine_id=self.engine_id,
            timestamp=telemetry.timestamp,
            operating_regime=operating_regime,
            system_operational_state="MONITORING" if anomaly_score < 0.6 else "DIAGNOSING",
            estimated_rpm=est["rpm"],
            estimated_load=self.current_expected.expected_load,
            estimated_thermal_stress=round(min(1.0, max(0.0, (est["egt"] - 600) / 250)), 2),
            residuals=self.current_residuals,
            anomaly=AnomalyScoreDetails(
                composite_score=round(anomaly_score, 3),
                physics_score=round(min(1.0, abs(self.current_residuals.egt_residual) / 60.0), 3),
                statistical_score=round(anomaly_score * 0.9, 3),
                ml_score=round(anomaly_score, 3),
                trend_score=round(min(1.0, (100.0 - overall_health) / 30.0), 3),
            ),
            health=SubsystemHealth(
                overall=overall_health,
                thermal=thermal_health,
                combustion=combustion_health,
                lubrication=lubrication_health,
                vibration=vibration_health,
                electrical=electrical_health,
                confidence=overall_confidence,
            ),
            rul=rul,
            mission_margin=round(mission_margin, 2),
            twin_confidence=overall_confidence,
        )

        self.current_state = twin_state
        self.history.append(twin_state)
        return twin_state

    def get_state(self) -> Optional[DigitalTwinState]:
        """Returns the current synchronized twin state."""
        return self.current_state

    def get_recent_history(self, limit: int = 50) -> List[DigitalTwinState]:
        """Returns the most recent N states from memory."""
        items = list(self.history)
        return items[-limit:]
