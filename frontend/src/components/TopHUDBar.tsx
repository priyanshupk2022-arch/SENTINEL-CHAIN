'use client';

import React from 'react';
import { Shield, Zap, RefreshCw, Activity, Database, CheckCircle2 } from 'lucide-react';

interface TopHUDBarProps {
  connectionStatus?: 'LIVE' | 'OFFLINE' | 'CONNECTING';
  activeChaosMode?: string;
  totalThreats?: number;
  isTriggering?: boolean;
  onTriggerPipeline?: () => void;
  lastRecoveryMs?: number;
}

export function TopHUDBar({
  connectionStatus = 'OFFLINE',
  activeChaosMode = 'clean',
  totalThreats = 0,
  isTriggering = false,
  onTriggerPipeline,
  lastRecoveryMs = 0
}: TopHUDBarProps) {
  return (
    <header className="flex h-14 items-center justify-between px-6 border-b border-white/[0.07] bg-[#080B11] shrink-0 text-slate-100 select-none">
      {/* Brand & Connection Indicator */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-[8px] bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-semibold tracking-wider text-slate-100 text-sm">
                SENTINEL-CHAIN
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-[6px] bg-white/[0.05] text-slate-400 border border-white/[0.08]">
                v1.0.0
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono tracking-tight">
              AUTONOMOUS THREAT HARVESTER & SELF-HEALING ENGINE
            </p>
          </div>
        </div>

        {/* Live SSE Pulse */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-[6px] bg-[#0F131C] border border-white/[0.07] ml-3">
          <div className="relative flex items-center justify-center w-2 h-2">
            {connectionStatus === 'LIVE' && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60"></span>
            )}
            <span className={`relative inline-flex rounded-full h-1.5 w-1.5 ${
              connectionStatus === 'LIVE' ? 'bg-emerald-400' :
              connectionStatus === 'CONNECTING' ? 'bg-amber-400' : 'bg-rose-500'
            }`}></span>
          </div>
          <span className="font-mono text-[11px] text-slate-300">
            SSE: <span className={connectionStatus === 'LIVE' ? 'text-emerald-400 font-medium' : 'text-slate-400'}>{connectionStatus}</span>
          </span>
        </div>
      </div>

      {/* Metrics Ticker */}
      <div className="hidden lg:flex items-center gap-6 font-mono text-xs text-slate-300">
        <div className="flex items-center gap-2">
          <span className="text-slate-500 text-[11px]">COLLECTOR:</span>
          <span className="text-slate-200 font-medium bg-[#0F131C] px-2 py-0.5 rounded-[6px] border border-white/[0.07]">
            c_sentinel_cve_threats
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-500 text-[11px]">CHAOS STATE:</span>
          <span className={`px-2 py-0.5 rounded-[6px] border uppercase text-[11px] font-medium ${
            activeChaosMode === 'clean' 
              ? 'text-emerald-400 bg-emerald-950/30 border-emerald-800/40' 
              : 'text-amber-400 bg-amber-950/30 border-amber-800/40'
          }`}>
            {activeChaosMode}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-500 text-[11px]">THREATS HARVESTED:</span>
          <span className="text-emerald-400 font-bold bg-[#0F131C] px-2 py-0.5 rounded-[6px] border border-white/[0.07]">
            {totalThreats}
          </span>
        </div>

        {lastRecoveryMs > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-slate-500 text-[11px]">RECOVERY LATENCY:</span>
            <span className="text-emerald-400 font-medium">
              {(lastRecoveryMs / 1000).toFixed(2)}s
            </span>
          </div>
        )}
      </div>

      {/* Action Trigger Button */}
      <div className="flex items-center gap-3">
        <button
          onClick={onTriggerPipeline}
          disabled={isTriggering}
          className="flex items-center gap-2 px-4 py-2 rounded-[8px] font-mono text-xs font-semibold bg-emerald-500 text-slate-950 hover:bg-emerald-400 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {isTriggering ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>EXECUTING PIPELINE...</span>
            </>
          ) : (
            <>
              <Zap className="w-3.5 h-3.5 fill-current" />
              <span>RUN PIPELINE</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
}
