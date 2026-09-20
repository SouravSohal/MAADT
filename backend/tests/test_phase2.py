"""
Unit Tests for Phase 2: Atmospheric Environment, Engine Dynamics, Fault Injection & Mission Runner.
"""

import pytest
from config.loader import ConfigManager
from schemas.telemetry import FaultType, OperatingRegime
from simulation.environment import AtmosphericEnvironment
from simulation.engine_sim import AeroEngineSimulator
from simulation.fault_injector import FaultInjector, FaultProgression
from simulation.mission_runner import MissionRunner


def test_atmospheric_isa_environment():
    """Verifies ISA atmospheric calculations at sea level and 18,000 ft (5,500 m)."""
    env = AtmosphericEnvironment()
    
    # Sea Level Check
    temp_c, press_kpa, density, sigma = env.get_conditions(altitude_m=0.0)
    assert round(temp_c, 1) == 15.0
    assert round(press_kpa, 1) == 101.3
    assert round(density, 3) == 1.225
    assert round(sigma, 2) == 1.0

    # 5,500m (~18,000 ft MALE cruise ceiling)
    temp_c_alt, press_kpa_alt, density_alt, sigma_alt = env.get_conditions(altitude_m=5500.0)
    # Temperature should drop by 0.0065 K/m -> 15.0 - (0.0065 * 5500) = -20.75°C
    assert temp_c_alt < -19.0
    assert press_kpa_alt < 55.0  # Pressure roughly halved
    assert density_alt < 0.75    # Density significantly lower
    assert sigma_alt < 0.65


def test_engine_simulator_dynamics():
    """Verifies rotational spool-up, fuel metering, and thermal differential equations."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    sim = AeroEngineSimulator(config=cfg)

    # Initial state at idle
    pkt_idle = sim.step(throttle_pct=0.0, altitude_m=0.0, dt=0.5)
    assert pkt_idle.rpm >= 1300.0
    assert pkt_idle.fuel_flow < 8.0

    # Apply 100% takeoff throttle and advance for 5 seconds
    for _ in range(10):
        pkt_takeoff = sim.step(throttle_pct=100.0, altitude_m=0.0, dt=0.5)

    # RPM should spool up significantly towards max
    assert pkt_takeoff.rpm > 2500.0
    # Fuel flow should surge to support takeoff power
    assert pkt_takeoff.fuel_flow > 16.0
    # Oil pressure should remain well within safe limits
    assert pkt_takeoff.oil_pressure > 3.5


def test_fault_injection_mechanical():
    """Verifies mechanical fault injection impacts on engine parameters."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    injector = FaultInjector()
    sim = AeroEngineSimulator(config=cfg, fault_injector=injector)

    # Establish steady-state baseline
    for _ in range(10):
        base_pkt = sim.step(throttle_pct=70.0, altitude_m=2000.0, dt=0.5)

    # Inject Injector Abnormality fault
    injector.inject_fault(
        fault_type=FaultType.INJECTOR_ABNORMALITY,
        severity=0.8,
        progression=FaultProgression.INSTANT
    )
    fault_pkt = sim.step(throttle_pct=70.0, altitude_m=2000.0, dt=0.5)

    # EGT and fuel flow should be noticeably higher than baseline
    assert fault_pkt.egt > base_pkt.egt
    assert fault_pkt.fuel_flow > base_pkt.fuel_flow

    # Inject Lubrication Issue
    injector.clear_all()
    injector.inject_fault(
        fault_type=FaultType.LUBRICATION_ISSUE,
        severity=0.9,
        progression=FaultProgression.INSTANT
    )
    lub_pkt = sim.step(throttle_pct=70.0, altitude_m=2000.0, dt=0.5)
    # Oil pressure should be significantly degraded
    assert lub_pkt.oil_pressure < 3.0


def test_fault_injection_sensor_drift():
    """Verifies sensor-level drift affects instrument output without altering mechanical state."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    injector = FaultInjector()
    sim = AeroEngineSimulator(config=cfg, fault_injector=injector)

    for _ in range(6):
        base_pkt = sim.step(throttle_pct=60.0, altitude_m=3000.0, dt=0.5)

    # Inject drift on EGT sensor
    injector.inject_fault(
        fault_type=FaultType.SENSOR_DRIFT,
        severity=1.0,
        progression=FaultProgression.INSTANT,
        target_sensor="egt"
    )
    drift_pkt = sim.step(throttle_pct=60.0, altitude_m=3000.0, dt=0.5)

    # Sensor reading has ~80°C offset added
    assert drift_pkt.egt - base_pkt.egt > 60.0
    # While CHT and RPM remain unaffected by the sensor drift
    assert abs(drift_pkt.cht - base_pkt.cht) < 5.0


def test_mission_runner_interpolation_and_regimes():
    """Verifies waypoint interpolation and operational regime transitions."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.get_engine_config()
    mission_cfg = cfg_mgr.get_mission_config("MIS-ENDURANCE-01")
    assert mission_cfg is not None

    sim = AeroEngineSimulator(config=cfg)
    runner = MissionRunner(simulator=sim, mission_config=mission_cfg)

    # At t = 0s (Waypoint 1: START)
    pkt0, reg0 = runner.step(dt=0.5)
    assert reg0 == OperatingRegime.START
    assert pkt0.throttle == 0.0

    # Fast forward to climb regime (e.g. t = 20 minutes = 1200s)
    runner.current_sim_time_s = 20.0 * 60.0
    pkt_climb, reg_climb = runner.step(dt=0.5)
    assert reg_climb == OperatingRegime.CLIMB
    assert pkt_climb.altitude > 100.0
    assert pkt_climb.throttle > 70.0
