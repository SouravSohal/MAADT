"""
Probabilistic Remaining Useful Life (RUL) Engine.
Extrapolates degradation trajectories towards maintenance thresholds,
producing calibrated point estimates, uncertainty intervals, and confidence scores.
Reference: overview.md Sections 26, 27, 98.
"""

import math
import numpy as np
from typing import Optional, Tuple

from config.engine_config import EngineConfig
from schemas.telemetry import RULPrediction
from .degradation_tracker import DegradationMetrics
from .stress_index import MissionStressDetails


class ProbabilisticRULEngine:
    """
    Computes probabilistic Remaining Useful Life (RUL) predictions.
    Avoids deterministic scalar outputs by delivering confidence intervals [Lower, Upper]
    and estimation uncertainty based on sensor trust and mission stress.
    """

    MAINTENANCE_THRESHOLD: float = 50.0   # Health index requiring overhaul (§23)
    FAILURE_THRESHOLD: float = 20.0       # Imminent failure threshold (§23)

    def __init__(self, config: EngineConfig):
        self.config = config
        # Default nominal time between overhauls (TBO) for aero-piston engine (e.g. 1500 operating hours)
        self.nominal_tbo_hours: float = 1500.0

    def predict_rul(
        self,
        current_health: float,
        degradation: DegradationMetrics,
        stress: MissionStressDetails,
        sensor_confidence: float = 0.95
    ) -> RULPrediction:
        """
        Extrapolates the degradation curve to maintenance threshold and bounds uncertainty.
        """
        h_curr = max(0.0, min(100.0, current_health))
        delta_h_to_maint = max(0.0, h_curr - self.MAINTENANCE_THRESHOLD)

        # 1. Effective Degradation Rate (% / operating hour)
        # Base nominal degradation: 100% health decays over 1500 hours -> ~0.033% / hour
        base_rate = (100.0 - self.MAINTENANCE_THRESHOLD) / self.nominal_tbo_hours  # ~0.033%/h

        # Observed empirical slope from tracker (negative slope converted to positive decay rate)
        observed_rate = abs(degradation.health_slope_per_hour)

        # Stress-weighted degradation acceleration factor (§63)
        stress_factor = 1.0 + (1.8 * stress.overall)

        # Effective decay rate combining empirical slope and stress
        if observed_rate > 0.05:
            # When active degradation is observed, blend empirical and stress-adjusted rates
            effective_rate = 0.7 * observed_rate + 0.3 * (base_rate * stress_factor)
        else:
            # Baseline steady cruising
            effective_rate = base_rate * stress_factor

        # Guard against zero division
        effective_rate = max(0.02, effective_rate)

        # 2. Point Estimate: RUL to Maintenance Threshold (Hours)
        rul_hours = delta_h_to_maint / effective_rate

        # 3. Uncertainty Quantification & Prediction Intervals (§26)
        # Higher stress, accelerating degradation, and low sensor trust expand prediction interval
        uncertainty_pct = 0.15 + (0.25 * stress.overall)
        if degradation.is_accelerating:
            uncertainty_pct += 0.18
        if sensor_confidence < 0.8:
            uncertainty_pct += (0.8 - sensor_confidence) * 0.5

        lower_bound = max(0.0, rul_hours * (1.0 - uncertainty_pct))
        upper_bound = rul_hours * (1.0 + uncertainty_pct)

        # 4. Confidence Score (§26, §98)
        # Drops when degradation is erratic/accelerating or sensor trust is degraded
        base_confidence = sensor_confidence * 0.85
        if degradation.is_accelerating:
            base_confidence *= 0.75
        confidence = round(max(0.30, min(0.95, base_confidence)), 2)

        return RULPrediction(
            estimate_hours=round(rul_hours, 1),
            lower_bound=round(lower_bound, 1),
            upper_bound=round(upper_bound, 1),
            confidence=confidence,
            degradation_trend=degradation.degradation_trend,
        )
