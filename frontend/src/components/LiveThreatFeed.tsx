'use client';

import React from 'react';
import { Database, AlertCircle, Clock, ExternalLink } from 'lucide-react';

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
      return 'bg-slate-900 text-slate-300 border-white/[0.08]';
    }
  };

  return (
    <div className="bg-[#0F131C] border border-white/[0.07] rounded-[12px] p-5 flex flex-col h-full overflow-hidden text-slate-200 shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-white/[0.07] pb-3 mb-3 shrink-0">
        <div className="flex items-center gap-2.5">
          <Database className="w-4 h-4 text-emerald-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200">
            Live Threat Stream ({threats.length})
          </h3>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded-[6px] border border-emerald-800/60">
          SQLITE WAL SYNCED
        </span>
      </div>

      {/* Threats List / Skeletons */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-2.5">
        {isLoading && threats.length === 0 ? (
          /* Skeleton Screen Loader */
          <div className="space-y-2.5">
            {[1, 2, 3].map((n) => (
              <div key={n} className="bg-[#080B11]/60 border border-white/[0.06] rounded-[8px] p-3.5 space-y-2">
                <div className="flex justify-between items-center">
                  <div className="h-4 w-28 rounded-[4px] skeleton-shimmer" />
                  <div className="h-4 w-14 rounded-[4px] skeleton-shimmer" />
                </div>
                <div className="h-3.5 w-full rounded-[4px] skeleton-shimmer" />
                <div className="h-3 w-1/2 rounded-[4px] skeleton-shimmer" />
              </div>
            ))}
          </div>
        ) : threats.length === 0 ? (
          <div className="h-44 flex flex-col items-center justify-center text-slate-500 font-mono text-xs border border-dashed border-white/[0.08] rounded-[8px] p-6 text-center">
            <AlertCircle className="w-6 h-6 mb-2 text-slate-600" />
            <span className="text-slate-300 font-medium">No threat records harvested yet.</span>
            <span className="text-[11px] text-slate-500 mt-1">Click "RUN PIPELINE" above to trigger autonomous extraction.</span>
          </div>
        ) : (
          threats.map((t, idx) => (
            <div
              key={t.cve_id || idx}
              className="bg-[#080B11]/60 border border-white/[0.06] rounded-[8px] p-3.5 hover:border-white/[0.14] hover:bg-[#121620] transition-all duration-150"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono font-semibold text-emerald-400 text-xs tracking-wide">
                  {t.cve_id}
                </span>
                <span className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded-[6px] border ${getSeverityBadge(t.severity)}`}>
                  {t.severity}
                </span>
              </div>

              <h4 className="text-xs font-normal text-slate-200 mb-2 font-sans line-clamp-2 leading-relaxed">
                {t.title || 'Security vulnerability advisory'}
              </h4>

              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-2 border-t border-white/[0.05]">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  {t.published_date || '2026-08-15'}
                </span>
                <span className="text-slate-500">{t.source || 'Exploit-DB'}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
