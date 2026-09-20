"use client";
import React from 'react';
import { ShieldCheck, AlertOctagon, ChevronRight, Clock, Plane, CheckCircle2 } from 'lucide-react';
import { TelemetryPacket } from '../../types/telemetry';
import CircularProgress from '../common/CircularProgress';
import StatusBadge from '../common/StatusBadge';

interface MissionStatusPanelProps {
  telemetry: TelemetryPacket;
  onViewAlerts: () => void;
}

export default function MissionStatusPanel({
  telemetry,
  onViewAlerts,
}: MissionStatusPanelProps) {
  const margin = telemetry.mission_margin || 72;
  const health = telemetry.health_index || 84;
  const rulHours = telemetry.rul?.hours_remaining || 147;
  const confidence = telemetry.twin_confidence ? Math.round(telemetry.twin_confidence * 100) : 94;

  const isAnomaly = telemetry.anomaly_score > 0.4 || telemetry.active_faults.length > 0;

  return (
    <div className="w-80 bg-[#0D1B2A] border border-[#1B344B] rounded-xl flex flex-col overflow-hidden font-mono select-none shrink-0 h-full shadow-lg">
      {/* Pinned Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-[#1B344B] bg-[#0B1725] shrink-0">
        <div>
          <span className="text-[10px] uppercase font-bold text-[#8FA4B8] tracking-wider">
            EXECUTIVE DIRECTIVE
          </span>
          <h3 className="text-xs font-bold text-[#F4F7FA]">Mission Status</h3>
        </div>
        <StatusBadge
          status={isAnomaly ? "WARNING" : "CONTINUE"}
          label={isAnomaly ? "ADVISORY" : "CONTINUE"}
        />
      </div>

      {/* Scrollable Content Body */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-2.5">
        {/* Mission Margin Indicator */}
        <div className="flex items-center justify-center py-2 bg-[#0B1725] border border-[#1B344B] rounded-xl">
          <CircularProgress
            value={margin}
            size={84}
            strokeWidth={7}
            sublabel="Margin"
          />
        </div>

        {/* Sortie Phase Details */}
        <div className="p-2 bg-[#0B1725] border border-[#1B344B] rounded-lg text-xs space-y-1">
          <div className="flex justify-between">
            <span className="text-[#8FA4B8]">Endurance:</span>
            <span className="text-[#F4F7FA] font-bold">05:42 / 08:00</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#8FA4B8]">Mission Profile:</span>
            <span className="text-[#F4F7FA] font-bold">Surveillance AOI</span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#8FA4B8]">Active Phase:</span>
            <span className="text-[#22AFFF] font-bold">{telemetry.operating_regime || "CRUISE"}</span>
          </div>
        </div>

        {/* 4 Metric Tiles */}
        <div className="grid grid-cols-2 gap-1.5">
          <div className="p-2 bg-[#0B1725] border border-[#1B344B] rounded-lg">
            <div className="text-[9px] uppercase text-[#8FA4B8]">Mission Margin</div>
            <div className="text-sm font-bold text-[#22AFFF] mt-0.5">{Math.round(margin)}%</div>
          </div>

          <div className="p-2 bg-[#0B1725] border border-[#1B344B] rounded-lg">
            <div className="text-[9px] uppercase text-[#8FA4B8]">Engine Health</div>
            <div
              className={`text-sm font-bold mt-0.5 ${
                health >= 85 ? 'text-[#22D88A]' : health >= 70 ? 'text-[#F4B942]' : 'text-[#FF4D4D]'
              }`}
            >
              {Math.round(health)}%
            </div>
          </div>

          <div className="p-2 bg-[#0B1725] border border-[#1B344B] rounded-lg">
            <div className="text-[9px] uppercase text-[#8FA4B8]">Remaining Life</div>
            <div className="text-sm font-bold text-[#F4F7FA] mt-0.5">
              {Math.round(rulHours)} <span className="text-[10px] text-[#8FA4B8] font-normal">h</span>
            </div>
          </div>

          <div className="p-2 bg-[#0B1725] border border-[#1B344B] rounded-lg">
            <div className="text-[9px] uppercase text-[#8FA4B8]">Twin Conf.</div>
            <div className="text-sm font-bold text-[#22AFFF] mt-0.5">{confidence}%</div>
          </div>
        </div>

        {/* Active Alert Card */}
        <div
          onClick={onViewAlerts}
          className="p-2.5 bg-[#1A0B0B] border border-[#7C2D12] hover:border-[#FF4D4D]/70 rounded-lg cursor-pointer transition-all hover:bg-[#251010] shadow-[0_0_8px_rgba(255,77,77,0.15)]"
          title="Click to open Emergency Checklist & Diagnostic Procedures"
        >
          <div className="flex items-center justify-between mb-0.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#FF8A3D]">
              <AlertOctagon className="w-3.5 h-3.5 text-[#FF4D4D] animate-pulse" />
              <span>Combustion anomaly detected</span>
            </div>
            <span className="text-[9px] px-1 py-0.2 bg-[#FF4D4D]/20 text-[#FF4D4D] rounded font-bold">
              OPEN CHECKLIST &rarr;
            </span>
          </div>
          <div className="text-[10px] text-[#8FA4B8]">
            Injector abnormality (P: {Math.round((telemetry.active_diagnostic?.probability || 0.87) * 100)}%)
          </div>
          <div className="flex items-center gap-1 text-[9px] text-[#60758A] mt-1">
            <Clock className="w-3 h-3" />
            <span>Timestamp: 14:31:52 UTC &bull; Click to Inspect</span>
          </div>
        </div>
      </div>

      {/* Pinned Action Button Footer */}
      <div className="p-2.5 border-t border-[#1B344B] bg-[#0B1725] shrink-0">
        <button
          onClick={onViewAlerts}
          className="w-full py-2 bg-[#101F30] hover:bg-[#102E4A] text-[#8FA4B8] hover:text-[#F4F7FA] border border-[#1B344B] rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer"
        >
          <span>View All Alerts</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
