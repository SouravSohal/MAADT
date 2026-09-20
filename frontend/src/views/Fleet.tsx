"use client";
import React, { useState } from 'react';
import { FLEET_AIRCRAFT } from '../data/mockTelemetry';
import { FleetAircraft } from '../types/mission';
import StatusBadge from '../components/common/StatusBadge';
import CircularProgress from '../components/common/CircularProgress';
import { Users, Plane, ShieldCheck, ChevronRight, Activity } from 'lucide-react';

interface FleetPageProps {
  onSelectAircraft: (uavId: string) => void;
}

export default function FleetPage({ onSelectAircraft }: FleetPageProps) {
  const [fleet] = useState<FleetAircraft[]>(FLEET_AIRCRAFT);
  const [selectedUav, setSelectedUav] = useState<string>("UAV-001");

  const activeAircraft = fleet.find((a) => a.uav_id === selectedUav) || fleet[0];

  return (
    <div className="flex-1 flex flex-col gap-4 p-4 overflow-y-auto font-mono">
      {/* Fleet Top Header */}
      <div className="bg-[#0D1B2A] border border-[#1B344B] rounded-xl px-5 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#101F30] border border-[#1B344B] rounded-lg text-[#22AFFF]">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-[#F4F7FA]">SQUADRON ALPHA &bull; FLEET DIGITAL TWIN OBSERVER</h2>
            <p className="text-[11px] text-[#8FA4B8]">
              Tactical Surveillance Squadron &bull; 3 MALE UAV Platforms &bull; Centralized Prognostics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="text-right">
            <span className="text-[10px] text-[#8FA4B8] block">FLEET AVERAGE HEALTH</span>
            <span className="text-lg font-bold text-[#22D88A]">80.9%</span>
          </div>
          <div className="text-right">
            <span className="text-[10px] text-[#8FA4B8] block">ACTIVE SORTIES</span>
            <span className="text-lg font-bold text-[#22AFFF]">1 of 3</span>
          </div>
        </div>
      </div>

      {/* Main Layout: Fleet Table (Left) + Selected Aircraft Overview (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
        {/* Fleet Table (8 Cols) */}
        <div className="lg:col-span-8 bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-[#1B344B] mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#8FA4B8]">
                AIRCRAFT PROPULSION REGISTRY
              </span>
              <span className="text-[11px] text-[#60758A]">Click a UAV to switch active twin</span>
            </div>

            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-[10px] uppercase text-[#60758A] border-b border-[#1B344B]/60 pb-2">
                  <th className="py-2 px-3">UAV ID</th>
                  <th className="py-2 px-3">Status</th>
                  <th className="py-2 px-3">Health</th>
                  <th className="py-2 px-3">RUL (Hours)</th>
                  <th className="py-2 px-3">Mission Profile</th>
                  <th className="py-2 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1B344B]/40">
                {fleet.map((ac) => {
                  const isSelected = selectedUav === ac.uav_id;
                  return (
                    <tr
                      key={ac.uav_id}
                      onClick={() => setSelectedUav(ac.uav_id)}
                      className={`transition-colors cursor-pointer ${
                        isSelected ? "bg-[#102E4A]/60" : "hover:bg-[#101F30]/60"
                      }`}
                    >
                      <td className="py-3 px-3 font-bold text-[#F4F7FA] flex items-center gap-2">
                        <Plane className="w-4 h-4 text-[#22AFFF]" />
                        <span>{ac.uav_id}</span>
                        <span className="text-[10px] text-[#8FA4B8] font-normal">({ac.engine_id})</span>
                      </td>
                      <td className="py-3 px-3">
                        <StatusBadge
                          status={ac.status === "AIRBORNE" ? "LIVE" : ac.status === "STANDBY" ? "HEALTHY" : "CRITICAL"}
                          label={ac.status}
                          size="sm"
                        />
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`font-bold ${
                            ac.health_index >= 85 ? 'text-[#22D88A]' : ac.health_index >= 70 ? 'text-[#F4B942]' : 'text-[#FF4D4D]'
                          }`}
                        >
                          {ac.health_index}%
                        </span>
                      </td>
                      <td className="py-3 px-3 font-bold text-[#F4F7FA]">{ac.rul_hours} h</td>
                      <td className="py-3 px-3 text-[#8FA4B8]">{ac.mission}</td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectAircraft(ac.uav_id);
                          }}
                          className="px-2.5 py-1 bg-[#101F30] hover:bg-[#22AFFF] hover:text-[#07111D] text-[#22AFFF] border border-[#1B344B] rounded text-[11px] font-bold transition-all cursor-pointer"
                        >
                          Open Twin &rarr;
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex justify-between items-center text-[10px] text-[#60758A] mt-4 pt-2 border-t border-[#1B344B]/60">
            <span>Fleet Architecture: Distributed Aero-Piston Sensors &bull; Centralized Fleet Twin Registry</span>
            <span>Total Flight Hours: 1,034.7 h</span>
          </div>
        </div>

        {/* Selected Aircraft Overview Card (4 Cols) */}
        <div className="lg:col-span-4 bg-[#0D1B2A] border border-[#1B344B] rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-[#1B344B] mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#8FA4B8]">
                AIRCRAFT TELEMETRY SUMMARY
              </span>
              <span className="text-xs font-bold text-[#22AFFF]">{activeAircraft.uav_id}</span>
            </div>

            <div className="flex items-center justify-center my-3">
              <CircularProgress
                value={activeAircraft.health_index}
                size={96}
                strokeWidth={8}
                sublabel="Health"
              />
            </div>

            <div className="space-y-2 text-xs bg-[#0B1725] p-3 rounded-lg border border-[#1B344B]/60">
              <div className="flex justify-between">
                <span className="text-[#8FA4B8]">Status:</span>
                <StatusBadge status={activeAircraft.status} size="sm" />
              </div>
              <div className="flex justify-between">
                <span className="text-[#8FA4B8]">Flight Hours:</span>
                <span className="text-[#F4F7FA] font-bold">{activeAircraft.flight_hours} hrs</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8FA4B8]">Active Faults:</span>
                <span className={`font-bold ${activeAircraft.active_faults > 0 ? 'text-[#FF4D4D]' : 'text-[#22D88A]'}`}>
                  {activeAircraft.active_faults} Detected
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8FA4B8]">Mission Margin:</span>
                <span className="text-[#22AFFF] font-bold">{activeAircraft.composite_margin}%</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => onSelectAircraft(activeAircraft.uav_id)}
            className="w-full mt-4 py-2.5 bg-[#22AFFF] hover:bg-[#1A90D6] text-[#07111D] font-bold rounded-lg flex items-center justify-center gap-2 text-xs transition-colors cursor-pointer"
          >
            <span>Launch Live Digital Twin Cockpit</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
