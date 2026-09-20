"use client";
import React from 'react';
import StatusBadge, { StatusType } from '../common/StatusBadge';

interface TelemetryCardProps {
  icon: any;
  label: string;
  value: number | string;
  unit: string;
  status: StatusType;
  history?: number[];
  onClick?: () => void;
}

export default function TelemetryCard({
  icon: Icon,
  label,
  value,
  unit,
  status,
  history = [20, 22, 21, 23, 22, 24, 25, 24, 26, 25],
  onClick,
}: TelemetryCardProps) {
  // Build minimal SVG sparkline
  const min = Math.min(...history);
  const max = Math.max(...history);
  const range = max - min || 1;
  const points = history
    .map((val, idx) => {
      const x = (idx / (history.length - 1)) * 56 + 2;
      const y = 18 - ((val - min) / range) * 14;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  const strokeColor =
    status === "CRITICAL"
      ? "#FF4D4D"
      : status === "WARNING"
      ? "#FF8A3D"
      : status === "ADVISORY"
      ? "#F4B942"
      : "#22D88A";

  return (
    <div
      onClick={onClick}
      className={`bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-3 flex flex-col justify-between select-none font-mono min-w-[130px] transition-all ${
        onClick ? "cursor-pointer hover:border-[#22AFFF]/60 hover:bg-[#102235] hover:shadow-[0_0_10px_rgba(34,175,255,0.15)]" : ""
      }`}
    >
      {/* Top Label & Icon */}
      <div className="flex items-center justify-between text-[#8FA4B8] mb-1">
        <div className="flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5 text-[#22AFFF]" />
          <span className="text-[10px] uppercase font-bold tracking-wider">{label}</span>
        </div>
      </div>

      {/* Large Value & Unit */}
      <div className="my-1">
        <span className="text-xl font-black text-[#F4F7FA] tracking-tight">{value}</span>
        <span className="text-[11px] text-[#8FA4B8] ml-1">{unit}</span>
      </div>

      {/* Sparkline & Status */}
      <div className="flex items-center justify-between mt-1 pt-1.5 border-t border-[#1B344B]/60">
        {/* Tiny Sparkline */}
        <div className="w-14 h-4">
          <svg viewBox="0 0 60 20" className="w-full h-full overflow-visible">
            <polyline
              fill="none"
              stroke={strokeColor}
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={points}
            />
          </svg>
        </div>

        <StatusBadge status={status} size="sm" />
      </div>
    </div>
  );
}
