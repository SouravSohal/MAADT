"use client";
import React, { Suspense, useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';
import * as THREE from 'three';
import { EngineComponentId, EngineViewMode } from '../../types/engine';
import { TelemetryPacket } from '../../types/telemetry';
import ProceduralAeroPistonEngine from './ProceduralAeroPistonEngine';
import { AirframeDisplayMode } from './TranslucentMaleUAVAirframe';
import { RotateCcw, Eye, Layers, Flame, Box, Plane } from 'lucide-react';

interface EngineDigitalTwinProps {
  telemetry: TelemetryPacket;
  viewMode: EngineViewMode;
  onViewModeChange: (mode: EngineViewMode) => void;
  selectedComponent: EngineComponentId | null;
  onSelectComponent: (id: EngineComponentId) => void;
}

export default function EngineDigitalTwin({
  telemetry,
  viewMode,
  onViewModeChange,
  selectedComponent,
  onSelectComponent,
}: EngineDigitalTwinProps) {
  const controlsRef = useRef<any>(null);
  const [airframeMode, setAirframeMode] = useState<AirframeDisplayMode>("translucent");

  const resetCamera = () => {
    if (controlsRef.current) {
      controlsRef.current.reset();
    }
  };

  const viewTabs: { id: EngineViewMode; label: string; icon: any }[] = [
    { id: "3D", label: "3D View", icon: Box },
    { id: "System", label: "System View", icon: Layers },
    { id: "Thermal", label: "Thermal View", icon: Flame },
    { id: "X-Ray", label: "X-Ray View", icon: Eye },
  ];

  return (
    <div className="flex-1 flex flex-col bg-[#0D1B2A] border border-[#1B344B] rounded-xl overflow-hidden relative select-none h-full">
      {/* View Mode Tabs & UAV Airframe Toolbar */}
      <div className="h-11 px-3 bg-[#0B1725] border-b border-[#1B344B] flex items-center justify-between z-10 gap-2 flex-wrap sm:flex-nowrap">
        {/* Left: View Mode Tabs */}
        <div className="flex items-center gap-1">
          {viewTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = viewMode === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onViewModeChange(tab.id)}
                className={`px-2.5 py-1.5 rounded-md font-mono text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                  isActive
                    ? "bg-[#102E4A] text-[#22AFFF] border border-[#22AFFF]/50 shadow-[0_0_8px_rgba(34,175,255,0.2)]"
                    : "text-[#8FA4B8] hover:text-[#F4F7FA] hover:bg-[#101F30]"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Center/Right: Indian MALE UAV Airframe Mode Selector */}
        <div className="flex items-center gap-1 bg-[#101F30] p-0.5 rounded-lg border border-[#1B344B]">
          <div className="flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-mono text-[#8FA4B8] border-r border-[#1B344B]">
            <Plane className="w-3.5 h-3.5 text-[#22AFFF]" />
            <span className="hidden md:inline font-semibold">UAV Airframe:</span>
          </div>
          {(["translucent", "ghost", "wireframe", "hidden"] as AirframeDisplayMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setAirframeMode(mode)}
              className={`px-2 py-1 rounded text-[10px] font-mono font-medium transition-all capitalize cursor-pointer ${
                airframeMode === mode
                  ? "bg-[#102E4A] text-[#22AFFF] border border-[#22AFFF]/50 font-bold"
                  : "text-[#8FA4B8] hover:text-[#F4F7FA]"
              }`}
            >
              {mode === "hidden" ? "Off" : mode}
            </button>
          ))}
        </div>

        {/* Camera Reset & Active Spec Tag */}
        <div className="flex items-center gap-2">
          <div className="items-center gap-1.5 hidden 2xl:flex">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[11px] font-mono text-[#60758A]">
              DRDO TAPAS-BH-201 &bull; AeroPiston-4X
            </span>
          </div>
          <button
            onClick={resetCamera}
            title="Reset View Angle"
            className="p-1.5 bg-[#101F30] hover:bg-[#1B344B] text-[#8FA4B8] hover:text-[#F4F7FA] rounded border border-[#1B344B] transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 3D WebGL Canvas */}
      <div className="flex-1 w-full relative min-h-0">
        <Canvas camera={{ position: [5.2, 3.2, 5.5], fov: 44 }}>
          {/* Engineering Dark Lighting */}
          <ambientLight intensity={0.6} />
          {/* Key Light */}
          <directionalLight position={[10, 14, 8]} intensity={1.5} color="#F4F7FA" />
          {/* Cool Blue Aerospace Fill / Rim Light */}
          <directionalLight position={[-10, -4, -8]} intensity={0.8} color="#22AFFF" />
          {/* Warm Thermal Fill */}
          <directionalLight position={[0, -6, 8]} intensity={0.35} color="#FF8A3D" />

          <Environment preset="night" />

          {/* Calibrated Aerospace Ground Grid for Full UAV Airframe Scale */}
          <gridHelper args={[14, 20, '#22AFFF', '#1B344B']} position={[0, -1.1, 0]} />

          <Suspense fallback={null}>
            <ProceduralAeroPistonEngine
              telemetry={telemetry}
              viewMode={viewMode}
              selectedComponent={selectedComponent}
              onSelectComponent={onSelectComponent}
              airframeMode={airframeMode}
            />
          </Suspense>

          <OrbitControls
            ref={controlsRef}
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            maxDistance={16}
            minDistance={1.2}
            target={[0, 0, 0]}
          />
        </Canvas>

        {/* Interaction Guidance Footer Banner */}
        <div className="absolute bottom-2 inset-x-0 flex justify-center pointer-events-none">
          <div className="bg-[#07111D]/80 backdrop-blur border border-[#1B344B] rounded-full px-4 py-1 text-[11px] font-mono text-[#8FA4B8] shadow-sm">
            Drag to rotate &bull; Scroll to zoom &bull; Click engine components through translucent UAV skin
          </div>
        </div>

        {/* Active Fault Notification in 3D Viewport */}
        {(telemetry.anomaly_score > 0.4 || (telemetry.active_faults && telemetry.active_faults.length > 0)) && (
          <div className="absolute top-3 left-3 bg-[#1A0B0B]/90 backdrop-blur border border-[#FF4D4D]/70 rounded-lg px-3 py-1.5 text-xs font-mono text-[#F4F7FA] pointer-events-none shadow-[0_0_15px_rgba(255,77,77,0.35)] flex items-center gap-2 animate-pulse z-20">
            <span className="w-2 h-2 rounded-full bg-[#FF4D4D] animate-ping" />
            <div>
              <span className="text-[10px] text-[#FF4D4D] uppercase font-bold tracking-wider block">
                FAULT DETECTED &bull; PULSING GLOW
              </span>
              <span className="text-xs text-[#F4F7FA] font-bold">
                {telemetry.active_faults?.[0]?.fault_type
                  ? telemetry.active_faults[0].fault_type.replace(/_/g, ' ').toUpperCase()
                  : "CYLINDER 3: INJECTOR ABNORMALITY"}
              </span>
            </div>
          </div>
        )}

        {/* Selected Component Badge (Top Right of Viewport) */}
        {selectedComponent && (
          <div className="absolute top-3 right-3 bg-[#07111D]/90 backdrop-blur border border-[#22AFFF]/50 rounded-lg px-3 py-1.5 text-xs font-mono text-[#F4F7FA] pointer-events-none shadow-md">
            <span className="text-[10px] text-[#22AFFF] uppercase font-bold block">ACTIVE INSPECTION</span>
            <span className="capitalize font-bold">{selectedComponent.replace(/_/g, ' ')}</span>
          </div>
        )}
      </div>
    </div>
  );
}
