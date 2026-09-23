# MAADT: Mission-Aware Adaptive Digital Twin
### *Physics-Informed, AI-Augmented Prognostics & Real-Time Mission Assurance for MALE UAV Aero-Piston Engines*

[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Defence%20GCS-0B1E33?style=flat-square&logo=linux)](https://github.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2016%20%7C%20React%2019-000000?style=flat-square&logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Three.js](https://img.shields.io/badge/3D%20Engine-Three.js%20%7C%20WebGL-049EF4?style=flat-square&logo=three.js)](https://threejs.org)
[![Local AI](https://img.shields.io/badge/Sovereign%20AI-Ollama%20%7C%20Qwen2.5%20%7C%20Mistral-FF6F00?style=flat-square)](https://ollama.com)
[![Build Status](https://img.shields.io/badge/Build-Passing%20(0%20Errors)-10B981?style=flat-square)](https://github.com)

---

## 1. Project Overview

**MAADT** is a mission-critical digital twin and prognostic intelligence platform engineered for **Medium Altitude Long Endurance (MALE) Unmanned Aerial Vehicles** (such as the TAPAS-BH-201, Archer-NG, and Rustom-II class) powered by turbocharged 4-cylinder aero-piston engines (Rotax 914 / 915 iS class).

In strategic long-duration missions (18 to 30+ hours of continuous loiter at 3,000 m to 6,000 m altitude), the propulsion unit represents a **critical single point of failure**. Conventional Health and Usage Monitoring Systems (HUMS) are purely reactive and threshold-based (triggering alarms only after temperatures or pressures breach catastrophic limits).

MAADT eliminates this vulnerability by running an **active, physics-informed computational twin** in lockstep with incoming telemetry at 10 Hz. By combining first-principles thermodynamics, an Extended Kalman Filter (EKF), 4-tier hybrid anomaly detection, real-time counterfactual "What-If" decision simulations, and an air-gapped sovereign AI copilot, MAADT provides operators with predictive foresight and actionable recovery directives hours before catastrophic failure occurs.

---

## 2. Core Capabilities

* **0D Thermodynamic Baseline Engine Model**: Solves the internal combustion Otto air-standard cycle combined with speed-density air mass flow equations and forced convective cylinder fin cooling across varying altitudes, airspeeds, and ambient temperatures.
* **Extended Kalman Filter (EKF) State Estimator**: Tracks hidden internal states (individual cylinder injector efficiencies $\eta_{inj}$, internal mechanical friction coefficient $\theta_{friction}$, indicated torque) while rejecting atmospheric gust disturbances and sensor noise.
* **4-Tier Composite Anomaly Engine**:
  1. *Tier 1 (Physics Residuals)*: Measures normalized deviations ($Z$-scores) between measured sensors and thermodynamic expected values.
  2. *Tier 2 (Statistical Covariance)*: Evaluates multi-sensor covariance breakdown using Mahalanobis distance ($D_M$).
  3. *Tier 3 (Autoencoder Latent Loss)*: Detects non-linear, multi-dimensional sensor envelope anomalies.
  4. *Tier 4 (CUSUM Drift Tracker)*: Tracks slow, creeping sub-threshold degradation over hours of loiter.
* **Counterfactual "What-If" Decision Simulator**: Evaluates 4 forward flight trajectories in real time (<50 ms rollout):
  * *Baseline*: Continue current cruise $\to$ reveals impending thermal runaway in 18 minutes.
  * *Directive 1 (Throttle Derate -15%)*: Cools cylinder head temperature by $-19^\circ\text{C}$ and **extends mission loiter by +3.5 hours**.
  * *Directive 2 (Step Descent -2,000 ft)*: Leverages denser air for fin cooling while evaluating aerodynamic drag penalties.
  * *Directive 3 (Immediate RTB Vector)*: Computes minimum safe energy recovery flight path.
* **Sovereign, 100% Air-Gapped AI Propulsion Copilot**: Directly interfaces with locally hosted Small Language Models via Ollama (`qwen2.5:3b`, `mistral:latest`, `qwen3:14b`). Ingests live telemetry context, explains acoustic/thermal micro-anomalies, and compiles formal DRDO-spec engineering diagnostic reports with **zero external cloud network egress**.
* **Interactive 3D WebGL Digital Twin**: Procedural, semi-translucent Indian MALE UAV airframe housing a detailed boxer-4 aero-piston engine (cylinders, crankcase, fuel rail, individual injectors, exhaust headers, turbocharger, rotating propeller). Includes real-time emissive pulsating warning glow shaders on distressed components and 4 visualization modes (*Photorealistic*, *Thermal Heatmap*, *Stress Gradient*, *Ghost Fuselage*).
* **Deterministic 8-Stage DRDO Flight Script Runner**: Integrated header controller to demonstrate the complete lifecycle: *Pre-flight $\to$ Takeoff $\to$ Cruise $\to$ Incipient Micro-Anomaly $\to$ Critical Injector Overheat $\to$ What-If Matrix $\to$ Directive Execution $\to$ Mission Stabilized (+3.5h Endurance)*.
* **Synchronized Sortie Replay Engine**: 8-hour historical flight scrubber with milestone time-travel jumps and synchronous telemetry reconstruction.

---

## 3. System Architecture

```
                                  MAADT SYSTEM TOPOLOGY
                                  
+──────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    UAV TELEMETRY / SIMULATION                                    |
|  - Engine Sensors: RPM, MAP, CHT (1-4), EGT (1-4), Fuel Flow, Oil P/T, Vibration, Bus Voltage     |
|  - Flight Context: Altitude, Airspeed (IAS/TAS), OAT, Throttle Lever Angle (TLA)                 |
+──────────────────────────────────────────────────────────────────────────────────────────────────+
                                                 │
                                                 │ 10 Hz Telemetry Stream (JSON / Binary)
                                                 ▼
+──────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    BACKEND CORE (Python / FastAPI)                                |
|                                                                                                  |
|  ┌─────────────────────────┐   ┌───────────────────────────┐   ┌──────────────────────────────┐  |
|  │  1. Telemetry Ingestion │──▶│  2. Physics Digital Twin  │──▶│  3. Physics Residual Engine  │  |
|  │     & Sanitization      │   │     - 0D Thermodynamic    │   │     r = y_measured - y_model │  |
|  │  - Range & Spike Filter │   │     - Extended Kalman Flt │   │     ΔCHT, ΔEGT, ΔRPM, ΔFF    │  |
|  │  - Sensor Trust Metric  │   │     - ISA Atmosphere Corr │   │                              │  |
|  └─────────────────────────┘   └───────────────────────────┘   └──────────────┬───────────────┘  |
|                                                                               │                  |
|  ┌────────────────────────────────────────────────────────────────────────────┘                  |
|  ▼                                                                                               |
|  ┌────────────────────────────────────────────────────────────────────────────────────────────┐  |
|  │  4. 4-Tier Hybrid Anomaly & Fault Classification Engine                                     │  |
|  │  - Tier 1: Physics Residual Analysis (Z-score deviation from thermodynamic expected)       │  |
|  │  - Tier 2: Statistical Adaptive Mahalanobis Distance (Covariance-aware multi-sensor drift)  │  |
|  │  - Tier 3: Machine Learning Autoencoder Reconstruction Loss (Latent feature deviation)     │  |
|  │  - Tier 4: Trend Divergence & CUSUM Cumulative Drift Tracker                               │  |
|  │  ==> Fused Anomaly Score: S_composite = 0.35*S_phys + 0.25*S_stat + 0.25*S_ml + 0.15*S_tr   │  |
|  │  ==> Multi-Class Diagnostic Classifier: Diagnoses Injector Clogging, Misfire, Friction, etc │  |
|  └────────────────────────────────────────────┬───────────────────────────────────────────────┘  |
|                                               │                                                  |
|  ┌─────────────────────────┐   ┌──────────────┴────────────┐   ┌──────────────────────────────┐  |
|  │  5. Prognostics (RUL)   │   │  6. Counterfactual Engine │   │  7. Local Ollama LLM Bridge  │  |
|  │  - Paris-Erdogan Fatigue│   │     "What-If" Simulation  │   │  - Zero-Cloud Sovereign AI   │  |
|  │  - Exponential Arrhenius│   │  - Branch 1: Derate Power │   │  - Qwen 2.5 / Mistral        │  |
|  │  - Particle Filter RUL  │   │  - Branch 2: Step Descent │   │  - Instant Engineering RAG   │  |
|  │  - Confidence Bounds    │   │  - Branch 3: RTB Vector   │   │  - Root-Cause Reasoning      │  |
|  └────────────┬────────────┘   └──────────────┬────────────┘   └──────────────┬───────────────┘  |
+───────────────┼───────────────────────────────┼───────────────────────────────┼──────────────────+
                │                               │                               │
                │ WebSockets (10 Hz Live Stream)│ REST APIs (Control & Query)   │ JSON RPC
                ▼                               ▼                               ▼
+──────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    FRONTEND CLIENT (Next.js 16 / React 19)                       |
|                                                                                                  |
|  ┌────────────────────────────────────────────────────────────────────────────────────────────┐  |
|  │  Header & Mission Controller: 8-Stage DRDO Flight Script, Mode Switcher, System Status     │  |
|  ├────────────────────────────────────────────────────────────────────────────────────────────┤  |
|  │  Telemetry Strip: 8 Live Sensor HUD Cards (Interactive 3D component focus on click)        │  |
|  ├────────────────────────────────────────────────────────────────────────────────────────────┤  |
|  │  Center Viewport: Interactive 3D Digital Twin (Three.js / React Three Fiber)                │  |
|  │  - Translucent Indian MALE UAV Fuselage + Rotating Pusher Propeller                       │  |
|  │  - 4-Cylinder Boxer Engine Core (Cylinders, Crankcase, Fuel Rail, Exhaust, Turbocharger)   │  |
|  │  - Pulsating Glow Shader for Faulting Subsystems + 4 View Modes (Heatmap/Stress/Ghost)     │  |
|  ├────────────────────────────────────────────┬───────────────────────────────────────────────┤  |
|  │  Left/Right Tactical Panels (Operator HUD) │  Tactical Decision Center                     │  |
|  │  - Mission Margin Radar & Breakdown (88%)  │  - Operator Recommendation Card               │  |
|  │  - Subsystem Health Gauges (Thermal/Comb)  │  - Instant "EXECUTE TACTICAL DIRECTIVE" Action│  |
|  │  - Active Fault Banner (Click -> Modal)    │  - Interactive 4-Branch "What-If Matrix"      │  |
|  │  - Dynamic Component Inspector HUD         │  - Parametric Throttle/Altitude Slider Sweep  │  |
|  ├────────────────────────────────────────────┴───────────────────────────────────────────────┤  |
|  │  Onboard AI Copilot Drawer (Local Ollama Engine, Model Selector, Live Diagnostic Reports)   │  |
+──────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 4. Repository Structure

```text
.
├── ARCHITECTURE.md                  # Comprehensive mathematical & engineering architecture
├── README.md                        # Master repository documentation
├── .gitignore                       # Clean Git tracking configuration
├── start_maadt.sh                   # One-Click Autonomous System Launch Script
│
├── backend/                         # Python Core (FastAPI, Physics, EKF, AI)
│   ├── analytics/                   # 4-Tier Anomaly Engine, Fault Classifier, Ollama AI
│   ├── api/                         # FastAPI Routes & 10 Hz WebSocket Gateway
│   ├── config/                      # Engine Specifications & Aerodynamic Constants
│   ├── core/                        # 0D Thermodynamics, EKF Estimator, Twin Manager
│   ├── gateway/                     # Edge Data Sanitization & Ingestion Gateway
│   ├── mission/                     # Counterfactual What-If Simulator & Margin Calculators
│   ├── prognostics/                 # Arrhenius-Coffin-Manson RUL & Particle Filter
│   ├── protocols/                   # CAN-bus & MAVLink Telemetry Protocol Adapters
│   ├── replay/                      # Historical Sortie Engine
│   ├── schemas/                     # Strict Pydantic Data Models
│   ├── simulation/                  # Aero-Piston Simulator & Fault Injector
│   ├── storage/                     # SQLite Telemetry & Event Persistence
│   ├── tests/                       # 55 Passing Unit & Integration Tests
│   └── requirements.txt             # Python Package Dependencies
│
├── frontend/                        # Next.js 16 (React 19, Turbopack, Tailwind)
│   ├── src/
│   │   ├── app/                     # Next.js App Router (Entrypoint)
│   │   ├── components/              # Tactical HUD Cards, Radar, Header, Modals
│   │   │   ├── ai/                  # Onboard Local AI Copilot Drawer
│   │   │   ├── engine/              # Three.js 3D UAV & Engine Twin Viewports
│   │   │   ├── mission/             # What-If Matrix, Decision Center, SOP Modal
│   │   │   └── telemetry/           # Live Interactive Telemetry Strip
│   │   ├── views/                   # Operator, Engineering, Simulation, Replay, Fleet
│   │   ├── data/                    # 8-Stage DRDO Flight Script & Catalog
│   │   ├── services/                # WebSockets, REST Client, Telemetry Pipeline
│   │   └── types/                   # TypeScript Definitions
│   ├── package.json                 # Frontend Dependencies & Scripts
│   └── tailwind.config.ts           # DRDO Tactical Color Scheme Theme
│
├── desktop/                         # Electron Linux GCS Shell
├── configs/                         # Rotax 914 / 915 iS Engine Calibration Yamls
└── scripts/                         # Automation & Packaging Utilities
```

---

## 5. Getting Started

### 5.1 System Prerequisites
* **OS**: Linux (Ubuntu 20.04 / 22.04 LTS or compatible Debian distribution)
* **Python**: `3.10` or higher
* **Node.js**: `18.17` or higher (tested on Node 20 LTS)
* **Local AI Runtime (Optional for AI Copilot)**: [Ollama](https://ollama.com) installed and serving models locally (`qwen2.5:3b` recommended for edge inference).

---

### 5.2 Docker Quick Start (Recommended)

Run the entire MAADT platform (FastAPI Backend + Next.js HUD) with Docker Compose:

```bash
# 1. (Optional) Copy sample environment variables
cp .env.example .env

# 2. Build and start all services in detached mode
docker compose up --build -d

# 3. View live unified logs
docker compose logs -f
```

* **Frontend Operator HUD**: [`http://localhost:3000`](http://localhost:3000)
* **Core Intelligence API**: [`http://localhost:8000`](http://localhost:8000)
* **Interactive API Docs**: [`http://localhost:8000/docs`](http://localhost:8000/docs)

#### Key Docker Features:
* **Micro-Footprint Multi-Stage Builds**: Lean images (Frontend: ~73 MB using Next.js standalone tracing; Backend: ~162 MB).
* **State Persistence**: SQLite telemetry database is persisted in a named Docker volume (`maadt_data`).
* **Live Configuration Mount**: `./configs` is mounted to `/app/configs:ro` so engine and mission YAMLs can be modified on the host without rebuilding.
* **Host Ollama Bridge**: Built-in `host.docker.internal` bridge connects seamlessly to your host machine's Ollama instance.
* **Containerized Ollama (Optional)**: If Ollama is not installed locally, launch it inside Docker:
  ```bash
  docker compose --profile ollama up -d
  docker compose exec ollama ollama pull qwen2.5:3b
  ```

To stop containers:
```bash
docker compose down
```

---

### 5.3 Local Script Launcher (One-Click)

From the project root:

```bash
chmod +x start_maadt.sh
./start_maadt.sh
```

This script:
1. Enters `backend/` and starts the FastAPI core gateway on `http://localhost:8000`.
2. Enters `frontend/` and starts the Next.js frontend on `http://localhost:3000`.

---

### 5.4 Manual Setup

#### Step 1: Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run pytest verification suite (55 tests)
pytest -q

# Start the Core Gateway
python api/main.py
```
*Backend Gateway runs on `http://localhost:8000`.*

#### Step 2: Frontend Setup
```bash
cd frontend
npm install

# Verify production build (zero TypeScript errors)
npm run build

# Start the development server
npm run dev
```
*Frontend Operator HUD runs on `http://localhost:3000`.*

#### Step 3: Local Sovereign AI Copilot (Ollama)
```bash
# In a separate terminal, pull and start the model
ollama pull qwen2.5:3b
ollama serve
```
The backend automatically detects the local Ollama instance on `http://localhost:11434` and sets AI Status to `ONLINE`.

---

## 6. How to Run the 8-Stage DRDO Flight Demonstration

1. Open `http://localhost:3000` in any modern web browser.
2. Look at the top **Header Controller**:
   ```
   [ ◀ PREV ]  [ STEP 1 / 8: PRE-FLIGHT & TAXI ]  [ NEXT ▶ ]  [ ⏸ PAUSE ]  [ ↺ RESET ]
   ```
3. Click `NEXT ▶` to step through the mission stages:
   * **Step 1 (Pre-Flight)**: Engine warm-up at ground idle (1400 RPM). Baseline calibration.
   * **Step 2 (Takeoff & Climb)**: Full-throttle climb (2650 RPM). Thermal loading predicted by physics twin.
   * **Step 3 (Cruise Ingress)**: Level flight at 5,100 m. Mission safety margin 96%.
   * **Step 4 (Micro-Anomaly)**: Incipient Cylinder 3 CHT drift (+6°C). Conventional HUMS misses this; MAADT flags a Tier-1 residual anomaly.
   * **Step 5 (Critical Overheat)**: Injector 3 clogs (35%). CHT spikes to 193°C! In the 3D twin, Cylinder 3 pulses in glowing red. Critical warning banner appears.
   * **Step 6 (What-If Evaluation)**: Click **"TACTICAL WHAT-IF MATRIX"**. Compare Baseline vs. Throttle Derate (-15%). Notice that derating throttle drops CHT by -19°C and extends endurance by +3.5 hours.
   * **Step 7 (Execute Directive)**: Click **"EXECUTE TACTICAL DIRECTIVE"** (or click `NEXT ▶`). CHT immediately drops from 193°C to 174°C. Acoustic vibration subsides.
   * **Step 8 (Mission Stabilized)**: Margin recovers to 88%. Click **"AI COPILOT"** on the right drawer and click **"GENERATE DIAGNOSTIC REPORT"** to see the local Ollama SLM output a formal incident debrief.

---

## 7. Mathematical & Scientific References

1. **Heywood, J. B.** (1988/2018). *Internal Combustion Engine Fundamentals*. McGraw-Hill.
2. **Taylor, C. F.** (1985). *The Internal Combustion Engine in Theory and Practice*. MIT Press.
3. **Gelb, A.** (1974). *Applied Optimal Estimation*. The M.I.T. Press.
4. **Simon, D.** (2006). *Optimal State Estimation: Kalman, H-infinity, and Nonlinear Approaches*. John Wiley & Sons.
5. **Mahalanobis, P. C.** (1936). *On the generalised distance in statistics*. Proc. Natl. Inst. Sci. India.
6. **Page, E. S.** (1954). *Continuous Inspection Schemes*. Biometrika, 41(1/2), 100-115.
7. **Paris, P., & Erdogan, F.** (1963). *A Critical Analysis of Crack Propagation Laws*. Journal of Basic Engineering, ASME.
8. **Pearl, J.** (2009). *Causality: Models, Reasoning, and Inference*. Cambridge University Press.
9. **SAE International ARP5783 / ARP6887**: *Health and Usage Monitoring Metrics for Aircraft Propulsion Systems*.
10. **FAA Advisory Circular AC 33.28-1**: *Compliance of Reciprocating Aircraft Engines with FADEC and Health Monitoring Systems*.
11. **U.S. Standard Atmosphere** (1976). NOAA, NASA, USAF. Washington, D.C.

---

## 8. License & Acknowledgments

Developed as an autonomous defence engineering standard for Indian MALE UAV propulsion systems. Built with first-principles physics, modern aerospace engineering guidelines, and sovereign edge computing standards.
