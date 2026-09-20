"use client";
import React, { useState } from 'react';
import { X, AlertOctagon, CheckSquare, Square, ShieldAlert, Zap, ArrowRight, Activity, Thermometer, Flame } from 'lucide-react';
import { TelemetryPacket } from '../../types/telemetry';

interface EmergencyChecklistModalProps {
  isOpen: boolean;
  onClose: () => void;
  telemetry: TelemetryPacket;
  onApplyDirective: (actionId: string) => void;
  onNavigateToEngineering: () => void;
}

export default function EmergencyChecklistModal({
  isOpen,
  onClose,
  telemetry,
  onApplyDirective,
  onNavigateToEngineering,
}: EmergencyChecklistModalProps) {
  if (!isOpen) return null;

  const [checkedItems, setCheckedItems] = useState<Record<number, boolean>>({
    0: true,
    1: true,
    2: false,
    3: false,
    4: false,
  });

  const toggleCheck = (idx: number) => {
    setCheckedItems((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const checklist = [
    {
      title: "Confirm Cylinder 3 Thermal Ceiling",
      desc: `Verify CHT does not exceed 200 °C threshold (Current: ${Math.round(telemetry.cht + 23)} °C).`,
    },
    {
      title: "Cross-Reference Fuel-Air Stoichiometry",
      desc: `Check fuel flow residual (+${(telemetry.residuals?.fuel_flow_residual || 1.8).toFixed(1)} L/h vs theoretical model).`,
    },
    {
      title: "Inspect Multi-Harmonic Rotational Vibration",
      desc: `Assess crankcase vibration levels (${telemetry.vibration.toFixed(2)} g RMS).`,
    },
    {
      title: "Execute Tactical Derate or Altitude Descent",
      desc: "Apply recommended power reduction (-15%) to relieve thermal combustion flux.",
    },
    {
      title: "Log Sortie Directive & Notify GCS Commander",
      desc: "Record autonomous advisory dispatch in DRDO flight log registry.",
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 select-none font-mono">
      <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#1B344B] bg-[#0B1725]">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-[#2D1606] text-[#FF8A3D] rounded border border-[#7C2D12]">
              <AlertOctagon className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#F4F7FA]">
                OPERATOR EMERGENCY CHECKLIST &bull; PROPULSION ADVISORY
              </h3>
              <p className="text-[11px] text-[#8FA4B8]">
                DRDO TAPAS-BH-201 MALE UAV &bull; In-Flight Fault Response Procedure §53-C
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[#8FA4B8] hover:text-[#F4F7FA] hover:bg-[#101F30] rounded transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 overflow-y-auto">
          {/* Active Anomaly Diagnostic Banner */}
          <div className="p-3.5 rounded-lg bg-[#2D1606]/80 border border-[#7C2D12] flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-[#FF8A3D] shrink-0 mt-0.5" />
            <div className="flex-1 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#FF8A3D] uppercase">
                  CONFIRMED: CYLINDER 3 INJECTOR ABNORMALITY
                </span>
                <span className="text-[10px] px-2 py-0.5 bg-[#FF8A3D]/20 text-[#FF8A3D] rounded font-bold">
                  PROBABILITY: 87%
                </span>
              </div>
              <p className="text-[#F4F7FA]/80 mt-1 leading-relaxed text-[11px]">
                Physics residuals indicate localized fuel starvation and abnormal combustion temperature divergence (+58 °C EGT above expected baseline). Mechanical vibration harmonic elevated.
              </p>
            </div>
          </div>

          {/* Real-time Telemetry Snapshot */}
          <div className="grid grid-cols-4 gap-2 text-xs">
            <div className="p-2.5 bg-[#0B1725] border border-[#1B344B] rounded-lg">
              <span className="text-[10px] text-[#8FA4B8] block">CYL 3 CHT</span>
              <span className="text-base font-bold text-[#FF4D4D]">{Math.round(telemetry.cht + 23)} °C</span>
            </div>
            <div className="p-2.5 bg-[#0B1725] border border-[#1B344B] rounded-lg">
              <span className="text-[10px] text-[#8FA4B8] block">EGT RESIDUAL</span>
              <span className="text-base font-bold text-[#FF8A3D]">+{Math.round(telemetry.residuals?.egt_residual || 58)} °C</span>
            </div>
            <div className="p-2.5 bg-[#0B1725] border border-[#1B344B] rounded-lg">
              <span className="text-[10px] text-[#8FA4B8] block">VIBRATION</span>
              <span className="text-base font-bold text-[#F4B942]">{telemetry.vibration.toFixed(2)} g</span>
            </div>
            <div className="p-2.5 bg-[#0B1725] border border-[#1B344B] rounded-lg">
              <span className="text-[10px] text-[#8FA4B8] block">MISSION MARGIN</span>
              <span className="text-base font-bold text-[#22AFFF]">{Math.round(telemetry.mission_margin)}%</span>
            </div>
          </div>

          {/* Interactive Checklist Items */}
          <div>
            <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider block mb-2">
              MANDATORY OPERATOR ACTION CHECKLIST
            </span>
            <div className="space-y-2">
              {checklist.map((item, idx) => {
                const isChecked = !!checkedItems[idx];
                return (
                  <div
                    key={idx}
                    onClick={() => toggleCheck(idx)}
                    className={`p-3 rounded-lg border flex items-start gap-3 transition-all cursor-pointer ${
                      isChecked
                        ? "bg-[#072418]/60 border-[#14532D]"
                        : "bg-[#0B1725] border-[#1B344B] hover:border-[#22AFFF]/40"
                    }`}
                  >
                    <div className="mt-0.5 text-[#22AFFF]">
                      {isChecked ? (
                        <CheckSquare className="w-4 h-4 text-[#22D88A]" />
                      ) : (
                        <Square className="w-4 h-4 text-[#60758A]" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className={`text-xs font-bold ${isChecked ? "text-[#22D88A] line-through" : "text-[#F4F7FA]"}`}>
                        {item.title}
                      </div>
                      <p className="text-[11px] text-[#8FA4B8] mt-0.5 leading-snug">
                        {item.desc}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Modal Footer Controls */}
        <div className="p-4 border-t border-[#1B344B] bg-[#0B1725] flex flex-wrap items-center justify-between gap-3">
          <button
            onClick={() => {
              onClose();
              onNavigateToEngineering();
            }}
            className="px-3 py-2 bg-[#101F30] hover:bg-[#1B344B] text-[#8FA4B8] hover:text-[#F4F7FA] border border-[#1B344B] rounded-lg text-xs font-bold transition-all cursor-pointer"
          >
            Open Engineering Suite
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                onApplyDirective("rtb");
                onClose();
              }}
              className="px-3.5 py-2 bg-[#2D1606] hover:bg-[#45220A] text-[#FF8A3D] border border-[#7C2D12] rounded-lg text-xs font-bold transition-all cursor-pointer"
            >
              Engage RTB Vector
            </button>
            <button
              onClick={() => {
                onApplyDirective("throttle_down");
                onClose();
              }}
              className="px-4 py-2 bg-[#102E4A] hover:bg-[#163D63] text-[#22AFFF] hover:text-[#F4F7FA] border border-[#22AFFF]/60 rounded-lg text-xs font-bold transition-all cursor-pointer shadow-[0_0_10px_rgba(34,175,255,0.3)] flex items-center gap-1.5"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Apply Derate (-15%)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
