"""
MAADT Persistence Layer (SQLite / Time-series store).
Implements persistent storage for raw/validated telemetry streams, synchronized
Digital Twin states, diagnostic fault events, maintenance advisories, and mission debriefs.
Reference: overview.md Section 50.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from schemas.telemetry import (
    Advisory,
    DigitalTwinState,
    FaultEvent,
    TelemetryPacket,
)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "maadt_data.db"


class Database:
    """Manages SQLite storage for MAADT telemetry, twin states, faults, and advisories."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or DEFAULT_DB_PATH)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables and indexes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Telemetry Stream Table (§50)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                engine_id TEXT NOT NULL,
                mission_id TEXT,
                sequence_id INTEGER,
                rpm REAL NOT NULL,
                cht REAL NOT NULL,
                egt REAL NOT NULL,
                oil_pressure REAL NOT NULL,
                oil_temperature REAL NOT NULL,
                fuel_flow REAL NOT NULL,
                vibration REAL NOT NULL,
                battery_voltage REAL,
                alternator_current REAL,
                injection_timing REAL,
                throttle REAL NOT NULL,
                altitude REAL NOT NULL,
                ambient_temperature REAL,
                ambient_pressure REAL,
                humidity REAL,
                sensor_quality TEXT,
                sensor_trust TEXT
            );
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_time 
            ON telemetry (engine_id, timestamp);
            """)

            # 2. Digital Twin State Table (§50)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS twin_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                engine_id TEXT NOT NULL,
                operating_regime TEXT NOT NULL,
                system_operational_state TEXT NOT NULL,
                estimated_rpm REAL NOT NULL,
                estimated_load REAL NOT NULL,
                health_index REAL NOT NULL,
                thermal_health REAL NOT NULL,
                combustion_health REAL NOT NULL,
                lubrication_health REAL NOT NULL,
                vibration_health REAL NOT NULL,
                electrical_health REAL NOT NULL,
                anomaly_composite REAL NOT NULL,
                mission_margin REAL NOT NULL,
                twin_confidence REAL NOT NULL,
                state_json TEXT
            );
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_twin_time 
            ON twin_state (engine_id, timestamp);
            """)

            # 3. Fault Events Table (§50)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fault_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                engine_id TEXT NOT NULL,
                fault_type TEXT NOT NULL,
                probability REAL NOT NULL,
                severity TEXT NOT NULL,
                subsystem TEXT NOT NULL,
                evidence TEXT,
                sensor_trust_verified INTEGER
            );
            """)

            # 4. Maintenance Advisories Table (§39, §50)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS advisories (
                id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                severity TEXT NOT NULL,
                subsystem TEXT NOT NULL,
                potential_issue TEXT NOT NULL,
                evidence TEXT,
                current_health REAL NOT NULL,
                estimated_rul TEXT,
                recommended_action TEXT NOT NULL,
                confidence REAL NOT NULL
            );
            """)

            # 5. Missions Table (§31, §104)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                mission_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                duration_seconds REAL,
                status TEXT NOT NULL,
                summary_json TEXT
            );
            """)

            conn.commit()

    # --- Telemetry Methods ---
    def insert_telemetry(self, packet: TelemetryPacket):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO telemetry (
                timestamp, engine_id, mission_id, sequence_id,
                rpm, cht, egt, oil_pressure, oil_temperature,
                fuel_flow, vibration, battery_voltage, alternator_current,
                injection_timing, throttle, altitude,
                ambient_temperature, ambient_pressure, humidity,
                sensor_quality, sensor_trust
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                packet.timestamp, packet.engine_id, packet.mission_id, packet.sequence_id,
                packet.rpm, packet.cht, packet.egt, packet.oil_pressure, packet.oil_temperature,
                packet.fuel_flow, packet.vibration, packet.battery_voltage, packet.alternator_current,
                packet.injection_timing, packet.throttle, packet.altitude,
                packet.ambient_temperature, packet.ambient_pressure, packet.humidity,
                json.dumps({k: v.value for k, v in packet.sensor_quality.items()}),
                json.dumps(packet.sensor_trust)
            ))
            conn.commit()

    def get_recent_telemetry(self, engine_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM telemetry 
            WHERE engine_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (engine_id, limit))
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]

    # --- Twin State Methods ---
    def insert_twin_state(self, state: DigitalTwinState):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO twin_state (
                timestamp, engine_id, operating_regime, system_operational_state,
                estimated_rpm, estimated_load, health_index,
                thermal_health, combustion_health, lubrication_health,
                vibration_health, electrical_health, anomaly_composite,
                mission_margin, twin_confidence, state_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                state.timestamp, state.engine_id, state.operating_regime.value, state.system_operational_state,
                state.estimated_rpm, state.estimated_load, state.health.overall,
                state.health.thermal, state.health.combustion, state.health.lubrication,
                state.health.vibration, state.health.electrical, state.anomaly.composite_score,
                state.mission_margin, state.twin_confidence, state.model_dump_json()
            ))
            conn.commit()

    def get_recent_twin_states(self, engine_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM twin_state 
            WHERE engine_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (engine_id, limit))
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]

    # --- Fault & Advisory Methods ---
    def insert_fault_event(self, fault: FaultEvent):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO fault_events (
                timestamp, engine_id, fault_type, probability,
                severity, subsystem, evidence, sensor_trust_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fault.timestamp, fault.engine_id, fault.fault_type.value, fault.probability,
                fault.severity.value, fault.subsystem, json.dumps(fault.evidence),
                1 if fault.sensor_trust_verified else 0
            ))
            conn.commit()

    def get_fault_history(self, engine_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM fault_events 
            WHERE engine_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (engine_id, limit))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("evidence"):
                    item["evidence"] = json.loads(item["evidence"])
                results.append(item)
            return results

    def insert_advisory(self, adv: Advisory):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO advisories (
                id, timestamp, severity, subsystem, potential_issue,
                evidence, current_health, estimated_rul, recommended_action, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                adv.id, adv.timestamp, adv.severity.value, adv.subsystem, adv.potential_issue,
                json.dumps(adv.evidence), adv.current_health, adv.estimated_rul,
                adv.recommended_action, adv.confidence
            ))
            conn.commit()

    def get_advisories(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM advisories 
            ORDER BY timestamp DESC 
            LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("evidence"):
                    item["evidence"] = json.loads(item["evidence"])
                results.append(item)
            return results

    # --- Mission Methods ---
    def record_mission(self, mission_id: str, name: str, start_time: float, status: str = "IN_PROGRESS"):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO missions (mission_id, name, start_time, status)
            VALUES (?, ?, ?, ?)
            """, (mission_id, name, start_time, status))
            conn.commit()

    def complete_mission(self, mission_id: str, end_time: float, summary: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE missions 
            SET end_time = ?, duration_seconds = ?, status = 'COMPLETED', summary_json = ?
            WHERE mission_id = ?
            """, (end_time, end_time - summary.get("start_time", end_time), json.dumps(summary), mission_id))
            conn.commit()

    # --- Replay & Time-Travel Methods (§36, §37) ---
    def get_telemetry_range(
        self,
        engine_id: str,
        start_time: float,
        end_time: float,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Queries continuous telemetry records within [start_time, end_time]."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM telemetry
            WHERE engine_id = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
            LIMIT ?
            """, (engine_id, start_time, end_time, limit))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("sensor_trust"):
                    item["sensor_trust"] = json.loads(item["sensor_trust"])
                if item.get("sensor_quality"):
                    item["sensor_quality"] = json.loads(item["sensor_quality"])
                results.append(item)
            return results

    def get_telemetry_at(self, engine_id: str, target_time: float) -> Optional[Dict[str, Any]]:
        """Finds nearest telemetry record at or preceding target_time."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM telemetry
            WHERE engine_id = ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
            """, (engine_id, target_time))
            row = cursor.fetchone()
            if row:
                item = dict(row)
                if item.get("sensor_trust"):
                    item["sensor_trust"] = json.loads(item["sensor_trust"])
                if item.get("sensor_quality"):
                    item["sensor_quality"] = json.loads(item["sensor_quality"])
                return item
            # If none preceding, try nearest following
            cursor.execute("""
            SELECT * FROM telemetry
            WHERE engine_id = ?
            ORDER BY ABS(timestamp - ?) ASC
            LIMIT 1
            """, (engine_id, target_time))
            row = cursor.fetchone()
            if row:
                item = dict(row)
                if item.get("sensor_trust"):
                    item["sensor_trust"] = json.loads(item["sensor_trust"])
                if item.get("sensor_quality"):
                    item["sensor_quality"] = json.loads(item["sensor_quality"])
                return item
            return None

    def get_twin_state_at(self, engine_id: str, target_time: float) -> Optional[Dict[str, Any]]:
        """Finds nearest synchronized Digital Twin state at or preceding target_time."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM twin_state
            WHERE engine_id = ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
            """, (engine_id, target_time))
            row = cursor.fetchone()
            if row:
                item = dict(row)
                if item.get("state_json"):
                    item["state"] = json.loads(item["state_json"])
                return item
            cursor.execute("""
            SELECT * FROM twin_state
            WHERE engine_id = ?
            ORDER BY ABS(timestamp - ?) ASC
            LIMIT 1
            """, (engine_id, target_time))
            row = cursor.fetchone()
            if row:
                item = dict(row)
                if item.get("state_json"):
                    item["state"] = json.loads(item["state_json"])
                return item
            return None

    def get_time_bounds(self, engine_id: str) -> Dict[str, Any]:
        """Returns earliest, latest timestamp, and total sample count recorded for engine."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time, COUNT(*) as count
            FROM telemetry
            WHERE engine_id = ?
            """, (engine_id,))
            row = cursor.fetchone()
            if row and row["count"] > 0:
                return {
                    "min_time": row["min_time"],
                    "max_time": row["max_time"],
                    "duration_seconds": round(row["max_time"] - row["min_time"], 1),
                    "total_samples": row["count"],
                }
            return {"min_time": 0.0, "max_time": 0.0, "duration_seconds": 0.0, "total_samples": 0}

    def get_all_faults(
        self,
        engine_id: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Returns chronological list of fault events within optional time window."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM fault_events WHERE engine_id = ?"
            params: List[Any] = [engine_id]
            if start_time is not None:
                query += " AND timestamp >= ?"
                params.append(start_time)
            if end_time is not None:
                query += " AND timestamp <= ?"
                params.append(end_time)
            query += " ORDER BY timestamp ASC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("evidence"):
                    item["evidence"] = json.loads(item["evidence"])
                results.append(item)
            return results


# Global singleton database instance
db = Database()
