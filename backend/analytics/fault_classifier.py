"""
Multi-Class Fault Classifier for Aero-Piston Engines.
Implements supervised physical signature matching and multi-class probability estimation
across all failure classes defined in overview.md Sections 20, 59.
"""

import math
from typing import Dict, List, Optional, Tuple

from schemas.telemetry import (
    FaultType,
    PhysicsResiduals,
    SensorQuality,
    TelemetryPacket,
)


class MultiClassFaultClassifier:
    """
    Evaluates physical residuals, temporal features, and sensor trust metrics
    to output a calibrated probability distribution over 11 fault classes.
    """

    ALL_CLASSES = [
        FaultType.HEALTHY,
        FaultType.INJECTOR_ABNORMALITY,
        FaultType.OVERHEATING,
        FaultType.MISFIRE,
        FaultType.LUBRICATION_ISSUE,
        FaultType.SENSOR_DRIFT,
        FaultType.SENSOR_FAILURE,
        FaultType.ABNORMAL_VIBRATION,
        FaultType.COMBUSTION_INSTABILITY,
        FaultType.IGNITION_DEGRADATION,
        FaultType.ELECTRICAL_ABNORMALITY,
    ]

    def classify(
        self,
        packet: TelemetryPacket,
        residuals: PhysicsResiduals,
        features: Dict[str, float]
    ) -> Tuple[FaultType, float, Dict[str, float]]:
        """
        Calculates likelihood scores for each fault hypothesis, normalizes via softmax,
        and returns (top_fault, top_probability, class_probabilities_dict).
        """
        scores: Dict[FaultType, float] = {ft: 0.05 for ft in self.ALL_CLASSES}

        # Extract primary physical features
        d_egt = residuals.egt_residual
        d_cht = residuals.cht_residual
        d_fuel = residuals.fuel_flow_residual
        d_oil_p = residuals.oil_pressure_residual
        d_oil_t = residuals.oil_temp_residual
        rpm_var = features.get("rpm_variance", 0.0)
        vib = packet.vibration
        v_bat = packet.battery_voltage

        # Average sensor trust and sensor qualities (§10, §11)
        trust_map = packet.sensor_trust or {}
        qualities = packet.sensor_quality or {}
        egt_trust = trust_map.get("egt", 1.0)
        cht_trust = trust_map.get("cht", 1.0)

        # 1. Check for Sensor Failure / Instrumentation Fault (§10)
        has_failed_sensor = any(
            q in (SensorQuality.MISSING, SensorQuality.OUT_OF_RANGE, SensorQuality.STALE)
            for q in qualities.values()
        )
        if has_failed_sensor:
            scores[FaultType.SENSOR_FAILURE] += 4.5

        # 2. Check for Sensor Drift (§10, §74 Scenario 6)
        # Signature: Large EGT residual BUT low EGT trust and CHT/Fuel Flow are completely normal!
        if abs(d_egt) > 35.0 and egt_trust < 0.85 and abs(d_cht) < 10.0 and abs(d_fuel) < 0.6:
            scores[FaultType.SENSOR_DRIFT] += 4.0
        elif abs(d_cht) > 20.0 and cht_trust < 0.85 and abs(d_egt) < 15.0:
            scores[FaultType.SENSOR_DRIFT] += 3.5

        # 3. Injector Abnormality (§20, §21): High fuel flow residual, elevated EGT, mild thermal imbalance
        if d_fuel > 0.8 and d_egt > 20.0:
            intensity = (d_fuel / 2.0) + (d_egt / 40.0)
            scores[FaultType.INJECTOR_ABNORMALITY] += min(5.0, 1.5 + intensity)

        # 4. Overheating (§20, §74 Scenario 2): CHT elevated significantly along with oil temperature
        if d_cht > 18.0 or d_oil_t > 15.0:
            intensity = (d_cht / 20.0) + (d_oil_t / 15.0)
            scores[FaultType.OVERHEATING] += min(5.0, 1.5 + intensity)

        # 5. Cylinder Misfire (§20, §74 Scenario 4): Elevated RPM variance, vibration spike, depressed/fluctuating EGT
        if (rpm_var > 60.0 or vib > 0.45) and d_egt < 10.0:
            intensity = (rpm_var / 120.0) + (vib / 0.5)
            scores[FaultType.MISFIRE] += min(5.0, 1.5 + intensity)

        # 6. Lubrication Issue (§20, §53): Oil pressure drop below nominal
        if d_oil_p < -0.6 or packet.oil_pressure < 3.0:
            intensity = abs(d_oil_p) / 1.0 + (max(0.0, 3.5 - packet.oil_pressure) / 1.0)
            scores[FaultType.LUBRICATION_ISSUE] += min(5.0, 1.8 + intensity)

        # 7. Abnormal Vibration (§20): Pure mechanical vibration without misfire RPM drop
        if vib > 0.60 and rpm_var < 50.0:
            scores[FaultType.ABNORMAL_VIBRATION] += min(5.0, 1.5 + (vib / 0.6))

        # 8. Combustion Instability (§20): Simultaneous RPM flutter and fuel variation
        if rpm_var > 40.0 and abs(d_fuel) > 0.6:
            scores[FaultType.COMBUSTION_INSTABILITY] += min(4.0, 1.2 + (rpm_var / 80.0))

        # 9. Electrical Abnormality (§20): Voltage sag
        if v_bat < 25.0:
            scores[FaultType.ELECTRICAL_ABNORMALITY] += min(5.0, 2.0 + (25.0 - v_bat))

        # 10. Healthy Baseline
        # If residuals and vibration are well within normal operating envelopes
        if (
            abs(d_egt) < 15.0 and
            abs(d_cht) < 10.0 and
            abs(d_fuel) < 0.5 and
            d_oil_p > -0.4 and
            vib < 0.38 and
            not has_failed_sensor
        ):
            scores[FaultType.HEALTHY] += 3.5

        # Compute Softmax Probabilities
        max_score = max(scores.values())
        exp_scores = {k: math.exp(v - max_score) for k, v in scores.items()}
        sum_exp = sum(exp_scores.values())
        probs = {k: round(v / sum_exp, 3) for k, v in exp_scores.items()}

        # Top hypothesis
        top_fault = max(probs.keys(), key=lambda k: probs[k])
        top_prob = probs[top_fault]

        # Convert keys to string representation for serialization
        str_probs = {k.value: v for k, v in probs.items()}

        return top_fault, top_prob, str_probs
