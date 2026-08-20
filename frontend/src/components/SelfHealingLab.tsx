'use client';

import React from 'react';
import { Sparkles, ShieldAlert, CheckCircle2, ArrowRight, RefreshCw, Zap, Cpu } from 'lucide-react';

interface SelfHealingLabProps {
  isHealing: boolean;
  onSimulateBreakAndHeal: () => void;
  latestDiagnosis?: any;
}

export function SelfHealingLab({
  isHealing,
  onSimulateBreakAndHeal,
  latestDiagnosis
}: SelfHealingLabProps) {
  const diagnosis = latestDiagnosis || {
    brokenSelector: 'table.cve-grid tr td.cve-id',
    healedSelector: 'div.exploit-card span.cve-tag',
    reason: 'Target website changed HTML table into responsive article card grid',
    status: 'HEALTHY'
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-5 h-5 rounded-full bg-purple-600 text-white font-mono text-xs flex items-center justify-center font-bold">
              3
            </span>
            <h2 className="text-base font-bold text-slate-900 font-mono tracking-tight">
              Real-World Self-Healing Engine (AI + Scraper Studio)
            </h2>
          </div>
          <p className="text-xs text-slate-500 font-sans">
            When target websites change their layout, Gemini 3.7 Flash diagnoses the DOM and executes <code className="bg-slate-100 px-1 py-0.5 rounded text-indigo-700 font-mono">bdata scraper heal</code> to restore data extraction in-place.
          </p>
        </div>

        <button
          onClick={onSimulateBreakAndHeal}
          disabled={isHealing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-xs font-bold text-white bg-purple-600 hover:bg-purple-700 active:scale-[0.98] transition-all shadow-sm cursor-pointer disabled:opacity-50"
        >
          {isHealing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>DIAGNOSING & HEALING...</span>
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 fill-current" />
              <span>SIMULATE WEBSITE BREAK & HEAL</span>
            </>
          )}
        </button>
      </div>

      {/* Before / After Selector Diff Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
        {/* Broken Selector (Red) */}
        <div className="p-4 rounded-lg bg-rose-50/70 border border-rose-200 space-y-2">
          <div className="flex items-center justify-between text-rose-800 font-semibold text-[11px]">
            <span className="flex items-center gap-1.5">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              MUTATED / BROKEN SELECTOR
            </span>
            <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 border border-rose-300 text-[10px]">
              FAILED
            </span>
          </div>
          <div className="p-2.5 rounded bg-white border border-rose-200 text-rose-900 font-mono text-xs">
            <code>{diagnosis.brokenSelector || 'table.cve-grid tr td.cve-id'}</code>
          </div>
          <p className="text-[11px] text-rose-700 font-sans">
            Target website modified container elements, resulting in 0 matches.
          </p>
        </div>

        {/* Repaired Selector (Green) */}
        <div className="p-4 rounded-lg bg-emerald-50/70 border border-emerald-200 space-y-2">
          <div className="flex items-center justify-between text-emerald-800 font-semibold text-[11px]">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              AI REPAIRED SELECTOR
            </span>
            <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 border border-emerald-300 text-[10px]">
              BDATA HEALED
            </span>
          </div>
          <div className="p-2.5 rounded bg-white border border-emerald-200 text-emerald-900 font-mono text-xs">
            <code>{diagnosis.healedSelector || 'div.exploit-card span.cve-tag'}</code>
          </div>
          <p className="text-[11px] text-emerald-700 font-sans">
            Gemini 3.7 Flash mapped AOM tree $\rightarrow$ executed <code className="font-mono font-semibold">bdata scraper heal</code>.
          </p>
        </div>
      </div>

      {/* Workflow Step Indicators */}
      <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-700">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-600" />
          <span className="font-semibold text-slate-900">Autonomous Self-Healing Pipeline:</span>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          <span className="px-2 py-1 rounded bg-white border border-slate-300">1. Detect Failure</span>
          <ArrowRight className="w-3 h-3 text-slate-400" />
          <span className="px-2 py-1 rounded bg-white border border-slate-300">2. Inspect AOM Tree</span>
          <ArrowRight className="w-3 h-3 text-slate-400" />
          <span className="px-2 py-1 rounded bg-white border border-slate-300">3. Gemini 3.7 Diagnosis</span>
          <ArrowRight className="w-3 h-3 text-slate-400" />
          <span className="px-2 py-1 rounded bg-emerald-50 border border-emerald-300 text-emerald-800 font-semibold">
            4. bdata scraper heal
          </span>
        </div>
      </div>
    </div>
  );
}
