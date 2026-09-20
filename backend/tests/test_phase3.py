"""
Unit Tests for Phase 3: Physics Model, EKF State Estimator & Digital Twin Manager.
"""

import time
import pytest
from config.loader import ConfigManager
from core.ekf import ExtendedKalmanFilter
from core.physics_model import AeroPistonPhysicsModel
from core.twin_manager import DigitalTwinManager
from schemas.telemetry import OperatingRegime, TelemetryPacket


def test_physics_model_calculations_and_residuals():
    """Verifies expected thermodynamic state calculation and residual generation."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    model = AeroPistonPhysicsModel(config=cfg)

    # Calculate expected state at cruise throttle 65% and 5500m
    expected = model.calculate_expected_state(throttle_pct=65.0, altitude_m=5500.0)
    assert 2200.0 <= expected.expected_rpm <= 2800.0
    assert 600.0 <= expected.expected_egt <= 750.0
    assert 140.0 <= expected.expected_cht <= 190.0
    assert expected.expected_fuel_flow > 10.0
    assert expected.expected_oil_pressure > 3.0

    # Synthetic observation with higher EGT (+35°C) and lower oil pressure (-1.0 bar)
    obs_packet = TelemetryPacket(
        timestamp=time.time(),
        rpm=expected.expected_rpm + 5.0,
        cht=expected.expected_cht + 2.0,
        egt=expected.expected_egt + 35.0,
        oil_pressure=expected.expected_oil_pressure - 1.0,
        oil_temperature=expected.expected_oil_temperature + 5.0,
        fuel_flow=expected.expected_fuel_flow + 1.2,
        vibration=0.28,
        throttle=65.0,
        altitude=5500.0
    )

    residuals = model.calculate_residuals(obs_packet, expected)
    assert residuals.egt_residual == 35.0
    assert residuals.oil_pressure_residual == -1.0
    assert residuals.fuel_flow_residual == 1.2


def test_ekf_state_estimation_and_sensor_trust_gating():
    """Verifies that low sensor trust prevents corrupted sensor readings from distorting the EKF state."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    model = AeroPistonPhysicsModel(config=cfg)
    ekf = ExtendedKalmanFilter(dt=0.5)

    expected = model.calculate_expected_state(throttle_pct=65.0, altitude_m=3000.0)

    # 1. Normal update with full trust
    normal_pkt = TelemetryPacket(
        timestamp=100.0,
        rpm=expected.expected_rpm,
        cht=expected.expected_cht,
        egt=expected.expected_egt,
        oil_pressure=expected.expected_oil_pressure,
        oil_temperature=expected.expected_oil_temperature,
        fuel_flow=expected.expected_fuel_flow,
        vibration=0.25,
        throttle=65.0,
        altitude=3000.0
    )
    ekf.predict(expected)
    state_vec, conf = ekf.update(normal_pkt, sensor_trust={"egt": 1.0})
    assert conf > 0.5

    # 2. Corrupted sensor spike with LOW sensor trust (e.g. sensor electrical fault)
    corrupted_pkt = TelemetryPacket(
        timestamp=100.5,
        rpm=expected.expected_rpm,
        cht=expected.expected_cht,
        egt=1200.0,  # Massive +500°C unphysical spike
        oil_pressure=expected.expected_oil_pressure,
        oil_temperature=expected.expected_oil_temperature,
        fuel_flow=expected.expected_fuel_flow,
        vibration=0.25,
        throttle=65.0,
        altitude=3000.0
    )
    ekf.predict(expected)
    # Give EGT a near-zero trust score
    corrupted_state, conf2 = ekf.update(corrupted_pkt, sensor_trust={"egt": 0.02})
    est = ekf.get_estimated_state_dict()

    # The estimated EGT should NOT be pulled up to 1200°C because trust gating rejected the measurement
    assert est["egt"] < 750.0


def test_digital_twin_manager_synchronization():
    """Verifies full Digital Twin State synchronization and subsystem health decomposition."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    manager = DigitalTwinManager(config=cfg, engine_id="ENG-TEST")

    # Packet with nominal healthy cruise readings
    pkt = TelemetryPacket(
        timestamp=1000.0,
        engine_id="ENG-TEST",
        rpm=2450.0,
        cht=165.0,
        egt=680.0,
        oil_pressure=4.6,
        oil_temperature=88.0,
        fuel_flow=18.2,
        vibration=0.25,
        throttle=65.0,
        altitude=4000.0,
        ambient_temperature=20.0
    )
    pkt.sensor_trust = {"rpm": 1.0, "egt": 1.0, "cht": 1.0, "oil_pressure": 1.0}

    twin_state = manager.synchronize(
        telemetry=pkt,
        operating_regime=OperatingRegime.CRUISE,
        anomaly_score=0.12,
        mission_margin=88.0
    )

    assert twin_state.engine_id == "ENG-TEST"
    assert twin_state.operating_regime == OperatingRegime.CRUISE
    assert twin_state.system_operational_state == "MONITORING"
    assert twin_state.health.overall > 85.0
    assert twin_state.residuals is not None

    # Verify history buffer retention (§30)
    history = manager.get_recent_history(limit=5)
    assert len(history) == 1
    assert history[0].timestamp == 1000.0
