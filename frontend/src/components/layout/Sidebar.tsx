"use client";
import React from 'react';
import {
  Activity,
  Sliders,
  Play,
  History,
  Users,
  Settings,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

export type NavigationPage = "operation" | "engineering" | "simulation" | "replay" | "fleet" | "settings";

interface SidebarProps {
  currentPage: NavigationPage;
  onSelectPage: (page: NavigationPage) => void;
}

export default function Sidebar({ currentPage, onSelectPage }: SidebarProps) {
  const primaryNav: { id: NavigationPage; label: string; icon: any }[] = [
    { id: "operation", label: "Operation", icon: Activity },
    { id: "engineering", label: "Engineering", icon: Sliders },
    { id: "simulation", label: "Simulation", icon: Play },
    { id: "replay", label: "Replay", icon: History },
    { id: "fleet", label: "Fleet", icon: Users },
  ];

  return (
    <aside className="w-48 bg-[#0B1725] border-r border-[#1B344B] flex flex-col justify-between p-3 select-none shrink-0 z-10">
      {/* Primary Navigation Rail */}
      <div className="space-y-1.5">
        <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-widest text-[#60758A]">
          WORKSTATION
        </div>

        {primaryNav.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectPage(item.id)}
              className={`w-full px-3 py-2.5 rounded-lg flex items-center justify-between text-xs font-mono font-medium transition-all cursor-pointer ${
                isActive
                  ? "bg-[#102E4A] text-[#22AFFF] border border-[#22AFFF]/50 font-bold shadow-[0_0_12px_rgba(34,175,255,0.15)]"
                  : "text-[#8FA4B8] hover:text-[#F4F7FA] hover:bg-[#101F30]"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-[#22AFFF]' : 'text-[#60758A]'}`} />
                <span>{item.label}</span>
              </div>
              {isActive && <ChevronRight className="w-3.5 h-3.5 text-[#22AFFF]" />}
            </button>
          );
        })}

        {/* Separator */}
        <div className="my-3 border-t border-[#1B344B]" />

        {/* Settings */}
        <button
          onClick={() => onSelectPage("settings")}
          className={`w-full px-3 py-2.5 rounded-lg flex items-center gap-2.5 text-xs font-mono font-medium transition-all cursor-pointer ${
            currentPage === "settings"
              ? "bg-[#102E4A] text-[#22AFFF] border border-[#22AFFF]/50 font-bold"
              : "text-[#8FA4B8] hover:text-[#F4F7FA] hover:bg-[#101F30]"
          }`}
        >
          <Settings className={`w-4 h-4 ${currentPage === "settings" ? 'text-[#22AFFF]' : 'text-[#60758A]'}`} />
          <span>Settings</span>
        </button>
      </div>

      {/* Bottom Subsystem Status Snapshot */}
      <div className="p-3 bg-[#0D1B2A] border border-[#1B344B] rounded-lg font-mono">
        <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-[#60758A] mb-1">
          <ShieldCheck className="w-3 h-3 text-[#22D88A]" />
          <span>AeroPiston-4X</span>
        </div>
        <div className="text-[11px] font-bold text-[#F4F7FA]">Turbocharged 1.35L</div>
        <div className="text-[10px] text-[#8FA4B8] mt-0.5">Boxer-4 Direct-Drive</div>
      </div>
    </aside>
  );
}
