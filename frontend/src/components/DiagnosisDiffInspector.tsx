'use client';

import React from 'react';
import { Sparkles, Code2, Terminal, CheckCircle, ArrowRight, ShieldCheck } from 'lucide-react';
import { TelemetryFrame } from '@/hooks/useTelemetryStream';

interface DiagnosisDiffInspectorProps {
  latestEvent?: TelemetryFrame | null;
  frames?: TelemetryFrame[];
}

export function DiagnosisDiffInspector({ latestEvent, frames = [] }: DiagnosisDiffInspectorProps) {
  // Extract diagnosis payload if available
  const diagnoserEvent = frames.find((f) => f.node_id === 'diagnoser' && f.status === 'DIAGNOSED');
  const proposal = diagnoserEvent?.payload;

  return (
    <div className="bg-[#0D131F] border border-slate-800 rounded-lg p-4 flex flex-col h-full overflow-hidden text-slate-200 gap-3">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-violet-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200">
            AI Diagnosis & Diff Inspector
          </h3>
        </div>
        <span className="text-[10px] font-mono text-violet-400 bg-violet-950/40 px-2 py-0.5 rounded border border-violet-800">
          GEMINI 3.1 PRO / 3.7 FLASH
        </span>
      </div>

      {/* Diagnosis Explanation Card */}
      <div className="bg-slate-950/70 border border-slate-800/90 rounded-md p-3">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
          Root Cause Diagnosis
        </span>
        <p className="text-xs text-slate-200 font-sans leading-relaxed">
          {proposal?.diagnosis || latestEvent?.message || 'Awaiting pipeline execution or failure trigger...'}
        </p>
      </div>

      {/* Selector Diff Card */}
      <div className="bg-slate-950/70 border border-slate-800/90 rounded-md p-3 flex flex-col gap-2">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
          Selector Transformation Diff
        </span>
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 font-mono text-xs">
          <div className="bg-rose-950/30 border border-rose-900/50 p-2 rounded text-rose-300 truncate">
            <span className="text-[9px] text-rose-500 block">BROKEN OLD</span>
            .cve-id
          </div>
          <ArrowRight className="w-4 h-4 text-slate-600 shrink-0" />
          <div className="bg-emerald-950/30 border border-emerald-900/50 p-2 rounded text-emerald-300 truncate">
            <span className="text-[9px] text-emerald-500 block">REPAIRED NEW</span>
            {proposal?.proposed_selector || '.vulnerability-badge'}
          </div>
        </div>
      </div>

      {/* Generated Natural Language Heal Prompt */}
      {proposal?.repair_prompt && (
        <div className="bg-slate-950/70 border border-sky-900/40 rounded-md p-3">
          <span className="text-[10px] font-mono text-sky-400 uppercase tracking-wider block mb-1">
            CLI Heal Prompt (bdata scraper heal)
          </span>
          <code className="text-xs text-sky-200 font-mono block bg-slate-900/80 p-2 rounded border border-slate-800 break-words">
            "{proposal.repair_prompt}"
          </code>
        </div>
      )}

      {/* Live Telemetry Log Stream */}
      <div className="flex-1 flex flex-col overflow-hidden bg-slate-950 border border-slate-900 rounded-md p-2.5">
        <div className="flex items-center gap-1.5 mb-1.5 pb-1 border-b border-slate-900 text-slate-400 font-mono text-[10px]">
          <Terminal className="w-3 h-3 text-slate-500" />
          <span>REAL-TIME PIPELINE LOGS</span>
        </div>
        <div className="flex-1 overflow-y-auto space-y-1.5 font-mono text-[11px] custom-scrollbar pr-1">
          {frames.length === 0 ? (
            <div className="text-slate-600 text-center py-6">Listening for pipeline events...</div>
          ) : (
            frames.map((f, i) => (
              <div key={i} className="flex items-start gap-2 leading-tight">
                <span className="text-slate-600 shrink-0">[{f.node_id || 'sys'}]</span>
                <span className={`text-[10px] uppercase font-bold shrink-0 ${
                  f.status === 'HEALTHY' || f.status === 'VALIDATED' || f.status === 'APPROVED' ? 'text-emerald-400' :
                  f.status === 'BROKEN' || f.status === 'FAILED' ? 'text-rose-400' : 'text-sky-400'
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
