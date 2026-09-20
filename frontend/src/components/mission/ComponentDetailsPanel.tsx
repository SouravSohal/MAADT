"use client";
import React from 'react';
import { X, AlertTriangle, CheckCircle2, ChevronRight, Activity, Thermometer, Flame, Waves, BrainCircuit } from 'lucide-react';
import { ComponentDetails } from '../../types/engine';
import StatusBadge from '../common/StatusBadge';

interface ComponentDetailsPanelProps {
  component: ComponentDetails;
  onClose: () => void;
  onViewMore: () => void;
  onAskAI?: (query: string) => void;
}

export default function ComponentDetailsPanel({
  component,
  onClose,
  onViewMore,
  onAskAI,
}: ComponentDetailsPanelProps) {
  const isAbnormal = component.status === "Abnormal" || component.status === "Critical";

  return (
    <div className="w-72 xl:w-80 bg-[#0D1B2A] border border-[#1B344B] rounded-xl flex flex-col overflow-hidden font-mono select-none shrink-0 h-full shadow-lg">
      {/* Pinned Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-[#1B344B] bg-[#0B1725] shrink-0">
        <div className="min-w-0 pr-2">
          <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider block">
            COMPONENT DETAILS
          </span>
          <h3 className="text-xs font-bold text-[#F4F7FA] truncate mt-0.5">{component.name}</h3>
        </div>
        <button
          onClick={onClose}
          title="Reset Selection"
          className="p-1 hover:bg-[#101F30] rounded text-[#8FA4B8] hover:text-[#F4F7FA] transition-colors cursor-pointer shrink-0"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Scrollable Content Body */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-2.5">
        {/* Component Core Metrics Grid */}
        <div className="grid grid-cols-2 gap-1.5">
          <div className="p-2 bg-[#0B1725] border border-[#1B344B] rounded-lg">
            <span className="text-[9px] uppercase tracking-wider text-[#8FA4B8] block">HEALTH</span>
            <span
              className={`text-base font-bold font-mono ${
                component.health >= 85
                  ? 'text-[#22D88A]'
                  : component.health >= 70
                  ? 'text-[#F4B942]'
                  : 'text-[#FF4D4D]'
              }`}
            >
              {component.health}%
            </span>
          </div>

          <div className="p-2 bg-[#0B1725] border border-[#1B344B] rounded-lg flex flex-col justify-between">
            <span className="text-[9px] uppercase tracking-wider text-[#8FA4B8] block">STATUS</span>
            <div className="mt-0.5">
              <StatusBadge status={component.status} size="sm" />
            </div>
          </div>

          {component.cht !== undefined && (
            <div className="p-2 bg-[#0B1725] border border-[#1B344B] rounded-lg">
              <span className="text-[9px] text-[#8FA4B8] flex items-center gap-1">
                <Thermometer className="w-3 h-3 text-[#FF8A3D]" />
                CHT
              </span>
              <span className="text-sm font-bold text-[#F4F7FA] mt-0.5 block">{component.cht} °C</span>
            </div>
          )}

          {component.egt !== undefined && (
            <div className="p-2 bg-[#0B1725] border border-[#1B344B] rounded-lg">
              <span className="text-[9px] text-[#8FA4B8] flex items-center gap-1">
                <Flame className="w-3 h-3 text-[#FF4D4D]" />
                EGT
              </span>
              <span className="text-sm font-bold text-[#F4F7FA] mt-0.5 block">{component.egt} °C</span>
            </div>
          )}

          {component.vibration !== undefined && (
            <div className="p-2 bg-[#0B1725] border border-[#1B344B] rounded-lg col-span-2">
              <span className="text-[9px] text-[#8FA4B8] flex items-center gap-1">
                <Waves className="w-3 h-3 text-[#22AFFF]" />
                VIBRATION
              </span>
              <span className="text-sm font-bold text-[#F4F7FA] mt-0.5 block">{component.vibration} g (RMS)</span>
            </div>
          )}
        </div>

        {/* Subsystem Status Box */}
        <div
          className={`p-2.5 rounded-lg border text-xs ${
            isAbnormal
              ? "bg-[#2D1606]/90 border-[#7C2D12] text-[#FF8A3D]"
              : "bg-[#072418]/90 border-[#14532D] text-[#22D88A]"
          }`}
        >
          <div className="flex items-center justify-between font-bold mb-1">
            <span className="text-[11px]">{component.subsystem} Status</span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-black/30">
              {component.status}
            </span>
          </div>
          <p className="text-[10px] text-[#F4F7FA]/80 leading-relaxed">
            {isAbnormal
              ? "Combustion anomaly detected. Residual divergence exceeds nominal envelope."
              : "Operating nominally within baseline thermodynamic envelopes."}
          </p>
        </div>

        {/* Diagnostic & Evidence Section */}
        {component.diagnostic && (
          <div className="p-2.5 bg-[#0B1725] border border-[#1B344B] rounded-lg space-y-1.5">
            <div className="flex items-center justify-between text-[9px] uppercase font-bold text-[#8FA4B8]">
              <span>DIAGNOSTIC OBSERVER</span>
              <span className="text-[#22AFFF] font-bold">
                P: {Math.round(component.diagnostic.probability * 100)}%
              </span>
            </div>
            <div className="text-xs font-bold text-[#F4F7FA]">
              {component.diagnostic.issue}
            </div>

            <div className="text-[9px] text-[#8FA4B8] uppercase font-bold pt-1 border-t border-[#1B344B]/60">
              PHYSICAL EVIDENCE
            </div>
            <ul className="space-y-1 text-[10px] text-[#8FA4B8]">
              {component.diagnostic.evidence.map((ev, i) => (
                <li key={i} className="flex items-start gap-1.5 text-[#F4F7FA]/90">
                  <span className="text-[#22AFFF] shrink-0 font-bold">&bull;</span>
                  <span className="leading-tight">{ev}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Pinned Action Button Footer */}
      <div className="p-2.5 border-t border-[#1B344B] bg-[#0B1725] shrink-0 space-y-1.5">
        {onAskAI && (
          <button
            onClick={() =>
              onAskAI(
                `Perform deep propulsion AI analysis on ${component.name}. Health: ${component.health}%, Status: ${component.status}${
                  component.cht ? `, CHT: ${component.cht}°C` : ''
                }${component.egt ? `, EGT: ${component.egt}°C` : ''}. What is the root cause and mechanical risk?`
              )
            }
            className="w-full py-1.5 bg-[#102E4A] hover:bg-[#153B5E] text-[#22AFFF] border border-[#22AFFF]/50 rounded-lg text-xs font-bold font-mono flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-[0_0_8px_rgba(34,175,255,0.2)]"
          >
            <BrainCircuit className="w-3.5 h-3.5 text-[#22AFFF]" />
            <span>AI Diagnostics</span>
          </button>
        )}

        <button
          onClick={onViewMore}
          className="w-full py-1.5 bg-[#101F30] hover:bg-[#1B344B] text-[#8FA4B8] hover:text-[#F4F7FA] border border-[#1B344B] rounded-lg text-xs font-bold font-mono flex items-center justify-center gap-1.5 transition-all cursor-pointer"
        >
          <span>View In Engineering</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
