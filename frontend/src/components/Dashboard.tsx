"use client";
import React, { useState, useEffect, useRef } from 'react';
import Header from './layout/Header';
import Sidebar, { NavigationPage } from './layout/Sidebar';
import OperationPage from '../views/Operation';
import EngineeringPage from '../views/Engineering';
import SimulationPage from '../views/Simulation';
import ReplayPage from '../views/Replay';
import FleetPage from '../views/Fleet';
import SettingsPage from '../views/Settings';
import AICopilotDrawer from './ai/AICopilotDrawer';
import { TelemetryPacket } from '../types/telemetry';
import { EngineComponentId, EngineViewMode } from '../types/engine';
import { BASELINE_TELEMETRY, COMPONENT_CATALOG } from '../data/mockTelemetry';
import { DEMO_STEPS } from '../data/demoScenario';
import { telemetryService } from '../services/websocket';
import { apiService } from '../services/api';

export default function Dashboard() {
  const [currentPage, setCurrentPage] = useState<NavigationPage>("operation");
  const [telemetry, setTelemetry] = useState<TelemetryPacket>(BASELINE_TELEMETRY);
  const [history, setHistory] = useState<TelemetryPacket[]>([BASELINE_TELEMETRY]);
  const [viewMode, setViewMode] = useState<EngineViewMode>("3D");
  const [selectedComponent, setSelectedComponent] = useState<EngineComponentId>("cylinder_3");
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  
  // Tactical directive applied state
  const [activeDirective, setActiveDirective] = useState<string>("none");

  // Demo walkthrough controller state
  const [isDemoRunning, setIsDemoRunning] = useState<boolean>(false);
  const [demoStepIndex, setDemoStepIndex] = useState<number>(0);
  const demoTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Local Ollama AI Copilot State
  const [isAICopilotOpen, setIsAICopilotOpen] = useState<boolean>(false);
  const [aiCopilotInitialQuery, setAICopilotInitialQuery] = useState<string | undefined>(undefined);

  // Initialize Telemetry WebSocket & Polling Fallback
  useEffect(() => {
    const unsubConn = telemetryService.subscribeConnection((connected) => {
      setIsWsConnected(connected);
    });

    const unsubscribe = telemetryService.subscribe((packet) => {
      // If demo is not manually overriding, accept incoming telemetry stream
      setTelemetry((prev) => {
        const nextPacket = isDemoRunning ? prev : packet;
        setHistory((h) => {
          const updated = [...h, nextPacket];
          if (updated.length > 30) updated.shift();
          return updated;
        });
        return nextPacket;
      });
    });

    return () => {
      unsubConn();
      unsubscribe();
    };
  }, [isDemoRunning]);

  // Demo Scenario Controller
  const handleToggleDemo = () => {
    if (isDemoRunning) {
      handlePauseDemo();
    } else {
      setIsDemoRunning(true);
      if (demoStepIndex >= DEMO_STEPS.length - 1) {
        setDemoStepIndex(0);
        runDemoStep(0);
      } else {
        runDemoStep(demoStepIndex);
      }
    }
  };

  const handlePauseDemo = () => {
    if (demoTimerRef.current) {
      clearTimeout(demoTimerRef.current);
      demoTimerRef.current = null;
    }
    setIsDemoRunning(false);
  };

  const handleResetDemo = () => {
    if (demoTimerRef.current) {
      clearTimeout(demoTimerRef.current);
      demoTimerRef.current = null;
    }
    setIsDemoRunning(false);
    setDemoStepIndex(0);
    setActiveDirective("none");
    setTelemetry(BASELINE_TELEMETRY);
    telemetryService.setManualPacket(BASELINE_TELEMETRY);
    setSelectedComponent("cylinder_3");
  };

  const applyDemoStepDirect = (stepIdx: number) => {
    if (demoTimerRef.current) {
      clearTimeout(demoTimerRef.current);
      demoTimerRef.current = null;
    }
    const currentStep = DEMO_STEPS[stepIdx];
    setDemoStepIndex(stepIdx);
    setIsDemoRunning(true);

    setTelemetry((prev) => {
      const patched: TelemetryPacket = {
        ...prev,
        ...currentStep.patch,
        timestamp: Date.now() / 1000,
      };
      telemetryService.setManualPacket(patched);
      return patched;
    });
  };

  const handleNextDemoStep = () => {
    const nextIdx = (demoStepIndex + 1) % DEMO_STEPS.length;
    applyDemoStepDirect(nextIdx);
  };

  const handlePrevDemoStep = () => {
    const prevIdx = demoStepIndex > 0 ? demoStepIndex - 1 : DEMO_STEPS.length - 1;
    applyDemoStepDirect(prevIdx);
  };

  const runDemoStep = (stepIdx: number) => {
    if (stepIdx >= DEMO_STEPS.length) {
      setIsDemoRunning(false);
      return;
    }

    const currentStep = DEMO_STEPS[stepIdx];
    setDemoStepIndex(stepIdx);

    // Apply partial patch
    setTelemetry((prev) => {
      const patched: TelemetryPacket = {
        ...prev,
        ...currentStep.patch,
        timestamp: Date.now() / 1000,
      };
      telemetryService.setManualPacket(patched);
      return patched;
    });

    // Schedule next step
    demoTimerRef.current = setTimeout(() => {
      runDemoStep(stepIdx + 1);
    }, currentStep.durationMs);
  };

  // Tactical Directives Controller
  const handleApplyDirective = (directiveId: string) => {
    setActiveDirective(directiveId);

    if (directiveId === "throttle_down") {
      setTelemetry((prev) => {
        const patched: TelemetryPacket = {
          ...prev,
          rpm: 2260,
          cht: 174,
          egt: 724,
          vibration: 0.34,
          fuel_flow: 18.2,
          anomaly_score: 0.26,
          health_index: 89,
          mission_margin: 84,
          operating_regime: "LOITER",
          active_faults: [],
        };
        telemetryService.setManualPacket(patched);
        return patched;
      });
    } else if (directiveId === "step_down") {
      setTelemetry((prev) => {
        const patched: TelemetryPacket = {
          ...prev,
          cht: 172,
          egt: 738,
          vibration: 0.48,
          mission_margin: 81,
          operating_regime: "DESCENT",
        };
        telemetryService.setManualPacket(patched);
        return patched;
      });
    } else if (directiveId === "rtb") {
      setTelemetry((prev) => {
        const patched: TelemetryPacket = {
          ...prev,
          rpm: 2100,
          cht: 164,
          egt: 695,
          vibration: 0.25,
          mission_margin: 96,
          operating_regime: "DESCENT",
        };
        telemetryService.setManualPacket(patched);
        return patched;
      });
    } else if (directiveId === "continue") {
      setActiveDirective("none");
      setTelemetry((prev) => {
        const patched: TelemetryPacket = {
          ...prev,
          operating_regime: "CRUISE",
        };
        telemetryService.setManualPacket(patched);
        return patched;
      });
    }
  };

  // Resolve active component details with live values
  const activeCatalogComponent = COMPONENT_CATALOG[selectedComponent] || COMPONENT_CATALOG.cylinder_3;
  const componentDetails = {
    ...activeCatalogComponent,
    health:
      selectedComponent === "cylinder_3" && telemetry.anomaly_score > 0.4
        ? 68
        : activeCatalogComponent.health,
    cht:
      selectedComponent === "cylinder_3"
        ? Math.round(telemetry.cht + 23)
        : activeCatalogComponent.cht,
    egt:
      selectedComponent === "cylinder_3"
        ? Math.round(telemetry.egt)
        : activeCatalogComponent.egt,
    vibration:
      selectedComponent === "cylinder_3"
        ? Number(telemetry.vibration.toFixed(2))
        : activeCatalogComponent.vibration,
    status:
      selectedComponent === "cylinder_3" && telemetry.anomaly_score > 0.4
        ? "Abnormal"
        : activeCatalogComponent.status,
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#07111D] text-[#F4F7FA] overflow-hidden select-none">
      {/* ================= PERMANENT TOP HEADER ================= */}
      <Header
        twinConfidence={telemetry.twin_confidence ? telemetry.twin_confidence * 100 : 94}
        telemetryHz={2}
        isConnected={isWsConnected}
        isDemoRunning={isDemoRunning}
        demoStepIndex={demoStepIndex}
        totalDemoSteps={DEMO_STEPS.length}
        demoStepLabel={DEMO_STEPS[demoStepIndex]?.label}
        onToggleDemo={handleToggleDemo}
        onResetDemo={handleResetDemo}
        onNextDemoStep={handleNextDemoStep}
        onPrevDemoStep={handlePrevDemoStep}
        onToggleAICopilot={() => setIsAICopilotOpen((prev) => !prev)}
      />

      {/* ================= MAIN APPLICATION WORKSPACE ================= */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Permanent Left Sidebar Navigation Rail */}
        <Sidebar
          currentPage={currentPage}
          onSelectPage={(page) => setCurrentPage(page)}
        />

        {/* Dynamic Main Workspace based on Screen */}
        <main className="flex-1 flex flex-col min-w-0 bg-[#07111D] overflow-hidden">
          {currentPage === "operation" && (
            <OperationPage
              telemetry={telemetry}
              history={history}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
              selectedComponent={selectedComponent}
              componentDetails={componentDetails as any}
              onSelectComponent={setSelectedComponent}
              onNavigateToEngineering={() => setCurrentPage("engineering")}
              onNavigateToSimulation={() => setCurrentPage("simulation")}
              onAskAI={(q) => {
                setAICopilotInitialQuery(q);
                setIsAICopilotOpen(true);
              }}
              activeDirective={activeDirective}
              onApplyDirective={handleApplyDirective}
            />
          )}

          {currentPage === "engineering" && (
            <EngineeringPage
              telemetry={telemetry}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
              selectedComponent={selectedComponent}
              onSelectComponent={setSelectedComponent}
            />
          )}

          {currentPage === "simulation" && (
            <SimulationPage
              telemetry={telemetry}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
              selectedComponent={selectedComponent}
              onSelectComponent={setSelectedComponent}
              onRunSimulation={async (throttle, alt) => {
                await apiService.simulateMission(throttle, alt);
              }}
              onInjectFault={async (type, sev) => {
                await apiService.injectFault(type, sev);
              }}
              onClearFaults={async () => {
                await apiService.clearFaults();
                handleResetDemo();
              }}
            />
          )}

          {currentPage === "replay" && (
            <ReplayPage
              telemetry={telemetry}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
              selectedComponent={selectedComponent}
              onSelectComponent={setSelectedComponent}
              onScrubTelemetry={(scrubbed) => setTelemetry(scrubbed)}
            />
          )}

          {currentPage === "fleet" && (
            <FleetPage
              onSelectAircraft={(uavId) => {
                setCurrentPage("operation");
              }}
            />
          )}

          {currentPage === "settings" && <SettingsPage />}
        </main>
      </div>
      
      {/* ================= ONBOARD LOCAL OLLAMA AI COPILOT DRAWER ================= */}
      <AICopilotDrawer
        isOpen={isAICopilotOpen}
        onClose={() => {
          setIsAICopilotOpen(false);
          setAICopilotInitialQuery(undefined);
        }}
        telemetry={telemetry}
        selectedComponent={selectedComponent}
        initialQuery={aiCopilotInitialQuery}
      />
    </div>
  );
}
