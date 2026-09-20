"""
Atmospheric Environment Model.
Implements the International Standard Atmosphere (ISA) barometric, temperature,
and density models for aero-piston engines across altitudes from sea level to 35,000 ft.
Reference: overview.md Sections 14, 15, 33.
"""

import math
from typing import Tuple


class AtmosphericEnvironment:
    """
    Computes ambient pressure, temperature, air density, and density ratios
    as a function of altitude and non-standard day temperature offsets.
    """

    # Physical constants (ISA)
    P0: float = 101325.0        # Sea level standard atmospheric pressure in Pa
    T0: float = 288.15          # Sea level standard temperature in Kelvin (15°C)
    L0: float = 0.0065          # Troposphere temperature lapse rate in K/m
    G: float = 9.80665          # Gravitational acceleration in m/s^2
    R: float = 287.05           # Specific gas constant for dry air in J/(kg*K)
    RHO0: float = 1.225         # Sea level standard air density in kg/m^3

    def __init__(self, delta_isa_c: float = 0.0):
        """
        :param delta_isa_c: Temperature offset from standard day in °C (e.g. +15°C for hot-and-high conditions).
        """
        self.delta_isa_c = delta_isa_c

    def get_conditions(self, altitude_m: float) -> Tuple[float, float, float, float]:
        """
        Computes ambient atmospheric conditions at a given geometric altitude.
        
        :param altitude_m: Geometric altitude in meters.
        :return: (temperature_c, pressure_kpa, density_kg_m3, density_ratio_sigma)
        """
        h = max(0.0, min(11000.0, altitude_m)) # Valid up to troposphere ceiling (11,000m)

        # Standard ISA temperature at altitude
        t_isa_k = self.T0 - (self.L0 * h)
        # Actual temperature with non-standard offset
        t_actual_k = t_isa_k + self.delta_isa_c
        t_actual_c = t_actual_k - 273.15

        # Barometric pressure equation: P = P0 * (1 - L*h/T0)^(g / (R*L))
        exponent = self.G / (self.R * self.L0)
        p_pa = self.P0 * ((1.0 - (self.L0 * h) / self.T0) ** exponent)
        p_kpa = p_pa / 1000.0

        # Air density via ideal gas law: rho = P / (R * T)
        density = p_pa / (self.R * t_actual_k)
        density_ratio_sigma = density / self.RHO0

        return t_actual_c, p_kpa, density, density_ratio_sigma

    def set_temperature_offset(self, delta_c: float):
        """Adjusts standard day temperature offset."""
        self.delta_isa_c = delta_c
