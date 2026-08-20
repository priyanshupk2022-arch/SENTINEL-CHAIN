'use client';

import React from 'react';
import { Database, AlertCircle, Clock, ExternalLink, ShieldCheck } from 'lucide-react';

export interface ThreatItem {
  id?: number;
  cve_id: string;
  title: string;
  severity: string;
  published_date?: string;
  url?: string;
  source?: string;
  timestamp?: string;
}

interface LiveThreatFeedProps {
  threats: ThreatItem[];
  isLoading?: boolean;
}

const SkeletonRow = () => (
  <div className="p-3.5 rounded-[8px] bg-[#18181B]/50 border border-zinc-800/40 space-y-2.5 animate-pulse">
    <div className="flex justify-between items-center">
      <div className="h-3 w-28 rounded bg-zinc-800" />
      <div className="h-4 w-12 rounded bg-zinc-800" />
    </div>
    <div className="h-3 w-full rounded bg-zinc-800" />
    <div className="h-2.5 w-1/3 rounded bg-zinc-800" />
  </div>
);

export function LiveThreatFeed({ threats, isLoading = false }: LiveThreatFeedProps) {
  const getSeverityBadge = (severity: string) => {
    const sev = severity.toUpperCase();
    if (sev === 'CRITICAL') {
      return 'bg-rose-950/40 text-rose-400 border-rose-800/60';
    } else if (sev === 'HIGH') {
      return 'bg-amber-950/40 text-amber-400 border-amber-800/60';
    } else if (sev === 'MEDIUM') {
      return 'bg-yellow-950/40 text-yellow-400 border-yellow-800/60';
    } else {
      return 'bg-zinc-800 text-zinc-300 border-zinc-700';
    }
  };

  return (
    <div className="bg-[#121215] border border-zinc-800/60 rounded-[12px] p-5 flex flex-col h-full overflow-hidden text-slate-200 shadow-[0_8px_30px_rgb(0,0,0,0.4)]">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-zinc-800/40 pb-3 mb-3 shrink-0">
        <div className="flex items-center gap-2.5">
          <Database className="w-4 h-4 text-emerald-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#F4F4F5]">
            Live Threat Stream ({threats.length})
          </h3>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded-[4px] border border-emerald-800/60 font-semibold">
          SQLITE WAL PERSISTED
        </span>
      </div>

      {/* Threats List / Skeletons */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-2.5">
        {isLoading && threats.length === 0 ? (
          <div className="space-y-2.5">
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
            <SkeletonRow />
          </div>
        ) : threats.length === 0 ? (
          <div className="h-36 flex flex-col items-center justify-center text-zinc-500 font-mono text-xs border border-dashed border-zinc-800 rounded-[8px] p-6 text-center">
            <AlertCircle className="w-6 h-6 mb-2 text-zinc-600" />
            <span className="text-zinc-300 font-medium">No threat records harvested yet.</span>
            <span className="text-[11px] text-zinc-500 mt-1">Click "RUN PIPELINE" or "INJECT SABOTAGE" to trigger.</span>
          </div>
        ) : (
          threats.map((t, idx) => (
            <div
              key={t.cve_id || idx}
              className="bg-[#18181B] border border-zinc-800/60 rounded-[8px] p-3.5 hover:border-zinc-700 transition-all duration-150 animate-in fade-in slide-in-from-top-1"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono font-bold text-indigo-400 text-xs tracking-wide">
                  {t.cve_id}
                </span>
                <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-[4px] border ${getSeverityBadge(t.severity)}`}>
                  {t.severity}
                </span>
              </div>

              <h4 className="text-xs font-normal text-zinc-200 mb-2 font-sans line-clamp-2 leading-relaxed">
                {t.title || 'Security vulnerability advisory'}
              </h4>

              <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 pt-2 border-t border-zinc-900">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-zinc-500" />
                  {t.published_date || '2026-08-15'}
                </span>
                <span className="text-zinc-500">{t.source || 'Exploit-DB'}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
