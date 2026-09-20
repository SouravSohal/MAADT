"""
4-Tier Composite Anomaly Detection Engine.
Combines Physics Residuals, Statistical Rolling Z-Scores, Isolation Forest ML,
and Temporal Trend Divergence into a calibrated composite anomaly score.
Reference: overview.md Sections 18, 19, 99.
"""

import math
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, List, Optional

from config.engine_config import EngineConfig
from schemas.telemetry import AnomalyScoreDetails, PhysicsResiduals, TelemetryPacket


class HybridAnomalyEngine:
    """
    Multi-source anomaly detector:
    Composite = w_phys * S_phys + w_stat * S_stat + w_ml * S_ml + w_trend * S_trend
    """

    FEATURE_KEYS = [
        "egt_residual",
        "cht_residual",
        "rpm_residual",
        "fuel_flow_residual",
        "oil_pressure_residual",
        "oil_temp_residual",
        "fuel_rpm_ratio",
        "vibration_variance",
    ]

    def __init__(self, config: EngineConfig):
        self.config = config
        self.weights = config.anomaly.weights
        self.thresholds = config.anomaly.thresholds

        # Multivariate Isolation Forest
        self.ml_model = IsolationForest(
            n_estimators=120,
            contamination=0.04,
            random_state=42,
            bootstrap=True
        )
        self._warmup_ml_model()

    def _warmup_ml_model(self):
        """Pre-fits the Isolation Forest on synthetic nominal healthy operating features."""
        np.random.seed(42)
        n_samples = 1500

        # Normal residual noise distributions under healthy cruise
        egt_res = np.random.normal(0.0, 3.0, n_samples)
        cht_res = np.random.normal(0.0, 1.2, n_samples)
        rpm_res = np.random.normal(0.0, 8.0, n_samples)
        fuel_res = np.random.normal(0.0, 0.25, n_samples)
        oil_p_res = np.random.normal(0.0, 0.08, n_samples)
        oil_t_res = np.random.normal(0.0, 0.6, n_samples)
        fuel_rpm = np.random.normal(7.8, 0.4, n_samples)
        vib_var = np.random.exponential(0.005, n_samples)

        X_train = np.column_stack([
            egt_res, cht_res, rpm_res, fuel_res,
            oil_p_res, oil_t_res, fuel_rpm, vib_var
        ])
        self.ml_model.fit(X_train)

    def evaluate(
        self,
        packet: TelemetryPacket,
        residuals: PhysicsResiduals,
        features: Dict[str, float]
    ) -> AnomalyScoreDetails:
        """
        Computes composite anomaly score and component breakdown (§18, §19).
        """
        # 1. Physics Residual Score (Normalized critical deviation)
        s_phys_egt = min(1.0, abs(residuals.egt_residual) / 50.0)
        s_phys_cht = min(1.0, abs(residuals.cht_residual) / 25.0)
        s_phys_fuel = min(1.0, abs(residuals.fuel_flow_residual) / 3.0)
        s_phys_oil_p = min(1.0, max(0.0, -residuals.oil_pressure_residual) / 1.5)
        s_phys_oil_t = min(1.0, abs(residuals.oil_temp_residual) / 20.0)

        # Max normalized deviation across critical thermodynamic circuits
        physics_score = round(max(s_phys_egt, s_phys_cht, s_phys_fuel, s_phys_oil_p, s_phys_oil_t), 3)

        # 2. Statistical Z-Score (Deviation from expected variance)
        # Compare current residual to nominal standard deviations
        z_egt = abs(residuals.egt_residual) / 3.0
        z_cht = abs(residuals.cht_residual) / 1.2
        z_oil_p = max(0.0, -residuals.oil_pressure_residual) / 0.08
        z_fuel = abs(residuals.fuel_flow_residual) / 0.25
        max_z = max(z_egt, z_cht, z_oil_p, z_fuel)
        # Convert Z-score to sigmoid probability: Z=3 gives ~0.5, Z=6 gives ~0.9
        statistical_score = round(1.0 / (1.0 + math.exp(-0.8 * (max_z - 3.0))), 3)

        # 3. Machine Learning Isolation Forest Score
        x_vec = np.array([[
            features.get("egt_residual", residuals.egt_residual),
            features.get("cht_residual", residuals.cht_residual),
            features.get("rpm_residual", residuals.rpm_residual),
            features.get("fuel_flow_residual", residuals.fuel_flow_residual),
            features.get("oil_pressure_residual", residuals.oil_pressure_residual),
            features.get("oil_temp_residual", residuals.oil_temp_residual),
            features.get("fuel_rpm_ratio", 7.8),
            features.get("vibration_variance", 0.005),
        ]], dtype=np.float64)

        raw_decision = self.ml_model.decision_function(x_vec)[0]
        # decision_function > 0 for nominal, < 0 for anomalous
        ml_score = round(max(0.0, min(1.0, 0.5 - (raw_decision * 4.0))), 3)

        # 4. Temporal Trend Score (§18)
        # Evaluates derivative persistence (e.g. rising EGT or falling oil pressure)
        egt_rate = max(0.0, features.get("egt_derivative", 0.0))
        cht_rate = max(0.0, features.get("cht_derivative", 0.0))
        oil_p_decay = max(0.0, -features.get("oil_p_derivative", 0.0))
        trend_intensity = (egt_rate / 8.0) + (cht_rate / 3.0) + (oil_p_decay / 0.5)
        trend_score = round(min(1.0, trend_intensity), 3)

        # 5. Out-of-Distribution (OOD) Check (§99)
        # Extreme flight envelope conditions (e.g. >28,000 ft or >50°C ambient)
        is_ood = packet.altitude > 8500.0 or packet.ambient_temperature > 48.0

        # 6. Weighted Composite Score (§19)
        composite = (
            self.weights.physics * physics_score +
            self.weights.statistical * statistical_score +
            self.weights.ml * ml_score +
            self.weights.trend * trend_score
        )
        composite_score = round(min(1.0, max(0.0, composite)), 3)

        return AnomalyScoreDetails(
            composite_score=composite_score,
            physics_score=physics_score,
            statistical_score=statistical_score,
            ml_score=ml_score,
            trend_score=trend_score,
            is_out_of_distribution=is_ood,
        )
