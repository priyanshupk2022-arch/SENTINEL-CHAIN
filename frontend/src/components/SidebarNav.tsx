'use client';

import React from 'react';
import { Database, Workflow, Shield, Terminal, Settings, Activity, Flame, LayoutDashboard, Globe } from 'lucide-react';

interface SidebarNavProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  totalThreats?: number;
}

export function SidebarNav({ activeTab, onSelectTab, totalThreats = 0 }: SidebarNavProps) {
  const navItems = [
    { id: 'harvests', label: 'HARVESTS', icon: Database, badge: `${totalThreats}` },
    { id: 'pipelines', label: 'PIPELINES', icon: Workflow, badge: 'ACTIVE' },
    { id: 'proxies', label: 'PROXIES', icon: Globe, badge: 'BRIGHT DATA' },
    { id: 'logs', label: 'SYSTEM LOGS', icon: Terminal },
    { id: 'chaos', label: 'CHAOS PROXY', icon: Flame, badge: 'TESTER' },
    { id: 'settings', label: 'SETTINGS', icon: Settings }
  ];

  return (
    <aside className="w-full h-full bg-[#121215] border-r border-zinc-800/40 p-4 flex flex-col justify-between select-none">
      <div className="space-y-6">
        {/* Navigation Items */}
        <div className="space-y-1">
          <span className="text-[10px] font-mono font-semibold tracking-wider text-zinc-500 uppercase px-3 block mb-2">
            SECOPS NAVIGATION
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
          SQLite WAL Active (Local Concurrency)
        </div>
      </div>
    </aside>
  );
}
