"""
Phase 10 Unit Tests: Validation Benchmark Suite & Scenario Matrix (§74-§77).
Verifies the execution of all 10 operational benchmark scenarios,
computes Detection Lead Time (§76), Digital Twin Fidelity metrics (§77),
and Anomaly / Fault Classification accuracy (§75).
"""

import pytest
from validation.benchmark_suite import ValidationBenchmarkRunner, ScenarioResult


def test_scenario_matrix_definitions():
    """Verifies all 10 scenarios from overview.md §74 are defined with explicit expectations."""
    runner = ValidationBenchmarkRunner()
    scenarios = runner.get_scenario_definitions()
    assert len(scenarios) == 10
    names = [s["name"] for s in scenarios]
    assert "Healthy Cruise" in names
    assert "Gradual Overheating" in names
    assert "Injector Degradation" in names
    assert "Cylinder Misfire" in names
    assert "Oil Pressure Degradation" in names
    assert "Sensor Bias Drift" in names
    assert "High Altitude Operations" in names
    assert "Hot Weather Exposure" in names
    assert "Rapid Throttle Transients" in names
    assert "Electrical / Alternator Fault" in names


def test_scenario_healthy_cruise():
    """Verifies Scenario 1: Healthy cruise exhibits zero false alarms and high health (§74)."""
    runner = ValidationBenchmarkRunner()
    res = runner.run_single_scenario(scenario_id=1, steps=25)
    assert res.scenario_id == 1
    assert res.passed is True
    assert res.details["final_health_index"] >= 90.0
    assert res.classified_fault in ["healthy", "nominal"]


def test_scenario_gradual_overheating_lead_time():
    """Verifies Scenario 2: Overheating is detected with positive lead time (§74, §76)."""
    runner = ValidationBenchmarkRunner()
    res = runner.run_single_scenario(scenario_id=2, steps=30)
    assert res.scenario_id == 2
    assert res.anomaly_detected is True
    assert res.detection_lead_time_seconds > 0.0
    assert res.passed is True


def test_scenario_injector_degradation():
    """Verifies Scenario 3: Injector degradation is classified with high confidence (§74)."""
    runner = ValidationBenchmarkRunner()
    res = runner.run_single_scenario(scenario_id=3, steps=30)
    assert res.scenario_id == 3
    assert res.anomaly_detected is True
    assert res.passed is True
    assert res.classified_fault in ["injector_abnormality", "combustion_degradation"]


def test_run_full_validation_matrix():
    """
    Executes full 10-scenario benchmark matrix and checks fidelity criteria:
    Pass rate >= 90%, average detection lead time > 0, and fidelity score calculated (§74-§77).
    """
    runner = ValidationBenchmarkRunner()
    results = runner.run_all_scenarios(steps_per_scenario=20)
    assert results["status"] == "COMPLETED"
    assert results["total_scenarios"] == 10
    assert results["pass_rate_pct"] >= 90.0
    assert results["average_detection_lead_time_minutes"] > 0.0

    # Twin Fidelity criteria (§77)
    fid = results["overall_fidelity"]
    assert "egt_mae_degc" in fid
    assert "cht_mae_degc" in fid
    assert "fuel_mae_lh" in fid
    assert fid["fidelity_score_pct"] > 50.0
