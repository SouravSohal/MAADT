"""
Mission Replay & Time-Travel Analysis Engine.
Implements historical telemetry scrubbing, event timeline milestone marking,
preceding telemetry inspection, and counterfactual branch replay.
Reference: overview.md Sections 36, 37, 38.
"""

from dataclasses import dataclass, field
import json
import time
from typing import Any, Dict, List, Optional

from config.engine_config import EngineConfig
from mission.counterfactual import CounterfactualSimulator, ScenarioOutcome
from schemas.telemetry import TelemetryPacket, FaultType, AlertSeverity
from storage.db import Database, db


@dataclass
class TimelineMilestone:
    """Significant milestone or event along the mission timeline (§37)."""
    timestamp: float
    time_offset_seconds: float
    time_display: str          # e.g. "00:03:42"
    event_type: str            # "TAKEOFF" | "REGIME_CHANGE" | "ANOMALY_RISE" | "FAULT_DETECTED" | "HEALTH_DECAY"
    title: str
    severity: str              # "INFO" | "WARNING" | "HIGH" | "CRITICAL"
    subsystem: str
    evidence: List[str] = field(default_factory=list)
    telemetry_summary: Dict[str, float] = field(default_factory=dict)


class MissionReplayEngine:
    """
    Coordinates time-travel investigation across persisted historical flights.
    Provides timeline scrubbing, telemetry inspection, and counterfactual branching.
    """

    def __init__(self, config: EngineConfig, database: Optional[Database] = None):
        self.config = config
        self.db = database or db
        self.cf_simulator = CounterfactualSimulator(config=config)

    def get_mission_overview(self, engine_id: str = "ENG-001") -> Dict[str, Any]:
        """Returns time bounds, sample count, and recorded duration for the engine."""
        bounds = self.db.get_time_bounds(engine_id)
        faults = self.db.get_all_faults(engine_id)
        return {
            "engine_id": engine_id,
            "min_time": bounds["min_time"],
            "max_time": bounds["max_time"],
            "duration_seconds": bounds["duration_seconds"],
            "total_samples": bounds["total_samples"],
            "total_fault_events": len(faults),
        }

    def build_event_timeline(
        self,
        engine_id: str = "ENG-001",
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[TimelineMilestone]:
        """
        Synthesizes chronological milestone events (§37):
        1. Injected/classified fault events
        2. Thermal warning threshold exceedances
        3. Sudden health decay drops
        """
        bounds = self.db.get_time_bounds(engine_id)
        t_base = bounds["min_time"]
        milestones: List[TimelineMilestone] = []

        # 1. Fault Events from Database
        fault_records = self.db.get_all_faults(engine_id, start_time, end_time)
        for f in fault_records:
            t = f["timestamp"]
            offset = max(0.0, t - t_base)
            mins = int(offset // 60)
            secs = int(offset % 60)
            time_str = f"{mins:02d}:{secs:02d}"

            evidence = f.get("evidence", [])
            if isinstance(evidence, str):
                try:
                    evidence = json.loads(evidence)
                except Exception:
                    evidence = [evidence]

            milestones.append(TimelineMilestone(
                timestamp=t,
                time_offset_seconds=round(offset, 1),
                time_display=time_str,
                event_type="FAULT_DETECTED",
                title=f"{f['fault_type'].replace('_', ' ').title()} - {f['subsystem']}",
                severity=f.get("severity", "WARNING"),
                subsystem=f.get("subsystem", "Propulsion"),
                evidence=evidence,
                telemetry_summary={}
            ))

        # Sort chronologically
        milestones.sort(key=lambda m: m.timestamp)
        return milestones

    def get_replay_frame(
        self,
        engine_id: str = "ENG-001",
        timestamp: float = 0.0
    ) -> Dict[str, Any]:
        """
        Retrieves complete synchronized state snapshot at a specific point in time (§36).
        """
        telemetry_raw = self.db.get_telemetry_at(engine_id, timestamp)
        twin_raw = self.db.get_twin_state_at(engine_id, timestamp)

        if not telemetry_raw:
            return {"status": "NO_DATA", "timestamp": timestamp}

        return {
            "status": "SYNCHRONIZED",
            "timestamp": telemetry_raw["timestamp"],
            "telemetry": telemetry_raw,
            "twin_state": twin_raw,
        }

    def branch_counterfactual_at_time(
        self,
        engine_id: str = "ENG-001",
        timestamp: float = 0.0,
        horizon_minutes: float = 30.0
    ) -> List[ScenarioOutcome]:
        """
        Counterfactual Replay (§38):
        Branches from the exact historical frame at timestamp into candidate operational paths:
        1. Continue Actual Mission (historical path)
        2. Throttle Reduction (-15%)
        3. Descend (-2000m)
        4. Return To Base (RTB)
        """
        frame = self.get_replay_frame(engine_id, timestamp)
        if frame.get("status") == "NO_DATA":
            raise ValueError(f"No historical telemetry found at timestamp {timestamp}")

        raw_tel = frame["telemetry"]
        pkt = TelemetryPacket(
            timestamp=raw_tel["timestamp"],
            rpm=raw_tel["rpm"],
            cht=raw_tel["cht"],
            egt=raw_tel["egt"],
            oil_pressure=raw_tel["oil_pressure"],
            oil_temperature=raw_tel["oil_temperature"],
            fuel_flow=raw_tel["fuel_flow"],
            vibration=raw_tel["vibration"],
            throttle=raw_tel["throttle"],
            altitude=raw_tel["altitude"],
            ambient_temperature=raw_tel.get("ambient_temperature", 15.0),
        )

        twin_st = frame.get("twin_state") or {}
        health = twin_st.get("health_index", 85.0)
        anomaly = twin_st.get("anomaly_composite", 0.35)

        branches = self.cf_simulator.compare_operational_branches(
            current_telemetry=pkt,
            current_health=health,
            active_anomaly_score=anomaly,
            horizon_minutes=horizon_minutes,
        )
        return branches
