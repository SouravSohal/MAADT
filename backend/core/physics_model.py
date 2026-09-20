"""
Thermodynamic & Aerodynamic Engine Physics Models.
Implements the abstract EngineModel interface and first-principles reduced-order
thermodynamic calculations for aero-piston UAV engines.
Reference: overview.md Sections 14, 15, 16, 17, 92.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import math
from typing import Dict, Optional, Tuple

from config.engine_config import EngineConfig
from schemas.telemetry import PhysicsResiduals, TelemetryPacket
from simulation.environment import AtmosphericEnvironment


@dataclass
class ExpectedEngineState:
    """Expected baseline outputs computed from first-principles physics."""
    expected_rpm: float
    expected_egt: float
    expected_cht: float
    expected_fuel_flow: float
    expected_oil_temperature: float
    expected_oil_pressure: float
    expected_load: float
    air_density: float
    density_ratio_sigma: float


class EngineModel(ABC):
    """Abstract interface for all engine physics twins (overview.md §92)."""

    @abstractmethod
    def calculate_expected_state(
        self,
        throttle_pct: float,
        altitude_m: float,
        ambient_temp_c: Optional[float] = None
    ) -> ExpectedEngineState:
        """Computes expected physical baseline given flight conditions and throttle."""
        pass

    @abstractmethod
    def calculate_residuals(
        self,
        telemetry: TelemetryPacket,
        expected: ExpectedEngineState
    ) -> PhysicsResiduals:
        """Generates physics residuals between observations and expected baseline (§17)."""
        pass


class AeroPistonPhysicsModel(EngineModel):
    """
    Reduced-order thermodynamic & performance model for turbocharged 4-cylinder aero-piston engine.
    Calculates nominal RPM, fuel metering, cylinder thermal equilibrium (EGT & CHT),
    and oil circuit thermodynamics.
    """

    def __init__(self, config: EngineConfig, environment: Optional[AtmosphericEnvironment] = None):
        self.config = config
        self.env = environment or AtmosphericEnvironment()
        self.limits = self.config.operating_limits
        self.params = self.config.physics_parameters

        # Engine dimensions
        self.disp_m3 = (self.config.displacement_cc / 1e6)
        self.fuel_density_kg_l = 0.72

    def calculate_expected_state(
        self,
        throttle_pct: float,
        altitude_m: float,
        ambient_temp_c: Optional[float] = None
    ) -> ExpectedEngineState:
        """Computes expected thermodynamic baseline for nominal healthy engine."""
        thr = max(0.0, min(100.0, throttle_pct))
        alt = max(0.0, altitude_m)

        # 1. Atmospheric conditions (§15)
        amb_temp, amb_press, density, sigma = self.env.get_conditions(alt)
        if ambient_temp_c is not None:
            amb_temp = ambient_temp_c

        # 2. Expected RPM
        # Nominal cruise RPM scales with throttle command and air density
        rpm_idle = self.limits.rpm.min_idle
        rpm_redline = self.limits.rpm.redline
        rpm_span = rpm_redline - rpm_idle
        expected_rpm = rpm_idle + (rpm_span * (thr / 100.0)) * math.sqrt(sigma)
        expected_rpm = min(rpm_redline, max(rpm_idle, expected_rpm))

        # 3. Expected Air & Fuel Flow
        # Turbocharger compensates for altitude air thinness up to critical ceiling (~6,000m)
        turbo_altitude_compensation = min(2.0, 1.0 / (sigma ** 0.65))
        turbo_boost = (1.0 + (0.42 * (thr / 100.0))) * turbo_altitude_compensation
        vol_eff = 0.88 * (0.9 + 0.1 * (expected_rpm / rpm_redline))
        manifold_density = density * turbo_boost
        air_flow_kg_s = (expected_rpm / 120.0) * self.disp_m3 * vol_eff * manifold_density
        
        # Nominal air-fuel ratio
        nominal_afr = 14.7 - (1.5 * (thr / 100.0))
        fuel_flow_kg_s = air_flow_kg_s / nominal_afr
        expected_fuel_flow = (fuel_flow_kg_s / self.fuel_density_kg_l) * 3600.0
        expected_fuel_flow = max(2.5, expected_fuel_flow)

        # 4. Expected Cylinder Head Temperature (CHT)
        # Thermal balance: heat generated from combustion vs cooling airflow dissipation
        cooling_speed_factor = max(0.7, 1.0 - (alt / 20000.0))
        expected_cht = 120.0 + (thr * 0.75) + ((amb_temp - 15.0) * 0.5) / cooling_speed_factor

        # 5. Expected Exhaust Gas Temperature (EGT)
        # Combustion energy release minus ambient altitude expansion
        expected_egt = 500.0 + (thr * 2.8) - ((15.0 - amb_temp) * 0.3)

        # 6. Expected Oil Circuit (Pressure & Temperature)
        expected_oil_temp = 75.0 + (thr * 0.35) + ((amb_temp - 15.0) * 0.3)
        viscosity_factor = max(0.6, 1.0 - ((expected_oil_temp - 80.0) * 0.005))
        expected_oil_pressure = (2.2 + (expected_rpm / 1000.0) * 1.1) * viscosity_factor

        # 7. Normalized Engine Load Proxy
        expected_load = round(thr / 100.0, 2)

        return ExpectedEngineState(
            expected_rpm=round(expected_rpm, 1),
            expected_egt=round(expected_egt, 1),
            expected_cht=round(expected_cht, 1),
            expected_fuel_flow=round(expected_fuel_flow, 2),
            expected_oil_temperature=round(expected_oil_temp, 1),
            expected_oil_pressure=round(expected_oil_pressure, 2),
            expected_load=expected_load,
            air_density=round(density, 3),
            density_ratio_sigma=round(sigma, 3)
        )

    def calculate_residuals(
        self,
        telemetry: TelemetryPacket,
        expected: ExpectedEngineState
    ) -> PhysicsResiduals:
        """
        Calculates physical residuals: Delta = Observed - Expected (§17).
        Positive EGT/CHT residual indicates thermal elevation.
        Positive fuel residual indicates over-fueling / injector leakage.
        Negative oil pressure residual indicates loss of lubrication pressure.
        """
        return PhysicsResiduals(
            egt_residual=round(telemetry.egt - expected.expected_egt, 1),
            cht_residual=round(telemetry.cht - expected.expected_cht, 1),
            rpm_residual=round(telemetry.rpm - expected.expected_rpm, 1),
            fuel_flow_residual=round(telemetry.fuel_flow - expected.expected_fuel_flow, 2),
            oil_temp_residual=round(telemetry.oil_temperature - expected.expected_oil_temperature, 1),
            oil_pressure_residual=round(telemetry.oil_pressure - expected.expected_oil_pressure, 2)
        )
