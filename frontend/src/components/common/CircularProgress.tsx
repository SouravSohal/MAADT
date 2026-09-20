"use client";
import React from 'react';

interface CircularProgressProps {
  value: number; // 0 to 100
  size?: number; // diameter in px
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
  color?: string; // hex or tailwind class
  showPercentage?: boolean;
}

export default function CircularProgress({
  value,
  size = 64,
  strokeWidth = 6,
  label,
  sublabel,
  color,
  showPercentage = true,
}: CircularProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const normalizedValue = Math.min(100, Math.max(0, value));
  const strokeDashoffset = circumference - (normalizedValue / 100) * circumference;

  // Default semantic color based on value
  const strokeColor =
    color ||
    (normalizedValue >= 85
      ? "#22D88A" // healthy
      : normalizedValue >= 65
      ? "#F4B942" // advisory
      : normalizedValue >= 45
      ? "#FF8A3D" // warning
      : "#FF4D4D"); // critical

  return (
    <div className="flex flex-col items-center justify-center relative select-none">
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#1B344B"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
      </svg>

      {/* Center Text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        {showPercentage && (
          <span className="font-mono font-bold leading-none tracking-tight text-[#F4F7FA]" style={{ fontSize: size * 0.28 }}>
            {Math.round(value)}%
          </span>
        )}
        {sublabel && (
          <span className="text-[10px] uppercase font-mono text-[#8FA4B8] mt-0.5">
            {sublabel}
          </span>
        )}
      </div>

      {label && (
        <span className="text-xs font-mono font-medium text-[#8FA4B8] mt-1 text-center">
          {label}
        </span>
      )}
    </div>
  );
}
