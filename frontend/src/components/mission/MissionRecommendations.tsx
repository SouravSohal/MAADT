"use client";
import React, { useState } from 'react';
import { ShieldCheck, ArrowDownRight, Compass, ShieldAlert, CheckCircle2, Zap, ArrowRight, RotateCcw } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';

interface RecommendationItem {
  id: string;
  title: string;
  desc: string;
  margin: number;
  status: string;
  badge: string;
  deltaCht: string;
  deltaEgt: string;
  enduranceImpact: string;
  risk: "Low" | "Nominal" | "High" | "None";
}

interface MissionRecommendationsProps {
  currentMargin: number;
  activeDirective?: string;
  onApplyDirective: (actionId: string) => void;
  onOpenWhatIf?: () => void;
}

export default function MissionRecommendations({
  currentMargin,
  activeDirective = "none",
  onApplyDirective,
  onOpenWhatIf,
}: MissionRecommendationsProps) {
  const [selectedAction, setSelectedAction] = useState<string>("throttle_down");

  const recommendations: RecommendationItem[] = [
    {
      id: "continue",
      title: "Continue Mission",
      desc: "Maintain nominal cruise at 65% throttle. Continued exposure if anomaly persists.",
      margin: Math.round(currentMargin),
      status: currentMargin >= 75 ? "SAFE" : "MARGINAL",
      badge: "Current Plan",
      deltaCht: "0 °C",
      deltaEgt: "0 °C",
      enduranceImpact: "3.4h remaining",
      risk: currentMargin < 65 ? "High" : "Nominal",
    },
    {
      id: "throttle_down",
      title: "Derate Throttle (-15%)",
      desc: "Derate to 50% power (2260 RPM). Relieves cylinder combustion thermal flux.",
      margin: 84,
      status: "SAFE",
      badge: "Recommended",
      deltaCht: "-19 °C",
      deltaEgt: "-44 °C",
      enduranceImpact: "+2.8h (6.2h total)",
      risk: "Low",
    },
    {
      id: "step_down",
      title: "Descent (-2000 ft)",
      desc: "Descend to 4,900m into denser air for increased ram-air cooling mass flow.",
      margin: 81,
      status: "SAFE",
      badge: "Alternative",
      deltaCht: "-16 °C",
      deltaEgt: "-28 °C",
      enduranceImpact: "+2.2h (5.6h total)",
      risk: "Low",
    },
    {
      id: "rtb",
      title: "Return to Base (RTB)",
      desc: "Vector to recovery base airfield at minimum drag glide (Heading 245°).",
      margin: 96,
      status: "SAFE",
      badge: "Safest Option",
      deltaCht: "-28 °C",
      deltaEgt: "-62 °C",
      enduranceImpact: "26m to touchdown",
      risk: "None",
    },
  ];

  const currentRec = recommendations.find((r) => r.id === selectedAction) || recommendations[1];
  const isSelectedActive = activeDirective === selectedAction;

  return (
    <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-3.5 font-mono select-none flex flex-col justify-between h-full shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider">
            TACTICAL ADVISORY
          </span>
          <h3 className="text-xs font-bold text-[#F4F7FA]">Operator Decision Center</h3>
        </div>
        {onOpenWhatIf && (
          <button
            onClick={onOpenWhatIf}
            className="text-[10px] text-[#22AFFF] hover:text-[#60C5FF] flex items-center gap-1 transition-colors cursor-pointer"
          >
            <span>What-If Matrix</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* 4 Action Cards Grid */}
      <div className="grid grid-cols-2 gap-2 my-1">
        {recommendations.map((rec) => {
          const isSelected = selectedAction === rec.id;
          const isApplied = activeDirective === rec.id;

          return (
            <div
              key={rec.id}
              onClick={() => setSelectedAction(rec.id)}
              className={`p-2 rounded-lg border transition-all cursor-pointer flex flex-col justify-between ${
                isApplied
                  ? "bg-[#072418] border-[#22D88A] shadow-[0_0_8px_rgba(34,216,138,0.25)]"
                  : isSelected
                  ? "bg-[#102E4A] border-[#22AFFF] shadow-[0_0_8px_rgba(34,175,255,0.2)]"
                  : rec.badge === "Recommended"
                  ? "bg-[#0E2034] border-[#1E3E5E] hover:border-[#22AFFF]/40"
                  : "bg-[#0B1725] border-[#1B344B] hover:border-[#22AFFF]/30 hover:bg-[#101F30]"
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1">
                  <span className="text-[11px] font-bold text-[#F4F7FA] leading-tight truncate">
                    {rec.title}
                  </span>
                  {isApplied ? (
                    <span className="text-[9px] px-1 py-0.2 bg-[#22D88A]/20 text-[#22D88A] rounded font-bold shrink-0 flex items-center gap-0.5">
                      <CheckCircle2 className="w-2.5 h-2.5" /> ACTIVE
                    </span>
                  ) : (
                    <span className="text-[9px] px-1 py-0.2 bg-[#1B344B] text-[#22AFFF] rounded font-mono shrink-0">
                      {rec.badge}
                    </span>
                  )}
                </div>
                <p className="text-[9.5px] text-[#8FA4B8] leading-snug line-clamp-2">
                  {rec.desc}
                </p>
              </div>

              <div className="flex items-center justify-between pt-1.5 mt-1 border-t border-[#1B344B]/40 text-[9.5px]">
                <span className="text-[#8FA4B8]">Survival Margin:</span>
                <span className={`font-bold ${rec.margin >= 80 ? 'text-[#22D88A]' : 'text-[#22AFFF]'}`}>
                  {rec.margin}%
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Recommendation Impact & Action Tray */}
      <div className="bg-[#0B1725] border border-[#1B344B] rounded-lg p-2.5 mt-1">
        <div className="flex items-center justify-between text-[10px] mb-1.5">
          <span className="text-[#8FA4B8]">Selected: <strong className="text-[#F4F7FA]">{currentRec.title}</strong></span>
          <div className="flex items-center gap-2">
            <span className="text-[#8FA4B8]">Impact:</span>
            <span className="text-[#22D88A] font-bold">{currentRec.deltaCht} CHT</span>
            <span className="text-[#22AFFF] font-bold">{currentRec.enduranceImpact}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isSelectedActive ? (
            <button
              onClick={() => onApplyDirective("continue")}
              className="flex-1 py-1.5 bg-[#072418] hover:bg-[#0E3523] text-[#22D88A] border border-[#22D88A]/60 rounded-md text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-[#22D88A]" />
              <span>DIRECTIVE CURRENTLY ACTIVE (CLICK TO REVERT)</span>
            </button>
          ) : (
            <button
              onClick={() => onApplyDirective(currentRec.id)}
              className="flex-1 py-1.5 bg-[#102E4A] hover:bg-[#163D63] text-[#22AFFF] hover:text-[#F4F7FA] border border-[#22AFFF]/60 rounded-md text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-[0_0_8px_rgba(34,175,255,0.2)]"
            >
              <Zap className="w-3.5 h-3.5 text-[#22AFFF]" />
              <span>EXECUTE TACTICAL DIRECTIVE</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
