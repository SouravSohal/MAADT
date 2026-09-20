"use client";
import React from 'react';
import { SubsystemHealth } from '../../types/telemetry';
import CircularProgress from '../common/CircularProgress';
import { Flame, Zap, Droplet, Waves, ShieldCheck } from 'lucide-react';

interface EngineHealthPanelProps {
  subsystemHealth: SubsystemHealth;
}

export default function EngineHealthPanel({ subsystemHealth }: EngineHealthPanelProps) {
  const overall = subsystemHealth.overall || 84;

  const subsystems: { name: string; val: number; icon: any; isDegraded?: boolean }[] = [
    { name: "Thermal", val: subsystemHealth.thermal || 89, icon: Flame },
    { name: "Combustion", val: subsystemHealth.combustion || 67, icon: Zap, isDegraded: (subsystemHealth.combustion || 67) < 75 },
    { name: "Lubrication", val: subsystemHealth.lubrication || 94, icon: Droplet },
    { name: "Vibration", val: subsystemHealth.vibration || 81, icon: Waves },
    { name: "Electrical", val: subsystemHealth.electrical || 97, icon: ShieldCheck },
  ];

  return (
    <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4 font-mono select-none flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider">
            HEALTH DECOMPOSITION
          </span>
          <h3 className="text-xs font-bold text-[#F4F7FA]">Engine Health Index</h3>
        </div>
        <span className="text-[10px] font-bold text-[#22AFFF]">
          Conf: {Math.round((subsystemHealth.confidence || 0.96) * 100)}%
        </span>
      </div>

      {/* Main Layout: Circular Overall on Left + Subsystems on Right */}
      <div className="flex items-center gap-4 my-auto">
        {/* Large Circular Indicator */}
        <div className="p-3 bg-[#0B1725] border border-[#1B344B] rounded-xl shrink-0 flex flex-col items-center">
          <CircularProgress
            value={overall}
            size={88}
            strokeWidth={8}
            sublabel="Overall"
          />
        </div>

        {/* Subsystems List */}
        <div className="flex-1 space-y-2">
          {subsystems.map((sub) => {
            const Icon = sub.icon;
            const barColor =
              sub.val >= 85
                ? "#22D88A"
                : sub.val >= 70
                ? "#F4B942"
                : "#FF4D4D";

            return (
              <div
                key={sub.name}
                className={`p-1.5 rounded transition-all ${
                  sub.isDegraded
                    ? "bg-[#2D1606]/80 border border-[#7C2D12] shadow-[0_0_8px_rgba(255,138,61,0.15)]"
                    : ""
                }`}
              >
                <div className="flex justify-between items-center text-[11px] mb-0.5">
                  <span className="flex items-center gap-1.5 text-[#8FA4B8]">
                    <Icon className={`w-3.5 h-3.5 ${sub.isDegraded ? 'text-[#FF8A3D]' : 'text-[#8FA4B8]'}`} />
                    <span className={sub.isDegraded ? 'text-[#FF8A3D] font-bold' : ''}>{sub.name}</span>
                  </span>
                  <span
                    className={`font-bold ${
                      sub.isDegraded ? 'text-[#FF8A3D]' : sub.val >= 85 ? 'text-[#22D88A]' : 'text-[#F4B942]'
                    }`}
                  >
                    {Math.round(sub.val)}%
                  </span>
                </div>

                <div className="w-full bg-[#07111D] rounded-full h-1.5 overflow-hidden border border-[#1B344B]/40">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(100, Math.max(0, sub.val))}%`,
                      backgroundColor: barColor,
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex justify-between items-center text-[10px] text-[#60758A] mt-2 pt-1.5 border-t border-[#1B344B]/60">
        <span>Limiting Subsystem: <strong className="text-[#FF8A3D]">Combustion Chamber</strong></span>
        <span>EKF Multi-Tier Observer</span>
      </div>
    </div>
  );
}
