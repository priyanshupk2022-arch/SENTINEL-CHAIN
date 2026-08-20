'use client';

import React from 'react';
import { Sparkles, Terminal, ArrowRight, CheckCircle2, ShieldAlert } from 'lucide-react';
import { TelemetryFrame } from '@/hooks/useTelemetryStream';

interface DiagnosisDiffInspectorProps {
  latestEvent?: TelemetryFrame | null;
  frames?: TelemetryFrame[];
}

export function DiagnosisDiffInspector({ latestEvent, frames = [] }: DiagnosisDiffInspectorProps) {
  const diagnoserEvent = frames.find((f) => f.node_id === 'diagnoser' && f.status === 'DIAGNOSED');
  const proposal = diagnoserEvent?.payload;

  return (
    <div className="bg-[#0F131C] border border-white/[0.07] rounded-[12px] p-5 flex flex-col h-full overflow-hidden text-slate-200 gap-3.5 shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.07] pb-3 shrink-0">
        <div className="flex items-center gap-2.5">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200">
            AI Diagnosis & Diff Inspector
          </h3>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded-[6px] border border-emerald-800/60 font-medium">
          GEMINI 3.7 FLASH
        </span>
      </div>

      {/* Diagnosis Explanation Box */}
      <div className="bg-[#080B11]/60 border border-white/[0.06] rounded-[8px] p-3.5">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
          Root Cause Diagnosis
        </span>
        <p className="text-xs text-slate-200 font-sans leading-relaxed">
          {proposal?.diagnosis || latestEvent?.message || 'Awaiting pipeline execution or failure trigger...'}
        </p>
      </div>

      {/* Selector Transformation Diff */}
      <div className="bg-[#080B11]/60 border border-white/[0.06] rounded-[8px] p-3.5 flex flex-col gap-2">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
          Selector Transformation Diff
        </span>
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2.5 font-mono text-xs">
          <div className="bg-rose-950/30 border border-rose-900/40 p-2.5 rounded-[6px] text-rose-300 truncate">
            <span className="text-[9px] text-rose-500 block font-medium">BROKEN OLD</span>
            .cve-id
          </div>
          <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />
          <div className="bg-emerald-950/30 border border-emerald-900/40 p-2.5 rounded-[6px] text-emerald-300 truncate">
            <span className="text-[9px] text-emerald-500 block font-medium">REPAIRED NEW</span>
            {proposal?.proposed_selector || '.vulnerability-badge'}
          </div>
        </div>
      </div>

      {/* CLI Heal Prompt */}
      {proposal?.repair_prompt && (
        <div className="bg-[#080B11]/60 border border-emerald-900/30 rounded-[8px] p-3.5">
          <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider block mb-1">
            CLI Heal Prompt (bdata scraper heal)
          </span>
          <code className="text-xs text-emerald-200 font-mono block bg-[#080B11] p-2 rounded-[6px] border border-white/[0.06] break-words">
            "{proposal.repair_prompt}"
          </code>
        </div>
      )}

      {/* Real-time Pipeline Logs */}
      <div className="flex-1 flex flex-col overflow-hidden bg-[#080B11] border border-white/[0.06] rounded-[8px] p-3">
        <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-white/[0.05] text-slate-400 font-mono text-[10px]">
          <Terminal className="w-3 h-3 text-slate-500" />
          <span>REAL-TIME PIPELINE LOGS</span>
        </div>
        <div className="flex-1 overflow-y-auto space-y-1.5 font-mono text-[11px] pr-1">
          {frames.length === 0 ? (
            <div className="text-slate-600 text-center py-6">Listening for pipeline events...</div>
          ) : (
            frames.map((f, i) => (
              <div key={i} className="flex items-start gap-2 leading-tight">
                <span className="text-slate-600 shrink-0">[{f.node_id || 'sys'}]</span>
                <span className={`text-[10px] uppercase font-semibold shrink-0 ${
                  f.status === 'HEALTHY' || f.status === 'VALIDATED' || f.status === 'APPROVED' ? 'text-emerald-400' :
                  f.status === 'BROKEN' || f.status === 'FAILED' ? 'text-rose-400' : 'text-slate-300'
                }`}>
                  {f.status}
                </span>
                <span className="text-slate-300 truncate">{f.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
