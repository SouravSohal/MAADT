"""
Counterfactual Mission Simulation Engine.
Predicts engine trajectory, thermal evolution, and degradation progression under
alternative pilot decisions, environmental shifts, or fault scenarios.
Reference: overview.md Sections 34, 38, 79.
"""

from dataclasses import dataclass, field
import copy
import math
from typing import Dict, List, Optional

from config.engine_config import EngineConfig
from core.physics_model import AeroPistonPhysicsModel
from simulation.environment import AtmosphericEnvironment
from schemas.telemetry import TelemetryPacket, DigitalTwinState
from .margin import MissionMarginCalculator, MissionMarginBreakdown


@dataclass
class TrajectoryPoint:
    """Predicted engine state at future time t."""
    time_offset_min: float
    throttle: float
    altitude: float
    rpm: float
    cht: float
    egt: float
    oil_pressure: float
    fuel_flow: float
    predicted_health: float
    survival_margin: float


@dataclass
class ScenarioOutcome:
    """Aggregated prediction results for a single counterfactual branch."""
    scenario_id: str
    scenario_name: str
    description: str
    target_throttle: float
    target_altitude: float
    horizon_minutes: float
    peak_cht: float
    peak_egt: float
    final_health: float
    final_survival_margin: float
    margin_breakdown: MissionMarginBreakdown
    safety_verdict: str  # "OPTIMAL" | "ACCEPTABLE" | "HAZARDOUS" | "PROHIBITED"
    recommendation: str
    trajectory: List[TrajectoryPoint] = field(default_factory=list)


class CounterfactualSimulator:
    """
    Simulates counterfactual "what-if" branches forward in time (§34, §38, §79).
    Enables pilots and autonomous mission planners to evaluate trade-offs
    between maintaining airspeed, descending, throttling back, or diverting.
    """

    def __init__(self, config: EngineConfig):
        self.config = config
        self.physics = AeroPistonPhysicsModel(config)
        self.environment = AtmosphericEnvironment()
        self.margin_calc = MissionMarginCalculator(config)

    def simulate_scenario(
        self,
        current_telemetry: TelemetryPacket,
        current_health: float,
        target_throttle: float,
        target_altitude: float,
        horizon_minutes: float = 30.0,
        active_anomaly_score: float = 0.0,
        scenario_id: str = "custom",
        scenario_name: str = "Custom Scenario",
        description: str = "User specified counterfactual flight condition",
        time_step_sec: float = 60.0,
    ) -> ScenarioOutcome:
        """
        Rolls forward engine thermodynamic ODEs and degradation models across the horizon.
        """
        t_steps = int((horizon_minutes * 60.0) / time_step_sec)
        
        curr_cht = current_telemetry.cht
        curr_egt = current_telemetry.egt
        curr_oil_p = current_telemetry.oil_pressure
        curr_health = current_health

        trajectory: List[TrajectoryPoint] = []
        peak_cht = curr_cht
        peak_egt = curr_egt

        # Environment at target altitude
        ambient_temp, _, _, _ = self.environment.get_conditions(target_altitude)

        # Target physics steady state
        exp_target = self.physics.calculate_expected_state(
            throttle_pct=target_throttle,
            altitude_m=target_altitude,
            ambient_temp_c=ambient_temp
        )

        for step in range(t_steps + 1):
            t_min = round((step * time_step_sec) / 60.0, 1)

            # Thermal convergence towards target steady state
            tau_cht = self.config.physics_parameters.thermal_cht_time_constant_s  # e.g. 45s
            tau_egt = self.config.physics_parameters.thermal_egt_time_constant_s  # e.g. 6s

            alpha_cht = 1.0 - math.exp(-time_step_sec / max(1.0, tau_cht))
            alpha_egt = 1.0 - math.exp(-time_step_sec / max(1.0, tau_egt))

            curr_cht += alpha_cht * (exp_target.expected_cht - curr_cht)
            curr_egt += alpha_egt * (exp_target.expected_egt - curr_egt)

            # Check peaks
            if curr_cht > peak_cht:
                peak_cht = curr_cht
            if curr_egt > peak_egt:
                peak_egt = curr_egt

            # Simulated health decay rate under counterfactual stress
            # Higher throttle and altitude accelerate decay if anomalous
            stress_multiplier = (target_throttle / 65.0) * (1.0 + (target_altitude / 10000.0) * 0.2)
            decay_per_min = 0.005 * stress_multiplier * (1.0 + 2.0 * active_anomaly_score)
            curr_health = max(0.0, curr_health - (decay_per_min * (time_step_sec / 60.0)))

            # Mock telemetry packet for margin evaluation
            pkt_sim = TelemetryPacket(
                timestamp=current_telemetry.timestamp + (step * time_step_sec),
                rpm=exp_target.expected_rpm,
                cht=curr_cht,
                egt=curr_egt,
                oil_pressure=curr_oil_p,
                oil_temperature=current_telemetry.oil_temperature,
                fuel_flow=exp_target.expected_fuel_flow,
                vibration=current_telemetry.vibration,
                throttle=target_throttle,
                altitude=target_altitude,
                ambient_temperature=ambient_temp
            )

            margin_info = self.margin_calc.compute_margin(
                current_health=curr_health,
                packet=pkt_sim,
                anomaly_score=active_anomaly_score,
                planned_mission_hours_remaining=max(0.5, (horizon_minutes - t_min) / 60.0)
            )

            trajectory.append(TrajectoryPoint(
                time_offset_min=t_min,
                throttle=round(target_throttle, 1),
                altitude=round(target_altitude, 1),
                rpm=round(exp_target.expected_rpm, 1),
                cht=round(curr_cht, 1),
                egt=round(curr_egt, 1),
                oil_pressure=round(curr_oil_p, 2),
                fuel_flow=round(exp_target.expected_fuel_flow, 1),
                predicted_health=round(curr_health, 1),
                survival_margin=margin_info.composite_margin
            ))

        final_point = trajectory[-1]
        final_margin_info = self.margin_calc.compute_margin(
            current_health=final_point.predicted_health,
            packet=pkt_sim,
            anomaly_score=active_anomaly_score,
            planned_mission_hours_remaining=1.0
        )

        # Safety Verdict Determination
        limits = self.config.operating_limits
        if peak_cht >= limits.cht.redline or peak_egt >= limits.egt.redline or final_margin_info.composite_margin < 0.0:
            safety_verdict = "PROHIBITED"
            rec = "CRITICAL RISK: Projected thermal exceedance or negative survival margin."
        elif peak_cht >= limits.cht.warning_threshold or final_margin_info.composite_margin < 20.0:
            safety_verdict = "HAZARDOUS"
            rec = "HIGH RISK: Approaching warning thresholds. Engine wear will accelerate."
        elif final_margin_info.composite_margin < 45.0:
            safety_verdict = "ACCEPTABLE"
            rec = "MODERATE: Sustainable with elevated caution. Monitor thermal headroom."
        else:
            safety_verdict = "OPTIMAL"
            rec = "FAVORABLE: High survival margin with minimal component degradation."

        return ScenarioOutcome(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            description=description,
            target_throttle=target_throttle,
            target_altitude=target_altitude,
            horizon_minutes=horizon_minutes,
            peak_cht=round(peak_cht, 1),
            peak_egt=round(peak_egt, 1),
            final_health=round(final_point.predicted_health, 1),
            final_survival_margin=final_margin_info.composite_margin,
            margin_breakdown=final_margin_info,
            safety_verdict=safety_verdict,
            recommendation=rec,
            trajectory=trajectory
        )

    def compare_operational_branches(
        self,
        current_telemetry: TelemetryPacket,
        current_health: float,
        active_anomaly_score: float = 0.0,
        horizon_minutes: float = 30.0
    ) -> List[ScenarioOutcome]:
        """
        Simulates and contrasts the 4 canonical operational decision branches (§38):
        1. Maintain Flight Plan
        2. Throttle Reduction (-15%)
        3. Step-Down Altitude (-2,000m)
        4. Immediate Return to Base (RTB)
        """
        curr_throt = current_telemetry.throttle
        curr_alt = current_telemetry.altitude

        # Branch 1: Maintain
        b1 = self.simulate_scenario(
            current_telemetry=current_telemetry,
            current_health=current_health,
            target_throttle=curr_throt,
            target_altitude=curr_alt,
            horizon_minutes=horizon_minutes,
            active_anomaly_score=active_anomaly_score,
            scenario_id="maintain",
            scenario_name="Continue Current Flight Plan",
            description="Maintain current throttle and cruise altitude."
        )

        # Branch 2: Throttle Down (-15%)
        b2 = self.simulate_scenario(
            current_telemetry=current_telemetry,
            current_health=current_health,
            target_throttle=max(40.0, curr_throt - 15.0),
            target_altitude=curr_alt,
            horizon_minutes=horizon_minutes,
            active_anomaly_score=active_anomaly_score,
            scenario_id="throttle_down",
            scenario_name="Throttle Reduction (-15%)",
            description="Reduce engine load to de-stress combustion and thermal cylinders."
        )

        # Branch 3: Step-Down Altitude
        descend_alt = max(1500.0, curr_alt - 2000.0)
        b3 = self.simulate_scenario(
            current_telemetry=current_telemetry,
            current_health=current_health,
            target_throttle=max(45.0, curr_throt - 5.0),
            target_altitude=descend_alt,
            horizon_minutes=horizon_minutes,
            active_anomaly_score=active_anomaly_score,
            scenario_id="descend",
            scenario_name=f"Descend to {int(descend_alt)}m",
            description="Descend to higher air density for cooler charge air and reduced turbo pressure ratio."
        )

        # Branch 4: Return to Base (RTB)
        b4 = self.simulate_scenario(
            current_telemetry=current_telemetry,
            current_health=current_health,
            target_throttle=48.0,
            target_altitude=1200.0,
            horizon_minutes=horizon_minutes,
            active_anomaly_score=active_anomaly_score,
            scenario_id="rtb",
            scenario_name="Return To Base (RTB)",
            description="Execute mission abort, descend to traffic pattern altitude at minimum continuous power."
        )

        return [b1, b2, b3, b4]
