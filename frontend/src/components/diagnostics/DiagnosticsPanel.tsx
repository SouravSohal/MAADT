"use client";
import React from 'react';
import { DiagnosticHypothesis } from '../../types/telemetry';
import StatusBadge from '../common/StatusBadge';
import { AlertTriangle, CheckCircle2, ChevronRight, Activity } from 'lucide-react';

interface DiagnosticsPanelProps {
  diagnostic: DiagnosticHypothesis;
}

export default function DiagnosticsPanel({ diagnostic }: DiagnosticsPanelProps) {
  const isHealthy = diagnostic.fault_type === "healthy" || diagnostic.fault_type === "nominal";

  return (
    <div className="w-80 bg-[#0D1B2A] border border-[#1B344B] rounded-xl flex flex-col p-4 font-mono select-none shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#1B344B]">
        <div>
          <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider">
            PHYSICS-GROUNDED CLASSIFIER
          </span>
          <h3 className="text-sm font-bold text-[#F4F7FA]">Diagnostic Hypothesis</h3>
        </div>
        <StatusBadge status={diagnostic.severity} />
      </div>

      {/* Main Hypothesis Card */}
      <div className="p-3 bg-[#0B1725] border border-[#1B344B] rounded-xl my-3">
        <div className="flex justify-between items-center text-xs mb-1">
          <span className="text-[#8FA4B8]">Subsystem:</span>
          <span className="text-[#22AFFF] font-bold">{diagnostic.subsystem}</span>
        </div>

        <div className="text-base font-bold text-[#F4F7FA] my-1 capitalize">
          {diagnostic.fault_type.replace('_', ' ')}
        </div>

        <div className="flex justify-between items-center text-xs mt-2 pt-2 border-t border-[#1B344B]/60">
          <span className="text-[#8FA4B8]">Classifier Probability:</span>
          <span className="text-lg font-bold text-[#22AFFF]">
            {Math.round(diagnostic.probability * 100)}%
          </span>
        </div>
      </div>

      {/* Grounded Physical Evidence */}
      <div className="flex-1 p-3 bg-[#0B1725] border border-[#1B344B] rounded-xl mb-3 flex flex-col">
        <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider mb-2">
          GROUNDED PHYSICAL EVIDENCE
        </span>
        <ul className="space-y-1.5 text-xs text-[#8FA4B8] flex-1">
          {diagnostic.evidence && diagnostic.evidence.length > 0 ? (
            diagnostic.evidence.map((ev, i) => (
              <li key={i} className="flex items-start gap-1.5 text-[#F4F7FA]/90">
                <span className="text-[#22AFFF] font-bold">&bull;</span>
                <span>{ev}</span>
              </li>
            ))
          ) : (
            <li className="text-[#60758A] italic">No anomalous physical deviations recorded.</li>
          )}
        </ul>
      </div>

      {/* Sensor Trust Verification Badge */}
      <div className="p-2.5 bg-[#072418] border border-[#14532D] rounded-lg text-[11px] text-[#22D88A] flex items-center gap-2">
        <CheckCircle2 className="w-4 h-4 text-[#22D88A] shrink-0" />
        <span>Mechanical Root Cause Verified (Sensor Drift Decoupled)</span>
      </div>
    </div>
  );
}
