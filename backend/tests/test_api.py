"""
API Gateway Integration Tests.
Verifies REST endpoints for system health, engine configuration, mission profiles,
recent telemetry, twin states, residuals, simulation controls, and fault injection.
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_system_status():
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert data["active_engine"] == "AeroPiston-4X"
    assert "operating_regime" in data
    assert "twin_confidence" in data


def test_engine_config_endpoint():
    response = client.get("/api/v1/config/engine")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AeroPiston-4X"
    assert data["cylinders"] == 4
    assert "operating_limits" in data
    assert data["operating_limits"]["rpm"]["redline"] == 3200.0


def test_missions_catalog_endpoint():
    response = client.get("/api/v1/config/missions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    ids = [m["id"] for m in data]
    assert "MIS-ENDURANCE-01" in ids


def test_telemetry_recent_endpoint():
    response = client.get("/api/v1/telemetry/recent?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_twin_state_and_residuals_endpoints():
    """Verifies Digital Twin state vector and residuals endpoints."""
    resp_state = client.get("/api/v1/twin/state")
    assert resp_state.status_code == 200

    resp_res = client.get("/api/v1/twin/residuals")
    assert resp_res.status_code == 200

    resp_diag = client.get("/api/v1/diagnostics/active")
    assert resp_diag.status_code == 200
    data = resp_diag.json()
    assert "fault_type" in data
    assert "probability" in data
    assert "evidence" in data


def test_what_if_simulation_endpoint():
    payload = {"target_throttle": 80.0, "target_altitude": 6000.0}
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "simulated_margin" in data
    assert "recommendation" in data


def test_fault_injection_and_clearing_endpoints():
    """Verifies dynamic fault injection and clearing REST APIs."""
    inject_payload = {
        "fault_type": "injector_abnormality",
        "severity": 0.85,
        "progression": "INSTANT",
        "ramp_duration_seconds": 10.0
    }
    resp_inject = client.post("/api/v1/simulation/fault/inject", json=inject_payload)
    assert resp_inject.status_code == 200
    inj_data = resp_inject.json()
    assert inj_data["status"] == "INJECTED"
    assert "fault_id" in inj_data

    resp_list = client.get("/api/v1/simulation/faults")
    assert resp_list.status_code == 200
    list_data = resp_list.json()
    assert len(list_data["active_faults"]) >= 1

    resp_clear = client.post("/api/v1/simulation/fault/clear")
    assert resp_clear.status_code == 200
    assert resp_clear.json()["status"] == "CLEARED"


def test_simulation_control_endpoint():
    """Verifies manual override of throttle and altitude."""
    control_payload = {
        "mode": "MANUAL",
        "manual_throttle": 85.0,
        "manual_altitude": 6500.0
    }
    response = client.post("/api/v1/simulation/control", json=control_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UPDATED"
    assert data["control_state"]["mode"] == "MANUAL"
    assert data["control_state"]["manual_throttle"] == 85.0


def test_twin_rul_and_stress_endpoints():
    """Verifies RUL prediction and stress index REST endpoints (§24, §63)."""
    resp_rul = client.get("/api/v1/twin/rul")
    assert resp_rul.status_code == 200
    rul_data = resp_rul.json()
    assert "hours_remaining" in rul_data
    assert "hours_lower_bound" in rul_data
    assert "hours_upper_bound" in rul_data
    assert "trend" in rul_data
    assert rul_data["hours_lower_bound"] <= rul_data["hours_remaining"] <= rul_data["hours_upper_bound"]

    resp_stress = client.get("/api/v1/twin/stress")
    assert resp_stress.status_code == 200
    stress_data = resp_stress.json()
    assert "thermal" in stress_data
    assert "mechanical" in stress_data
    assert "cumulative_stress" in stress_data


def test_mission_margin_and_counterfactual_endpoints():
    """Verifies detailed mission margin and counterfactual simulation REST endpoints (§34, §35, §79)."""
    resp_margin = client.get("/api/v1/mission/margin")
    assert resp_margin.status_code == 200
    m_data = resp_margin.json()
    assert "thermal_margin" in m_data
    assert "load_margin" in m_data
    assert "fuel_margin" in m_data
    assert "composite_margin" in m_data
    assert "recommendation" in m_data

    # Test multi-branch comparison
    cf_payload = {
        "horizon_minutes": 20.0,
        "compare_branches": True
    }
    resp_cf = client.post("/api/v1/mission/counterfactual", json=cf_payload)
    assert resp_cf.status_code == 200
    cf_data = resp_cf.json()
    assert cf_data["status"] == "success"
    assert cf_data["mode"] == "multi_branch_comparison"
    assert len(cf_data["branches"]) == 4

    # Test single scenario
    single_payload = {
        "target_throttle": 55.0,
        "target_altitude": 4000.0,
        "horizon_minutes": 15.0,
        "compare_branches": False
    }
    resp_single = client.post("/api/v1/mission/counterfactual", json=single_payload)
    assert resp_single.status_code == 200
    single_data = resp_single.json()
    assert single_data["status"] == "success"
    assert "outcome" in single_data
    assert len(single_data["outcome"]["trajectory"]) > 0


def test_mission_replay_endpoints():
    """Verifies Mission Replay overview, timeline, frame scrubbing, and branch APIs (§36, §37, §38)."""
    # 1. Overview
    resp_over = client.get("/api/v1/replay/overview")
    assert resp_over.status_code == 200
    over_data = resp_over.json()
    assert "engine_id" in over_data
    assert "min_time" in over_data
    assert "max_time" in over_data
    assert "total_samples" in over_data

    # 2. Timeline milestones
    resp_time = client.get("/api/v1/replay/timeline")
    assert resp_time.status_code == 200
    milestones = resp_time.json()
    assert isinstance(milestones, list)

    # 3. Frame retrieval (use min_time if records exist, otherwise now)
    t = over_data["min_time"] if over_data["min_time"] else 0.0
    resp_frame = client.get(f"/api/v1/replay/frame?timestamp={t}")
    assert resp_frame.status_code == 200
    frame_data = resp_frame.json()
    assert "timestamp" in frame_data
    assert "telemetry" in frame_data

    # 4. Branch counterfactual replay
    branch_payload = {
        "timestamp": t,
        "horizon_minutes": 10.0
    }
    resp_branch = client.post("/api/v1/replay/branch", json=branch_payload)
    assert resp_branch.status_code == 200
    branch_data = resp_branch.json()
    assert branch_data["status"] == "success"
    assert len(branch_data["branches"]) == 4


def test_fleet_registry_analytics_endpoints():
    """Verifies fleet overview, model registry, and analytics trends APIs (§51, §65, §87)."""
    resp_fleet = client.get("/api/v1/fleet/overview")
    assert resp_fleet.status_code == 200
    fleet_data = resp_fleet.json()
    assert "fleet_id" in fleet_data
    assert len(fleet_data["aircraft"]) == 3
    assert fleet_data["aircraft"][0]["uav_id"] == "UAV-001"

    resp_reg = client.get("/api/v1/registry/models")
    assert resp_reg.status_code == 200
    reg_data = resp_reg.json()
    assert "models" in reg_data
    assert len(reg_data["models"]) >= 5

    resp_ana = client.get("/api/v1/analytics/trends")
    assert resp_ana.status_code == 200
    ana_data = resp_ana.json()
    assert "sample_count" in ana_data
    assert "sensor_trust_aggregates" in ana_data


def test_edge_gateway_api_endpoints():
    """Verifies Edge Gateway status, start/stop, and mock packet injection APIs (§47, §67, §81)."""
    # 1. Status
    resp_stat = client.get("/api/v1/gateway/status")
    assert resp_stat.status_code == 200
    stat_data = resp_stat.json()
    assert "status" in stat_data
    assert "buffer_capacity" in stat_data

    # 2. Start
    resp_start = client.post("/api/v1/gateway/start")
    assert resp_start.status_code == 200
    assert resp_start.json()["gateway"]["status"] == "LISTENING"

    # 3. Inject MAVLink mock
    resp_mav = client.post("/api/v1/gateway/inject_mock?protocol=MAVLINK")
    assert resp_mav.status_code == 200
    mav_data = resp_mav.json()
    assert mav_data["status"] == "INJECTED"
    assert len(mav_data["decoded_records"]) == 1

    # 4. Inject CAN mock
    resp_can = client.post("/api/v1/gateway/inject_mock?protocol=CAN")
    assert resp_can.status_code == 200
    can_data = resp_can.json()
    assert can_data["status"] == "INJECTED"
    assert len(can_data["decoded_records"]) == 1

    # 5. Stop
    resp_stop = client.post("/api/v1/gateway/stop")
    assert resp_stop.status_code == 200
    assert resp_stop.json()["gateway"]["status"] == "STOPPED"


def test_validation_benchmark_api_endpoints():
    """Verifies Validation Benchmark Suite definitions and execution APIs (§74-§77)."""
    # 1. Scenarios catalog
    resp_cat = client.get("/api/v1/validation/scenarios")
    assert resp_cat.status_code == 200
    cat_data = resp_cat.json()
    assert cat_data["status"] == "SUCCESS"
    assert len(cat_data["scenarios"]) == 10

    # 2. Run single scenario
    resp_single = client.post("/api/v1/validation/run", json={"scenario_id": 1, "steps": 15})
    assert resp_single.status_code == 200
    single_data = resp_single.json()
    assert single_data["status"] == "COMPLETED"
    assert single_data["scenario"]["scenario_id"] == 1
    assert single_data["scenario"]["passed"] is True

    # 3. Run full validation matrix (fast steps)
    resp_all = client.post("/api/v1/validation/run", json={"steps": 15})
    assert resp_all.status_code == 200
    all_data = resp_all.json()
    assert all_data["status"] == "COMPLETED"
    assert all_data["total_scenarios"] == 10
    assert all_data["pass_rate_pct"] >= 90.0
    assert all_data["overall_fidelity"]["fidelity_score_pct"] > 50.0




