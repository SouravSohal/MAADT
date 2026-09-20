"""
Mission Trajectory Profile Runner.
Interpolates flight waypoints (time, altitude, throttle, operational regime)
and drives the AeroEngineSimulator along realistic mission profiles.
Reference: overview.md Sections 31, 32, 55.
"""

from typing import Generator, List, Optional, Tuple

from config.engine_config import MissionConfig
from schemas.telemetry import OperatingRegime, TelemetryPacket
from .engine_sim import AeroEngineSimulator


class MissionRunner:
    """
    Executes flight missions by interpolating flight waypoints and
    driving the continuous aero-engine dynamical simulator.
    """

    def __init__(self, simulator: AeroEngineSimulator, mission_config: MissionConfig):
        self.sim = simulator
        self.mission = mission_config
        self.current_sim_time_s: float = 0.0
        self.current_regime: OperatingRegime = OperatingRegime.START

        # Parse waypoints: [time_min, alt_m, throttle_pct, regime_str]
        self.waypoints = sorted(self.mission.waypoints, key=lambda w: w[0])
        if not self.waypoints:
            # Fallback single cruise waypoint
            self.waypoints = [
                [0.0, 0.0, 0.0, "START"],
                [480.0, self.mission.target_altitude_m, 65.0, "CRUISE"]
            ]

    def get_interpolated_state(self, time_s: float) -> Tuple[float, float, OperatingRegime]:
        """
        Interpolates target altitude and throttle for the current simulation time.
        Returns (target_throttle_pct, target_altitude_m, regime).
        """
        time_min = time_s / 60.0

        # Before first waypoint
        if time_min <= self.waypoints[0][0]:
            wp = self.waypoints[0]
            regime = self._parse_regime(wp[3])
            return wp[2], wp[1], regime

        # After last waypoint
        if time_min >= self.waypoints[-1][0]:
            wp = self.waypoints[-1]
            regime = self._parse_regime(wp[3])
            return wp[2], wp[1], regime

        # Between waypoints: linear interpolation
        for i in range(len(self.waypoints) - 1):
            w1 = self.waypoints[i]
            w2 = self.waypoints[i + 1]
            t1, alt1, thr1, reg1 = w1[0], w1[1], w1[2], w1[3]
            t2, alt2, thr2, reg2 = w2[0], w2[1], w2[2], w2[3]

            if t1 <= time_min <= t2:
                fraction = (time_min - t1) / (t2 - t1) if (t2 - t1) > 0 else 0.0
                curr_alt = alt1 + fraction * (alt2 - alt1)
                curr_thr = thr1 + fraction * (thr2 - thr1)
                
                # Active flight regime selection
                if alt2 > alt1 and curr_alt > 100.0:
                    curr_reg = OperatingRegime.CLIMB
                elif alt2 < alt1 and curr_alt < 2000.0:
                    curr_reg = OperatingRegime.DESCENT
                else:
                    curr_reg = self._parse_regime(reg2 if fraction >= 0.5 else reg1)
                return curr_thr, curr_alt, curr_reg

        return 65.0, 5000.0, OperatingRegime.CRUISE

    def step(self, dt: float = 0.5) -> Tuple[TelemetryPacket, OperatingRegime]:
        """
        Advances the mission simulation by dt seconds.
        Returns the generated TelemetryPacket and current OperatingRegime.
        """
        target_thr, target_alt, regime = self.get_interpolated_state(self.current_sim_time_s)
        self.current_regime = regime

        packet = self.sim.step(throttle_pct=target_thr, altitude_m=target_alt, dt=dt)
        packet.mission_id = self.mission.id
        self.current_sim_time_s += dt

        return packet, regime

    def stream_mission(self, dt: float = 0.5, max_steps: Optional[int] = None) -> Generator[Tuple[TelemetryPacket, OperatingRegime], None, None]:
        """Generator that continuously yields mission telemetry packets."""
        steps = 0
        total_duration_s = self.mission.duration_minutes * 60.0
        while self.current_sim_time_s <= total_duration_s:
            if max_steps and steps >= max_steps:
                break
            yield self.step(dt=dt)
            steps += 1

    def _parse_regime(self, regime_str: str) -> OperatingRegime:
        try:
            return OperatingRegime(regime_str.upper())
        except ValueError:
            return OperatingRegime.CRUISE
