"use client";
import React, { useState } from 'react';
import { TelemetryPacket } from '../types/telemetry';
import { EngineComponentId, EngineViewMode } from '../types/engine';
import { CounterfactualBranch } from '../types/mission';
import { DEFAULT_BRANCHES } from '../data/mockTelemetry';
import EngineDigitalTwin from '../components/engine/EngineDigitalTwin';
import { Play, RotateCcw, AlertTriangle, ShieldCheck, Thermometer, Flame } from 'lucide-react';
import StatusBadge from '../components/common/StatusBadge';

interface SimulationPageProps {
  telemetry: TelemetryPacket;
  viewMode: EngineViewMode;
  onViewModeChange: (mode: EngineViewMode) => void;
  selectedComponent: EngineComponentId;
  onSelectComponent: (id: EngineComponentId) => void;
  onRunSimulation: (throttle: number, altitude: number) => Promise<void>;
  onInjectFault: (type: string, severity: number) => Promise<void>;
  onClearFaults: () => Promise<void>;
}

export default function SimulationPage({
  telemetry,
  viewMode,
  onViewModeChange,
  selectedComponent,
  onSelectComponent,
  onRunSimulation,
  onInjectFault,
  onClearFaults,
}: SimulationPageProps) {
  const [altitude, setAltitude] = useState(5500);
  const [throttle, setThrottle] = useState(65);
  const [ambientTemp, setAmbientTemp] = useState(25);
  const [faultType, setFaultType] = useState("injector_abnormality");
  const [severity, setSeverity] = useState(0.85);
  const [progression, setProgression] = useState("LINEAR");
  const [rampDuration, setRampDuration] = useState(15);
  const [isSimulating, setIsSimulating] = useState(false);
  const [branches, setBranches] = useState<CounterfactualBranch[]>(DEFAULT_BRANCHES);

  const handleSimulate = async () => {
    setIsSimulating(true);
    await onRunSimulation(throttle, altitude);
    setTimeout(() => {
      setIsSimulating(false);
    }, 600);
  };

  return (
    <div className="flex-1 flex flex-col gap-4 p-4 overflow-y-auto font-mono">
      {/* Upper Area: Scenario Controls (Left) + 3D Engine (Center) */}
      <div className="flex flex-col lg:flex-row gap-4 h-auto lg:min-h-[440px] xl:min-h-[480px]">
        {/* Scenario Controls Panel (Left, 320px) */}
        <div className="w-full lg:w-80 bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4 flex flex-col justify-between shrink-0">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-[#1B344B] mb-3">
              <div>
                <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider">
                  FLIGHT LAB
                </span>
                <h3 className="text-xs font-bold text-[#F4F7FA]">Scenario Controls</h3>
              </div>
              <button
                onClick={onClearFaults}
                title="Clear All Faults"
                className="px-2 py-1 bg-[#101F30] hover:bg-[#1B344B] text-[#8FA4B8] hover:text-[#F4F7FA] rounded text-[10px] border border-[#1B344B] transition-colors cursor-pointer"
              >
                Clear Injections
              </button>
            </div>

            {/* Parameter Sliders */}
            <div className="space-y-3 text-xs">
              <div>
                <div className="flex justify-between text-[#8FA4B8] mb-1">
                  <span>Target Altitude</span>
                  <span className="font-bold text-[#F4F7FA]">{altitude} m ({(altitude * 3.28084).toFixed(0)} ft)</span>
                </div>
                <input
                  type="range"
                  min="500"
                  max="8000"
                  step="250"
                  value={altitude}
                  onChange={(e) => setAltitude(Number(e.target.value))}
                  className="w-full accent-[#22AFFF] bg-[#0B1725]"
                />
              </div>

              <div>
                <div className="flex justify-between text-[#8FA4B8] mb-1">
                  <span>Throttle Command</span>
                  <span className="font-bold text-[#F4F7FA]">{throttle}%</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="100"
                  step="5"
                  value={throttle}
                  onChange={(e) => setThrottle(Number(e.target.value))}
                  className="w-full accent-[#22AFFF] bg-[#0B1725]"
                />
              </div>

              <div>
                <div className="flex justify-between text-[#8FA4B8] mb-1">
                  <span>Ambient Temperature</span>
                  <span className="font-bold text-[#F4F7FA]">{ambientTemp} °C</span>
                </div>
                <input
                  type="range"
                  min="-20"
                  max="50"
                  step="5"
                  value={ambientTemp}
                  onChange={(e) => setAmbientTemp(Number(e.target.value))}
                  className="w-full accent-[#22AFFF] bg-[#0B1725]"
                />
              </div>

              {/* Fault Injection Bench */}
              <div className="pt-2 border-t border-[#1B344B]/60 space-y-2">
                <span className="text-[10px] uppercase font-bold text-[#8FA4B8] block">
                  FAULT INJECTION BENCH (§53)
                </span>

                <select
                  value={faultType}
                  onChange={(e) => setFaultType(e.target.value)}
                  className="w-full p-2 bg-[#0B1725] border border-[#1B344B] rounded text-xs text-[#F4F7FA] font-mono focus:border-[#22AFFF]"
                >
                  <option value="injector_abnormality">Injector Abnormality (Cyl 3)</option>
                  <option value="misfire">Cylinder Misfire</option>
                  <option value="lubrication_issue">Oil Pressure Degradation</option>
                  <option value="overheating">Thermal Heat Exchanger Loss</option>
                  <option value="sensor_drift">Sensor Bias Drift (EGT)</option>
                </select>

                <div className="flex gap-2">
                  <div className="flex-1">
                    <span className="text-[10px] text-[#8FA4B8] block mb-0.5">Severity</span>
                    <input
                      type="number"
                      min="0.1"
                      max="1.0"
                      step="0.05"
                      value={severity}
                      onChange={(e) => setSeverity(Number(e.target.value))}
                      className="w-full p-1.5 bg-[#0B1725] border border-[#1B344B] rounded text-xs text-[#F4F7FA]"
                    />
                  </div>
                  <div className="flex-1">
                    <span className="text-[10px] text-[#8FA4B8] block mb-0.5">Progression</span>
                    <select
                      value={progression}
                      onChange={(e) => setProgression(e.target.value)}
                      className="w-full p-1.5 bg-[#0B1725] border border-[#1B344B] rounded text-xs text-[#F4F7FA]"
                    >
                      <option value="INSTANT">Instant</option>
                      <option value="LINEAR">Linear</option>
                      <option value="EXPONENTIAL">Exponential</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={() => onInjectFault(faultType, severity)}
                  className="w-full py-1.5 bg-[#2D1606] hover:bg-[#7C2D12] text-[#FF8A3D] border border-[#7C2D12] rounded text-xs font-bold transition-all cursor-pointer"
                >
                  Inject Fault Vector
                </button>
              </div>
            </div>
          </div>

          {/* Action Button */}
          <button
            onClick={handleSimulate}
            disabled={isSimulating}
            className="w-full mt-3 py-2.5 bg-[#22AFFF] hover:bg-[#1A90D6] disabled:bg-[#101F30] text-[#07111D] font-bold rounded-lg flex items-center justify-center gap-2 transition-all cursor-pointer shadow-[0_0_12px_rgba(34,175,255,0.3)]"
          >
            <Play className={`w-4 h-4 fill-current ${isSimulating ? 'animate-spin' : ''}`} />
            <span>{isSimulating ? "Computing Forward Trajectory..." : "RUN SIMULATION"}</span>
          </button>
        </div>

        {/* Center: 3D Engine Digital Twin */}
        <div className="flex-1 min-w-0 flex flex-col">
          <EngineDigitalTwin
            telemetry={telemetry}
            viewMode={viewMode}
            onViewModeChange={onViewModeChange}
            selectedComponent={selectedComponent}
            onSelectComponent={onSelectComponent}
          />
        </div>
      </div>

      {/* Bottom: Counterfactual Simulation Comparison Cards (4 Branches) */}
      <div className="w-full">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[#8FA4B8]">
              COUNTERFACTUAL DECISION ROLL-OUT (4 OPERATIONAL BRANCHES &bull; §34)
            </span>
          </div>
          <span className="text-[10px] text-[#60758A]">Forward Horizon: 30 Minutes</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {branches.map((b) => (
            <div
              key={b.scenario_id}
              className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-3.5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1.5">
                  <h4 className="text-xs font-bold text-[#F4F7FA] truncate">{b.scenario_name}</h4>
                  <StatusBadge status={b.safety_verdict} size="sm" />
                </div>
                <p className="text-[11px] text-[#8FA4B8] mb-3 leading-snug">
                  {b.description}
                </p>

                <div className="space-y-1.5 text-xs bg-[#0B1725] p-2.5 rounded-lg border border-[#1B344B]/60">
                  <div className="flex justify-between">
                    <span className="text-[#8FA4B8]">Survival Margin:</span>
                    <span className="text-[#22AFFF] font-bold">{Math.round(b.final_survival_margin)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8FA4B8]">Final Health:</span>
                    <span className="text-[#F4F7FA] font-bold">{Math.round(b.final_health)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8FA4B8]">Peak CHT:</span>
                    <span className="text-[#FF8A3D] font-bold">{b.peak_cht} °C</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#8FA4B8]">Peak EGT:</span>
                    <span className="text-[#FF4D4D] font-bold">{b.peak_egt} °C</span>
                  </div>
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-[#1B344B]/60 text-[10px] text-[#8FA4B8] leading-tight">
                {b.recommendation}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
