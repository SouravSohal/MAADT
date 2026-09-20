"""
Controlled Fault Injection Framework.
Supports physical engine degradation and sensor instrumentation faults with
configurable onset, progression dynamics (instant, linear, exponential), and severity.
Reference: overview.md Sections 20, 53, 54, 74.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import time

from schemas.telemetry import FaultType


class FaultProgression(str, Enum):
    """Rate profile for fault development."""
    INSTANT = "INSTANT"
    LINEAR = "LINEAR"
    EXPONENTIAL = "EXPONENTIAL"


@dataclass
class ActiveFault:
    """Represents an active or pending fault scenario."""
    id: str
    fault_type: FaultType
    severity: float = 0.5                  # [0.0 - 1.0]
    progression: FaultProgression = FaultProgression.LINEAR
    onset_seconds: float = 0.0             # Delay before onset begins
    ramp_duration_seconds: float = 60.0    # Time to ramp to peak severity
    duration_seconds: float = 3600.0       # Total duration (0 for infinite)
    target_sensor: Optional[str] = None    # Specific sensor for sensor faults (e.g. "egt")
    param_override: Dict[str, float] = field(default_factory=dict)
    
    # Internal runtime state
    start_sim_time: Optional[float] = None
    active: bool = False

    def get_effective_severity(self, sim_time: float) -> float:
        """Calculates current progression-scaled severity [0.0 - 1.0]."""
        if self.start_sim_time is None:
            self.start_sim_time = sim_time

        elapsed = sim_time - self.start_sim_time
        if elapsed < self.onset_seconds:
            return 0.0

        active_elapsed = elapsed - self.onset_seconds
        if self.duration_seconds > 0 and active_elapsed > self.duration_seconds:
            return 0.0

        if self.progression == FaultProgression.INSTANT:
            return self.severity

        progress = min(1.0, active_elapsed / max(1.0, self.ramp_duration_seconds))
        if self.progression == FaultProgression.EXPONENTIAL:
            progress = progress ** 2

        return self.severity * progress


class FaultInjector:
    """
    Coordinates active fault scenarios and mutates mechanical engine state
    or raw telemetry signals.
    """

    def __init__(self):
        self._faults: Dict[str, ActiveFault] = {}

    def inject_fault(
        self,
        fault_type: FaultType,
        severity: float = 0.5,
        progression: FaultProgression = FaultProgression.LINEAR,
        onset_seconds: float = 0.0,
        ramp_duration_seconds: float = 60.0,
        duration_seconds: float = 0.0,
        target_sensor: Optional[str] = None,
        fault_id: Optional[str] = None,
    ) -> str:
        """Registers a fault to be injected into the simulation."""
        fid = fault_id or f"{fault_type.value}_{int(time.time() * 1000) % 10000}"
        self._faults[fid] = ActiveFault(
            id=fid,
            fault_type=fault_type,
            severity=max(0.0, min(1.0, severity)),
            progression=progression,
            onset_seconds=onset_seconds,
            ramp_duration_seconds=ramp_duration_seconds,
            duration_seconds=duration_seconds,
            target_sensor=target_sensor,
        )
        return fid

    def remove_fault(self, fault_id: str):
        """Removes an active fault scenario."""
        self._faults.pop(fault_id, None)

    def clear_all(self):
        """Clears all active and scheduled faults."""
        self._faults.clear()

    def list_active_faults(self, sim_time: float) -> List[Dict]:
        """Returns all currently executing faults with their effective severities."""
        result = []
        for fid, fault in self._faults.items():
            eff = fault.get_effective_severity(sim_time)
            if eff > 0.0:
                result.append({
                    "id": fid,
                    "fault_type": fault.fault_type.value,
                    "effective_severity": round(eff, 3),
                    "target_sensor": fault.target_sensor,
                })
        return result

    def apply_mechanical_faults(self, sim_state: Dict[str, float], sim_time: float):
        """
        Mutates the mechanical simulation variables (EGT, CHT, RPM, Oil, Vibration, Fuel Flow)
        before telemetry sensor observation.
        """
        for fault in self._faults.values():
            sev = fault.get_effective_severity(sim_time)
            if sev <= 0.0:
                continue

            ftype = fault.fault_type

            # 1. Injector Abnormality (§20, §53): High fuel flow, elevated EGT, slight RPM instability
            if ftype == FaultType.INJECTOR_ABNORMALITY:
                sim_state["fuel_flow"] += sim_state["fuel_flow"] * (0.18 * sev)
                sim_state["egt"] += (45.0 * sev)
                sim_state["cht"] += (12.0 * sev)
                sim_state["vibration"] += (0.12 * sev)

            # 2. Overheating (§20, §74): Radiator blockage or coolant loss
            elif ftype == FaultType.OVERHEATING:
                sim_state["cht"] += (55.0 * sev)
                sim_state["oil_temperature"] += (30.0 * sev)
                sim_state["egt"] += (25.0 * sev)

            # 3. Cylinder Misfire (§20, §74): Periodic lost combustion cycle
            elif ftype == FaultType.MISFIRE:
                sim_state["rpm"] -= (180.0 * sev)
                sim_state["egt"] -= (75.0 * sev)
                sim_state["vibration"] += (0.45 * sev)

            # 4. Lubrication Issue (§20, §53): Oil pump decay or line leakage
            elif ftype == FaultType.LUBRICATION_ISSUE:
                # Progressive oil pressure loss: e.g. 4.8 -> 2.2 bar
                sim_state["oil_pressure"] = max(0.5, sim_state["oil_pressure"] - (2.6 * sev))
                sim_state["oil_temperature"] += (22.0 * sev)
                sim_state["vibration"] += (0.15 * sev)

            # 5. Abnormal Vibration (§20): Propeller or main bearing imbalance
            elif ftype == FaultType.ABNORMAL_VIBRATION:
                sim_state["vibration"] += (0.85 * sev)
                sim_state["rpm"] -= (40.0 * sev)

            # 6. Combustion Instability (§20): Lean/rich surge
            elif ftype == FaultType.COMBUSTION_INSTABILITY:
                sim_state["fuel_flow"] += sim_state["fuel_flow"] * (0.12 * sev)
                sim_state["rpm"] -= (60.0 * sev)
                sim_state["egt"] += (35.0 * sev)

            # 7. Electrical Abnormality (§20): Alternator diode failure
            elif ftype == FaultType.ELECTRICAL_ABNORMALITY:
                sim_state["battery_voltage"] = max(20.0, sim_state["battery_voltage"] - (4.5 * sev))
                sim_state["alternator_current"] = max(0.0, sim_state["alternator_current"] - (12.0 * sev))

    def apply_sensor_faults(self, sensor_readings: Dict[str, float], sim_time: float):
        """
        Applies instrument-level faults (sensor drift, freeze, out-of-range)
        directly to sensor outputs AFTER mechanical state has been computed.
        This tests the Sensor Trust Layer's ability to avoid false engine alarms (§10, §11).
        """
        for fault in self._faults.values():
            sev = fault.get_effective_severity(sim_time)
            if sev <= 0.0:
                continue

            target = fault.target_sensor or "egt"
            if target not in sensor_readings:
                continue

            # Sensor Drift (§10, §74 Scenario 6)
            if fault.fault_type == FaultType.SENSOR_DRIFT:
                drift_bias = 80.0 * sev if target in ("egt", "cht") else 2.0 * sev
                sensor_readings[target] += drift_bias

            # Sensor Failure / Out of Range
            elif fault.fault_type == FaultType.SENSOR_FAILURE:
                if sev > 0.5:
                    # Drive out of bounds or freeze
                    sensor_readings[target] = 1250.0 if target == "egt" else 0.0
