"use client";
import React, { useState } from 'react';
import { TelemetryPacket } from '../types/telemetry';
import { EngineComponentId, EngineViewMode } from '../types/engine';
import EngineDigitalTwin from '../components/engine/EngineDigitalTwin';
import DiagnosticsPanel from '../components/diagnostics/DiagnosticsPanel';
import EngineeringResidualChart from '../components/charts/EngineeringResidualChart';
import AnomalyBreakdown from '../components/diagnostics/AnomalyBreakdown';
import SensorTrustTable from '../components/telemetry/SensorTrustTable';
import { Flame, Zap, Droplet, Waves, ShieldCheck } from 'lucide-react';

interface EngineeringPageProps {
  telemetry: TelemetryPacket;
  viewMode: EngineViewMode;
  onViewModeChange: (mode: EngineViewMode) => void;
  selectedComponent: EngineComponentId;
  onSelectComponent: (id: EngineComponentId) => void;
}

export default function EngineeringPage({
  telemetry,
  viewMode,
  onViewModeChange,
  selectedComponent,
  onSelectComponent,
}: EngineeringPageProps) {
  const [selectedSubsystem, setSelectedSubsystem] = useState<string>("Combustion");

  const subHealth = telemetry?.subsystem_health || {
    combustion: 67,
    thermal: 89,
    lubrication: 94,
    vibration: 81,
    electrical: 97,
  };

  const subsystems = [
    { id: "Combustion", label: "Combustion Subsystem", icon: Zap, health: subHealth.combustion },
    { id: "Thermal", label: "Thermal Circuit", icon: Flame, health: subHealth.thermal },
    { id: "Lubrication", label: "Lubrication & Oil", icon: Droplet, health: subHealth.lubrication },
    { id: "Vibration", label: "Vibration / Dynamics", icon: Waves, health: subHealth.vibration },
    { id: "Electrical", label: "Electrical Bus", icon: ShieldCheck, health: subHealth.electrical },
  ];

  return (
    <div className="flex-1 flex flex-col gap-4 p-4 overflow-y-auto font-mono">
      {/* ================= UPPER WORKSPACE ================= */}
      <div className="flex flex-col lg:flex-row gap-4 h-auto lg:min-h-[440px] xl:min-h-[480px]">
        {/* Left: Subsystem Navigation Rail (180px) */}
        <div className="w-full lg:w-56 bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-3 flex flex-col justify-between shrink-0">
          <div>
            <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider mb-2 block">
              SUBSYSTEM EXPLORER
            </span>
            <div className="space-y-1.5">
              {subsystems.map((sub) => {
                const Icon = sub.icon;
                const isSelected = selectedSubsystem === sub.id;
                return (
                  <button
                    key={sub.id}
                    onClick={() => {
                      setSelectedSubsystem(sub.id);
                      if (sub.id === "Combustion") onSelectComponent("cylinder_3");
                      else if (sub.id === "Thermal") onSelectComponent("turbocharger");
                      else if (sub.id === "Lubrication") onSelectComponent("lubrication");
                      else if (sub.id === "Vibration") onSelectComponent("crankshaft");
                    }}
                    className={`w-full p-2.5 rounded-lg border text-left transition-all cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? "bg-[#102E4A] border-[#22AFFF]/50 text-[#22AFFF] font-bold"
                        : "bg-[#0B1725] border-[#1B344B] text-[#8FA4B8] hover:text-[#F4F7FA] hover:bg-[#101F30]"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Icon className="w-3.5 h-3.5" />
                      <span className="text-xs">{sub.id}</span>
                    </div>
                    <span className="text-xs font-bold text-[#F4F7FA]">{Math.round(sub.health)}%</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="p-2.5 bg-[#0B1725] border border-[#1B344B] rounded-lg mt-3 text-[10px] text-[#8FA4B8]">
            <div>Focused Subsystem: <strong className="text-[#22AFFF]">{selectedSubsystem}</strong></div>
            <div className="mt-0.5 text-[#60758A]">Coupled Physics Invariant</div>
          </div>
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

        {/* Right: Diagnostic Panel */}
        <DiagnosticsPanel diagnostic={telemetry.active_diagnostic} />
      </div>

      {/* ================= BOTTOM: ENGINEERING ANALYSIS GRID ================= */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pb-2">
        <div className="h-68">
          <EngineeringResidualChart telemetry={telemetry} />
        </div>

        <div className="h-68">
          <AnomalyBreakdown details={telemetry.anomaly_breakdown} />
        </div>

        <div className="h-68">
          <SensorTrustTable
            trust={telemetry.sensor_trust}
            quality={telemetry.sensor_quality}
          />
        </div>
      </div>
    </div>
  );
}
