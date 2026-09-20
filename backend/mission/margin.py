"""
Multi-Factor Mission Survival Margin Engine.
Calculates project-specific Mission Margin % by synthesizing thermal, load, fuel,
degradation, and RUL headroom against mission operational requirements.
Reference: overview.md Sections 35, 79.
"""

from dataclasses import dataclass
import math
from typing import Dict, Optional

from config.engine_config import EngineConfig
from schemas.telemetry import TelemetryPacket, DigitalTwinState


@dataclass
class MissionMarginBreakdown:
    """Detailed breakdown of multi-factor mission capability headroom."""
    thermal_margin: float       # % headroom before reaching redline CHT/EGT
    load_margin: float          # % reserve power margin at current density altitude
    fuel_margin: float          # % fuel capacity vs remaining planned burn
    degradation_margin: float   # % health headroom above 50.0 overhaul threshold
    rul_margin: float           # % RUL buffer over planned mission hours
    composite_margin: float     # Combined Mission Survival Margin % [-100.0 to 100.0]
    confidence: float           # Estimation confidence score [0.0 to 1.0]
    is_critical: bool           # True if composite margin < 15% or health < 50
    recommendation: str         # "SAFE TO CONTINUE" | "REDUCE POWER" | "ABORT / RTB"


class MissionMarginCalculator:
    """
    Computes calibrated Mission Survival Margin based on the difference between
    Available Engine Capability and Required Mission Capability (§35).
    """

    def __init__(self, config: EngineConfig):
        self.config = config
        self.limits = config.operating_limits

    def compute_margin(
        self,
        current_health: float,
        packet: TelemetryPacket,
        anomaly_score: float = 0.0,
        planned_mission_hours_remaining: float = 4.0,
        rul_hours: Optional[float] = None,
        twin_confidence: float = 0.95
    ) -> MissionMarginBreakdown:
        """
        Synthesizes individual subsystem margins into a unified Mission Survival Margin.
        """
        # 1. Thermal Margin: Distance from current temps to redlines
        # CHT: 185 nominal max, 230 redline
        cht_headroom = max(0.0, (self.limits.cht.redline - packet.cht) / (self.limits.cht.redline - self.limits.cht.nominal_min))
        # EGT: 760 nominal max, 880 redline
        egt_headroom = max(0.0, (self.limits.egt.redline - packet.egt) / (self.limits.egt.redline - self.limits.egt.nominal_min))
        thermal_margin = round(min(100.0, max(0.0, (0.6 * cht_headroom + 0.4 * egt_headroom) * 100.0)), 1)

        # 2. Load / Power Reserve Margin: Available throttle headroom
        # Lower density at altitude reduces margin
        alt_density_factor = max(0.6, 1.0 - (packet.altitude / 20000.0))
        throttle_reserve = max(0.0, 100.0 - packet.throttle)
        load_margin = round(min(100.0, max(0.0, throttle_reserve * alt_density_factor)), 1)

        # 3. Fuel Margin: Flow rate vs typical cruise
        nominal_flow = self.limits.fuel_flow.nominal_cruise
        if packet.fuel_flow <= nominal_flow:
            fuel_margin = 100.0
        else:
            flow_penalty = (packet.fuel_flow - nominal_flow) / (self.limits.fuel_flow.max_takeoff - nominal_flow)
            fuel_margin = round(max(0.0, (1.0 - flow_penalty) * 100.0), 1)

        # 4. Degradation Margin: Health headroom above overhaul threshold (50.0)
        # 100% health = 100% margin; 50% health = 0% margin; <50% = negative margin
        degradation_margin = round(max(-100.0, min(100.0, (current_health - 50.0) * 2.0)), 1)

        # 5. RUL Margin: Ratio of RUL hours remaining to planned flight duration
        effective_rul = rul_hours if rul_hours is not None else 600.0
        safe_mission_buffer = max(1.0, planned_mission_hours_remaining)
        rul_ratio = effective_rul / safe_mission_buffer
        if rul_ratio >= 10.0:
            rul_margin = 100.0
        elif rul_ratio >= 1.0:
            rul_margin = round((rul_ratio / 10.0) * 100.0, 1)
        else:
            # RUL is less than mission duration: danger
            rul_margin = round((rul_ratio - 1.0) * 100.0, 1)

        # 6. Composite Mission Margin (§35)
        # Weighted combination penalized by active anomaly
        base_composite = (
            0.30 * degradation_margin +
            0.25 * thermal_margin +
            0.20 * rul_margin +
            0.15 * load_margin +
            0.10 * fuel_margin
        )

        # Anomaly penalty factor: severe anomaly heavily degrades survival margin
        anomaly_factor = max(0.1, 1.0 - (0.75 * anomaly_score))
        composite_margin = round(max(-100.0, min(100.0, base_composite * anomaly_factor)), 1)

        # 7. Operational Recommendation & Criticality
        is_critical = composite_margin < 15.0 or current_health < 50.0 or packet.cht >= self.limits.cht.warning_threshold
        if composite_margin >= 45.0 and not is_critical:
            recommendation = "SAFE TO CONTINUE MISSION"
        elif composite_margin >= 15.0:
            recommendation = "CAUTION: REDUCE THROTTLE OR DESCEND TO SHADOW ALTITUDE"
        else:
            recommendation = "ABORT MISSION: IMMEDIATE RETURN TO BASE (RTB) RECOMMENDED"

        # 8. Confidence estimation
        calibrated_conf = round(twin_confidence * (1.0 - 0.2 * anomaly_score), 2)

        return MissionMarginBreakdown(
            thermal_margin=thermal_margin,
            load_margin=load_margin,
            fuel_margin=fuel_margin,
            degradation_margin=degradation_margin,
            rul_margin=rul_margin,
            composite_margin=composite_margin,
            confidence=max(0.2, min(0.98, calibrated_conf)),
            is_critical=is_critical,
            recommendation=recommendation
        )
