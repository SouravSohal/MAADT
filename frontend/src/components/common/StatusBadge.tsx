"use client";
import React from 'react';

export type StatusType = "HEALTHY" | "ADVISORY" | "WARNING" | "CRITICAL" | "LIVE" | "NOMINAL" | "ABNORMAL";

interface StatusBadgeProps {
  status: StatusType | string;
  label?: string;
  size?: "sm" | "md";
  showDot?: boolean;
}

export default function StatusBadge({ status, label, size = "md", showDot = true }: StatusBadgeProps) {
  const norm = status.toUpperCase();

  let dotColor = "#22D88A";
  let bg = "bg-[#072418]";
  let border = "border-[#14532D]";
  let text = "text-[#22D88A]";

  if (norm === "LIVE" || norm === "HEALTHY" || norm === "NOMINAL" || norm === "SAFE" || norm === "CONTINUE") {
    dotColor = "#22D88A";
    bg = "bg-[#072418]";
    border = "border-[#14532D]";
    text = "text-[#22D88A]";
  } else if (norm === "ADVISORY" || norm === "MARGINAL") {
    dotColor = "#F4B942";
    bg = "bg-[#291F0A]";
    border = "border-[#785412]";
    text = "text-[#F4B942]";
  } else if (norm === "WARNING" || norm === "ABNORMAL") {
    dotColor = "#FF8A3D";
    bg = "bg-[#2D1606]";
    border = "border-[#7C2D12]";
    text = "text-[#FF8A3D]";
  } else if (norm === "CRITICAL" || norm === "UNSAFE" || norm === "EMERGENCY") {
    dotColor = "#FF4D4D";
    bg = "bg-[#2E0B0B]";
    border = "border-[#7F1D1D]";
    text = "text-[#FF4D4D]";
  }

  const isSmall = size === "sm";

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-mono font-bold uppercase rounded border ${bg} ${border} ${text} ${
        isSmall ? "px-1.5 py-0.5 text-[9px]" : "px-2 py-0.5 text-[11px]"
      }`}
    >
      {showDot && (
        <span
          className="w-1.5 h-1.5 rounded-full inline-block"
          style={{ backgroundColor: dotColor }}
        />
      )}
      <span>{label || status}</span>
    </span>
  );
}
