"""
Unit Tests for Phase 1: Foundation, Schemas, Configuration, Validator & Storage.
"""

import os
import tempfile
import time
from pathlib import Path
import pytest

from schemas.telemetry import (
    Advisory,
    AlertSeverity,
    DigitalTwinState,
    FaultEvent,
    FaultType,
    OperatingRegime,
    SensorQuality,
    SubsystemHealth,
    TelemetryPacket,
)
from config.loader import ConfigManager
from telemetry.validator import TelemetryValidator
from storage.db import Database


def test_telemetry_schema_validation():
    """Verifies standard TelemetryPacket validation and serialization."""
    packet = TelemetryPacket(
        timestamp=time.time(),
        engine_id="ENG-001",
        mission_id="MIS-TEST",
        rpm=2450.0,
        cht=165.2,
        egt=710.5,
        oil_pressure=4.8,
        oil_temperature=92.0,
        fuel_flow=18.4,
        vibration=0.28,
        throttle=65.0,
        altitude=5500.0,
        ambient_temperature=22.0,
        ambient_pressure=85.0
    )
    assert packet.rpm == 2450.0
    assert packet.schema_version == "v1.0"
    data = packet.model_dump()
    assert data["engine_id"] == "ENG-001"
    assert "battery_voltage" in data


def test_config_loader():
    """Verifies YAML configuration loading and typing."""
    cfg_mgr = ConfigManager()
    engine_cfg = cfg_mgr.get_engine_config("aero_piston_x")
    assert engine_cfg is not None
    assert engine_cfg.name == "AeroPiston-4X"
    assert engine_cfg.operating_limits.rpm.redline == 3200.0
    assert engine_cfg.anomaly.weights.physics == 0.40
    assert engine_cfg.subsystem_health_weights.combustion == 0.28

    missions = cfg_mgr.list_missions()
    assert len(missions) >= 1
    endurance = cfg_mgr.get_mission_config("MIS-ENDURANCE-01")
    assert endurance is not None
    assert endurance.duration_minutes == 480.0
    assert len(endurance.waypoints) > 5


def test_telemetry_validator_valid_and_out_of_bounds():
    """Verifies that TelemetryValidator flags normal, out-of-range, and spike data."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    validator = TelemetryValidator(config=cfg, window_size=5)

    # 1. Normal packet
    pkt = TelemetryPacket(
        timestamp=1000.0,
        rpm=2400.0,
        cht=160.0,
        egt=700.0,
        oil_pressure=4.5,
        oil_temperature=90.0,
        fuel_flow=18.0,
        vibration=0.25,
        throttle=65.0,
        altitude=2000.0
    )
    validated = validator.validate_and_tag(pkt, dt=0.5)
    assert validated.sensor_quality["rpm"] == SensorQuality.VALID
    assert validated.sensor_quality["egt"] == SensorQuality.VALID
    assert validated.sensor_trust["rpm"] == 1.0

    # 2. Out of range packet (impossible EGT)
    pkt_bad = TelemetryPacket(
        timestamp=1000.5,
        rpm=2400.0,
        cht=160.0,
        egt=1500.0,  # Far above redline limit
        oil_pressure=4.5,
        oil_temperature=90.0,
        fuel_flow=18.0,
        vibration=0.25,
        throttle=65.0,
        altitude=2000.0
    )
    validated_bad = validator.validate_and_tag(pkt_bad, dt=0.5)
    assert validated_bad.sensor_quality["egt"] == SensorQuality.OUT_OF_RANGE
    # Trust should have decreased for EGT
    assert validated_bad.sensor_trust["egt"] < 1.0


def test_telemetry_validator_spike_detection():
    """Verifies rate-of-change spike detection."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    validator = TelemetryValidator(config=cfg, window_size=5)

    # Initial frame
    pkt1 = TelemetryPacket(
        timestamp=100.0,
        rpm=2400.0,
        cht=160.0,
        egt=700.0,
        oil_pressure=4.5,
        oil_temperature=90.0,
        fuel_flow=18.0,
        vibration=0.25,
        throttle=65.0,
        altitude=2000.0
    )
    validator.validate_and_tag(pkt1, dt=0.5)

    # Immediate massive unphysical spike in CHT (e.g. +80C in 0.5 sec)
    pkt2 = TelemetryPacket(
        timestamp=100.5,
        rpm=2400.0,
        cht=240.0,  # Impossible +80 C thermal jump in 0.5s
        egt=700.0,
        oil_pressure=4.5,
        oil_temperature=90.0,
        fuel_flow=18.0,
        vibration=0.25,
        throttle=65.0,
        altitude=2000.0
    )
    validated2 = validator.validate_and_tag(pkt2, dt=0.5)
    assert validated2.sensor_quality["cht"] == SensorQuality.SUSPECT


def test_database_persistence():
    """Verifies SQLite persistence for telemetry, twin states, faults, and advisories."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db_path = Path(tmp.name)

    try:
        test_db = Database(db_path=temp_db_path)

        # 1. Test Telemetry Storage
        pkt = TelemetryPacket(
            timestamp=1700000000.0,
            engine_id="ENG-TEST",
            mission_id="MIS-01",
            rpm=2500.0,
            cht=168.0,
            egt=712.0,
            oil_pressure=4.7,
            oil_temperature=92.0,
            fuel_flow=19.0,
            vibration=0.30,
            throttle=70.0,
            altitude=4500.0
        )
        pkt.sensor_quality = {"rpm": SensorQuality.VALID}
        pkt.sensor_trust = {"rpm": 1.0}
        test_db.insert_telemetry(pkt)

        recent = test_db.get_recent_telemetry("ENG-TEST", limit=5)
        assert len(recent) == 1
        assert recent[0]["rpm"] == 2500.0
        assert recent[0]["engine_id"] == "ENG-TEST"

        # 2. Test Twin State Storage
        twin_state = DigitalTwinState(
            engine_id="ENG-TEST",
            timestamp=1700000000.0,
            operating_regime=OperatingRegime.CRUISE,
            system_operational_state="MONITORING",
            estimated_rpm=2495.0,
            estimated_load=0.68,
            health=SubsystemHealth(overall=92.5, thermal=90.0, combustion=91.0),
            mission_margin=84.0,
            twin_confidence=0.96
        )
        test_db.insert_twin_state(twin_state)

        states = test_db.get_recent_twin_states("ENG-TEST", limit=5)
        assert len(states) == 1
        assert states[0]["health_index"] == 92.5
        assert states[0]["operating_regime"] == "CRUISE"

        # 3. Test Fault Event Storage
        fault = FaultEvent(
            timestamp=1700000001.0,
            engine_id="ENG-TEST",
            fault_type=FaultType.INJECTOR_ABNORMALITY,
            probability=0.88,
            severity=AlertSeverity.HIGH,
            subsystem="Combustion",
            evidence=["Fuel flow deviation +12%", "EGT residual +35°C"],
            sensor_trust_verified=True
        )
        test_db.insert_fault_event(fault)

        faults = test_db.get_fault_history("ENG-TEST", limit=5)
        assert len(faults) == 1
        assert faults[0]["fault_type"] == "injector_abnormality"
        assert len(faults[0]["evidence"]) == 2

        # 4. Test Advisory Storage
        adv = Advisory(
            id="ADV-001",
            timestamp=1700000002.0,
            severity=AlertSeverity.WARNING,
            subsystem="Combustion",
            potential_issue="Injector Flow Restriction",
            evidence=["EGT residual increasing", "Fuel-RPM ratio offset"],
            current_health=88.5,
            estimated_rul="142 h [120-165 h]",
            recommended_action="Inspect injector rail at next scheduled maintenance.",
            confidence=0.85
        )
        test_db.insert_advisory(adv)

        advisories = test_db.get_advisories(limit=5)
        assert len(advisories) == 1
        assert advisories[0]["id"] == "ADV-001"
        assert advisories[0]["severity"] == "WARNING"

    finally:
        if temp_db_path.exists():
            os.remove(temp_db_path)
