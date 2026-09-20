"use client";
import React from 'react';
import { AnomalyScoreDetails } from '../../types/telemetry';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

interface AnomalyBreakdownProps {
  details: AnomalyScoreDetails;
}

export default function AnomalyBreakdown({ details }: AnomalyBreakdownProps) {
  const scores = [
    { label: "Composite Score", val: details.composite_score || 0.04, isComposite: true },
    { label: "Physics Residual", val: details.physics_score || 0.02 },
    { label: "Statistical Z-Score", val: details.statistical_score || 0.03 },
    { label: "Machine Learning (IF)", val: details.ml_score || 0.04 },
    { label: "Temporal Trajectory", val: details.trend_score || 0.01 },
  ];

  return (
    <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4 font-mono select-none flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider">
            DETECTION ENGINE
          </span>
          <h3 className="text-xs font-bold text-[#F4F7FA]">4-Tier Anomaly Decomposition</h3>
        </div>

        {/* Out of Distribution Badge */}
        <div
          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
            details.is_out_of_distribution
              ? "bg-[#2E0B0B] text-[#FF4D4D] border-[#7F1D1D]"
              : "bg-[#072418] text-[#22D88A] border-[#14532D]"
          }`}
        >
          {details.is_out_of_distribution ? "OUT OF DISTRIBUTION" : "IN-DISTRIBUTION"}
        </div>
      </div>

      {/* Horizontal Bar Breakdown */}
      <div className="space-y-2 my-auto">
        {scores.map((s) => {
          const pct = Math.min(100, Math.max(0, s.val * 100));
          const color =
            pct >= 60 ? "#FF4D4D" : pct >= 35 ? "#FF8A3D" : pct >= 15 ? "#F4B942" : "#22D88A";

          return (
            <div key={s.label}>
              <div className="flex justify-between text-[11px] text-[#8FA4B8] mb-0.5">
                <span className={s.isComposite ? "font-bold text-[#F4F7FA]" : ""}>{s.label}</span>
                <span className="font-bold text-[#F4F7FA]">
                  {s.val.toFixed(2)} ({Math.round(pct)}%)
                </span>
              </div>
              <div className="w-full bg-[#07111D] rounded-full h-1.5 overflow-hidden border border-[#1B344B]/40">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex justify-between items-center text-[10px] text-[#60758A] mt-2 pt-1.5 border-t border-[#1B344B]/60">
        <span>Lead Time Target: &ge; 12 min</span>
        <span>Hybrid Physics + CUSUM + Isolation Forest</span>
      </div>
    </div>
  );
}
