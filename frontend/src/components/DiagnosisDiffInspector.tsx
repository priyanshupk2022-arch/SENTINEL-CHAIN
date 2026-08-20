'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Sparkles, Terminal, ArrowRight, CheckCircle2, ShieldAlert, Code2, Copy, Check } from 'lucide-react';
import { TelemetryFrame } from '@/hooks/useTelemetryStream';
import confetti from 'canvas-confetti';

interface DiagnosisDiffInspectorProps {
  latestEvent?: TelemetryFrame | null;
  frames?: TelemetryFrame[];
}

export function DiagnosisDiffInspector({ latestEvent, frames = [] }: DiagnosisDiffInspectorProps) {
  const diagnoserEvent = frames.find((f) => f.node_id === 'diagnoser' && f.status === 'DIAGNOSED');
  const proposal = diagnoserEvent?.payload;
  const [copied, setCopied] = useState(false);
  const [flashGreen, setFlashGreen] = useState(false);
  const prevStatusRef = useRef<string | null>(null);

  // Trigger confetti and green flash when a self-healing event completes
  useEffect(() => {
    if (latestEvent?.node_id === 'verifier' && latestEvent?.status === 'HEALTHY' && prevStatusRef.current !== 'HEALTHY') {
      setFlashGreen(true);
      try {
        confetti({
          particleCount: 40,
          spread: 60,
          origin: { y: 0.85, x: 0.85 },
          colors: ['#10B981', '#6366F1', '#38BDF8']
        });
      } catch (e) {
        // confetti fallback
      }
      const timer = setTimeout(() => setFlashGreen(false), 1400);
      return () => clearTimeout(timer);
    }
    prevStatusRef.current = latestEvent?.status || null;
  }, [latestEvent]);

  const handleCopyPrompt = () => {
    if (proposal?.repair_prompt) {
      navigator.clipboard.writeText(proposal.repair_prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-[#121215] border border-zinc-800/60 rounded-[12px] p-5 flex flex-col h-full overflow-hidden text-slate-200 gap-4 shadow-[0_8px_30px_rgb(0,0,0,0.4)]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800/40 pb-3 shrink-0">
        <div className="flex items-center gap-2.5">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#F4F4F5]">
            Value Diff & Diagnostic Inspector
          </h3>
        </div>
        <span className="text-[10px] font-mono text-indigo-300 bg-indigo-950/40 px-2 py-0.5 rounded-[4px] border border-indigo-800/60 font-semibold">
          GEMINI 3.7 FLASH
        </span>
      </div>

      {/* Root Cause Diagnosis Box */}
      <div className="bg-[#18181B] border border-zinc-800/60 rounded-[8px] p-3.5">
        <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block mb-1">
          Root Cause Diagnosis
        </span>
        <p className="text-xs text-zinc-200 font-sans leading-relaxed">
          {proposal?.diagnosis || latestEvent?.message || 'Awaiting pipeline execution or failure trigger...'}
        </p>
      </div>

      {/* Split-Screen Code Diff Remediator */}
      <div className="bg-[#18181B] border border-zinc-800/60 rounded-[8px] p-3.5 flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block">
            Split-Screen Selector Diff
          </span>
          <span className="text-[10px] font-mono text-zinc-500">
            YAML / Py Remediation
          </span>
        </div>

        {/* Diff Code Container */}
        <div className={`p-3 rounded-[6px] bg-[#09090B] border font-mono text-xs space-y-1.5 transition-all duration-300 ${
          flashGreen ? 'border-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.3)]' : 'border-zinc-800/80'
        }`}>
          <div className="text-rose-400 bg-rose-950/30 px-2 py-0.5 rounded-[4px] border-l-2 border-rose-500/80 truncate">
            --- Scraper_Run_190.py (Failed)
          </div>
          <div className="text-rose-300/80 pl-2 text-[11px]">
            - select = select_raw_div(".cve-id")
          </div>

          <div className="text-emerald-400 bg-emerald-950/30 px-2 py-0.5 rounded-[4px] border-l-2 border-emerald-500/80 truncate mt-2">
            +++ Scraper_Run_190_Remediated.py (Healed)
          </div>
          <div className="text-emerald-300 pl-2 text-[11px] font-semibold">
            + select = select_llm_selector("{proposal?.proposed_selector || '.vulnerability-badge'}")
          </div>
        </div>
      </div>

      {/* CLI Heal Prompt */}
      {proposal?.repair_prompt && (
        <div className="bg-[#18181B] border border-indigo-900/30 rounded-[8px] p-3.5">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-mono text-indigo-400 uppercase tracking-wider block">
              CLI HEAL INSTRUCTION
            </span>
            <button
              onClick={handleCopyPrompt}
              className="flex items-center gap-1 text-[10px] font-mono text-zinc-400 hover:text-white cursor-pointer"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? 'COPIED' : 'COPY'}</span>
            </button>
          </div>
          <code className="text-xs text-indigo-200 font-mono block bg-[#09090B] p-2 rounded-[4px] border border-zinc-800/80 break-words">
            bdata scraper heal -- "{proposal.repair_prompt}"
          </code>
        </div>
      )}

      {/* Real-time Pipeline Logs */}
      <div className="flex-1 flex flex-col overflow-hidden bg-[#09090B] border border-zinc-800/60 rounded-[8px] p-3">
        <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-zinc-800/40 text-zinc-400 font-mono text-[10px]">
          <Terminal className="w-3 h-3 text-indigo-400" />
          <span>REAL-TIME PIPELINE TELEMETRY LOGS</span>
        </div>
        <div className="flex-1 overflow-y-auto space-y-1.5 font-mono text-[11px] pr-1">
          {frames.length === 0 ? (
            <div className="text-zinc-600 text-center py-6">Listening for live pipeline events...</div>
          ) : (
            frames.map((f, i) => (
              <div key={i} className="flex items-start gap-2 leading-tight">
                <span className="text-zinc-500 shrink-0">[{f.node_id || 'sys'}]</span>
                <span className={`text-[10px] uppercase font-semibold shrink-0 ${
                  f.status === 'HEALTHY' || f.status === 'VALIDATED' || f.status === 'APPROVED' ? 'text-emerald-400' :
                  f.status === 'BROKEN' || f.status === 'FAILED' ? 'text-rose-400' : 'text-indigo-400'
                }`}>
                  {f.status}
                </span>
                <span className="text-zinc-300 truncate">{f.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
