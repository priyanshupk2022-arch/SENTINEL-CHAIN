'use client';

import React from 'react';
import { Database, Workflow, Shield, Terminal, Settings, Activity, Flame, LayoutDashboard, Globe, Plus } from 'lucide-react';

interface SidebarNavProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  onOpenOnboarding?: () => void;
  totalTargets?: number;
  totalThreats?: number;
}

export function SidebarNav({
  activeTab,
  onSelectTab,
  onOpenOnboarding,
  totalTargets = 0,
  totalThreats = 0
}: SidebarNavProps) {
  const navItems = [
    { id: 'targets', label: 'TARGETS REGISTRY', icon: Globe, badge: `${totalTargets}` },
    { id: 'cockpit', label: 'MISSION CONTROL', icon: LayoutDashboard },
    { id: 'harvests', label: 'DATA HARVESTS', icon: Database, badge: `${totalThreats}` },
    { id: 'proxies', label: 'BRIGHT DATA PROXIES', icon: Shield, badge: 'ACTIVE' },
    { id: 'chaos', label: 'CHAOS SANDBOX', icon: Flame, badge: 'DEMO' },
    { id: 'logs', label: 'SYSTEM LOGS', icon: Terminal }
  ];

  return (
    <aside className="w-full h-full bg-[#121215] border-r border-zinc-800/40 p-4 flex flex-col justify-between select-none">
      <div className="space-y-5">
        {/* Onboard Target Button */}
        {onOpenOnboarding && (
          <button
            onClick={onOpenOnboarding}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-[8px] font-mono text-xs font-semibold bg-[#6366F1] text-white hover:bg-indigo-500 active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(99,102,241,0.25)] cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>ONBOARD TARGET</span>
          </button>
        )}

        {/* Navigation Items */}
        <div className="space-y-1">
          <span className="text-[10px] font-mono font-semibold tracking-wider text-zinc-500 uppercase px-3 block mb-2">
            PLATFORM NAVIGATION
          </span>
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-[8px] font-mono text-xs transition-all duration-150 cursor-pointer ${
                  isActive
                    ? 'bg-[#6366F1] text-white font-semibold shadow-[0_0_20px_rgba(99,102,241,0.25)]'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-[#18181B]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <item.icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-zinc-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-[4px] font-mono ${
                    isActive ? 'bg-black/30 text-white' : 'bg-[#18181B] text-zinc-400 border border-zinc-800'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* System Status Footer Card */}
      <div className="p-3.5 rounded-[8px] bg-[#18181B] border border-zinc-800/60 font-mono text-xs">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-zinc-400 font-medium">CORE HEALTH</span>
          <span className="flex items-center gap-1 text-emerald-400 text-[10px] font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            99.98%
          </span>
        </div>
        <div className="text-[11px] text-zinc-500">
          SQLite WAL Active (Multi-Target)
        </div>
      </div>
    </aside>
  );
}
