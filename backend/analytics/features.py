"""
Feature Engineering Engine for Aero-Piston Propulsion Analytics.
Computes multi-window temporal statistics, derivatives, physics residual features,
non-dimensional engine ratios, and vibration metrics.
Reference: overview.md Section 57.
"""

from collections import deque
import math
import numpy as np
from typing import Deque, Dict, List, Optional

from schemas.telemetry import PhysicsResiduals, TelemetryPacket


class FeatureExtractor:
    """
    Extracts temporal and physical features from continuous telemetry streams.
    Maintains rolling memory over short (5s), medium (30s), and long (60s) windows.
    """

    def __init__(self, short_window: int = 10, med_window: int = 60):
        self.short_window = short_window  # 10 frames @ 0.5s = 5s
        self.med_window = med_window      # 60 frames @ 0.5s = 30s

        # Rolling buffers for parameters
        self._buffers: Dict[str, Deque[float]] = {
            "rpm": deque(maxlen=med_window),
            "egt": deque(maxlen=med_window),
            "cht": deque(maxlen=med_window),
            "oil_pressure": deque(maxlen=med_window),
            "oil_temperature": deque(maxlen=med_window),
            "fuel_flow": deque(maxlen=med_window),
            "vibration": deque(maxlen=med_window),
            "throttle": deque(maxlen=med_window),
            # Residual buffers
            "egt_res": deque(maxlen=med_window),
            "cht_res": deque(maxlen=med_window),
            "rpm_res": deque(maxlen=med_window),
            "fuel_res": deque(maxlen=med_window),
            "oil_p_res": deque(maxlen=med_window),
            "oil_t_res": deque(maxlen=med_window),
        }

    def update_and_extract(
        self,
        packet: TelemetryPacket,
        residuals: PhysicsResiduals,
        dt: float = 0.5
    ) -> Dict[str, float]:
        """
        Appends latest packet and residuals to rolling buffers and computes feature vector.
        """
        # Append latest observations
        self._buffers["rpm"].append(packet.rpm)
        self._buffers["egt"].append(packet.egt)
        self._buffers["cht"].append(packet.cht)
        self._buffers["oil_pressure"].append(packet.oil_pressure)
        self._buffers["oil_temperature"].append(packet.oil_temperature)
        self._buffers["fuel_flow"].append(packet.fuel_flow)
        self._buffers["vibration"].append(packet.vibration)
        self._buffers["throttle"].append(packet.throttle)

        # Append residuals
        self._buffers["egt_res"].append(residuals.egt_residual)
        self._buffers["cht_res"].append(residuals.cht_residual)
        self._buffers["rpm_res"].append(residuals.rpm_residual)
        self._buffers["fuel_res"].append(residuals.fuel_flow_residual)
        self._buffers["oil_p_res"].append(residuals.oil_pressure_residual)
        self._buffers["oil_t_res"].append(residuals.oil_temp_residual)

        features: Dict[str, float] = {}

        # 1. Instantaneous Physics Residual Features (§17)
        features["egt_residual"] = residuals.egt_residual
        features["cht_residual"] = residuals.cht_residual
        features["rpm_residual"] = residuals.rpm_residual
        features["fuel_flow_residual"] = residuals.fuel_flow_residual
        features["oil_pressure_residual"] = residuals.oil_pressure_residual
        features["oil_temp_residual"] = residuals.oil_temp_residual

        # 2. Non-dimensional Performance Ratios (§57)
        # Fuel-to-RPM ratio: L/h per 1000 RPM (indicates fueling efficiency)
        rpm_safe = max(500.0, packet.rpm)
        features["fuel_rpm_ratio"] = round((packet.fuel_flow / (rpm_safe / 1000.0)), 3)

        # Thermal ratio: EGT / CHT
        cht_safe = max(20.0, packet.cht)
        features["thermal_ratio"] = round(packet.egt / cht_safe, 3)

        # 3. Derivatives (dx/dt) over short window (5s)
        features["rpm_derivative"] = self._compute_derivative("rpm", dt)
        features["egt_derivative"] = self._compute_derivative("egt", dt)
        features["cht_derivative"] = self._compute_derivative("cht", dt)
        features["oil_p_derivative"] = self._compute_derivative("oil_pressure", dt)
        features["oil_t_derivative"] = self._compute_derivative("oil_temperature", dt)
        features["fuel_derivative"] = self._compute_derivative("fuel_flow", dt)

        # 4. Variances & Standard Deviations (detects misfires & combustion flutter)
        features["rpm_variance"] = self._compute_variance("rpm", self.short_window)
        features["egt_variance"] = self._compute_variance("egt", self.short_window)
        features["vibration_variance"] = self._compute_variance("vibration", self.short_window)

        # 5. Residual Moving Averages over medium window (30s)
        features["egt_res_mean_30s"] = self._compute_mean("egt_res", self.med_window)
        features["cht_res_mean_30s"] = self._compute_mean("cht_res", self.med_window)
        features["oil_p_res_mean_30s"] = self._compute_mean("oil_p_res", self.med_window)
        features["fuel_res_mean_30s"] = self._compute_mean("fuel_res", self.med_window)

        return features

    def _compute_derivative(self, key: str, dt: float) -> float:
        buf = self._buffers[key]
        if len(buf) < 2:
            return 0.0
        # Average derivative over the last 3-5 steps
        span = min(5, len(buf))
        diff = buf[-1] - buf[-span]
        time_span = max(dt, (span - 1) * dt)
        return round(diff / time_span, 3)

    def _compute_variance(self, key: str, window: int) -> float:
        buf = self._buffers[key]
        if len(buf) < 3:
            return 0.0
        vals = list(buf)[-window:]
        mean = sum(vals) / len(vals)
        var = sum((x - mean) ** 2 for x in vals) / len(vals)
        return round(var, 3)

    def _compute_mean(self, key: str, window: int) -> float:
        buf = self._buffers[key]
        if not buf:
            return 0.0
        vals = list(buf)[-window:]
        return round(sum(vals) / len(vals), 3)
