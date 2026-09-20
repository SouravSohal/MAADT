"use client";
import React, { useState, useEffect, useRef } from 'react';
import { TelemetryPacket } from '../types/telemetry';
import { EngineComponentId, EngineViewMode } from '../types/engine';
import { REPLAY_MILESTONES } from '../data/mockTelemetry';
import EngineDigitalTwin from '../components/engine/EngineDigitalTwin';
import TelemetryStrip from '../components/telemetry/TelemetryStrip';
import { Play, Pause, RotateCcw, FastForward, History, ShieldAlert } from 'lucide-react';
import StatusBadge from '../components/common/StatusBadge';

interface ReplayPageProps {
  telemetry: TelemetryPacket;
  viewMode: EngineViewMode;
  onViewModeChange: (mode: EngineViewMode) => void;
  selectedComponent: EngineComponentId;
  onSelectComponent: (id: EngineComponentId) => void;
  onScrubTelemetry: (scrubbed: TelemetryPacket) => void;
}

function computeScrubbedPacket(
  val: number,
  base: TelemetryPacket,
  eventType: string,
  maxDuration: number
): TelemetryPacket {
  const isPastAnomaly = val >= 16200;
  const validRegimes = ["START", "WARM_UP", "IDLE", "TAXI", "TAKEOFF", "CLIMB", "CRUISE", "LOITER", "THROTTLE_TRANSIENT", "DESCENT", "LANDING", "SHUTDOWN"];
  const safeRegime = validRegimes.includes(eventType) ? (eventType as any) : "CRUISE";

  return {
    ...base,
    timestamp: Date.now() / 1000 - (maxDuration - val),
    rpm: val < 900 ? 1450 : val < 2100 ? 2650 : 2450,
    egt: isPastAnomaly ? 768.0 : 710.0,
    cht: isPastAnomaly ? 193.0 : 170.0,
    fuel_flow: isPastAnomaly ? 21.8 : 20.0,
    vibration: isPastAnomaly ? 0.62 : 0.35,
    health_index: isPastAnomaly ? 84.0 : 96.0,
    anomaly_score: isPastAnomaly ? 0.76 : 0.04,
    mission_margin: isPastAnomaly ? 72.0 : 92.0,
    operating_regime: safeRegime,
    active_faults: isPastAnomaly ? [{ fault_type: "injector_abnormality", severity: 0.85 }] : [],
  };
}

export default function ReplayPage({
  telemetry,
  viewMode,
  onViewModeChange,
  selectedComponent,
  onSelectComponent,
  onScrubTelemetry,
}: ReplayPageProps) {
  const [sliderVal, setSliderVal] = useState(16200); // Default to Anomaly milestone (04:30)
  const [isPlaying, setIsPlaying] = useState(false);
  const maxDuration = 28800; // 8 hours in seconds

  const sliderValRef = useRef(sliderVal);
  sliderValRef.current = sliderVal;

  const telemetryRef = useRef(telemetry);
  telemetryRef.current = telemetry;

  const onScrubTelemetryRef = useRef(onScrubTelemetry);
  onScrubTelemetryRef.current = onScrubTelemetry;

  const currentMilestone = REPLAY_MILESTONES.reduce((prev, curr) => {
    return curr.timestamp <= sliderVal ? curr : prev;
  }, REPLAY_MILESTONES[0]);

  // Safely execute timeline scrubbing without setState-in-render violations
  const handleScrub = (val: number) => {
    setSliderVal(val);
    sliderValRef.current = val;
    const milestone = REPLAY_MILESTONES.reduce((prev, curr) => {
      return curr.timestamp <= val ? curr : prev;
    }, REPLAY_MILESTONES[0]);
    const scrubbedPacket = computeScrubbedPacket(val, telemetryRef.current, milestone.event_type, maxDuration);
    onScrubTelemetryRef.current(scrubbedPacket);
  };

  useEffect(() => {
    if (!isPlaying) return;

    const timer = setInterval(() => {
      const current = sliderValRef.current;
      if (current >= maxDuration) {
        setIsPlaying(false);
        return;
      }
      const next = Math.min(current + 120, maxDuration);
      handleScrub(next);
    }, 200);

    return () => clearInterval(timer);
  }, [isPlaying]);

  const formatTime = (secs: number) => {
    const hrs = Math.floor(secs / 3600);
    const mins = Math.floor((secs % 3600) / 60);
    return `${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
  };

  return (
    <div className="flex-1 flex flex-col gap-4 p-4 overflow-y-auto font-mono">
      {/* Flight Information Top Banner */}
      <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl px-5 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-[#101F30] border border-[#1B344B] rounded-lg text-[#22AFFF]">
            <History className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#8FA4B8]">SORTIE ARCHIVE:</span>
              <span className="text-sm font-bold text-[#F4F7FA]">FLT-2026-0919 &bull; MIS-ENDURANCE-01</span>
              <StatusBadge status="ADVISORY" label="REPLAY MODE" />
            </div>
            <p className="text-[11px] text-[#60758A]">
              Date: 19 SEP 2026 &bull; Target: AeroPiston-4X (ENG-001) &bull; Synchronous Time-Travel Engine
            </p>
          </div>
        </div>

        {/* Current Replay Timestamp */}
        <div className="flex items-center gap-4 text-xs">
          <div className="text-right">
            <span className="text-[10px] text-[#8FA4B8] block uppercase">MISSION TIME ELAPSED</span>
            <span className="text-lg font-bold text-[#22AFFF]">
              {formatTime(sliderVal)} <span className="text-xs text-[#8FA4B8]">/ 08:00</span>
            </span>
          </div>
          <div className="text-right">
            <span className="text-[10px] text-[#8FA4B8] block uppercase">CURRENT EVENT</span>
            <span className="text-xs font-bold text-[#F4F7FA]">{currentMilestone.event_type}</span>
          </div>
        </div>
      </div>

      {/* Center: 3D Engine Digital Twin in Replay State */}
      <div className="h-[420px] xl:h-[480px] w-full flex flex-col">
        <EngineDigitalTwin
          telemetry={telemetry}
          viewMode={viewMode}
          onViewModeChange={onViewModeChange}
          selectedComponent={selectedComponent}
          onSelectComponent={onSelectComponent}
        />
      </div>

      {/* Replay Timeline Controls & Scrubber */}
      <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-3.5 py-1.5 bg-[#22AFFF] hover:bg-[#1A90D6] text-[#07111D] font-bold rounded-lg flex items-center gap-1.5 text-xs transition-colors cursor-pointer"
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>{isPlaying ? "PAUSE" : "PLAY BACK"}</span>
            </button>
            <button
              onClick={() => handleScrub(0)}
              title="Rewind to Start"
              className="p-1.5 bg-[#101F30] hover:bg-[#1B344B] text-[#8FA4B8] rounded border border-[#1B344B] transition-colors cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Milestone Quick Jumps */}
          <div className="flex items-center gap-1.5 text-xs overflow-x-auto">
            {REPLAY_MILESTONES.map((m) => (
              <button
                key={m.event_type}
                onClick={() => handleScrub(m.timestamp)}
                className={`px-2 py-1 rounded text-[10px] font-bold border transition-all cursor-pointer ${
                  currentMilestone.event_type === m.event_type
                    ? "bg-[#102E4A] text-[#22AFFF] border-[#22AFFF]/60 shadow-sm"
                    : "bg-[#0B1725] text-[#8FA4B8] border-[#1B344B] hover:text-[#F4F7FA]"
                }`}
              >
                {m.time_formatted} {m.event_type}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Slider Track */}
        <div className="space-y-1">
          <input
            type="range"
            min="0"
            max={maxDuration}
            step="30"
            value={sliderVal}
            onChange={(e) => handleScrub(Number(e.target.value))}
            className="w-full accent-[#22AFFF] bg-[#0B1725] cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-[#60758A]">
            <span>00:00 (Start)</span>
            <span>02:00</span>
            <span className="text-[#FF8A3D] font-bold">04:30 (Anomaly)</span>
            <span>06:00</span>
            <span>08:00 (Landing)</span>
          </div>
        </div>
      </div>

      {/* Synchronized Replay Telemetry Strip */}
      <div className="w-full">
        <TelemetryStrip telemetry={telemetry} />
      </div>
    </div>
  );
}
