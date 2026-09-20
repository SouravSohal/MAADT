import math

class AeroPhysicsModel:
    def __init__(self):
        # Standard sea-level conditions (ISA)
        self.T0 = 288.15  # Kelvin
        self.P0 = 101325  # Pascals
        self.L = 0.0065   # Temp lapse rate (K/m)
        self.R = 287.05   # Specific gas constant for air

    def get_atmospheric_conditions(self, altitude_m):
        # Calculate standard atmospheric conditions based on altitude
        T = self.T0 - (self.L * altitude_m)
        P = self.P0 * (1 - (self.L * altitude_m) / self.T0) ** (9.80665 / (self.R * self.L))
        density = P / (self.R * T)
        return T, P, density

    def calculate_expected_state(self, throttle_pct, altitude_m):
        T, P, density = self.get_atmospheric_conditions(altitude_m)
        
        # Reduced-order correlation models
        # Expected RPM scales with throttle and air density
        expected_rpm = 1200 + (throttle_pct * 16.0) * (density / 1.225)
        
        # Expected EGT increases with throttle, decreases slightly in colder high-alt air
        expected_egt = 450 + (throttle_pct * 3.2) - ((self.T0 - T) * 0.4)
        
        return expected_rpm, expected_egt
