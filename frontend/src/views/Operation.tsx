"use client";
import React, { useState } from 'react';
import { TelemetryPacket } from '../types/telemetry';
import { ComponentDetails, EngineComponentId, EngineViewMode } from '../types/engine';
import EngineDigitalTwin from '../components/engine/EngineDigitalTwin';
import ComponentDetailsPanel from '../components/mission/ComponentDetailsPanel';
import MissionStatusPanel from '../components/mission/MissionStatusPanel';
import TelemetryStrip from '../components/telemetry/TelemetryStrip';
import EGTTrendChart from '../components/charts/EGTTrendChart';
import EngineHealthPanel from '../components/mission/EngineHealthPanel';
import MissionRecommendations from '../components/mission/MissionRecommendations';
import TacticalWhatIfMatrix from '../components/mission/TacticalWhatIfMatrix';
import EmergencyChecklistModal from '../components/mission/EmergencyChecklistModal';
import { Sliders, LineChart, Zap, CheckCircle2, RotateCcw, AlertTriangle, ShieldCheck } from 'lucide-react';

interface OperationPageProps {
  telemetry: TelemetryPacket;
  history: TelemetryPacket[];
  viewMode: EngineViewMode;
  onViewModeChange: (mode: EngineViewMode) => void;
  selectedComponent: EngineComponentId;
  componentDetails: ComponentDetails;
  onSelectComponent: (id: EngineComponentId) => void;
  onNavigateToEngineering: () => void;
  onNavigateToSimulation: () => void;
  onAskAI?: (query: string) => void;
  activeDirective?: string;
  onApplyDirective?: (actionId: string) => void;
}

export default function OperationPage({
  telemetry,
  history,
  viewMode,
  onViewModeChange,
  selectedComponent,
  componentDetails,
  onSelectComponent,
  onNavigateToEngineering,
  onNavigateToSimulation,
  onAskAI,
  activeDirective = "none",
  onApplyDirective,
}: OperationPageProps) {
  const [isWhatIfView, setIsWhatIfView] = useState<boolean>(false);
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState<boolean>(false);

  const handleDirectiveAction = (actionId: string) => {
    if (onApplyDirective) {
      onApplyDirective(actionId);
    }
  };

  return (
    <div className="flex-1 flex flex-col gap-3.5 p-4 overflow-y-auto font-mono select-none">
      {/* ================= TACTICAL DIRECTIVE ACTIVE HUD BANNER ================= */}
      {activeDirective !== "none" && (
        <div className="bg-[#072418] border border-[#22D88A] rounded-xl px-4 py-2 flex flex-wrap items-center justify-between gap-2 shadow-[0_0_12px_rgba(34,216,138,0.2)]">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#22D88A] animate-pulse" />
            <div className="text-xs">
              <span className="font-bold text-[#22D88A] uppercase tracking-wider">
                {activeDirective === "throttle_down" && "TACTICAL DIRECTIVE ACTIVE: THROTTLE DERATED TO 50% POWER (-15%)"}
                {activeDirective === "step_down" && "TACTICAL DIRECTIVE ACTIVE: DESCENT TO 4,900M RAM COOLING ALTITUDE"}
                {activeDirective === "rtb" && "EMERGENCY RECOVERY ENGAGED: RETURN TO BASE VECTOR (HEADING 245°)"}
              </span>
              <span className="text-[#8FA4B8] ml-2 hidden sm:inline text-[11px]">
                {activeDirective === "throttle_down" && "Thermal flux relieved (-19°C CHT). Loiter endurance extended +2.8 hrs."}
                {activeDirective === "step_down" && "Denser air mass cooling cylinder banks. CHT stabilized at 172°C."}
                {activeDirective === "rtb" && "Engine in minimum drag glide. ETA Base Runway: 26 min."}
              </span>
            </div>
          </div>
          <button
            onClick={() => handleDirectiveAction("continue")}
            className="px-2.5 py-1 bg-[#0B1725] hover:bg-[#102E4A] text-[#8FA4B8] hover:text-[#F4F7FA] border border-[#1B344B] rounded text-[11px] font-bold transition-all cursor-pointer flex items-center gap-1.5"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Revert to Nominal Cruise</span>
          </button>
        </div>
      )}

      {/* ================= UPPER WORKSPACE (3D Engine + Details + Mission Status) ================= */}
      <div className="flex flex-col lg:flex-row gap-4 h-auto lg:h-[480px] xl:h-[520px]">
        {/* Left/Center: 3D Engine Hero Area (50-55% width) */}
        <div className="flex-1 min-w-0 flex flex-col h-full">
          <EngineDigitalTwin
            telemetry={telemetry}
            viewMode={viewMode}
            onViewModeChange={onViewModeChange}
            selectedComponent={selectedComponent}
            onSelectComponent={onSelectComponent}
          />
        </div>

        {/* Middle-Right: Component Details Panel (260-300px) */}
        <ComponentDetailsPanel
          component={componentDetails}
          onClose={() => onSelectComponent("cylinder_3")}
          onViewMore={onNavigateToEngineering}
          onAskAI={onAskAI}
        />

        {/* Far-Right: Mission Status Panel (300-340px) */}
        <MissionStatusPanel
          telemetry={telemetry}
          onViewAlerts={() => setIsEmergencyModalOpen(true)}
        />
      </div>

      {/* ================= MIDDLE: LIVE TELEMETRY STRIP (8 INTERACTIVE CARDS) ================= */}
      <div className="w-full">
        <TelemetryStrip
          telemetry={telemetry}
          history={history}
          onSelectComponent={onSelectComponent}
        />
      </div>

      {/* ================= BOTTOM WORKSPACE SWITCHER BAR ================= */}
      <div className="flex items-center justify-between pt-1 pb-0 border-b border-[#1B344B]/70">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsWhatIfView(false)}
            className={`px-3 py-1.5 rounded-t-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer border-t border-x ${
              !isWhatIfView
                ? "bg-[#0D1B2A] text-[#22AFFF] border-[#1B344B] border-b-transparent shadow-sm"
                : "bg-transparent text-[#8FA4B8] hover:text-[#F4F7FA] border-transparent"
            }`}
          >
            <LineChart className="w-3.5 h-3.5" />
            <span>Mission Telemetry & Health Decomposition</span>
          </button>

          <button
            onClick={() => setIsWhatIfView(true)}
            className={`px-3 py-1.5 rounded-t-lg text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer border-t border-x ${
              isWhatIfView
                ? "bg-[#0D1B2A] text-[#22AFFF] border-[#1B344B] border-b-transparent shadow-sm"
                : "bg-transparent text-[#8FA4B8] hover:text-[#F4F7FA] border-transparent"
            }`}
          >
            <Sliders className="w-3.5 h-3.5 text-[#22AFFF]" />
            <span>Tactical What-If Decision Matrix (4 Multi-Branch Projections)</span>
          </button>
        </div>

        <span className="text-[10px] text-[#60758A] hidden sm:inline">
          Continuous Prognostics &bull; Automated Autonomy Directives
        </span>
      </div>

      {/* ================= BOTTOM ANALYTICS AREA ================= */}
      {!isWhatIfView ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 pb-2">
          {/* Column 1: EGT Trend Chart */}
          <div className="h-64">
            <EGTTrendChart
              history={history}
              currentEgt={telemetry.egt}
              expectedEgt={telemetry.expected_egt}
            />
          </div>

          {/* Column 2: Engine Health Decomposition */}
          <div className="h-64">
            <EngineHealthPanel subsystemHealth={telemetry.subsystem_health} />
          </div>

          {/* Column 3: Mission Recommendations with In-Place Execution */}
          <div className="h-64">
            <MissionRecommendations
              currentMargin={telemetry.mission_margin}
              activeDirective={activeDirective}
              onApplyDirective={handleDirectiveAction}
              onOpenWhatIf={() => setIsWhatIfView(true)}
            />
          </div>
        </div>
      ) : (
        /* Full-Width Tactical What-If Scenario Matrix */
        <div className="w-full pb-2">
          <TacticalWhatIfMatrix
            currentCht={telemetry.cht + (selectedComponent === "cylinder_3" ? 23 : 0)}
            currentEgt={telemetry.egt}
            currentMargin={telemetry.mission_margin}
            activeDirective={activeDirective}
            onApplyDirective={handleDirectiveAction}
            onClose={() => setIsWhatIfView(false)}
          />
        </div>
      )}

      {/* ================= OPERATOR EMERGENCY CHECKLIST MODAL ================= */}
      <EmergencyChecklistModal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModalOpen(false)}
        telemetry={telemetry}
        onApplyDirective={handleDirectiveAction}
        onNavigateToEngineering={onNavigateToEngineering}
      />
    </div>
  );
}
