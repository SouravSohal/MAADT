"""
Phase 6 Unit Tests: Mission Intelligence & Counterfactual What-If Simulator.
Verifies multi-factor Mission Survival Margin calculations and forward
trajectory simulations across candidate operational branches (§34, §35, §79).
"""

import pytest
from config.loader import ConfigManager
from schemas.telemetry import TelemetryPacket, OperatingRegime
from mission import (
    MissionMarginCalculator,
    MissionMarginBreakdown,
    CounterfactualSimulator,
    ScenarioOutcome,
)


def test_mission_margin_calculator_nominal_and_degraded():
    """Verifies multi-factor margin calculations under nominal and stressed conditions (§35)."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    calculator = MissionMarginCalculator(config=cfg)

    # 1. Nominal cruise packet
    pkt_nominal = TelemetryPacket(
        timestamp=100.0,
        rpm=2400.0,
        cht=160.0,
        egt=710.0,
        oil_pressure=4.5,
        oil_temperature=90.0,
        fuel_flow=18.0,
        vibration=0.22,
        throttle=65.0,
        altitude=4000.0,
        ambient_temperature=12.0
    )

    margin_nom = calculator.compute_margin(
        current_health=98.0,
        packet=pkt_nominal,
        anomaly_score=0.05,
        planned_mission_hours_remaining=4.0,
        rul_hours=800.0,
        twin_confidence=0.96
    )

    assert margin_nom.composite_margin > 60.0
    assert margin_nom.thermal_margin > 60.0
    assert margin_nom.degradation_margin > 90.0
    assert not margin_nom.is_critical
    assert "SAFE" in margin_nom.recommendation

    # 2. Degraded & Overheating condition
    pkt_stressed = TelemetryPacket(
        timestamp=200.0,
        rpm=2750.0,
        cht=215.0,  # Warning threshold exceeded
        egt=840.0,
        oil_pressure=2.8,
        oil_temperature=118.0,
        fuel_flow=28.0,
        vibration=0.75,
        throttle=90.0,
        altitude=7500.0,
        ambient_temperature=28.0
    )

    margin_stressed = calculator.compute_margin(
        current_health=48.0,  # Below 50% overhaul threshold
        packet=pkt_stressed,
        anomaly_score=0.88,
        planned_mission_hours_remaining=4.0,
        rul_hours=12.0,
        twin_confidence=0.90
    )

    assert margin_stressed.composite_margin < 25.0
    assert margin_stressed.is_critical is True
    assert "ABORT" in margin_stressed.recommendation or "CAUTION" in margin_stressed.recommendation


def test_counterfactual_trajectory_projection():
    """Verifies forward thermodynamic ODE roll-out across time horizon (§34)."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    simulator = CounterfactualSimulator(config=cfg)

    current_pkt = TelemetryPacket(
        timestamp=500.0,
        rpm=2450.0,
        cht=165.0,
        egt=720.0,
        oil_pressure=4.4,
        oil_temperature=92.0,
        fuel_flow=18.5,
        vibration=0.25,
        throttle=65.0,
        altitude=4500.0
    )

    # Simulate 20 minutes with 10% lower throttle
    outcome = simulator.simulate_scenario(
        current_telemetry=current_pkt,
        current_health=95.0,
        target_throttle=55.0,
        target_altitude=4500.0,
        horizon_minutes=20.0,
        active_anomaly_score=0.10,
        time_step_sec=60.0
    )

    assert isinstance(outcome, ScenarioOutcome)
    assert len(outcome.trajectory) == 21  # 0 to 20 minutes inclusive
    assert outcome.trajectory[0].time_offset_min == 0.0
    assert outcome.trajectory[-1].time_offset_min == 20.0
    # Throttling down should keep final CHT and EGT within safe limits
    assert outcome.peak_cht < cfg.operating_limits.cht.warning_threshold
    assert outcome.peak_egt < cfg.operating_limits.egt.warning_threshold
    assert outcome.safety_verdict in ("OPTIMAL", "ACCEPTABLE")


def test_counterfactual_branch_comparison():
    """Verifies comparison across 4 candidate operational branches (§38, §79)."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    simulator = CounterfactualSimulator(config=cfg)

    current_pkt = TelemetryPacket(
        timestamp=1000.0,
        rpm=2600.0,
        cht=195.0,  # High CHT
        egt=790.0,
        oil_pressure=3.6,
        oil_temperature=108.0,
        fuel_flow=24.0,
        vibration=0.45,
        throttle=80.0,
        altitude=6000.0
    )

    branches = simulator.compare_operational_branches(
        current_telemetry=current_pkt,
        current_health=70.0,
        active_anomaly_score=0.65,
        horizon_minutes=30.0
    )

    assert len(branches) == 4
    branch_ids = [b.scenario_id for b in branches]
    assert "maintain" in branch_ids
    assert "throttle_down" in branch_ids
    assert "descend" in branch_ids
    assert "rtb" in branch_ids

    maintain_branch = next(b for b in branches if b.scenario_id == "maintain")
    throttle_branch = next(b for b in branches if b.scenario_id == "throttle_down")
    rtb_branch = next(b for b in branches if b.scenario_id == "rtb")

    # Derating power or RTB should provide higher survival margin than maintaining stressed condition
    assert throttle_branch.final_survival_margin > maintain_branch.final_survival_margin
    assert rtb_branch.final_survival_margin >= throttle_branch.final_survival_margin
