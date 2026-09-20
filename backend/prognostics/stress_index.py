"""
Mission Stress Index Formulation.
Quantifies normalized operating stress across thermal, mechanical, combustion,
lubrication, and throttle transient domains to determine accelerated degradation.
Reference: overview.md Sections 63, 64.
"""

from dataclasses import dataclass
import math
from typing import Dict, Optional

from config.engine_config import EngineConfig
from schemas.telemetry import OperatingRegime, TelemetryPacket


@dataclass
class MissionStressDetails:
    """Normalized operational stress indicators [0.0 - 1.0]."""
    thermal: float
    mechanical: float
    combustion: float
    lubrication: float
    transient: float
    overall: float
    cumulative_stress: float


class MissionStressCalculator:
    """
    Computes real-time and accumulated mission stress based on environmental
    operating regimes, thermodynamics, and throttle dynamics.
    """

    def __init__(self, config: EngineConfig):
        self.config = config
        self.limits = config.operating_limits
        self.cumulative_stress: float = 0.0
        self.last_throttle: float = 0.0

    def compute_stress(
        self,
        packet: TelemetryPacket,
        regime: OperatingRegime = OperatingRegime.CRUISE,
        dt: float = 0.5
    ) -> MissionStressDetails:
        """
        Calculates instantaneous stress components and integrates cumulative stress.
        """
        # 1. Thermal Stress: Exceedance above nominal cruise CHT/EGT
        cht_norm = max(0.0, (packet.cht - 150.0) / (self.limits.cht.redline - 150.0))
        egt_norm = max(0.0, (packet.egt - 680.0) / (self.limits.egt.redline - 680.0))
        thermal_stress = min(1.0, max(0.0, (0.6 * cht_norm + 0.4 * egt_norm)))

        # 2. Mechanical Stress: RPM intensity + vibration amplitude
        rpm_norm = max(0.0, (packet.rpm - self.limits.rpm.min_idle) / (self.limits.rpm.redline - self.limits.rpm.min_idle))
        vib_norm = max(0.0, packet.vibration / self.limits.vibration.warning_threshold)
        mechanical_stress = min(1.0, max(0.0, (0.5 * rpm_norm + 0.5 * vib_norm)))

        # 3. Combustion Stress: Fuel flow exceedance and high power regime
        fuel_norm = min(1.0, packet.fuel_flow / self.limits.fuel_flow.max_takeoff)
        combustion_stress = min(1.0, max(0.0, fuel_norm * (1.1 if regime == OperatingRegime.TAKEOFF else 1.0)))

        # 4. Lubrication Stress: Oil temperature elevated or oil pressure low
        oil_t_norm = max(0.0, (packet.oil_temperature - 90.0) / (self.limits.oil_temperature.redline - 90.0))
        oil_p_deficit = max(0.0, (4.5 - packet.oil_pressure) / (4.5 - self.limits.oil_pressure.critical_low))
        lubrication_stress = min(1.0, max(0.0, (0.4 * oil_t_norm + 0.6 * oil_p_deficit)))

        # 5. Transient Stress: Rapid throttle movement
        throttle_derivative = abs(packet.throttle - self.last_throttle) / max(0.01, dt)
        self.last_throttle = packet.throttle
        transient_stress = min(1.0, throttle_derivative / 20.0)  # 20%/s is high transient

        # 6. Weighted Overall Instantaneous Stress (§64)
        overall_stress = (
            0.28 * thermal_stress +
            0.24 * mechanical_stress +
            0.20 * combustion_stress +
            0.18 * lubrication_stress +
            0.10 * transient_stress
        )
        overall_stress = round(min(1.0, max(0.0, overall_stress)), 3)

        # 7. Accumulate Cumulative Stress (Stress-hours equivalent)
        # 1 second of 1.0 stress = (1 / 3600) stress-hours
        delta_stress_hours = (overall_stress * dt) / 3600.0
        self.cumulative_stress += delta_stress_hours

        return MissionStressDetails(
            thermal=round(thermal_stress, 3),
            mechanical=round(mechanical_stress, 3),
            combustion=round(combustion_stress, 3),
            lubrication=round(lubrication_stress, 3),
            transient=round(transient_stress, 3),
            overall=overall_stress,
            cumulative_stress=round(self.cumulative_stress, 6),
        )
