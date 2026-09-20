"use client";
import React, { useState } from 'react';
import { Sliders, ShieldCheck, AlertTriangle, ArrowRight, Zap, CheckCircle2, RotateCcw, Compass, Activity, Thermometer, Flame } from 'lucide-react';

export interface TacticalBranch {
  id: string;
  name: string;
  throttle: number;
  altitude: number;
  projectedCht: number;
  projectedEgt: number;
  projectedVibration: number;
  margin: number;
  endurance: string;
  failureRisk: string;
  badge: string;
  recommended?: boolean;
}

interface TacticalWhatIfMatrixProps {
  currentCht?: number;
  currentEgt?: number;
  currentMargin?: number;
  activeDirective?: string;
  onApplyDirective: (branchId: string) => void;
  onClose?: () => void;
}

export default function TacticalWhatIfMatrix({
  currentCht = 193,
  currentEgt = 768,
  currentMargin = 54,
  activeDirective = "none",
  onApplyDirective,
  onClose,
}: TacticalWhatIfMatrixProps) {
  const [customThrottle, setCustomThrottle] = useState<number>(55);
  const [customAlt, setCustomAlt] = useState<number>(5000);

  // 4 Pre-computed tactical branches
  const branches: TacticalBranch[] = [
    {
      id: "continue",
      name: "Branch A: Baseline Cruise",
      throttle: 65,
      altitude: 5500,
      projectedCht: Math.round(currentCht),
      projectedEgt: Math.round(currentEgt),
      projectedVibration: 0.62,
      margin: Math.round(currentMargin),
      endurance: "3.4 hrs",
      failureRisk: "High (68%)",
      badge: "Current Plan",
    },
    {
      id: "throttle_down",
      name: "Branch B: Throttle Derate (-15%)",
      throttle: 50,
      altitude: 5500,
      projectedCht: 174,
      projectedEgt: 724,
      projectedVibration: 0.34,
      margin: 84,
      endurance: "6.2 hrs (+2.8h)",
      failureRisk: "Minimal (4%)",
      badge: "AI Recommended",
      recommended: true,
    },
    {
      id: "step_down",
      name: "Branch C: Step Descent (-2000 ft)",
      throttle: 60,
      altitude: 4900,
      projectedCht: 172,
      projectedEgt: 738,
      projectedVibration: 0.48,
      margin: 81,
      endurance: "5.6 hrs (+2.2h)",
      failureRisk: "Low (8%)",
      badge: "Alternative",
    },
    {
      id: "rtb",
      name: "Branch D: Emergency RTB Vector",
      throttle: 45,
      altitude: 3800,
      projectedCht: 164,
      projectedEgt: 695,
      projectedVibration: 0.25,
      margin: 96,
      endurance: "26 min to Base",
      failureRisk: "None (<1%)",
      badge: "Asset Safety",
    },
  ];

  // Dynamic calculation for the custom parametric branch
  const customCht = Math.round(170 + (customThrottle - 50) * 1.4 - (5500 - customAlt) * 0.005);
  const customMargin = Math.max(20, Math.min(98, Math.round(85 - (customThrottle - 50) * 1.8 + (5500 - customAlt) * 0.004)));

  return (
    <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4 font-mono select-none flex flex-col justify-between shadow-xl">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between pb-3 border-b border-[#1B344B] gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-[#102E4A] text-[#22AFFF] rounded-md border border-[#22AFFF]/40">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-[#F4F7FA] uppercase tracking-wider">
                Operator Tactical What-If Decision Matrix
              </h3>
              <span className="text-[10px] px-2 py-0.5 bg-[#102E4A] text-[#22AFFF] rounded font-bold">
                Counterfactual Roll-Out Horizon: 60 min
              </span>
            </div>
            <p className="text-[11px] text-[#8FA4B8]">
              Evaluate multi-branch thermodynamic projections & command tactical directives to extend mission endurance.
            </p>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="text-xs text-[#8FA4B8] hover:text-[#F4F7FA] px-2.5 py-1 rounded bg-[#101F30] hover:bg-[#1B344B] border border-[#1B344B] transition-colors cursor-pointer"
          >
            Switch to Telemetry Trends
          </button>
        )}
      </div>

      {/* 4 Counterfactual Branches Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3 my-3">
        {branches.map((b) => {
          const isApplied = activeDirective === b.id;

          return (
            <div
              key={b.id}
              className={`p-3 rounded-xl border flex flex-col justify-between transition-all ${
                isApplied
                  ? "bg-[#072418] border-[#22D88A] shadow-[0_0_12px_rgba(34,216,138,0.3)] ring-1 ring-[#22D88A]"
                  : b.recommended
                  ? "bg-[#0E2238] border-[#22AFFF]/60 shadow-[0_0_10px_rgba(34,175,255,0.2)]"
                  : "bg-[#0B1725] border-[#1B344B] hover:border-[#1E3E5E]"
              }`}
            >
              <div>
                {/* Branch Header */}
                <div className="flex items-start justify-between gap-1 mb-2">
                  <span className="text-xs font-bold text-[#F4F7FA] leading-tight">
                    {b.name}
                  </span>
                  <span
                    className={`text-[9px] px-1.5 py-0.5 rounded font-bold shrink-0 ${
                      isApplied
                        ? "bg-[#22D88A]/20 text-[#22D88A]"
                        : b.recommended
                        ? "bg-[#22AFFF]/20 text-[#22AFFF] border border-[#22AFFF]/50"
                        : "bg-[#1B344B] text-[#8FA4B8]"
                    }`}
                  >
                    {isApplied ? "ACTIVE ORDER" : b.badge}
                  </span>
                </div>

                {/* Key Simulation Projections */}
                <div className="space-y-1.5 text-xs py-2 border-y border-[#1B344B]/60">
                  <div className="flex justify-between items-center">
                    <span className="text-[#8FA4B8] text-[11px]">Command Throttle:</span>
                    <span className="text-[#F4F7FA] font-bold">{b.throttle}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#8FA4B8] text-[11px]">Sortie Altitude:</span>
                    <span className="text-[#F4F7FA] font-bold">{b.altitude} m</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#8FA4B8] text-[11px]">Projected CHT (Cyl 3):</span>
                    <span
                      className={`font-bold ${
                        b.projectedCht >= 190
                          ? 'text-[#FF4D4D]'
                          : b.projectedCht <= 175
                          ? 'text-[#22D88A]'
                          : 'text-[#F4B942]'
                      }`}
                    >
                      {b.projectedCht} °C
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#8FA4B8] text-[11px]">Survival Margin:</span>
                    <span
                      className={`font-bold ${
                        b.margin >= 80 ? 'text-[#22D88A]' : b.margin >= 65 ? 'text-[#F4B942]' : 'text-[#FF4D4D]'
                      }`}
                    >
                      {b.margin}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#8FA4B8] text-[11px]">Endurance Remaining:</span>
                    <span className="text-[#22AFFF] font-bold">{b.endurance}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-[#8FA4B8] text-[11px]">60-Min In-Flight Risk:</span>
                    <span
                      className={`font-bold text-[10px] ${
                        b.failureRisk.includes("High")
                          ? 'text-[#FF4D4D]'
                          : b.failureRisk.includes("Minimal") || b.failureRisk.includes("None")
                          ? 'text-[#22D88A]'
                          : 'text-[#F4B942]'
                      }`}
                    >
                      {b.failureRisk}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-3">
                {isApplied ? (
                  <button
                    onClick={() => onApplyDirective("continue")}
                    className="w-full py-2 bg-[#072418] hover:bg-[#0C3822] text-[#22D88A] border border-[#22D88A]/60 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>ACTIVE (REVERT)</span>
                  </button>
                ) : (
                  <button
                    onClick={() => onApplyDirective(b.id)}
                    className={`w-full py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer border ${
                      b.recommended
                        ? "bg-[#102E4A] hover:bg-[#184670] text-[#22AFFF] hover:text-[#F4F7FA] border-[#22AFFF]/60 shadow-[0_0_10px_rgba(34,175,255,0.25)]"
                        : "bg-[#101F30] hover:bg-[#1B344B] text-[#8FA4B8] hover:text-[#F4F7FA] border-[#1B344B]"
                    }`}
                  >
                    <Zap className="w-3.5 h-3.5" />
                    <span>{b.id === "rtb" ? "ENGAGE RTB VECTOR" : "APPLY THIS DIRECTIVE"}</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom Parametric Quick-Test Slider Tray */}
      <div className="bg-[#0B1725] border border-[#1B344B] rounded-lg p-3 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#22AFFF]" />
          <span className="font-bold text-[#F4F7FA]">Quick Parameter Sweep:</span>
        </div>

        <div className="flex items-center gap-6 flex-wrap">
          {/* Throttle Slider */}
          <div className="flex items-center gap-2">
            <span className="text-[#8FA4B8]">Throttle:</span>
            <input
              type="range"
              min="35"
              max="90"
              value={customThrottle}
              onChange={(e) => setCustomThrottle(Number(e.target.value))}
              className="accent-[#22AFFF] w-28 cursor-pointer"
            />
            <span className="text-[#F4F7FA] font-bold w-9">{customThrottle}%</span>
          </div>

          {/* Altitude Slider */}
          <div className="flex items-center gap-2">
            <span className="text-[#8FA4B8]">Altitude:</span>
            <input
              type="range"
              min="2000"
              max="8000"
              step="200"
              value={customAlt}
              onChange={(e) => setCustomAlt(Number(e.target.value))}
              className="accent-[#22AFFF] w-28 cursor-pointer"
            />
            <span className="text-[#F4F7FA] font-bold w-14">{customAlt} m</span>
          </div>

          {/* Projected Result */}
          <div className="flex items-center gap-3 pl-2 border-l border-[#1B344B]">
            <span className="text-[#8FA4B8]">Projected CHT:</span>
            <span className="font-bold text-[#22D88A]">{customCht} °C</span>
            <span className="text-[#8FA4B8]">Margin:</span>
            <span className="font-bold text-[#22AFFF]">{customMargin}%</span>
          </div>
        </div>

        <button
          onClick={() => onApplyDirective("throttle_down")}
          className="px-3 py-1.5 bg-[#102E4A] hover:bg-[#163D63] text-[#22AFFF] border border-[#22AFFF]/50 rounded text-xs font-bold transition-all cursor-pointer"
        >
          Execute Tuned Directive
        </button>
      </div>
    </div>
  );
}
