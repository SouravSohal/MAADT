"""
Degradation Trajectory Tracker.
Tracks continuous health index decline, first derivative (degradation slope),
second derivative (degradation acceleration), and classifies degradation dynamics.
Reference: overview.md Sections 23, 25.
"""

from collections import deque
from dataclasses import dataclass
import numpy as np
from typing import Deque, Dict, List, Optional


@dataclass
class DegradationMetrics:
    """Quantitative metrics of engine health decay."""
    current_health: float
    health_slope_per_hour: float    # % decline per operating hour
    health_acceleration: float      # %/h^2
    degradation_trend: str          # STABLE | LINEAR | ACCELERATING | SUDDEN
    mission_total_decay: float      # Total % drop during current mission
    is_accelerating: bool


class DegradationTracker:
    """
    Maintains a rolling window of health index evaluations to estimate
    trajectory curvature, decay velocity, and dynamic trend classification.
    """

    def __init__(self, window_size: int = 120, baseline_health: float = 100.0):
        self.window_size = window_size
        self.initial_health: float = baseline_health
        self.current_health: float = baseline_health
        
        # History of (sim_time_s, health_index)
        self._history: Deque[tuple[float, float]] = deque(maxlen=window_size)

    def update(self, health_index: float, sim_time_s: float) -> DegradationMetrics:
        """
        Updates tracker with latest health observation and computes velocity and acceleration.
        """
        self.current_health = max(0.0, min(100.0, health_index))
        self._history.append((sim_time_s, self.current_health))

        # Defaults
        slope_per_hour = 0.0
        accel = 0.0
        trend = "STABLE"
        is_accel = False

        if len(self._history) >= 10:
            times = np.array([pt[0] for pt in self._history])
            healths = np.array([pt[1] for pt in self._history])

            # Convert time delta to hours
            time_span_h = (times[-1] - times[0]) / 3600.0

            if time_span_h > 1e-4:
                # 1. First-order linear regression for slope (dHI/dt)
                # polyfit returns [slope, intercept]
                p = np.polyfit(times / 3600.0, healths, 1)
                slope_per_hour = float(p[0])  # Negative for degradation

                # 2. Second-order polynomial fit for acceleration (d^2HI/dt^2)
                if len(self._history) >= 20:
                    p2 = np.polyfit(times / 3600.0, healths, 2)
                    # p2[0]*t^2 + p2[1]*t + p2[2] -> acceleration is 2 * p2[0]
                    accel = float(2.0 * p2[0])

                # 3. Dynamic Trend Classification (§25)
                # Check for sudden drop over recent 5 frames
                recent_drop = self._history[-5][1] - self.current_health if len(self._history) >= 5 else 0.0
                if recent_drop > 2.5:
                    trend = "SUDDEN"
                    is_accel = True
                elif accel < -0.10 or slope_per_hour < -0.60:
                    trend = "ACCELERATING"
                    is_accel = True
                elif slope_per_hour < -0.05:
                    trend = "LINEAR"
                else:
                    trend = "STABLE"

        mission_decay = max(0.0, self.initial_health - self.current_health)

        return DegradationMetrics(
            current_health=round(self.current_health, 2),
            health_slope_per_hour=round(slope_per_hour, 3),
            health_acceleration=round(accel, 4),
            degradation_trend=trend,
            mission_total_decay=round(mission_decay, 2),
            is_accelerating=is_accel,
        )
