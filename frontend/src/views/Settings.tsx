"use client";
import React, { useState } from 'react';
import { Settings as SettingsIcon, Shield, Radio, Cpu, RefreshCw, CheckCircle2 } from 'lucide-react';
import StatusBadge from '../components/common/StatusBadge';

export default function SettingsPage() {
  const [gatewayStatus, setGatewayStatus] = useState("LISTENING");
  const [bufferFill, setBufferFill] = useState(12);

  const models = [
    { id: "physics-v1.0", name: "Reduced-Order Thermodynamic Physics", version: "1.0.4", status: "ACTIVE", target: "MAE < 3.5%" },
    { id: "ekf-state-v1.0", name: "Extended Kalman Filter State Estimator", version: "1.0.2", status: "ACTIVE", target: "50Hz Synchronous" },
    { id: "anomaly-v1.2", name: "4-Tier Composite Residual & ML Estimator", version: "1.2.0", status: "ACTIVE", target: "Lead Time >= 12 min" },
    { id: "fault-classifier-v1.1", name: "Physics-Grounded Diagnostic Classifier", version: "1.1.0", status: "ACTIVE", target: "8 Fault Classes" },
    { id: "rul-v0.8", name: "Probabilistic Monte Carlo Log-Linear RUL", version: "0.8.5", status: "ACTIVE", target: "P10 - P90 Bands" },
    { id: "mission-margin-v1.0", name: "Multi-Factor Mission Margin & Counterfactual", version: "1.0.0", status: "ACTIVE", target: "4 Decision Branches" },
  ];

  return (
    <div className="flex-1 flex flex-col gap-4 p-4 overflow-y-auto font-mono">
      {/* Header */}
      <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl px-5 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#101F30] border border-[#1B344B] rounded-lg text-[#22AFFF]">
            <SettingsIcon className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-[#F4F7FA]">SYSTEM CONFIGURATION & MODEL REGISTRY</h2>
            <p className="text-[11px] text-[#8FA4B8]">
              AeroPiston-4X Twin Architecture &bull; DRDO / Smart India Hackathon Prototype
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <StatusBadge status="LIVE" label="CORE ONLINE" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Model Registry (7 Cols) */}
        <div className="lg:col-span-7 bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4">
          <div className="flex items-center justify-between pb-2 border-b border-[#1B344B] mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-[#8FA4B8]">
              DIGITAL TWIN MODEL REGISTRY (§51)
            </span>
            <span className="text-[10px] text-[#22AFFF]">Version: Registry v1.0</span>
          </div>

          <div className="space-y-2 text-xs">
            {models.map((m) => (
              <div key={m.id} className="p-2.5 bg-[#0B1725] border border-[#1B344B] rounded-lg flex items-center justify-between">
                <div>
                  <div className="font-bold text-[#F4F7FA]">{m.name}</div>
                  <div className="text-[10px] text-[#8FA4B8]">
                    ID: {m.id} &bull; Target: {m.target}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] px-1.5 py-0.5 bg-[#101F30] text-[#8FA4B8] rounded border border-[#1B344B]">
                    v{m.version}
                  </span>
                  <StatusBadge status="HEALTHY" label={m.status} size="sm" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Operating Limits & Gateway (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4">
            <span className="text-xs font-bold uppercase tracking-wider text-[#8FA4B8] mb-3 block pb-2 border-b border-[#1B344B]">
              PROPULSION OPERATING LIMITS
            </span>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-[#1B344B]/40">
                <span className="text-[#8FA4B8]">RPM Redline:</span>
                <span className="font-bold text-[#FF4D4D]">3200 RPM</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1B344B]/40">
                <span className="text-[#8FA4B8]">Max Continuous EGT:</span>
                <span className="font-bold text-[#FF4D4D]">820 °C</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1B344B]/40">
                <span className="text-[#8FA4B8]">Max Cylinder Head Temp (CHT):</span>
                <span className="font-bold text-[#FF8A3D]">220 °C</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1B344B]/40">
                <span className="text-[#8FA4B8]">Min Safe Oil Pressure:</span>
                <span className="font-bold text-[#F4B942]">2.5 bar</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-[#8FA4B8]">DC Electrical Bus:</span>
                <span className="font-bold text-[#22D88A]">24 - 32 V</span>
              </div>
            </div>
          </div>

          <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4">
            <span className="text-xs font-bold uppercase tracking-wider text-[#8FA4B8] mb-3 block pb-2 border-b border-[#1B344B]">
              EDGE TELEMETRY GATEWAY (§47, §81)
            </span>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-[#8FA4B8]">Protocol Handler:</span>
                <span className="font-bold text-[#F4F7FA]">MAVLink v2 & SocketCAN 2.0B</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8FA4B8]">Gateway Status:</span>
                <StatusBadge status="LIVE" label={gatewayStatus} size="sm" />
              </div>
              <div className="flex justify-between">
                <span className="text-[#8FA4B8]">Ring-Buffer Fill (10k frames):</span>
                <span className="font-bold text-[#22AFFF]">{bufferFill}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
