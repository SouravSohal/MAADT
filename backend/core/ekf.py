"""
Extended Kalman Filter (EKF) Sensor Fusion State Estimator.
Combines noisy telemetry measurements and reduced-order physics into a continuous,
filtered engine state vector with dynamic sensor trust gating.
Reference: overview.md Sections 10, 11, 12, 98.
"""

import numpy as np
from typing import Dict, Optional, Tuple

from schemas.telemetry import TelemetryPacket
from .physics_model import ExpectedEngineState


class ExtendedKalmanFilter:
    """
    Discrete-time Extended Kalman Filter for aero-piston engine state estimation.
    State vector: x = [RPM, EGT, CHT, OilTemp, OilPressure, FuelFlow]^T
    """

    STATE_DIM = 6
    MEAS_DIM = 6
    STATE_NAMES = ["rpm", "egt", "cht", "oil_temperature", "oil_pressure", "fuel_flow"]

    def __init__(self, dt: float = 0.5):
        self.dt = dt

        # State vector: [RPM, EGT, CHT, OilTemp, OilPressure, FuelFlow]
        self.x = np.array([2400.0, 680.0, 155.0, 90.0, 4.5, 18.0], dtype=np.float64)

        # State error covariance P
        self.P = np.diag([100.0, 25.0, 10.0, 5.0, 0.2, 1.0]).astype(np.float64)

        # Process noise covariance Q (mechanical physics uncertainty)
        self.Q = np.diag([40.0, 9.0, 2.0, 1.0, 0.05, 0.3]).astype(np.float64) * dt

        # Nominal measurement noise covariance R0 (sensor instrument precision)
        self.R0 = np.diag([25.0, 10.0, 2.0, 1.0, 0.04, 0.2]).astype(np.float64)

        # Measurement matrix H (direct observation of state variables)
        self.H = np.eye(self.MEAS_DIM, dtype=np.float64)

    def predict(self, expected: ExpectedEngineState):
        """
        Physics-driven state prediction step:
        x_k^- = x_{k-1} + alpha * (x_{expected} - x_{k-1})
        """
        target = np.array([
            expected.expected_rpm,
            expected.expected_egt,
            expected.expected_cht,
            expected.expected_oil_temperature,
            expected.expected_oil_pressure,
            expected.expected_fuel_flow,
        ], dtype=np.float64)

        # Relaxation factors based on component time constants
        alpha = np.array([0.35, 0.12, 0.03, 0.015, 0.25, 0.30], dtype=np.float64)
        
        # State transition: x_pred = x + alpha * (target - x)
        self.x = self.x + alpha * (target - self.x)

        # Jacobian F of transition function
        F = np.diag(1.0 - alpha)

        # Prior covariance: P^- = F * P * F^T + Q
        self.P = F @ self.P @ F.T + self.Q

    def update(self, packet: TelemetryPacket, sensor_trust: Optional[Dict[str, float]] = None) -> Tuple[np.ndarray, float]:
        """
        Measurement correction step with dynamic sensor trust scaling (§11).
        If a sensor's trust is degraded, its measurement noise variance R_i is scaled up,
        forcing the filter to rely on physics predictions rather than corrupted sensor signals.
        """
        z = np.array([
            packet.rpm,
            packet.egt,
            packet.cht,
            packet.oil_temperature,
            packet.oil_pressure,
            packet.fuel_flow,
        ], dtype=np.float64)

        # Scale measurement noise R by dynamic sensor trust scores: R_i = R0_i / max(0.01, trust^2)
        R = self.R0.copy()
        trust = sensor_trust or {}
        for i, name in enumerate(self.STATE_NAMES):
            t_score = trust.get(name, 1.0)
            t_safe = max(0.02, min(1.0, t_score))
            R[i, i] = self.R0[i, i] / (t_safe ** 2)

        # Innovation: y = z - H * x
        y = z - (self.H @ self.x)

        # Innovation covariance: S = H * P * H^T + R
        S = self.H @ self.P @ self.H.T + R

        # Kalman gain: K = P * H^T * inv(S)
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Posterior state: x = x + K * y
        self.x = self.x + (K @ y)

        # Posterior covariance: P = (I - K * H) * P
        I = np.eye(self.STATE_DIM)
        self.P = (I - (K @ self.H)) @ self.P

        # Calculate state estimation confidence score [0.0 - 1.0] (§98)
        # Lower covariance trace = higher confidence
        trace_p = float(np.trace(self.P))
        confidence = max(0.2, min(1.0, 1.0 / (1.0 + (trace_p / 150.0))))

        return self.x.copy(), round(confidence, 3)

    def get_estimated_state_dict(self) -> Dict[str, float]:
        """Returns the current filtered state as a key-value dictionary."""
        return {
            name: round(float(self.x[i]), 2)
            for i, name in enumerate(self.STATE_NAMES)
        }
