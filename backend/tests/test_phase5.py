"""
Unit Tests for Phase 5: Mission Stress Index, Degradation Tracking & Probabilistic RUL.
"""

import pytest
from config.loader import ConfigManager
from prognostics import (
    DegradationTracker,
    MissionStressCalculator,
    ProbabilisticRULEngine,
)
from schemas.telemetry import OperatingRegime, TelemetryPacket


def test_mission_stress_calculator():
    """Verifies normalized stress computations across components and cumulative stress integration."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    calculator = MissionStressCalculator(config=cfg)

    # 1. Benign cruise packet
    pkt_cruise = TelemetryPacket(
        timestamp=100.0,
        rpm=2400.0,
        cht=160.0,
        egt=700.0,
        oil_pressure=4.5,
        oil_temperature=90.0,
        fuel_flow=18.0,
        vibration=0.22,
        throttle=65.0,
        altitude=4000.0
    )
    stress_cruise = calculator.compute_stress(pkt_cruise, regime=OperatingRegime.CRUISE, dt=0.5)
    assert 0.0 <= stress_cruise.thermal <= 0.5
    assert 0.0 <= stress_cruise.overall <= 0.6
    assert stress_cruise.cumulative_stress > 0.0

    # 2. High-stress takeoff packet (full throttle, elevated vibration, takeoff power)
    pkt_takeoff = TelemetryPacket(
        timestamp=100.5,
        rpm=3100.0,
        cht=200.0,
        egt=820.0,
        oil_pressure=5.2,
        oil_temperature=105.0,
        fuel_flow=30.0,
        vibration=0.45,
        throttle=100.0,
        altitude=50.0
    )
    stress_takeoff = calculator.compute_stress(pkt_takeoff, regime=OperatingRegime.TAKEOFF, dt=0.5)
    assert stress_takeoff.thermal > stress_cruise.thermal
    assert stress_takeoff.combustion > stress_cruise.combustion
    assert stress_takeoff.overall > stress_cruise.overall


def test_degradation_tracker_trends():
    """Verifies degradation slope, acceleration, and trend classification (STABLE, LINEAR, ACCELERATING, SUDDEN)."""
    tracker = DegradationTracker(window_size=30, baseline_health=100.0)

    # 1. Stable health
    for i in range(15):
        m = tracker.update(health_index=99.8 - (i * 0.001), sim_time_s=float(i * 10))
    assert m.degradation_trend in ("STABLE", "LINEAR")

    # 2. Linear progressive decay
    for i in range(15, 30):
        m = tracker.update(health_index=99.8 - ((i - 15) * 0.15), sim_time_s=float(i * 10))
    assert m.health_slope_per_hour < -0.1

    # 3. Sudden failure / catastrophic drop
    m_sudden = tracker.update(health_index=85.0, sim_time_s=310.0)
    assert m_sudden.degradation_trend in ("SUDDEN", "ACCELERATING")
    assert m_sudden.is_accelerating


def test_probabilistic_rul_engine():
    """Verifies that RUL produces calibrated prediction intervals [Lower, Upper] and confidence ratings."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    rul_engine = ProbabilisticRULEngine(config=cfg)
    stress_calc = MissionStressCalculator(config=cfg)
    tracker = DegradationTracker(baseline_health=100.0)

    # Simulate 20 steps of mild degradation
    pkt = TelemetryPacket(
        timestamp=100.0,
        rpm=2450.0,
        cht=165.0,
        egt=710.0,
        oil_pressure=4.6,
        oil_temperature=92.0,
        fuel_flow=18.5,
        vibration=0.25,
        throttle=65.0,
        altitude=4500.0
    )
    stress = stress_calc.compute_stress(pkt, dt=0.5)

    for i in range(25):
        h = 95.0 - (i * 0.02)
        deg_metrics = tracker.update(health_index=h, sim_time_s=float(i * 10))

    rul_pred = rul_engine.predict_rul(
        current_health=deg_metrics.current_health,
        degradation=deg_metrics,
        stress=stress,
        sensor_confidence=0.95
    )

    # Prediction interval checks (§26)
    assert rul_pred.estimate_hours > 0.0
    assert rul_pred.lower_bound < rul_pred.estimate_hours
    assert rul_pred.upper_bound > rul_pred.estimate_hours
    assert 0.50 <= rul_pred.confidence <= 1.0
    assert rul_pred.degradation_trend is not None
