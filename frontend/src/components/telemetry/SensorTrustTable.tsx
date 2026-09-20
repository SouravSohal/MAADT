"use client";
import React from 'react';
import { SensorQuality } from '../../types/telemetry';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

interface SensorTrustTableProps {
  trust: Record<string, number>;
  quality: Record<string, SensorQuality>;
}

export default function SensorTrustTable({ trust, quality }: SensorTrustTableProps) {
  const sensorList = [
    { key: "rpm", name: "Engine RPM" },
    { key: "egt", name: "Exhaust Gas (EGT)" },
    { key: "cht", name: "Cylinder Head (CHT)" },
    { key: "oil_pressure", name: "Oil Pressure" },
    { key: "oil_temperature", name: "Oil Temperature" },
    { key: "fuel_flow", name: "Fuel Flow Rate" },
    { key: "vibration", name: "Vibration RMS" },
    { key: "battery_voltage", name: "Electrical Bus" },
  ];

  const getQualityBadge = (q: SensorQuality | undefined) => {
    const val = q || "MISSING";
    let bg = "bg-[#072418] text-[#22D88A] border-[#14532D]";
    if (val === "SUSPECT" || val === "NOISY") {
      bg = "bg-[#291F0A] text-[#F4B942] border-[#785412]";
    } else if (val === "OUT_OF_RANGE" || val === "STALE" || val === "MISSING") {
      bg = "bg-[#2E0B0B] text-[#FF4D4D] border-[#7F1D1D]";
    }

    return (
      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border font-mono ${bg}`}>
        {val}
      </span>
    );
  };

  return (
    <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4 font-mono select-none flex flex-col justify-between h-full">
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider">
            SIGNAL INTEGRITY
          </span>
          <h3 className="text-xs font-bold text-[#F4F7FA]">Dynamic Sensor Trust Matrix</h3>
        </div>
        <span className="text-[10px] text-[#22AFFF]">Decoupled Trust Isolation</span>
      </div>

      <div className="overflow-x-auto my-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="text-[10px] uppercase text-[#60758A] border-b border-[#1B344B]/60 pb-1">
              <th className="py-1">Sensor Channel</th>
              <th className="py-1">Trust Score</th>
              <th className="py-1 text-right">Quality State</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1B344B]/40">
            {sensorList.map((s) => {
              const trVal = trust[s.key] !== undefined ? trust[s.key] : 0.98;
              const qVal = quality[s.key] || "VALID";

              return (
                <tr key={s.key} className="hover:bg-[#101F30]/50 transition-colors">
                  <td className="py-1 text-[#F4F7FA] font-medium">{s.name}</td>
                  <td className="py-1">
                    <div className="flex items-center gap-2">
                      <span className="w-9 font-bold text-[#22AFFF]">
                        {(trVal * 100).toFixed(0)}%
                      </span>
                      <div className="w-16 bg-[#07111D] rounded-full h-1 overflow-hidden border border-[#1B344B]/40">
                        <div
                          className="h-full bg-[#22AFFF] rounded-full"
                          style={{ width: `${trVal * 100}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-1 text-right">{getQualityBadge(qVal)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center text-[10px] text-[#60758A] mt-2 pt-1.5 border-t border-[#1B344B]/60">
        <span>Dual Redundant Validation</span>
        <span className="text-[#22D88A]">&bull; Sensor Drift Decoupled</span>
      </div>
    </div>
  );
}
