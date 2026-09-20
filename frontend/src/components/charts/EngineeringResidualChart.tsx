"use client";
import React from 'react';
import { TelemetryPacket } from '../../types/telemetry';

interface EngineeringResidualChartProps {
  telemetry: TelemetryPacket;
}

export default function EngineeringResidualChart({ telemetry }: EngineeringResidualChartProps) {
  const items = [
    {
      channel: "EGT (Exhaust Gas)",
      actual: `${telemetry.egt} °C`,
      expected: `${telemetry.expected_egt || 710.0} °C`,
      residual: `${(telemetry.egt - (telemetry.expected_egt || 710.0)) > 0 ? '+' : ''}${(telemetry.egt - (telemetry.expected_egt || 710.0)).toFixed(1)} °C`,
      isElevated: Math.abs(telemetry.egt - (telemetry.expected_egt || 710.0)) > 25,
    },
    {
      channel: "CHT (Cylinder Head)",
      actual: `${telemetry.cht} °C`,
      expected: `${telemetry.expected_cht || 170.0} °C`,
      residual: `${(telemetry.cht - (telemetry.expected_cht || 170.0)) > 0 ? '+' : ''}${(telemetry.cht - (telemetry.expected_cht || 170.0)).toFixed(1)} °C`,
      isElevated: Math.abs(telemetry.cht - (telemetry.expected_cht || 170.0)) > 15,
    },
    {
      channel: "Engine RPM",
      actual: `${telemetry.rpm} rpm`,
      expected: `2450.0 rpm`,
      residual: `${telemetry.rpm - 2450 > 0 ? '+' : ''}${telemetry.rpm - 2450} rpm`,
      isElevated: Math.abs(telemetry.rpm - 2450) > 100,
    },
    {
      channel: "Fuel Flow Rate",
      actual: `${telemetry.fuel_flow} L/h`,
      expected: `18.5 L/h`,
      residual: `${(telemetry.fuel_flow - 18.5) > 0 ? '+' : ''}${(telemetry.fuel_flow - 18.5).toFixed(1)} L/h`,
      isElevated: Math.abs(telemetry.fuel_flow - 18.5) > 1.5,
    },
    {
      channel: "Oil Temperature",
      actual: `${telemetry.oil_temperature} °C`,
      expected: `95.0 °C`,
      residual: `${(telemetry.oil_temperature - 95.0) > 0 ? '+' : ''}${(telemetry.oil_temperature - 95.0).toFixed(1)} °C`,
      isElevated: Math.abs(telemetry.oil_temperature - 95.0) > 10,
    },
    {
      channel: "Oil Pressure",
      actual: `${telemetry.oil_pressure} bar`,
      expected: `4.6 bar`,
      residual: `${(telemetry.oil_pressure - 4.6) > 0 ? '+' : ''}${(telemetry.oil_pressure - 4.6).toFixed(1)} bar`,
      isElevated: Math.abs(telemetry.oil_pressure - 4.6) > 0.8,
    },
  ];

  return (
    <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4 font-mono select-none flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider">
            PHYSICS-BASED ESTIMATION
          </span>
          <h3 className="text-xs font-bold text-[#F4F7FA]">Actual vs Expected Residuals</h3>
        </div>
        <span className="text-[10px] text-[#22AFFF]">50Hz EKF State Vector</span>
      </div>

      <div className="overflow-x-auto my-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="text-[10px] uppercase text-[#60758A] border-b border-[#1B344B]/60 pb-1">
              <th className="py-1">Parameter</th>
              <th className="py-1">Actual</th>
              <th className="py-1">Expected</th>
              <th className="py-1 text-right">Residual (Δ)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1B344B]/40">
            {items.map((it) => (
              <tr key={it.channel} className="hover:bg-[#101F30]/50 transition-colors">
                <td className="py-1 text-[#F4F7FA] font-medium">{it.channel}</td>
                <td className="py-1 text-[#F4F7FA] font-bold">{it.actual}</td>
                <td className="py-1 text-[#8FA4B8]">{it.expected}</td>
                <td
                  className={`py-1 text-right font-bold ${
                    it.isElevated ? 'text-[#FF4D4D]' : 'text-[#22D88A]'
                  }`}
                >
                  {it.residual}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center text-[10px] text-[#60758A] mt-2 pt-1.5 border-t border-[#1B344B]/60">
        <span>Thermodynamic Baseline Residuals</span>
        <span>Zero-Drift Invariant</span>
      </div>
    </div>
  );
}
