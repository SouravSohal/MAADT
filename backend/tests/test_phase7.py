"""
Phase 7 Unit Tests: Mission Replay & Time-Travel Analysis Engine.
Verifies timeline milestone aggregation, historical telemetry retrieval,
and counterfactual branching at historical events (§36, §37, §38).
"""

import pytest
from config.loader import ConfigManager
from replay import MissionReplayEngine, TimelineMilestone
from schemas.telemetry import (
    AlertSeverity,
    DigitalTwinState,
    FaultEvent,
    FaultType,
    TelemetryPacket,
)
from storage.db import Database


def test_mission_replay_engine_overview_and_timeline(tmp_path):
    """Verifies mission time bounds, milestone extraction, and scrubbing."""
    test_db_path = tmp_path / "test_replay.db"
    db_inst = Database(db_path=test_db_path)
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    replay = MissionReplayEngine(config=cfg, database=db_inst)

    # 1. Insert series of telemetry frames
    for i in range(10):
        t = 1000.0 + (i * 1.0)
        pkt = TelemetryPacket(
            timestamp=t,
            engine_id="ENG-REPLAY",
            rpm=2400.0 + i * 10,
            cht=160.0 + i * 2,
            egt=700.0 + i * 5,
            oil_pressure=4.5,
            oil_temperature=90.0,
            fuel_flow=18.0,
            vibration=0.22,
            throttle=65.0,
            altitude=4000.0
        )
        db_inst.insert_telemetry(pkt)

    # 2. Insert Fault Event at t=1005.0
    fault = FaultEvent(
        timestamp=1005.0,
        engine_id="ENG-REPLAY",
        fault_type=FaultType.INJECTOR_ABNORMALITY,
        probability=0.88,
        severity=AlertSeverity.HIGH,
        subsystem="Combustion Core",
        evidence=["Elevated EGT residual +42°C", "Fuel flow discrepancy"],
        sensor_trust_verified=True
    )
    db_inst.insert_fault_event(fault)

    # 3. Test overview
    overview = replay.get_mission_overview("ENG-REPLAY")
    assert overview["total_samples"] == 10
    assert overview["min_time"] == 1000.0
    assert overview["max_time"] == 1009.0
    assert overview["duration_seconds"] == 9.0
    assert overview["total_fault_events"] == 1

    # 4. Test timeline milestones (§37)
    timeline = replay.build_event_timeline("ENG-REPLAY")
    assert len(timeline) == 1
    m0 = timeline[0]
    assert isinstance(m0, TimelineMilestone)
    assert m0.timestamp == 1005.0
    assert m0.severity == "HIGH"
    assert "Combustion" in m0.title or "Injector" in m0.title
    assert len(m0.evidence) == 2


def test_replay_frame_retrieval_and_branching(tmp_path):
    """Verifies retrieval of exact historical state and branching counterfactual replay (§36, §38)."""
    test_db_path = tmp_path / "test_replay_branch.db"
    db_inst = Database(db_path=test_db_path)
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    replay = MissionReplayEngine(config=cfg, database=db_inst)

    # Seed frames
    for i in range(5):
        t = 200.0 + (i * 2.0)
        pkt = TelemetryPacket(
            timestamp=t,
            engine_id="ENG-REPLAY-2",
            rpm=2500.0,
            cht=170.0,
            egt=740.0,
            oil_pressure=4.2,
            oil_temperature=95.0,
            fuel_flow=20.0,
            vibration=0.28,
            throttle=70.0,
            altitude=5000.0
        )
        db_inst.insert_telemetry(pkt)

    # Fetch frame at t=204.0
    frame = replay.get_replay_frame("ENG-REPLAY-2", timestamp=204.0)
    assert frame["status"] == "SYNCHRONIZED"
    assert frame["timestamp"] == 204.0
    assert frame["telemetry"]["rpm"] == 2500.0
    assert frame["telemetry"]["throttle"] == 70.0

    # Branch counterfactual from historical frame (§38)
    branches = replay.branch_counterfactual_at_time(
        engine_id="ENG-REPLAY-2",
        timestamp=204.0,
        horizon_minutes=20.0
    )
    assert len(branches) == 4
    branch_ids = [b.scenario_id for b in branches]
    assert "maintain" in branch_ids
    assert "throttle_down" in branch_ids
    assert "descend" in branch_ids
    assert "rtb" in branch_ids
