'use client';

import React, { useState } from 'react';
import { Shield, Zap, RefreshCw, AlertTriangle, CheckCircle, Flame } from 'lucide-react';

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
    <header className="flex h-14 items-center justify-between px-5 border-b border-slate-800 bg-[#090D16] shrink-0 text-white select-none">
      {/* Brand & Connection Indicator */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold tracking-wider text-white text-sm">
                SENTINEL-CHAIN
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30">
                v1.0.0
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono">
              AUTONOMOUS THREAT INTELLIGENCE // SELF-HEALING ENGINE
            </p>
          </div>
        </div>

        {/* Live SSE Pulse */}
        <div className="flex items-center gap-2 px-3 py-1 rounded bg-slate-900 border border-slate-800 ml-4">
          <div className="relative flex items-center justify-center w-2.5 h-2.5">
            {connectionStatus === 'LIVE' && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            )}
            <span className={`relative inline-flex rounded-full h-2 w-2 ${
              connectionStatus === 'LIVE' ? 'bg-emerald-400' :
              connectionStatus === 'CONNECTING' ? 'bg-amber-400' : 'bg-rose-500'
            }`}></span>
          </div>
          <span className="font-mono text-[11px] text-slate-300">
            SSE: <span className={connectionStatus === 'LIVE' ? 'text-emerald-400 font-semibold' : 'text-slate-400'}>{connectionStatus}</span>
          </span>
        </div>
      </div>

      {/* Metrics Ticker */}
      <div className="hidden md:flex items-center gap-6 font-mono text-xs text-slate-300">
        <div className="flex items-center gap-2">
          <span className="text-slate-500">ACTIVE COLLECTOR:</span>
          <span className="text-sky-400 font-semibold bg-sky-950/40 px-2 py-0.5 rounded border border-sky-800/40">
            c_sentinel_cve_threats
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-500">CHAOS STATE:</span>
          <span className={`px-2 py-0.5 rounded border uppercase text-[11px] font-semibold ${
            activeChaosMode === 'clean' 
              ? 'text-emerald-400 bg-emerald-950/30 border-emerald-800/40' 
              : 'text-amber-400 bg-amber-950/30 border-amber-800/40 animate-pulse'
          }`}>
            {activeChaosMode}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-500">THREATS HARVESTED:</span>
          <span className="text-white font-bold bg-slate-800 px-2 py-0.5 rounded">
            {totalThreats}
          </span>
        </div>

        {lastRecoveryMs > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-slate-500">RECOVERY TIME:</span>
            <span className="text-emerald-400 font-semibold">
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
          className="flex items-center gap-2 px-4 py-2 rounded font-mono text-xs font-semibold bg-sky-500 text-slate-950 hover:bg-sky-400 active:scale-95 transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
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
