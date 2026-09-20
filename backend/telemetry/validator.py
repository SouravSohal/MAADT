"""
Telemetry Validation and Data Quality Layer.
Implements physical bounds checking, spike detection, rate-of-change validation,
noise estimation, and sensor quality tagging.
Reference: overview.md Sections 9, 10, 11.
"""

import math
from collections import deque
from typing import Dict, Optional, Tuple

from schemas.telemetry import SensorQuality, TelemetryPacket
from config.engine_config import EngineConfig


class TelemetryValidator:
    """
    Evaluates incoming raw telemetry against physical and operational bounds,
    detecting noise, spikes, staleness, and out-of-range values.
    """

    def __init__(self, config: EngineConfig, window_size: int = 15):
        self.config = config
        self.window_size = window_size
        
        # History buffers for rate-of-change, variance, and staleness detection
        self._history: Dict[str, deque] = {
            "rpm": deque(maxlen=window_size),
            "egt": deque(maxlen=window_size),
            "cht": deque(maxlen=window_size),
            "oil_pressure": deque(maxlen=window_size),
            "oil_temperature": deque(maxlen=window_size),
            "fuel_flow": deque(maxlen=window_size),
            "vibration": deque(maxlen=window_size),
            "battery_voltage": deque(maxlen=window_size),
        }
        
        # Track dynamic sensor trust scores (0.0 - 1.0)
        self.trust_scores: Dict[str, float] = {k: 1.0 for k in self._history.keys()}

        # Maximum physically plausible rates of change per second (dx/dt)
        self.max_rate_of_change: Dict[str, float] = {
            "rpm": 1200.0,            # Max 1200 RPM/s jump
            "egt": 60.0,              # Max 60°C/s jump
            "cht": 15.0,              # Max 15°C/s thermal inertia limit
            "oil_pressure": 4.0,       # Max 4 bar/s
            "oil_temperature": 5.0,   # Max 5°C/s
            "fuel_flow": 25.0,        # Max 25 L/h/s
            "vibration": 3.0,         # Max 3 g/s
            "battery_voltage": 8.0,   # Max 8 V/s
        }

    def validate_and_tag(self, packet: TelemetryPacket, dt: float = 0.5) -> TelemetryPacket:
        """
        Validates telemetry packet in-place, annotating sensor_quality and sensor_trust.
        Returns the annotated packet.
        """
        limits = self.config.operating_limits
        qualities: Dict[str, SensorQuality] = {}
        
        # 1. Evaluate RPM
        qualities["rpm"] = self._evaluate_sensor(
            name="rpm",
            val=packet.rpm,
            abs_min=0.0,
            abs_max=limits.rpm.redline * 1.25,
            dt=dt
        )

        # 2. Evaluate EGT
        qualities["egt"] = self._evaluate_sensor(
            name="egt",
            val=packet.egt,
            abs_min=0.0,
            abs_max=limits.egt.redline * 1.3,
            dt=dt
        )

        # 3. Evaluate CHT
        qualities["cht"] = self._evaluate_sensor(
            name="cht",
            val=packet.cht,
            abs_min=-20.0,
            abs_max=limits.cht.redline * 1.3,
            dt=dt
        )

        # 4. Evaluate Oil Pressure
        qualities["oil_pressure"] = self._evaluate_sensor(
            name="oil_pressure",
            val=packet.oil_pressure,
            abs_min=0.0,
            abs_max=limits.oil_pressure.max_limit * 1.5,
            dt=dt
        )

        # 5. Evaluate Oil Temperature
        qualities["oil_temperature"] = self._evaluate_sensor(
            name="oil_temperature",
            val=packet.oil_temperature,
            abs_min=-20.0,
            abs_max=limits.oil_temperature.redline * 1.3,
            dt=dt
        )

        # 6. Evaluate Fuel Flow
        qualities["fuel_flow"] = self._evaluate_sensor(
            name="fuel_flow",
            val=packet.fuel_flow,
            abs_min=0.0,
            abs_max=limits.fuel_flow.max_takeoff * 1.8,
            dt=dt
        )

        # 7. Evaluate Vibration
        qualities["vibration"] = self._evaluate_sensor(
            name="vibration",
            val=packet.vibration,
            abs_min=0.0,
            abs_max=limits.vibration.critical_limit * 3.0,
            dt=dt
        )

        # 8. Evaluate Battery Voltage
        qualities["battery_voltage"] = self._evaluate_sensor(
            name="battery_voltage",
            val=packet.battery_voltage,
            abs_min=10.0,
            abs_max=36.0,
            dt=dt
        )

        # Update dynamic sensor trust scores (§11)
        self._update_trust_scores(qualities)

        packet.sensor_quality = qualities
        packet.sensor_trust = dict(self.trust_scores)
        return packet

    def _evaluate_sensor(
        self,
        name: str,
        val: Optional[float],
        abs_min: float,
        abs_max: float,
        dt: float
    ) -> SensorQuality:
        """Determines the data quality state of a single sensor signal."""
        # Check missing or NaN
        if val is None or math.isnan(val) or math.isinf(val):
            return SensorQuality.MISSING

        # Check physical boundary limit
        if val < abs_min or val > abs_max:
            return SensorQuality.OUT_OF_RANGE

        buf = self._history[name]

        # Rate of change check (impossible spike)
        if len(buf) > 0 and dt > 0:
            last_val = buf[-1]
            rate = abs(val - last_val) / dt
            max_rate = self.max_rate_of_change.get(name, 1000.0)
            if rate > max_rate:
                buf.append(val)
                return SensorQuality.SUSPECT

        # Staleness check: check if value has not moved even a tiny bit for window_size frames
        # when the engine is active
        if len(buf) >= self.window_size:
            diffs = [abs(buf[i] - buf[i - 1]) for i in range(1, len(buf))]
            if max(diffs) < 1e-6:
                buf.append(val)
                return SensorQuality.STALE

        # High-frequency noise detection
        if len(buf) >= 5:
            mean = sum(buf) / len(buf)
            variance = sum((x - mean) ** 2 for x in buf) / len(buf)
            # If variance is abnormally massive
            if name == "egt" and variance > 400.0:  # std > 20C instant jitter
                buf.append(val)
                return SensorQuality.NOISY
            elif name == "rpm" and variance > 10000.0: # std > 100 RPM instant jitter
                buf.append(val)
                return SensorQuality.NOISY

        buf.append(val)
        return SensorQuality.VALID

    def _update_trust_scores(self, qualities: Dict[str, SensorQuality]):
        """
        Dynamically adjusts trust scores (§11):
        Trust increases with VALID signals, decays with NOISY, STALE, SUSPECT, or OUT_OF_RANGE.
        """
        for sensor, quality in qualities.items():
            curr = self.trust_scores.get(sensor, 1.0)
            if quality == SensorQuality.VALID:
                # Gradual recovery
                new_trust = min(1.0, curr + 0.02)
            elif quality in (SensorQuality.NOISY, SensorQuality.SUSPECT):
                # Moderate penalty
                new_trust = max(0.1, curr - 0.08)
            elif quality == SensorQuality.STALE:
                # Progressive decay
                new_trust = max(0.05, curr - 0.15)
            elif quality == SensorQuality.OUT_OF_RANGE:
                # Severe penalty
                new_trust = max(0.0, curr - 0.35)
            elif quality == SensorQuality.MISSING:
                new_trust = max(0.0, curr - 0.50)
            else:
                new_trust = curr

            self.trust_scores[sensor] = round(new_trust, 3)
