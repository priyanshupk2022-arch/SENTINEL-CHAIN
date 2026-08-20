'use client';

import React from 'react';
import { Shield, Zap, RefreshCw, Flame, Download, LayoutDashboard, Globe, ArrowLeft } from 'lucide-react';

interface TopHUDBarProps {
  connectionStatus?: 'LIVE' | 'OFFLINE' | 'CONNECTING';
  activeChaosMode?: string;
  totalThreats?: number;
  isTriggering?: boolean;
  onTriggerPipeline?: () => void;
  onInjectSabotage?: () => void;
  onExportCSV?: () => void;
  lastRecoveryMs?: number;
  currentView?: 'cockpit' | 'landing';
  onToggleView?: () => void;
}

export function TopHUDBar({
  connectionStatus = 'OFFLINE',
  activeChaosMode = 'clean',
  totalThreats = 0,
  isTriggering = false,
  onTriggerPipeline,
  onInjectSabotage,
  onExportCSV,
  lastRecoveryMs = 0,
  currentView = 'cockpit',
  onToggleView
}: TopHUDBarProps) {
  return (
    <header className="flex h-14 items-center justify-between px-5 border-b border-zinc-800/60 bg-[#09090B] shrink-0 text-slate-100 select-none z-30 shadow-md">
      {/* Brand & Connection Indicator */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-[8px] bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold tracking-wider text-[#F4F4F5] text-sm">
                SENTINEL-CHAIN
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-[4px] bg-indigo-950/40 text-indigo-300 border border-indigo-800/60 font-semibold">
                v1.0.0
              </span>
            </div>
            <p className="text-[10px] text-zinc-400 font-mono tracking-tight">
              AUTONOMOUS THREAT INTELLIGENCE // SELF-HEALING ENGINE
            </p>
          </div>
        </div>

        {/* Live SSE Pulse */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-[4px] bg-[#121215] border border-zinc-800/60 ml-2">
          <div className="relative flex items-center justify-center w-2 h-2">
            {connectionStatus === 'LIVE' && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60"></span>
            )}
            <span className={`relative inline-flex rounded-full h-1.5 w-1.5 ${
              connectionStatus === 'LIVE' ? 'bg-emerald-400' :
              connectionStatus === 'CONNECTING' ? 'bg-amber-400' : 'bg-rose-500'
            }`}></span>
          </div>
          <span className="font-mono text-[11px] text-zinc-300">
            SSE: <span className={connectionStatus === 'LIVE' ? 'text-emerald-400 font-semibold' : 'text-zinc-500'}>{connectionStatus}</span>
          </span>
        </div>
      </div>

      {/* Metrics Ticker */}
      <div className="hidden lg:flex items-center gap-6 font-mono text-xs text-zinc-300">
        <div className="flex items-center gap-2">
          <span className="text-zinc-500 text-[11px]">COLLECTOR:</span>
          <span className="text-zinc-200 font-medium bg-[#121215] px-2 py-0.5 rounded-[4px] border border-zinc-800">
            c_sentinel_cve_threats
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-zinc-500 text-[11px]">CHAOS STATE:</span>
          <span className={`px-2 py-0.5 rounded-[4px] border uppercase text-[11px] font-semibold ${
            activeChaosMode === 'clean' 
              ? 'text-emerald-400 bg-emerald-950/30 border-emerald-800/60' 
              : 'text-amber-400 bg-amber-950/30 border-amber-800/60 animate-pulse'
          }`}>
            {activeChaosMode}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-zinc-500 text-[11px]">THREATS HARVESTED:</span>
          <span className="text-emerald-400 font-bold bg-[#121215] px-2 py-0.5 rounded-[4px] border border-zinc-800">
            {totalThreats}
          </span>
        </div>

        {lastRecoveryMs > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-zinc-500 text-[11px]">RECOVERY LATENCY:</span>
            <span className="text-emerald-400 font-semibold">
              {(lastRecoveryMs / 1000).toFixed(2)}s
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {/* Toggle Landing / Cockpit */}
        {onToggleView && (
          <button
            onClick={onToggleView}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] font-mono text-xs text-zinc-300 bg-[#121215] border border-zinc-800 hover:text-white hover:bg-[#18181B] transition-all cursor-pointer"
          >
            {currentView === 'cockpit' ? (
              <>
                <Globe className="w-3.5 h-3.5 text-indigo-400" />
                <span>LANDING PAGE</span>
              </>
            ) : (
              <>
                <LayoutDashboard className="w-3.5 h-3.5 text-emerald-400" />
                <span>OPEN COCKPIT</span>
              </>
            )}
          </button>
        )}

        {/* Export CSV */}
        {onExportCSV && (
          <button
            onClick={onExportCSV}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] font-mono text-xs text-zinc-300 bg-[#121215] border border-zinc-800 hover:text-white hover:bg-[#18181B] transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>EXPORT CSV</span>
          </button>
        )}

        {/* Primary Sabotage Ignition Button for Hackathon Judge (Leverage Point) */}
        {onInjectSabotage && (
          <button
            onClick={onInjectSabotage}
            disabled={isTriggering}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-[6px] font-mono text-xs font-semibold bg-rose-950/40 border border-rose-800/80 text-rose-300 hover:bg-rose-900/60 hover:text-white active:scale-[0.98] transition-all shadow-[0_0_15px_rgba(239,68,68,0.2)] disabled:opacity-50 cursor-pointer"
          >
            <Flame className="w-3.5 h-3.5 text-rose-400" />
            <span>INJECT SABOTAGE</span>
          </button>
        )}

        {/* Action Trigger Button */}
        {onTriggerPipeline && (
          <button
            onClick={onTriggerPipeline}
            disabled={isTriggering}
            className="flex items-center gap-2 px-4 py-2 rounded-[8px] font-mono text-xs font-semibold bg-[#6366F1] text-white hover:bg-indigo-500 active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(99,102,241,0.25)] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isTriggering ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>EXECUTING...</span>
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5 fill-current" />
                <span>RUN PIPELINE</span>
              </>
            )}
          </button>
        )}
      </div>
    </header>
  );
}
