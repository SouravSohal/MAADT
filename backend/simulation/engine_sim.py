"""
Dynamic Engine Physics Simulator.
Implements first-principles dynamical modeling for a 4-cylinder aero-piston engine:
rotational inertia, air mass flow, fuel consumption, thermodynamic differential equations
(EGT, CHT, oil temperature), oil hydraulic circuit, mechanical vibrations, and sensor noise.
Reference: overview.md Sections 14, 15, 16, 20, 32, 54.
"""

import math
import random
import time
from typing import Dict, Optional, Tuple

from config.engine_config import EngineConfig
from schemas.telemetry import TelemetryPacket
from .environment import AtmosphericEnvironment
from .fault_injector import FaultInjector


class AeroEngineSimulator:
    """
    Continuous state aero-piston propulsion simulator.
    Advances continuous thermodynamic and mechanical state forward in time (dt).
    """

    def __init__(
        self,
        config: EngineConfig,
        environment: Optional[AtmosphericEnvironment] = None,
        fault_injector: Optional[FaultInjector] = None,
        engine_id: str = "ENG-001",
    ):
        self.config = config
        self.env = environment or AtmosphericEnvironment()
        self.injector = fault_injector or FaultInjector()
        self.engine_id = engine_id

        # Physical Constants & Specifications
        limits = self.config.operating_limits
        self.idle_rpm = limits.rpm.min_idle
        self.redline_rpm = limits.rpm.redline
        self.disp_m3 = (self.config.displacement_cc / 1e6)  # displacement in m^3
        self.fuel_density_kg_l = 0.72  # AVGAS 100LL / Mogas density

        # Thermal Time Constants from Config (§14, §16)
        params = self.config.physics_parameters
        self.tau_rpm = 1.2                          # Rotational spool-up time constant (seconds)
        self.tau_egt = params.thermal_egt_time_constant_s # ~6.0s
        self.tau_cht = params.thermal_cht_time_constant_s # ~45.0s
        self.tau_oil = params.oil_thermal_time_constant_s # ~90.0s

        # Runtime State Variables
        self.sim_time: float = 0.0
        self.throttle: float = 0.0          # Current throttle position %
        self.altitude: float = 0.0          # Current altitude meters
        
        # Continuous mechanical states
        self.rpm: float = self.idle_rpm
        self.egt: float = 520.0
        self.cht: float = 85.0
        self.oil_temperature: float = 75.0
        self.oil_pressure: float = 4.2
        self.fuel_flow: float = 4.0
        self.vibration: float = 0.20
        self.battery_voltage: float = 28.0
        self.alternator_current: float = 14.0

    def step(self, throttle_pct: float, altitude_m: float, dt: float = 0.5) -> TelemetryPacket:
        """
        Advances the engine dynamics by dt seconds under the given throttle and altitude.
        Returns the resulting TelemetryPacket with realistic sensor noise and injected faults.
        """
        self.sim_time += dt
        self.throttle = max(0.0, min(100.0, throttle_pct))
        self.altitude = max(0.0, altitude_m)

        # 1. Atmospheric Conditions at Altitude (§15)
        amb_temp, amb_press, density, sigma = self.env.get_conditions(self.altitude)

        # 2. Engine Rotational Dynamics (RPM)
        # Target RPM depends on throttle and air density (reduced density at high alt lowers propeller load)
        rpm_range = self.redline_rpm - self.idle_rpm
        target_rpm = self.idle_rpm + (rpm_range * (self.throttle / 100.0)) * math.sqrt(sigma)
        target_rpm = min(self.redline_rpm, max(self.idle_rpm * 0.85, target_rpm))

        # First-order rotational spool-up lag
        alpha_rpm = dt / (self.tau_rpm + dt)
        self.rpm += alpha_rpm * (target_rpm - self.rpm)

        # 3. Volumetric Air Mass Flow & Fuel Flow Rate
        # Turbocharger delivers manifold boost pressure (MAP) up to ~1.38 bar at 100% throttle with altitude compensation
        turbo_altitude_compensation = min(2.0, 1.0 / (sigma ** 0.65))
        turbo_boost_ratio = (1.0 + (0.42 * (self.throttle / 100.0))) * turbo_altitude_compensation
        volumetric_eff = 0.88 * (0.9 + 0.1 * (self.rpm / self.redline_rpm))
        air_mass_flow_kg_s = (self.rpm / 120.0) * self.disp_m3 * volumetric_eff * density * turbo_boost_ratio
        
        # Stoichiometric / slightly rich fuel metering (AFR ~ 13.5:1 at high power, 14.7 at cruise)
        afr = 14.7 - (1.5 * (self.throttle / 100.0))
        fuel_mass_flow_kg_s = air_mass_flow_kg_s / afr
        # Convert to Liters/hour: (kg/s / (kg/L)) * 3600
        target_fuel_flow = (fuel_mass_flow_kg_s / self.fuel_density_kg_l) * 3600.0
        self.fuel_flow = max(2.5, target_fuel_flow)

        # 4. Thermodynamic Differential Equations (EGT & CHT)
        # Steady-state EGT scales with combustion energy and mixture
        target_egt = 500.0 + (self.throttle * 2.8) - ((15.0 - amb_temp) * 0.3)
        alpha_egt = dt / (self.tau_egt + dt)
        self.egt += alpha_egt * (target_egt - self.egt)

        # Steady-state CHT scales with engine load, ambient cooling, and thermal dissipation
        cooling_airspeed_factor = max(0.7, 1.0 - (self.altitude / 20000.0))
        target_cht = 120.0 + (self.throttle * 0.75) + ((amb_temp - 15.0) * 0.5) / cooling_airspeed_factor
        alpha_cht = dt / (self.tau_cht + dt)
        self.cht += alpha_cht * (target_cht - self.cht)

        # 5. Oil Circuit Dynamics (Temperature & Pressure)
        target_oil_temp = 75.0 + (self.throttle * 0.35) + ((amb_temp - 15.0) * 0.3)
        alpha_oil = dt / (self.tau_oil + dt)
        self.oil_temperature += alpha_oil * (target_oil_temp - self.oil_temperature)

        # Oil pressure from positive-displacement pump: increases with RPM, drops with oil thinning (higher temp)
        viscosity_factor = max(0.6, 1.0 - ((self.oil_temperature - 80.0) * 0.005))
        self.oil_pressure = (2.2 + (self.rpm / 1000.0) * 1.1) * viscosity_factor

        # 6. Mechanical Vibration
        # Base engine vibration proportional to RPM harmonic + piston excitation
        self.vibration = 0.15 + 0.14 * ((self.rpm / 3000.0) ** 2)

        # 7. Electrical Generation
        self.battery_voltage = 28.0
        self.alternator_current = 10.0 + (self.throttle * 0.12)

        # 8. Apply Mechanical Faults (§20, §53)
        sim_state = {
            "rpm": self.rpm,
            "egt": self.egt,
            "cht": self.cht,
            "fuel_flow": self.fuel_flow,
            "oil_temperature": self.oil_temperature,
            "oil_pressure": self.oil_pressure,
            "vibration": self.vibration,
            "battery_voltage": self.battery_voltage,
            "alternator_current": self.alternator_current,
        }
        self.injector.apply_mechanical_faults(sim_state, self.sim_time)

        # 9. Add Realistic Gaussian Sensor Measurement Noise
        noisy_readings = {
            "rpm": sim_state["rpm"] + random.gauss(0, 5.0),
            "egt": sim_state["egt"] + random.gauss(0, 2.5),
            "cht": sim_state["cht"] + random.gauss(0, 0.8),
            "fuel_flow": sim_state["fuel_flow"] + random.gauss(0, 0.15),
            "oil_temperature": sim_state["oil_temperature"] + random.gauss(0, 0.4),
            "oil_pressure": sim_state["oil_pressure"] + random.gauss(0, 0.05),
            "vibration": max(0.05, sim_state["vibration"] + random.gauss(0, 0.015)),
            "battery_voltage": sim_state["battery_voltage"] + random.gauss(0, 0.08),
            "alternator_current": sim_state["alternator_current"] + random.gauss(0, 0.3),
        }

        # 10. Apply Instrument Sensor Faults (Drift, Failure) (§10, §11)
        self.injector.apply_sensor_faults(noisy_readings, self.sim_time)

        # Return standardized TelemetryPacket
        return TelemetryPacket(
            timestamp=time.time(),
            engine_id=self.engine_id,
            sequence_id=int(self.sim_time / dt),
            rpm=round(noisy_readings["rpm"], 1),
            cht=round(noisy_readings["cht"], 1),
            egt=round(noisy_readings["egt"], 1),
            oil_pressure=round(max(0.0, noisy_readings["oil_pressure"]), 2),
            oil_temperature=round(noisy_readings["oil_temperature"], 1),
            fuel_flow=round(max(0.0, noisy_readings["fuel_flow"]), 2),
            vibration=round(noisy_readings["vibration"], 3),
            battery_voltage=round(noisy_readings["battery_voltage"], 2),
            alternator_current=round(noisy_readings["alternator_current"], 1),
            injection_timing=22.0,
            throttle=round(self.throttle, 1),
            altitude=round(self.altitude, 1),
            ambient_temperature=round(amb_temp, 1),
            ambient_pressure=round(amb_press, 1),
        )
