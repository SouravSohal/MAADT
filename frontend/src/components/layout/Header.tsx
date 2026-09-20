"use client";
import React from 'react';
import { Plane, Play, Pause, RotateCcw, User, Shield, Radio, Cpu, BrainCircuit, ChevronLeft, ChevronRight, CheckCircle2 } from 'lucide-react';
import CircularProgress from '../common/CircularProgress';

interface HeaderProps {
  twinConfidence: number;
  telemetryHz?: number;
  isConnected?: boolean;
  isDemoRunning: boolean;
  demoStepIndex?: number;
  totalDemoSteps?: number;
  demoStepLabel?: string;
  onToggleDemo: () => void;
  onResetDemo: () => void;
  onNextDemoStep?: () => void;
  onPrevDemoStep?: () => void;
  onToggleAICopilot?: () => void;
}

export default function Header({
  twinConfidence,
  telemetryHz = 2,
  isConnected = true,
  isDemoRunning,
  demoStepIndex = 0,
  totalDemoSteps = 8,
  demoStepLabel = "Healthy Baseline",
  onToggleDemo,
  onResetDemo,
  onNextDemoStep,
  onPrevDemoStep,
  onToggleAICopilot,
}: HeaderProps) {
  return (
    <header className="h-20 bg-[#0D1B2A] border-b border-[#1B344B] px-6 flex items-center justify-between select-none z-20 shrink-0">
      {/* Left Branding & Live Status */}
      <div className="flex items-center gap-5">
        {/* MAADT Mark */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-[#101F30] border border-[#1B344B] flex items-center justify-center text-[#22AFFF] shadow-sm">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-black tracking-wider font-mono text-[#F4F7FA]">MAADT</span>
              <span className="text-xs font-semibold text-[#8FA4B8] tracking-wide hidden sm:inline">
                Mission-Aware Aero-Engine Digital Twin
              </span>
            </div>
            <p className="text-[11px] font-mono text-[#60758A] tracking-wider">
              Fly Safer. Fly Longer.
            </p>
          </div>
        </div>

        {/* Separator */}
        <div className="h-8 w-px bg-[#1B344B] hidden md:block" />

        {/* UAV Identifier & Live Pill */}
        <div className="hidden md:flex items-center gap-3 font-mono">
          <div className="px-2.5 py-1 bg-[#101F30] border border-[#1B344B] rounded text-xs font-bold text-[#F4F7FA]">
            UAV-001 (TAPAS)
          </div>

          {isConnected ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#072418] border border-[#14532D] rounded text-xs font-bold text-[#22D88A]" title="Connected to Backend WebSocket at ws://localhost:8000/ws/telemetry">
              <span className="w-2 h-2 rounded-full bg-[#22D88A] animate-pulse inline-block" />
              <span>WS CONNECTED</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#2D1606] border border-[#7C2D12] rounded text-xs font-bold text-[#FF8A3D]" title="Backend disconnected; streaming deterministic simulation telemetry">
              <span className="w-2 h-2 rounded-full bg-[#FF8A3D] inline-block" />
              <span>STANDALONE</span>
            </div>
          )}

          <div className="text-xs text-[#8FA4B8] flex items-center gap-1">
            <Radio className="w-3.5 h-3.5 text-[#22AFFF]" />
            <span>Telemetry: {telemetryHz} Hz</span>
          </div>
        </div>

        {/* Separator */}
        <div className="h-8 w-px bg-[#1B344B] hidden lg:block" />

        {/* Twin Confidence Circular Indicator */}
        <div className="hidden lg:flex items-center gap-2.5 font-mono">
          <CircularProgress
            value={twinConfidence}
            size={40}
            strokeWidth={4}
            color="#22AFFF"
          />
          <div className="text-left">
            <div className="text-[10px] uppercase font-bold text-[#8FA4B8]">Twin Confidence</div>
            <div className="text-xs font-bold text-[#F4F7FA]">{Math.round(twinConfidence)}%</div>
          </div>
        </div>
      </div>

      {/* Right Controls: Mission Demo Walkthrough & AI Copilot */}
      <div className="flex items-center gap-3 font-mono">
        {/* Full Mission Scenario Walkthrough Controller (Optimized for Video Recording) */}
        <div className="flex items-center gap-1.5 bg-[#0B1725] border border-[#1B344B] p-1 rounded-lg">
          {isDemoRunning ? (
            <>
              {/* Prev Step */}
              <button
                onClick={onPrevDemoStep}
                title="Previous Demo Stage"
                className="p-1.5 hover:bg-[#101F30] text-[#8FA4B8] hover:text-[#F4F7FA] rounded transition-colors cursor-pointer"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>

              {/* Stage Badge & Label */}
              <div className="px-2 py-0.5 flex items-center gap-2 text-xs">
                <span className="text-[10px] px-1.5 py-0.5 bg-[#FF8A3D]/20 text-[#FF8A3D] rounded font-bold">
                  STAGE {demoStepIndex + 1}/{totalDemoSteps}
                </span>
                <span className="font-bold text-[#F4F7FA] max-w-[150px] sm:max-w-[200px] truncate text-[11px]">
                  {demoStepLabel}
                </span>
              </div>

              {/* Next Step */}
              <button
                onClick={onNextDemoStep}
                title="Next Demo Stage"
                className="p-1.5 hover:bg-[#101F30] text-[#8FA4B8] hover:text-[#F4F7FA] rounded transition-colors cursor-pointer"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>

              {/* Pause / Resume */}
              <button
                onClick={onToggleDemo}
                title="Pause/Play Auto-Advance"
                className="px-2 py-1 bg-[#102E4A] hover:bg-[#163D63] text-[#22AFFF] rounded text-[10px] font-bold flex items-center gap-1 transition-all cursor-pointer"
              >
                <Pause className="w-3 h-3" />
                <span>PAUSE</span>
              </button>

              {/* Reset */}
              <button
                onClick={onResetDemo}
                title="Reset Scenario to Cruise Baseline"
                className="p-1.5 bg-[#101F30] hover:bg-[#1B344B] text-[#8FA4B8] hover:text-[#FF4D4D] rounded transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </>
          ) : (
            <button
              onClick={onToggleDemo}
              title="Launch 8-Stage DRDO Mission Simulation Demo for Video Recording"
              className="px-3 py-1.5 rounded font-mono text-xs font-bold flex items-center gap-2 bg-[#101F30] hover:bg-[#102E4A] text-[#22AFFF] border border-[#1B344B] hover:border-[#22AFFF]/50 transition-all cursor-pointer shadow-sm"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>RUN MISSION DEMO (8 STAGES)</span>
            </button>
          )}
        </div>

        {/* AI Copilot Trigger Button */}
        <button
          onClick={onToggleAICopilot}
          title="Open Local Ollama AI Propulsion Copilot (qwen2.5:3b)"
          className="px-3 py-1.5 rounded font-mono text-xs font-bold flex items-center gap-2 bg-[#102E4A] hover:bg-[#153B5E] text-[#22AFFF] border border-[#22AFFF]/50 shadow-[0_0_12px_rgba(34,175,255,0.25)] transition-all cursor-pointer"
        >
          <BrainCircuit className="w-4 h-4 text-[#22AFFF]" />
          <span>AI COPILOT</span>
        </button>

        {/* Separator */}
        <div className="h-8 w-px bg-[#1B344B] hidden sm:block" />

        {/* Defence / Research Rig Identity Badge */}
        <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 bg-[#101F30] border border-[#1B344B] rounded text-right">
          <Shield className="w-4 h-4 text-[#8FA4B8]" />
          <div className="text-left">
            <div className="text-[9px] uppercase font-mono tracking-widest text-[#60758A]">EVALUATION RIG</div>
            <div className="text-[11px] font-mono font-bold text-[#8FA4B8]">DRDO / GCS WORKSTATION</div>
          </div>
        </div>

        {/* Workstation Operator Profile */}
        <div className="flex items-center gap-2.5 pl-1">
          <div className="w-9 h-9 rounded-full bg-[#101F30] border border-[#1B344B] flex items-center justify-center text-[#8FA4B8]">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    </header>
  );
}
