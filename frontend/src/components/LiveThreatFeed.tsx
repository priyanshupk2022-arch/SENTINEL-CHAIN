'use client';

import React from 'react';
import { ShieldAlert, Terminal, AlertCircle, Clock, ExternalLink, Database } from 'lucide-react';

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
      return 'bg-rose-950/60 text-rose-400 border-rose-800/80';
    } else if (sev === 'HIGH') {
      return 'bg-amber-950/60 text-amber-400 border-amber-800/80';
    } else if (sev === 'MEDIUM') {
      return 'bg-yellow-950/60 text-yellow-400 border-yellow-800/80';
    } else {
      return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="bg-[#0D131F] border border-slate-800 rounded-lg p-4 flex flex-col h-full overflow-hidden text-slate-200">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3 shrink-0">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-sky-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200">
            Live Threat Stream ({threats.length})
          </h3>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800">
          SQLITE WAL SYNCED
        </span>
      </div>

      {/* Threats List */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-2.5 custom-scrollbar">
        {threats.length === 0 ? (
          <div className="h-40 flex flex-col items-center justify-center text-slate-500 font-mono text-xs border border-dashed border-slate-800 rounded-md">
            <AlertCircle className="w-6 h-6 mb-2 text-slate-600" />
            <span>No threat records harvested yet.</span>
            <span className="text-[11px] text-slate-600 mt-1">Click "RUN PIPELINE" to trigger scraper.</span>
          </div>
        ) : (
          threats.map((t, idx) => (
            <div
              key={t.cve_id || idx}
              className="bg-slate-950/60 border border-slate-800/90 rounded-md p-3 hover:border-slate-700 transition-all"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-mono font-bold text-sky-400 text-xs tracking-wide">
                  {t.cve_id}
                </span>
                <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${getSeverityBadge(t.severity)}`}>
                  {t.severity}
                </span>
              </div>

              <h4 className="text-xs font-medium text-slate-200 mb-2 font-sans line-clamp-2 leading-relaxed">
                {t.title || 'Security vulnerability patch advisory'}
              </h4>

              <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-1.5 border-t border-slate-900">
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
