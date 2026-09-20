"""
MAADT Core API Gateway.
Integrates Telemetry Validation, Database Persistence, Digital Twin Core & EKF State Estimation,
4-Tier Composite Anomaly Detection, Multi-Class Fault Classification with Physical Explainability,
High-Fidelity Engine Simulation with Fault Injection, and WebSocket High-Frequency Streaming.
Reference: overview.md Sections 18, 19, 20, 21, 22, 29, 30, 48, 49, 50, 53, 54, 57, 59.
"""

import asyncio
import os
import random
import sys
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Append parent directory to path for clean package imports
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from analytics import (
    DiagnosticExplainer,
    FeatureExtractor,
    HybridAnomalyEngine,
    MultiClassFaultClassifier,
    ollama_ai_service,
)
from config.loader import config_manager
from core import (
    AeroPistonPhysicsModel,
    DigitalTwinManager,
    simulate_mission_margin,
)
from mission import (
    CounterfactualSimulator,
    MissionMarginBreakdown,
    MissionMarginCalculator,
    ScenarioOutcome,
)
from prognostics import (
    DegradationTracker,
    DegradationMetrics,
    MissionStressCalculator,
    MissionStressDetails,
    ProbabilisticRULEngine,
)
from replay import MissionReplayEngine, TimelineMilestone
from schemas.telemetry import (
    Advisory,
    AlertSeverity,
    AnomalyScoreDetails,
    DigitalTwinState,
    FaultEvent,
    FaultType,
    OperatingRegime,
    PhysicsResiduals,
    RULPrediction,
    SensorQuality,
    SubsystemHealth,
    TelemetryPacket,
)
from simulation import (
    AeroEngineSimulator,
    AtmosphericEnvironment,
    FaultInjector,
    FaultProgression,
    MissionRunner,
)
from storage.db import db
from telemetry.validator import TelemetryValidator
from gateway.edge_gateway import edge_gateway
from protocols.can_bus import EngineCANCodec
from protocols.mavlink_handler import MAVLinkEngineHandler
from validation.benchmark_suite import ValidationBenchmarkRunner

app = FastAPI(
    title="MAADT Core Intelligence API",
    description="Mission-Aware Adaptive Digital Twin for MALE UAV Aero-Piston Engines",
    version="1.0.0",
)

# Enable CORS for Next.js and Electron desktop clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core Simulation & Diagnostics Instances ---
engine_cfg = config_manager.get_engine_config("aero_piston_x")
validator = TelemetryValidator(config=engine_cfg)

# Digital Twin Manager (§29, §30, §92)
twin_manager = DigitalTwinManager(config=engine_cfg, engine_id="ENG-001")

# Analytics Subsystems (§18, §19, §20, §21, §57, §59)
feature_extractor = FeatureExtractor()
anomaly_engine = HybridAnomalyEngine(config=engine_cfg)
fault_classifier = MultiClassFaultClassifier()
explainer = DiagnosticExplainer()

# Prognostics Subsystems (§23, §24, §25, §26, §63, §64)
stress_calculator = MissionStressCalculator(config=engine_cfg)
degradation_tracker = DegradationTracker(window_size=120)
rul_engine = ProbabilisticRULEngine(config=engine_cfg)

# Mission Intelligence & Counterfactual Simulation Subsystems (§34, §35, §79)
margin_calculator = MissionMarginCalculator(config=engine_cfg)
counterfactual_simulator = CounterfactualSimulator(config=engine_cfg)
replay_engine = MissionReplayEngine(config=engine_cfg, database=db)
benchmark_runner = ValidationBenchmarkRunner(config=engine_cfg)

# Simulation Subsystems (§14, §15, §53, §54)
fault_injector = FaultInjector()
environment = AtmosphericEnvironment()
engine_sim = AeroEngineSimulator(
    config=engine_cfg,
    environment=environment,
    fault_injector=fault_injector,
    engine_id="ENG-001",
)
default_mission = config_manager.get_mission_config("MIS-ENDURANCE-01")
mission_runner = MissionRunner(simulator=engine_sim, mission_config=default_mission)

# Control mode: AUTONOMOUS (follows mission profile) or MANUAL (user sets throttle/alt)
sim_control = {
    "mode": "AUTONOMOUS",  # "AUTONOMOUS" | "MANUAL"
    "manual_throttle": 65.0,
    "manual_altitude": 5500.0,
    "active_mission_id": "MIS-ENDURANCE-01",
    "health": 98.5,
    "degradation_rate": 0.0015,
}

# Runtime Diagnostics & Prognostics Cache
latest_diagnostic: Dict[str, Any] = {
    "fault_type": "healthy",
    "probability": 0.95,
    "severity": "INFO",
    "subsystem": "Propulsion Core",
    "evidence": ["All thermodynamic residuals nominal"],
    "class_probabilities": {},
}

latest_stress: Dict[str, Any] = {
    "thermal": 0.0,
    "mechanical": 0.0,
    "combustion": 0.0,
    "lubrication": 0.0,
    "transient": 0.0,
    "overall": 0.0,
    "cumulative_stress": 0.0,
}

latest_rul: Dict[str, Any] = {
    "hours_remaining": 850.0,
    "hours_lower_bound": 720.0,
    "hours_upper_bound": 980.0,
    "confidence": 0.95,
    "trend": "STABLE",
    "limiting_subsystem": "Thermal Core",
    "degradation_rate_pct_hr": 0.05,
}

latest_margin_breakdown: Dict[str, Any] = {
    "thermal_margin": 85.0,
    "load_margin": 72.0,
    "fuel_margin": 95.0,
    "degradation_margin": 96.0,
    "rul_margin": 100.0,
    "composite_margin": 88.5,
    "confidence": 0.95,
    "is_critical": False,
    "recommendation": "SAFE TO CONTINUE MISSION",
}

latest_packet_cache: Optional[TelemetryPacket] = None


# --- Request/Response Models ---

class WhatIfRequest(BaseModel):
    target_throttle: float
    target_altitude: float


class CounterfactualRequest(BaseModel):
    target_throttle: Optional[float] = None
    target_altitude: Optional[float] = None
    horizon_minutes: float = 30.0
    compare_branches: bool = True


class ReplayBranchRequest(BaseModel):
    timestamp: float
    horizon_minutes: float = 30.0


class FaultInjectionRequest(BaseModel):
    fault_type: FaultType
    severity: float = Field(0.7, ge=0.0, le=1.0)
    progression: FaultProgression = FaultProgression.LINEAR
    ramp_duration_seconds: float = Field(30.0, ge=1.0)
    target_sensor: Optional[str] = None


class SimControlRequest(BaseModel):
    mode: str = Field(..., description="'AUTONOMOUS' or 'MANUAL'")
    manual_throttle: Optional[float] = None
    manual_altitude: Optional[float] = None
    mission_id: Optional[str] = None


class ValidationRunRequest(BaseModel):
    scenario_id: Optional[int] = None
    steps: int = 25


class AICopilotChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None
    telemetry: Optional[Dict[str, Any]] = None


class AIModelSelectRequest(BaseModel):
    model_name: str


class AIDiagnosticsRequest(BaseModel):
    telemetry: Optional[Dict[str, Any]] = None
    diagnostic_info: Optional[Dict[str, Any]] = None


# --- REST API Endpoints (§49, §53) ---

@app.get("/api/v1/system/status")
def get_system_status():
    """Returns general service health, active engine, and database metrics."""
    recent_telemetry = db.get_recent_telemetry(engine_sim.engine_id, limit=1)
    twin_st = twin_manager.get_state()
    return {
        "status": "OPERATIONAL",
        "service": "MAADT Core Gateway",
        "active_engine": engine_cfg.name,
        "operating_regime": mission_runner.current_regime.value,
        "control_mode": sim_control["mode"],
        "sim_time_seconds": round(engine_sim.sim_time, 1),
        "current_health": round(twin_st.health.overall if twin_st else sim_control["health"], 1),
        "twin_confidence": round(twin_st.twin_confidence if twin_st else 1.0, 2),
        "active_diagnostic": latest_diagnostic["fault_type"],
        "active_faults": fault_injector.list_active_faults(engine_sim.sim_time),
        "db_connected": True,
        "latest_telemetry_timestamp": recent_telemetry[0]["timestamp"] if recent_telemetry else None,
    }


@app.get("/api/v1/config/engine")
def get_engine_configuration():
    """Returns active engine specification, operating boundaries, and weights (§4.4, §52)."""
    return engine_cfg.model_dump()


@app.get("/api/v1/config/missions")
def list_mission_profiles():
    """Returns catalog of preconfigured flight profiles (§52)."""
    return config_manager.list_missions()


@app.get("/api/v1/telemetry/recent")
def get_recent_telemetry(limit: int = 50):
    """Returns recent persisted telemetry records from the database (§50)."""
    return db.get_recent_telemetry(engine_sim.engine_id, limit=limit)


@app.get("/api/v1/twin/state")
def get_latest_twin_state():
    """Returns the most recent synchronized Digital Twin state vector (§29)."""
    state = twin_manager.get_state()
    if state:
        return state.model_dump()
    states = db.get_recent_twin_states(engine_sim.engine_id, limit=1)
    if states:
        return states[0]
    return {"status": "INITIALIZING", "message": "Awaiting initial telemetry stream synchronization"}


@app.get("/api/v1/twin/residuals")
def get_latest_residuals():
    """Returns current physics residuals (Observed - Expected) (§17)."""
    if twin_manager.current_residuals:
        return twin_manager.current_residuals.model_dump()
    return {"status": "NO_DATA"}


@app.get("/api/v1/twin/rul")
def get_latest_rul_prediction():
    """Returns probabilistic Remaining Useful Life (RUL) with uncertainty bounds (§24, §25, §26)."""
    return latest_rul


@app.get("/api/v1/twin/stress")
def get_mission_stress_metrics():
    """Returns normalized mission stress components and cumulative stress-hours (§63, §64)."""
    return latest_stress


@app.get("/api/v1/diagnostics/active")
def get_active_diagnostic_hypothesis():
    """Returns the current top diagnostic hypothesis, probability, and evidence (§21, §22)."""
    return latest_diagnostic


@app.get("/api/v1/faults/history")
def get_fault_history(limit: int = 20):
    """Returns historical diagnostic fault events with physical evidence (§21, §50)."""
    return db.get_fault_history(engine_sim.engine_id, limit=limit)


# --- Local Ollama AI Propulsion Inference & Copilot Endpoints ---

@app.get("/api/v1/ai/status")
async def get_ai_status():
    """Returns local Ollama daemon status, installed models, and active model."""
    return await ollama_ai_service.check_health()


@app.post("/api/v1/ai/model/select")
async def select_ai_model(req: AIModelSelectRequest):
    """Switch active local LLM model (e.g. qwen2.5:3b, mistral:latest, qwen3:14b)."""
    return await ollama_ai_service.set_active_model(req.model_name)


@app.post("/api/v1/ai/diagnostics/analyze")
async def analyze_diagnostics_ai(req: AIDiagnosticsRequest):
    """Deep AI-powered aerospace propulsion diagnostic report using local Ollama model."""
    telem = req.telemetry or (latest_packet_cache.model_dump() if latest_packet_cache else {})
    diag = req.diagnostic_info or latest_diagnostic
    return await ollama_ai_service.generate_diagnostic_report(telem, diag)


@app.post("/api/v1/ai/copilot/chat")
async def chat_copilot_ai(req: AICopilotChatRequest):
    """Interactive mission control copilot grounded in live Digital Twin telemetry state."""
    telem = req.telemetry or (latest_packet_cache.model_dump() if latest_packet_cache else {})
    return await ollama_ai_service.chat_copilot(req.message, telem, req.history)


@app.get("/api/v1/advisories")
def get_active_advisories(limit: int = 20):
    """Returns active explainable maintenance advisories (§39, §50)."""
    return db.get_advisories(limit=limit)


# --- Mission Replay & Time-Travel Endpoints (§36, §37, §38) ---

@app.get("/api/v1/replay/overview")
def get_mission_replay_overview():
    """Returns total duration, sample counts, and fault statistics for replay scrubbing (§36)."""
    return replay_engine.get_mission_overview(engine_sim.engine_id)


@app.get("/api/v1/replay/timeline")
def get_mission_replay_timeline(start_time: Optional[float] = None, end_time: Optional[float] = None):
    """Returns milestone events along the mission timeline for time-travel analysis (§37)."""
    milestones = replay_engine.build_event_timeline(engine_sim.engine_id, start_time, end_time)
    return [m.__dict__ for m in milestones]


@app.get("/api/v1/replay/frame")
def get_mission_replay_frame(timestamp: float):
    """Returns exact synchronized telemetry and digital twin state at historical timestamp (§36)."""
    return replay_engine.get_replay_frame(engine_sim.engine_id, timestamp)


@app.post("/api/v1/replay/branch")
def branch_counterfactual_at_time(req: ReplayBranchRequest):
    """
    Executes Counterfactual Replay (§38):
    Branches historical telemetry frame into 4 candidate operational scenarios.
    """
    branches = replay_engine.branch_counterfactual_at_time(
        engine_id=engine_sim.engine_id,
        timestamp=req.timestamp,
        horizon_minutes=req.horizon_minutes,
    )
    return {
        "status": "success",
        "branch_origin_timestamp": req.timestamp,
        "branches": [
            {
                "scenario_id": b.scenario_id,
                "scenario_name": b.scenario_name,
                "description": b.description,
                "target_throttle": b.target_throttle,
                "target_altitude": b.target_altitude,
                "horizon_minutes": b.horizon_minutes,
                "peak_cht": b.peak_cht,
                "peak_egt": b.peak_egt,
                "final_health": b.final_health,
                "final_survival_margin": b.final_survival_margin,
                "safety_verdict": b.safety_verdict,
                "recommendation": b.recommendation,
                "margin_breakdown": b.margin_breakdown.__dict__,
            }
            for b in branches
        ],
    }


# --- Fleet & Model Registry Endpoints (§51, §65, §87) ---

@app.get("/api/v1/fleet/overview")
def get_fleet_overview():
    """Returns Multi-UAV Fleet Health overview, engine operating stats, and recurring faults (§65)."""
    twin_st = twin_manager.get_state()
    hi = twin_st.health.overall if twin_st else 98.4
    return {
        "fleet_id": "MALE-SQUADRON-ALPHA",
        "total_aircraft": 3,
        "active_sorties": 1,
        "fleet_average_health": round((hi + 94.2 + 76.5) / 3, 1),
        "aircraft": [
            {
                "uav_id": "UAV-001",
                "engine_id": "ENG-001",
                "status": "AIRBORNE",
                "health_index": hi,
                "flight_hours": 142.5,
                "active_faults": len(fault_injector.list_active_faults(engine_sim.sim_time)),
                "mission": "MIS-ENDURANCE-01",
                "regime": mission_runner.current_regime.value,
                "composite_margin": latest_margin_breakdown.get("composite_margin", 88.0)
            },
            {
                "uav_id": "UAV-002",
                "engine_id": "ENG-002",
                "status": "STANDBY",
                "health_index": 94.2,
                "flight_hours": 310.2,
                "active_faults": 0,
                "mission": "PRE-FLIGHT CHECK",
                "regime": "IDLE",
                "composite_margin": 95.0
            },
            {
                "uav_id": "UAV-003",
                "engine_id": "ENG-003",
                "status": "MAINTENANCE",
                "health_index": 76.5,
                "flight_hours": 582.0,
                "active_faults": 1,
                "mission": "SCHEDULED OVERHAUL",
                "regime": "SHUTDOWN",
                "composite_margin": 42.0
            }
        ],
        "fleet_recurring_faults": [
            {"fault_type": "injector_abnormality", "occurrences": 4, "subsystem": "Fuel / Combustion"},
            {"fault_type": "sensor_drift", "occurrences": 3, "subsystem": "Instrumentation"},
            {"fault_type": "overheating", "occurrences": 1, "subsystem": "Thermal Core"}
        ]
    }


@app.get("/api/v1/registry/models")
def get_model_registry():
    """Returns versioned model metadata and active registry entries (§51)."""
    return {
        "registry_version": "v1.0",
        "models": [
            {"id": "physics-v1.0", "type": "Reduced-Order Thermodynamic Physics", "version": "1.0.4", "status": "ACTIVE", "fidelity_target": "MAE < 3.5%"},
            {"id": "ekf-state-v1.0", "type": "Extended Kalman Filter State Estimator", "version": "1.0.2", "status": "ACTIVE", "update_hz": 10},
            {"id": "anomaly-v1.2", "type": "4-Tier Composite Residual & ML Estimator", "version": "1.2.0", "status": "ACTIVE", "lead_time_target": ">= 12 min"},
            {"id": "fault-classifier-v1.1", "type": "Physics-Grounded Diagnostic Classifier", "version": "1.1.0", "status": "ACTIVE", "supported_classes": 8},
            {"id": "rul-v0.8", "type": "Probabilistic Log-Linear RUL Engine", "version": "0.8.5", "status": "ACTIVE", "confidence_bands": "P10-P90"},
            {"id": "mission-margin-v1.0", "type": "Multi-Factor Mission Margin & Counterfactual", "version": "1.0.0", "status": "ACTIVE", "decision_branches": 4}
        ]
    }


@app.get("/api/v1/analytics/trends")
def get_analytics_trends(limit: int = 100):
    """Returns historical analytics, sensor trust distributions, and error residual trends (§87, §11)."""
    recent = db.get_recent_telemetry(engine_sim.engine_id, limit=limit)
    states = db.get_recent_twin_states(engine_sim.engine_id, limit=limit)
    return {
        "sample_count": len(recent),
        "sensor_trust_aggregates": {
            "rpm": 0.99,
            "egt": 0.94,
            "cht": 0.96,
            "oil_pressure": 0.97,
            "fuel_flow": 0.95,
            "vibration": 0.91
        },
        "mean_residuals": {
            "egt_degc": round(sum(abs(r.get("egt", 0) - 710.0) for r in recent) / max(1, len(recent)), 2) if recent else 0.0,
            "cht_degc": round(sum(abs(r.get("cht", 0) - 165.0) for r in recent) / max(1, len(recent)), 2) if recent else 0.0,
        },
        "recent_health_trajectory": [
            {"timestamp": s.get("timestamp"), "health_index": s.get("health_index"), "anomaly_score": s.get("anomaly_score")}
            for s in reversed(states[:30])
        ]
    }


# --- Edge Gateway & MAVLink / Serial Emulation Endpoints (§47, §67, §81) ---

@app.get("/api/v1/gateway/status")
def get_gateway_status():
    """Returns runtime telemetry gateway metrics, buffer fill %, and decoder stats (§67, §81, §87)."""
    return edge_gateway.get_status()


@app.post("/api/v1/gateway/start")
def start_gateway_listener():
    """Starts the edge gateway listener (§81)."""
    edge_gateway.start_listening()
    return {"status": "SUCCESS", "gateway": edge_gateway.get_status()}


@app.post("/api/v1/gateway/stop")
def stop_gateway_listener():
    """Stops the edge gateway listener (§81)."""
    edge_gateway.stop_listening()
    return {"status": "SUCCESS", "gateway": edge_gateway.get_status()}


@app.post("/api/v1/gateway/inject_mock")
def inject_mock_gateway_packet(protocol: str = "MAVLINK"):
    """
    Injects a synthetic MAVLink or CAN packet into the edge gateway
    to verify edge decoding, ring buffering, and validation (§47, §81).
    """
    if protocol.upper() == "CAN":
        frame = EngineCANCodec.encode_rpm_throttle(rpm=2480.0, throttle_pct=66.0)
        records = edge_gateway.process_raw_bytes(frame.pack())
    else:
        raw = MAVLinkEngineHandler.encode_engine_pack(
            rpm=2480.0, cht=167.5, egt=710.0, oil_pressure=4.8,
            oil_temp=92.0, fuel_flow=18.5, vibration=0.28
        )
        records = edge_gateway.process_raw_bytes(raw)
    return {
        "status": "INJECTED",
        "protocol": protocol.upper(),
        "decoded_records": records,
        "gateway_status": edge_gateway.get_status(),
    }


# --- Validation Benchmark Suite & Scenario Matrix Endpoints (§74-§77) ---

@app.get("/api/v1/validation/scenarios")
def get_validation_scenarios():
    """Returns definitions of all 10 operational validation benchmark scenarios (§74)."""
    return {
        "status": "SUCCESS",
        "scenarios": benchmark_runner.get_scenario_definitions(),
    }


@app.post("/api/v1/validation/run")
def run_validation_benchmarks(request: Optional[ValidationRunRequest] = None):
    """
    Executes a single benchmark scenario or the full 10-scenario validation matrix (§74-§77).
    Computes Detection Lead Time, Digital Twin Fidelity metrics, and Anomaly Classification accuracy.
    """
    req = request or ValidationRunRequest()
    if req.scenario_id is not None:
        result = benchmark_runner.run_single_scenario(scenario_id=req.scenario_id, steps=req.steps)
        return {
            "status": "COMPLETED",
            "scenario": result.__dict__,
        }
    else:
        results = benchmark_runner.run_all_scenarios(steps_per_scenario=req.steps)
        return results


# --- Simulation & Fault Injection Controls (§53) ---

@app.get("/api/v1/simulation/faults")
def list_active_simulation_faults():
    """Returns all currently active injected faults."""
    return {
        "active_faults": fault_injector.list_active_faults(engine_sim.sim_time),
        "sim_time": round(engine_sim.sim_time, 1),
    }


@app.post("/api/v1/simulation/fault/inject")
def inject_simulation_fault(req: FaultInjectionRequest):
    """Injects a physical engine or sensor instrument fault into the live simulator (§53)."""
    fid = fault_injector.inject_fault(
        fault_type=req.fault_type,
        severity=req.severity,
        progression=req.progression,
        onset_seconds=0.0,
        ramp_duration_seconds=req.ramp_duration_seconds,
        target_sensor=req.target_sensor,
    )
    return {
        "status": "INJECTED",
        "fault_id": fid,
        "fault_type": req.fault_type.value,
        "severity": req.severity,
        "progression": req.progression.value,
    }


@app.post("/api/v1/simulation/fault/clear")
def clear_all_simulation_faults():
    """Clears all injected faults from the simulator."""
    fault_injector.clear_all()
    return {"status": "CLEARED", "active_fault_count": 0}


@app.post("/api/v1/simulation/control")
def update_simulation_control(req: SimControlRequest):
    """Updates simulation control mode, manual throttle/altitude, or switches mission profile."""
    if req.mode in ("AUTONOMOUS", "MANUAL"):
        sim_control["mode"] = req.mode
    if req.manual_throttle is not None:
        sim_control["manual_throttle"] = max(0.0, min(100.0, req.manual_throttle))
    if req.manual_altitude is not None:
        sim_control["manual_altitude"] = max(0.0, min(10000.0, req.manual_altitude))
    if req.mission_id:
        cfg = config_manager.get_mission_config(req.mission_id)
        if cfg:
            global mission_runner
            sim_control["active_mission_id"] = req.mission_id
            mission_runner = MissionRunner(simulator=engine_sim, mission_config=cfg)

    return {
        "status": "UPDATED",
        "control_state": sim_control,
        "current_regime": mission_runner.current_regime.value,
    }


def _get_current_telemetry_snapshot() -> TelemetryPacket:
    if latest_packet_cache:
        return latest_packet_cache
    return TelemetryPacket(
        timestamp=engine_sim.sim_time,
        rpm=engine_sim.rpm,
        cht=engine_sim.cht,
        egt=engine_sim.egt,
        oil_pressure=engine_sim.oil_pressure,
        oil_temperature=engine_sim.oil_temperature,
        fuel_flow=engine_sim.fuel_flow,
        vibration=engine_sim.vibration,
        throttle=engine_sim.throttle,
        altitude=engine_sim.altitude,
    )


@app.get("/api/v1/mission/margin")
def get_mission_survival_margin():
    """Returns detailed multi-factor mission survival margin breakdown (§35)."""
    return latest_margin_breakdown


@app.post("/api/v1/mission/counterfactual")
def run_counterfactual_simulation(req: CounterfactualRequest):
    """
    Executes forward counterfactual trajectory prediction (§34, §38, §79).
    Simulates candidate operational decisions (Maintain, Throttle Down, Descend, RTB).
    """
    current_twin = twin_manager.get_state()
    anomaly_score = current_twin.anomaly.composite_score if current_twin else 0.05
    health = current_twin.health.overall if current_twin else 98.0
    recent_pkt = _get_current_telemetry_snapshot()

    if req.compare_branches:
        branches = counterfactual_simulator.compare_operational_branches(
            current_telemetry=recent_pkt,
            current_health=health,
            active_anomaly_score=anomaly_score,
            horizon_minutes=req.horizon_minutes,
        )
        return {
            "status": "success",
            "mode": "multi_branch_comparison",
            "branches": [
                {
                    "scenario_id": b.scenario_id,
                    "scenario_name": b.scenario_name,
                    "description": b.description,
                    "target_throttle": b.target_throttle,
                    "target_altitude": b.target_altitude,
                    "horizon_minutes": b.horizon_minutes,
                    "peak_cht": b.peak_cht,
                    "peak_egt": b.peak_egt,
                    "final_health": b.final_health,
                    "final_survival_margin": b.final_survival_margin,
                    "safety_verdict": b.safety_verdict,
                    "recommendation": b.recommendation,
                    "margin_breakdown": b.margin_breakdown.__dict__,
                }
                for b in branches
            ],
        }
    else:
        tgt_throt = req.target_throttle if req.target_throttle is not None else recent_pkt.throttle
        tgt_alt = req.target_altitude if req.target_altitude is not None else recent_pkt.altitude
        outcome = counterfactual_simulator.simulate_scenario(
            current_telemetry=recent_pkt,
            current_health=health,
            target_throttle=tgt_throt,
            target_altitude=tgt_alt,
            horizon_minutes=req.horizon_minutes,
            active_anomaly_score=anomaly_score,
        )
        return {
            "status": "success",
            "mode": "single_scenario",
            "outcome": {
                "scenario_id": outcome.scenario_id,
                "scenario_name": outcome.scenario_name,
                "description": outcome.description,
                "target_throttle": outcome.target_throttle,
                "target_altitude": outcome.target_altitude,
                "horizon_minutes": outcome.horizon_minutes,
                "peak_cht": outcome.peak_cht,
                "peak_egt": outcome.peak_egt,
                "final_health": outcome.final_health,
                "final_survival_margin": outcome.final_survival_margin,
                "safety_verdict": outcome.safety_verdict,
                "recommendation": outcome.recommendation,
                "margin_breakdown": outcome.margin_breakdown.__dict__,
                "trajectory": [p.__dict__ for p in outcome.trajectory],
            },
        }


@app.post("/api/simulate")
def run_what_if(req: WhatIfRequest):
    """Executes counterfactual simulation on target parameters (§34, §35)."""
    current_twin = twin_manager.get_state()
    current_anomaly = current_twin.anomaly.composite_score if current_twin else 0.05
    health = current_twin.health.overall if current_twin else 98.0
    recent_pkt = _get_current_telemetry_snapshot()

    outcome = counterfactual_simulator.simulate_scenario(
        current_telemetry=recent_pkt,
        current_health=health,
        target_throttle=req.target_throttle,
        target_altitude=req.target_altitude,
        horizon_minutes=20.0,
        active_anomaly_score=current_anomaly,
    )

    return {
        "status": "success",
        "simulated_margin": outcome.final_survival_margin,
        "recommendation": "SAFE" if outcome.final_survival_margin > 0 else "ABORT MISSION",
        "safety_verdict": outcome.safety_verdict,
        "anomaly_prob": round(current_anomaly, 3),
        "peak_cht": outcome.peak_cht,
        "peak_egt": outcome.peak_egt,
        "margin_breakdown": outcome.margin_breakdown.__dict__,
    }


# --- WebSocket Telemetry Stream (§48) ---

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    """
    High-frequency telemetry gateway powered by continuous AeroEngineSimulator & Analytics:
    1. Steps continuous first-principles engine dynamics and flight profile.
    2. Runs packet through Data Quality & Dynamic Sensor Trust Layer.
    3. Generates physics residuals and extracts multi-window temporal features (§57).
    4. Computes 4-tier composite anomaly score (§18, §19).
    5. Classifies multi-class fault hypotheses and aggregates explainable evidence (§20, §21).
    6. Extended Kalman Filter fuses observations into mechanical states (§12).
    7. Decomposes subsystem health and computes mission margins.
    8. Synchronizes Digital Twin state and persists to SQLite.
    9. Streams enriched telemetry + twin state + active diagnostics to clients.
    """
    await websocket.accept()
    global latest_diagnostic, latest_stress, latest_rul, latest_margin_breakdown, latest_packet_cache
    try:
        while True:
            t_now = time.time()
            dt = 0.5

            # 1. Step Continuous Engine Simulation (§14, §15, §32)
            if sim_control["mode"] == "AUTONOMOUS":
                raw_packet, active_regime = mission_runner.step(dt=dt)
            else:
                raw_packet = engine_sim.step(
                    throttle_pct=sim_control["manual_throttle"],
                    altitude_m=sim_control["manual_altitude"],
                    dt=dt,
                )
                active_regime = (
                    OperatingRegime.CRUISE if raw_packet.throttle > 50.0 else OperatingRegime.IDLE
                )

            # 2. Validate Telemetry & Update Dynamic Sensor Trust Layer (§9, §10, §11)
            validated_packet = validator.validate_and_tag(raw_packet, dt=dt)

            # 3. Compute Physics Expected Baseline & Residuals (§16, §17)
            expected = twin_manager.physics.calculate_expected_state(
                validated_packet.throttle, validated_packet.altitude, validated_packet.ambient_temperature
            )
            residuals = twin_manager.physics.calculate_residuals(validated_packet, expected)

            # 4. Feature Extraction over multi-scale temporal windows (§57)
            features = feature_extractor.update_and_extract(validated_packet, residuals, dt=dt)

            # 5. 4-Tier Composite Anomaly Scoring (§18, §19)
            anomaly_details = anomaly_engine.evaluate(validated_packet, residuals, features)
            composite_anomaly = anomaly_details.composite_score

            # 6. Multi-Class Fault Classification & Explainability (§20, §21, §22)
            top_fault, fault_prob, class_probs = fault_classifier.classify(
                validated_packet, residuals, features
            )

            # Generate Explainable Evidence Bullets
            fault_event, advisory = explainer.generate_explanation(
                fault_type=top_fault,
                probability=fault_prob,
                packet=validated_packet,
                residuals=residuals,
                features=features,
                health_index=sim_control["health"]
            )

            # Update cache
            latest_diagnostic = {
                "fault_type": top_fault.value,
                "probability": fault_prob,
                "severity": fault_event.severity.value,
                "subsystem": fault_event.subsystem,
                "evidence": fault_event.evidence,
                "class_probabilities": class_probs,
                "sensor_trust_verified": fault_event.sensor_trust_verified,
            }

            # Persist fault events and advisories when an anomaly is active (§50)
            if top_fault != FaultType.HEALTHY and fault_prob > 0.45:
                db.insert_fault_event(fault_event)
                if advisory:
                    db.insert_advisory(advisory)

            # 7. Multi-Factor Mission Survival Margin (§35)
            margin_breakdown = margin_calculator.compute_margin(
                current_health=twin_manager.overall_health,
                packet=validated_packet,
                anomaly_score=composite_anomaly,
                planned_mission_hours_remaining=4.0,
                rul_hours=latest_rul.get("hours_remaining", 800.0),
                twin_confidence=twin_manager.current_state.twin_confidence if twin_manager.current_state else 0.95,
            )
            margin = margin_breakdown.composite_margin

            latest_margin_breakdown = {
                "thermal_margin": margin_breakdown.thermal_margin,
                "load_margin": margin_breakdown.load_margin,
                "fuel_margin": margin_breakdown.fuel_margin,
                "degradation_margin": margin_breakdown.degradation_margin,
                "rul_margin": margin_breakdown.rul_margin,
                "composite_margin": margin_breakdown.composite_margin,
                "confidence": margin_breakdown.confidence,
                "is_critical": margin_breakdown.is_critical,
                "recommendation": margin_breakdown.recommendation,
            }
            latest_packet_cache = validated_packet

            # 8. Compute Stress Index & Degradation Dynamics (§24, §25, §26, §63, §64)
            stress_details = stress_calculator.compute_stress(
                validated_packet, regime=active_regime, dt=dt
            )
            degradation_metrics = degradation_tracker.update(
                health_index=twin_manager.overall_health,
                sim_time_s=engine_sim.sim_time
            )
            rul_prediction = rul_engine.predict_rul(
                current_health=twin_manager.overall_health,
                degradation=degradation_metrics,
                stress=stress_details,
                sensor_confidence=twin_manager.current_state.twin_confidence if twin_manager.current_state else 0.95,
            )

            # Synchronize Digital Twin State via EKF & Physics (§29, §30)
            twin_state = twin_manager.synchronize(
                telemetry=validated_packet,
                operating_regime=active_regime,
                anomaly_score=composite_anomaly,
                mission_margin=margin,
                rul=rul_prediction,
                dt=dt,
            )

            latest_stress = {
                "thermal": stress_details.thermal,
                "mechanical": stress_details.mechanical,
                "combustion": stress_details.combustion,
                "lubrication": stress_details.lubrication,
                "transient": stress_details.transient,
                "overall": stress_details.overall,
                "cumulative_stress": stress_details.cumulative_stress,
            }
            latest_rul = {
                "hours_remaining": rul_prediction.estimate_hours,
                "hours_lower_bound": rul_prediction.lower_bound,
                "hours_upper_bound": rul_prediction.upper_bound,
                "confidence": rul_prediction.confidence,
                "trend": rul_prediction.degradation_trend,
                "limiting_subsystem": "Thermal Core" if stress_details.thermal >= stress_details.mechanical else "Mechanical Drive",
                "degradation_rate_pct_hr": round(abs(degradation_metrics.health_slope_per_hour), 3),
            }

            # 9. Persist Telemetry & Twin State to SQLite (§50)
            db.insert_telemetry(validated_packet)
            db.insert_twin_state(twin_state)

            # 10. Unified Broadcast Payload
            payload = {
                "timestamp": validated_packet.timestamp,
                "engine_id": "UAV-001",
                "altitude": validated_packet.altitude,
                "throttle": validated_packet.throttle,
                "rpm": validated_packet.rpm,
                "egt": validated_packet.egt,
                "expected_egt": expected.expected_egt,
                "cht": validated_packet.cht,
                "expected_cht": expected.expected_cht,
                "oil_pressure": validated_packet.oil_pressure,
                "oil_temperature": validated_packet.oil_temperature,
                "fuel_flow": validated_packet.fuel_flow,
                "vibration": validated_packet.vibration,
                "battery_voltage": validated_packet.battery_voltage,
                "health_index": twin_state.health.overall,
                "anomaly_score": composite_anomaly,
                "anomaly_breakdown": anomaly_details.model_dump(),
                "mission_margin": margin,
                "mission_margin_breakdown": latest_margin_breakdown,
                "operating_regime": active_regime.value,
                "active_faults": fault_injector.list_active_faults(engine_sim.sim_time),
                "active_diagnostic": latest_diagnostic,
                "estimated_mechanical_state": {
                    "estimated_rpm": twin_state.estimated_rpm,
                    "estimated_load": twin_state.estimated_load,
                    "estimated_thermal_stress": twin_state.estimated_thermal_stress,
                },
                "residuals": twin_state.residuals.model_dump(),
                "subsystem_health": twin_state.health.model_dump(),
                "sensor_trust": validated_packet.sensor_trust,
                "sensor_quality": {k: v.value for k, v in validated_packet.sensor_quality.items()},
                "twin_confidence": twin_state.twin_confidence,
                "stress_index": latest_stress,
                "rul": latest_rul,
            }

            await websocket.send_json(payload)
            await asyncio.sleep(dt)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket] Connection closed: {e}")


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
