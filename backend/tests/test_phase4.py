"""
Unit Tests for Phase 4: Feature Extraction, Composite Anomaly Engine,
Multi-Class Fault Classifier, and Explainable Diagnostics.
"""

import time
import pytest
from analytics.anomaly_engine import HybridAnomalyEngine
from analytics.explainability import DiagnosticExplainer
from analytics.fault_classifier import MultiClassFaultClassifier
from analytics.features import FeatureExtractor
from config.loader import ConfigManager
from schemas.telemetry import (
    AlertSeverity,
    FaultType,
    PhysicsResiduals,
    SensorQuality,
    TelemetryPacket,
)


def test_feature_extraction():
    """Verifies feature extraction, derivatives, variances, and ratios."""
    extractor = FeatureExtractor(short_window=5, med_window=15)
    packet = TelemetryPacket(
        timestamp=100.0,
        rpm=2500.0,
        cht=165.0,
        egt=710.0,
        oil_pressure=4.8,
        oil_temperature=92.0,
        fuel_flow=18.5,
        vibration=0.28,
        throttle=65.0,
        altitude=5000.0
    )
    residuals = PhysicsResiduals(
        egt_residual=12.0,
        cht_residual=3.0,
        rpm_residual=10.0,
        fuel_flow_residual=0.4,
        oil_temp_residual=2.0,
        oil_pressure_residual=0.1
    )

    feats = extractor.update_and_extract(packet, residuals, dt=0.5)
    assert "fuel_rpm_ratio" in feats
    assert feats["fuel_rpm_ratio"] > 5.0
    assert "thermal_ratio" in feats
    assert "egt_residual" in feats
    assert feats["egt_residual"] == 12.0


def test_composite_anomaly_engine_healthy_vs_faulted():
    """Verifies that composite anomaly score remains low on healthy data and rises on severe residuals."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    engine = HybridAnomalyEngine(config=cfg)
    extractor = FeatureExtractor()

    # 1. Healthy baseline
    pkt_healthy = TelemetryPacket(
        timestamp=100.0,
        rpm=2450.0,
        cht=160.0,
        egt=680.0,
        oil_pressure=4.7,
        oil_temperature=90.0,
        fuel_flow=18.0,
        vibration=0.22,
        throttle=65.0,
        altitude=4000.0
    )
    res_healthy = PhysicsResiduals(egt_residual=0.5, cht_residual=-0.2, fuel_flow_residual=0.05)
    feats_healthy = extractor.update_and_extract(pkt_healthy, res_healthy)
    anomaly_healthy = engine.evaluate(pkt_healthy, res_healthy, feats_healthy)

    assert anomaly_healthy.composite_score < 0.35
    assert not anomaly_healthy.is_out_of_distribution

    # 2. Severe overheating fault
    pkt_fault = TelemetryPacket(
        timestamp=105.0,
        rpm=2450.0,
        cht=215.0,
        egt=840.0,
        oil_pressure=4.0,
        oil_temperature=125.0,
        fuel_flow=18.0,
        vibration=0.32,
        throttle=65.0,
        altitude=4000.0
    )
    res_fault = PhysicsResiduals(egt_residual=55.0, cht_residual=32.0, oil_temp_residual=28.0)
    feats_fault = extractor.update_and_extract(pkt_fault, res_fault)
    anomaly_fault = engine.evaluate(pkt_fault, res_fault, feats_fault)

    assert anomaly_fault.composite_score > 0.55
    assert anomaly_fault.physics_score > 0.70


def test_multiclass_fault_classifier_identification():
    """Verifies classification accuracy across healthy, injector, and lubrication failure classes."""
    classifier = MultiClassFaultClassifier()

    # 1. Injector Abnormality
    pkt_inj = TelemetryPacket(
        timestamp=100.0,
        rpm=2450.0,
        cht=172.0,
        egt=735.0,
        oil_pressure=4.6,
        oil_temperature=92.0,
        fuel_flow=21.5,
        vibration=0.28,
        throttle=65.0,
        altitude=4000.0
    )
    res_inj = PhysicsResiduals(egt_residual=38.0, fuel_flow_residual=2.2)
    top_fault, prob, all_probs = classifier.classify(pkt_inj, res_inj, {"rpm_variance": 15.0})
    assert top_fault == FaultType.INJECTOR_ABNORMALITY
    assert prob > 0.40

    # 2. Lubrication Issue
    pkt_oil = TelemetryPacket(
        timestamp=101.0,
        rpm=2450.0,
        cht=165.0,
        egt=685.0,
        oil_pressure=2.1,  # Critical low
        oil_temperature=110.0,
        fuel_flow=18.0,
        vibration=0.30,
        throttle=65.0,
        altitude=4000.0
    )
    res_oil = PhysicsResiduals(oil_pressure_residual=-1.8, oil_temp_residual=14.0)
    top_fault_oil, prob_oil, _ = classifier.classify(pkt_oil, res_oil, {})
    assert top_fault_oil == FaultType.LUBRICATION_ISSUE
    assert prob_oil > 0.40


def test_sensor_drift_vs_engine_fault_isolation():
    """Verifies that large EGT residual with decaying sensor trust is classified as SENSOR_DRIFT."""
    classifier = MultiClassFaultClassifier()
    pkt_drift = TelemetryPacket(
        timestamp=102.0,
        rpm=2450.0,
        cht=160.0,  # Perfectly normal
        egt=765.0,  # Elevated due to electrical drift
        oil_pressure=4.7,
        oil_temperature=90.0,
        fuel_flow=18.0,  # Perfectly normal
        vibration=0.22,
        throttle=65.0,
        altitude=4000.0
    )
    pkt_drift.sensor_trust = {"egt": 0.40, "cht": 1.0, "rpm": 1.0}
    res_drift = PhysicsResiduals(egt_residual=45.0, cht_residual=0.0, fuel_flow_residual=0.0)

    top_fault, prob, _ = classifier.classify(pkt_drift, res_drift, {})
    assert top_fault == FaultType.SENSOR_DRIFT
    assert prob > 0.35


def test_explainable_diagnostics_evidence_generation():
    """Verifies that DiagnosticExplainer aggregates physical evidence bullets and creates an Advisory."""
    explainer = DiagnosticExplainer()
    pkt = TelemetryPacket(
        timestamp=1700000000.0,
        engine_id="ENG-001",
        rpm=2450.0,
        cht=170.0,
        egt=740.0,
        oil_pressure=4.6,
        oil_temperature=92.0,
        fuel_flow=21.2,
        vibration=0.28,
        throttle=65.0,
        altitude=5000.0
    )
    residuals = PhysicsResiduals(egt_residual=34.0, fuel_flow_residual=1.8)
    features = {"fuel_rpm_ratio": 8.65}

    fault_event, advisory = explainer.generate_explanation(
        fault_type=FaultType.INJECTOR_ABNORMALITY,
        probability=0.88,
        packet=pkt,
        residuals=residuals,
        features=features,
        health_index=84.5
    )

    assert fault_event.fault_type == FaultType.INJECTOR_ABNORMALITY
    assert fault_event.subsystem == "Combustion / Fuel"
    assert len(fault_event.evidence) >= 2
    # Ensure evidence mentions physical fuel or EGT metrics
    assert any("Fuel flow deviation" in e or "EGT residual" in e for e in fault_event.evidence)

    assert advisory is not None
    assert advisory.severity in (AlertSeverity.HIGH, AlertSeverity.WARNING)
    assert "injector" in advisory.recommended_action.lower()
