  # MAADT: System Architecture & Technical Specifications
### *Physics-Informed, AI-Augmented Digital Twin Framework for MALE UAV Aero-Piston Engines*

---

## 1. High-Level Architectural Topology

MAADT (*Mission-Aware Adaptive Digital Twin*) is architected as an aerospace-grade, high-performance monorepo uniting a **FastAPI / Python analytical core** with a **Next.js 16 (React 19) / Three.js WebGL tactical Ground Control Station (GCS) HUD**. 

```
                                  MAADT SYSTEM DATAFLOW
                                  
+──────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    UAV TELEMETRY / SENSORS                                       |
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

## 2. Mathematical Formulations & Physical Models

### 2.1 0D Thermodynamic Cycle & Lumped Thermal Model (`core/engine_model.py`)
The baseline digital twin models an air-cooled, turbocharged 4-stroke spark-ignition boxer engine (Rotax 914/915 iS specification).

#### 1. Altitude Atmosphere (1976 US Standard Atmosphere)
At geometric altitude $z$:
$$T_{amb}(z) = T_0 - L \cdot z \quad (L = 0.0065\text{ K/m}, \, T_0 = 288.15\text{ K})$$
$$P_{amb}(z) = P_0 \left( 1 - \frac{L \cdot z}{T_0} \right)^{\frac{g \cdot M}{R \cdot L}} \quad (P_0 = 101,325\text{ Pa})$$
$$\rho_{air}(z) = \frac{P_{amb}(z)}{R_{specific} \cdot T_{amb}(z)}$$

#### 2. Intake Manifold Density & Air Mass Flow ($\dot{m}_{air}$)
The turbocharger with automatic wastegate maintains manifold pressure up to critical altitude:
$$MAP = \min\left( MAP_{max}, P_{amb} \cdot \Pi_{turbo}(TLA) \right)$$
Using the speed-density formulation:
$$\dot{m}_{air} = \frac{MAP \cdot V_d \cdot N}{2 \cdot R_{specific} \cdot T_{intake}} \cdot \eta_v(N, MAP)$$
where:
* $V_d = 1.352 \times 10^{-3}\text{ m}^3$ (Displacement volume)
* $N$ = Engine speed in RPM
* $\eta_v(N, MAP) \in [0.78, 0.92]$ = Volumetric efficiency curve calibrated from engine dynamometer test records.

#### 3. Fuel Flow & Combustion Heat Input ($\dot{Q}_{in}$)
Per-cylinder fuel mass injection rate:
$$\dot{m}_{fuel, i} = \frac{\dot{m}_{air} / 4}{(A/F)_{stoich}} \cdot \phi_i \cdot \eta_{inj, i}$$
where $(A/F)_{stoich} = 14.7$, $\phi_i$ is fuel-air equivalence ratio, and $\eta_{inj, i} \in [0, 1]$ represents nozzle discharge coefficient health.  
Chemical heat release per cylinder:
$$\dot{Q}_{in, i} = \dot{m}_{fuel, i} \cdot LHV_{fuel} \cdot \eta_{combustion} \quad (LHV_{fuel} \approx 44.0\text{ MJ/kg})$$

#### 4. Cylinder Head Lumped Thermal Differential Equation
Heat transfer to the cylinder wall versus heat rejection through fin convection:
$$C_{th} \frac{dT_{cht, i}}{dt} = \dot{Q}_{comb \to wall, i} - \dot{Q}_{wall \to ambient, i}$$
$$\dot{Q}_{comb \to wall, i} = h_{gas}(N, MAP) \cdot A_{comb} \cdot (T_{flame} - T_{cht, i})$$
$$\dot{Q}_{wall \to ambient, i} = \left[ h_{natural} + h_{forced}(V_{TAS}, \rho_{air}) \right] \cdot A_{fin} \cdot (T_{cht, i} - T_{amb})$$
For forced convection over finned cylinder barrels:
$$h_{forced} = C_{fin} \cdot \left( \frac{\rho_{air} \cdot V_{TAS} \cdot d_{fin}}{\mu_{air}} \right)^{0.68} \cdot \text{Pr}^{0.33} \cdot \frac{k_{air}}{d_{fin}}$$
Under steady-state cruise ($\frac{dT}{dt} \approx 0$), this differential equation yields the **theoretically expected temperature** $T_{cht, expected}$ for each cylinder.

#### 5. Physics Residual Vector ($\vec{r}(t)$)
$$\vec{r}(t) = \vec{y}_{sensor}(t) - \vec{y}_{physics\_model}(\text{altitude}, \text{airspeed}, \text{throttle}, OAT)$$
$$\vec{r}(t) = \begin{bmatrix} r_{EGT}(t) & r_{CHT}(t) & r_{RPM}(t) & r_{FF}(t) & r_{OilT}(t) & r_{OilP}(t) \end{bmatrix}^T$$

---

### 2.2 Extended Kalman Filter (EKF) State Estimator (`core/ekf.py`)
To isolate mechanical and combustion degradation from ambient wind gusts and atmospheric noise:

* **State Vector**:
  $$\mathbf{x} = \left[ N, \, T_{cht, 1..4}, \, T_{egt, 1..4}, \, P_{oil}, \, \theta_{friction}, \, \eta_{inj, 1..4} \right]^T \in \mathbb{R}^{15}$$
* **Non-linear Dynamics**: $\dot{\mathbf{x}} = f(\mathbf{x}, \mathbf{u}) + \mathbf{w}(t), \quad \mathbf{w} \sim \mathcal{N}(0, \mathbf{Q})$
* **Observation Function**: $\mathbf{z}_k = h(\mathbf{x}_k) + \mathbf{v}_k, \quad \mathbf{v} \sim \mathcal{N}(0, \mathbf{R})$
* **Jacobian Matrices**:
  $$F_k = \left. \frac{\partial f}{\partial \mathbf{x}} \right|_{\hat{\mathbf{x}}_{k-1|k-1}}, \quad H_k = \left. \frac{\partial h}{\partial \mathbf{x}} \right|_{\hat{\mathbf{x}}_{k|k-1}}$$
* **Filter Innovation & Gain**:
  $$\tilde{\mathbf{y}}_k = \mathbf{z}_k - h(\hat{\mathbf{x}}_{k|k-1})$$
  $$S_k = H_k P_{k|k-1} H_k^T + R_k$$
  $$K_k = P_{k|k-1} H_k^T S_k^{-1}$$
  $$\hat{\mathbf{x}}_{k|k} = \hat{\mathbf{x}}_{k|k-1} + K_k \tilde{\mathbf{y}}_k$$
  $$P_{k|k} = (I - K_k H_k) P_{k|k-1}$$

---

### 2.3 4-Tier Hybrid Anomaly Engine (`analytics/hybrid_anomaly_engine.py`)
Combines four distinct diagnostic paradigms to eliminate single-model blind spots:

1. **Tier 1 — Physics Residual Z-Score ($S_{phys}$)**:
   $$S_{phys} = \frac{1}{M} \sum_{j=1}^M \min\left( 1.0, \, \frac{|r_j(t) - \mu_{r, j}|}{3 \cdot \sigma_{r, j}} \right)$$
2. **Tier 2 — Statistical Mahalanobis Covariance Distance ($S_{stat}$)**:
   $$D_M(\mathbf{z}) = \sqrt{ (\mathbf{z} - \boldsymbol{\mu})^T \mathbf{\Sigma}^{-1} (\mathbf{z} - \boldsymbol{\mu}) }$$
   $$S_{stat} = 1 - \exp\left( -\frac{D_M(\mathbf{z})^2}{2 \cdot \chi^2_{p, 0.95}} \right)$$
   Detects cross-sensor correlation breakdowns (e.g. RPM climbing while fuel flow drops).
3. **Tier 3 — Autoencoder Latent Reconstruction Loss ($S_{ml}$)**:
   $$S_{ml} = \tanh\left( \frac{\|\mathbf{z} - \hat{\mathbf{z}}\|_2^2}{\epsilon_{threshold}} \right)$$
   Trained exclusively on healthy nominal flight sorties to catch non-linear multi-dimensional anomalies.
4. **Tier 4 — CUSUM Trend Drift Tracker ($S_{trend}$)**:
   $$C_k^+ = \max\left(0, \, C_{k-1}^+ + (r_k - \mu_0) - k_{slack}\right)$$
   $$S_{trend} = \min\left(1.0, \, \frac{C_k^+}{H_{decision}}\right)$$
   Detects subtle micro-degradations accumulating over hours of loiter.

**Fused Composite Anomaly Metric**:
$$S_{comp}(t) = 0.35 \cdot S_{phys}(t) + 0.25 \cdot S_{stat}(t) + 0.25 \cdot S_{ml}(t) + 0.15 \cdot S_{trend}(t)$$
*Classification*: $< 0.35$ (Nominal), $0.35 - 0.65$ (Advisory), $> 0.65$ (Critical Alarm).

---

### 2.4 Counterfactual "What-If" Forward Simulation (`mission/counterfactual.py`)
Using Judea Pearl's Structural Causal Models (SCM), when an anomaly is diagnosed at time $t_0$, the engine evaluates prospective actions $\text{do}(A = a)$ by integrating the calibrated physics ODEs forward across a 30-minute horizon ($< 50\text{ ms}$ compute rollout):

$$\mathcal{T}_k = \left\{ \mathbf{x}(t) \;\Big|\; t \in [t_0, t_0 + \Delta t_{horizon}], \, \mathbf{u}(t) = \pi_k(\mathbf{x}(t)) \right\}$$

* **Trajectory 0 (Baseline / Continue Cruise)**: Reveals thermal runaway ($T_{cht, 3} \to 204^\circ\text{C}$ in 18 minutes $\to$ piston seizure).
* **Trajectory 1 (Throttle Derate -15%)**: Drops $\dot{Q}_{in}$ by 22%, dropping $T_{cht, 3}$ by $-19^\circ\text{C}$ and **extending loiter endurance by +3.5 hours**.
* **Trajectory 2 (Step Descent -2000 ft)**: Explores trade-off between denser air cooling mass flow vs aerodynamic drag and fuel consumption.
* **Trajectory 3 (Immediate RTB Vector)**: Calculates minimum energy recovery trajectory back to recovery airfield.

---

### 2.5 Prognostics & Remaining Useful Life (RUL) Engine (`prognostics/rul_engine.py`)
* **Arrhenius-Coffin-Manson Thermal Fatigue Model**:
  $$D_{thermal}(t) = \int_0^t A \cdot \exp\left( -\frac{E_a}{k_B \cdot T_{cht}(\tau)} \right) \cdot [\sigma_{mech}(\tau)]^\beta \, d\tau$$
* **Sequential Monte Carlo Particle Filter**:
  Propagates 500 stochastic degradation particles forward:
  $$x_k^{(i)} = x_{k-1}^{(i)} + \alpha_k^{(i)} \cdot \Delta t + \xi_k^{(i)}, \quad \xi \sim \mathcal{N}(0, \sigma_{deg}^2)$$
  Produces robust confidence intervals: **$RUL_{median}$**, **$RUL_{lower\,90\%}$**, and **$RUL_{upper\,90\%}$**.

---

## 3. Sovereign Air-Gapped AI Architecture

* **Military Air-Gap Requirement**: Defence aircraft telemetry must never be sent to commercial cloud endpoints.
* **Edge Engine**: Directly communicates with the local **Ollama** daemon (`http://localhost:11434`) on the GCS workstation.
* **Models**:
  * `qwen2.5:3b`: Default sub-second diagnostic copilot (~3 GB VRAM).
  * `mistral:latest`: Formal engineering incident report generator.
  * `qwen3:14b`: Advanced multi-system structural reasoning.
* **Telemetry Grounding Pipeline**: Active telemetry vectors, Kalman residual states, and classified fault hypotheses are serialized into prompt contexts. The model generates root-cause explanations and standard operating procedures (SOP) with zero external network connectivity.

---

## 4. Frontend WebGL 3D Twin & Operator HUD Architecture

* **Framework**: Next.js 16.3 (React 19, Turbopack, App Router).
* **Styling**: Custom tactical dark theme (`#07111D`, `#0B1E33`, `#00F0FF`, `#10B981`, `#F59E0B`, `#EF4444`).
* **3D Visualizer**: Three.js / React Three Fiber:
  * Procedural, semi-translucent Indian MALE UAV airframe with twin booms, inverted V-tail, and spinning pusher propeller.
  * Anatomically accurate Boxer-4 engine core (cylinders, fin barrels, crankcase, fuel rail, individual injectors, exhaust headers, turbocharger).
  * Real-time sine-wave emissive pulsating warning glow on degraded components.
  * 4 rendering modes: *Interactive Photorealistic*, *Thermal Heatmap*, *Stress Gradient*, and *Ghost Fuselage*.
* **Operator Interactivity**:
  * Clicking any of the 8 telemetry cards (CHT, EGT, RPM, Vibration, Oil Temp/Pressure, Fuel Flow) rotates and focuses the 3D camera on that specific mechanical part.
  * Clicking the active anomaly banner opens the **Emergency SOP Checklist Modal**.
  * Single-click **"EXECUTE TACTICAL DIRECTIVE"** applies counterfactual recovery actions immediately.
  * Integrated **8-Stage DRDO Flight Script runner** in the header for deterministic video demonstrations.

---

## 5. Directory & File Organization

```text
maadt-app/
├── backend/                             # Python Core Service
│   ├── analytics/                       # Diagnostic Intelligence
│   │   ├── hybrid_anomaly_engine.py     # 4-tier composite anomaly engine
│   │   ├── fault_classifier.py          # Multi-class physics-guided classifier
│   │   ├── features.py                  # Real-time feature extraction
│   │   ├── explainability.py            # SHAP & physical attribution
│   │   └── ollama_ai_service.py         # Local Ollama sovereign SLM client
│   │
│   ├── api/                             # Communication Gateway
│   │   └── main.py                      # FastAPI app & 10 Hz WebSocket streamer
│   │
│   ├── config/                          # Engine Specifications
│   │   ├── engine_config.py             # Rotax 914 / 915 iS physical parameters
│   │   └── loader.py                    # Dynamic configuration manager
│   │
│   ├── core/                            # Physics & State Estimation
│   │   ├── engine_model.py              # 0D thermodynamic Otto cycle model
│   │   ├── ekf.py                       # Extended Kalman Filter state estimator
│   │   ├── twin_manager.py              # Digital twin lifecycle coordinator
│   │   └── physics_model.py             # Lumped thermal differential solver
│   │
│   ├── mission/                         # Tactical Decision Center
│   │   ├── counterfactual.py            # High-speed What-If rollout engine
│   │   └── margin_calculator.py         # Composite mission safety margin
│   │
│   ├── prognostics/                     # Remaining Useful Life
│   │   ├── rul_engine.py                # Arrhenius-Coffin-Manson & Particle Filter
│   │   ├── degradation_tracker.py       # Cumulative wear tracking
│   │   └── stress_index.py              # Multi-subsystem stress evaluator
│   │
│   ├── simulation/                      # Synthetic Simulation
│   │   ├── engine_sim.py                # 10 Hz telemetry generator
│   │   ├── fault_injector.py            # Realistic fault injection module
│   │   └── mission_runner.py            # Autonomous sortie state machine
│   │
│   ├── storage/                         # Persistence
│   │   └── database.py                  # SQLite telemetry & event schema
│   │
│   └── tests/                           # Verification Suite
│       └── test_*.py                    # 55 passing unit and integration tests
│
├── frontend/                            # Next.js 16 Tactical Client
│   ├── src/
│   │   ├── app/                         # App Router root
│   │   ├── components/                  # UI Components
│   │   │   ├── ai/                      # AICopilotDrawer.tsx (Ollama UI)
│   │   │   ├── engine/                  # ProceduralUavTwin.tsx & ProceduralEngineTwin.tsx
│   │   │   ├── layout/                  # Header.tsx (8-stage DRDO demo controller)
│   │   │   ├── mission/                 # TacticalWhatIfMatrix.tsx, EmergencyChecklistModal.tsx
│   │   │   └── telemetry/               # TelemetryStrip.tsx, TelemetryCard.tsx
│   │   ├── views/                       # Primary Screens
│   │   │   ├── Operation.tsx            # Operator GCS Command Center
│   │   │   ├── Engineering.tsx          # Deep Diagnostic Engineering Suite
│   │   │   ├── Simulation.tsx           # Interactive Sandbox & Fault Injector
│   │   │   ├── Replay.tsx               # Historical Sortie Time-Travel Engine
│   │   │   └── Fleet.tsx                # Multi-UAV Squadron Health Aggregator
│   │   ├── data/                        # demoScenario.ts (8-stage DRDO mission script)
│   │   ├── services/                    # api.ts, telemetryService.ts (WebSocket)
│   │   └── types/                       # telemetry.ts, engine.ts
│   └── package.json                     # Frontend configuration
│
└── start_maadt.sh                       # One-Click Autonomous System Launcher
```
