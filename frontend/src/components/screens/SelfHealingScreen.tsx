'use client';

import React from 'react';
import { Sparkles, ShieldAlert, CheckCircle2, ArrowLeft, RefreshCw, Zap, Cpu, Terminal, ArrowRight, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BrightDataTerminal } from '@/components/BrightDataTerminal';

interface SelfHealingScreenProps {
  isHealing: boolean;
  onSimulateBreakAndHeal: () => void;
  latestDiagnosis?: any;
  terminalLogs: any[];
  collectorId: string;
  targetUrl: string;
  onBack: () => void;
  onRestart: () => void;
}

export function SelfHealingScreen({
  isHealing,
  onSimulateBreakAndHeal,
  latestDiagnosis,
  terminalLogs,
  collectorId,
  targetUrl,
  onBack,
  onRestart
}: SelfHealingScreenProps) {
  const diagnosis = latestDiagnosis || {
    brokenSelector: 'table.cve-grid tr td.cve-id',
    healedSelector: 'div.exploit-card span.cve-tag',
    reason: 'Target security advisory feed redesigned from HTML table into responsive article card grid',
    status: 'HEALTHY'
  };

  return (
    <div className="flex-1 max-w-7xl mx-auto w-full p-6 lg:p-8 flex flex-col justify-between space-y-6 animate-in fade-in duration-200 font-sans">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-purple-600 text-white font-mono text-xs flex items-center justify-center font-bold">
              3
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 font-mono tracking-tight">
              Real-World Self-Healing Engine (Bright Data Scraper Studio)
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 font-sans mt-0.5">
            When target websites change their HTML structure, Gemini 3.7 Flash analyzes the DOM and executes <code className="bg-slate-100 px-1 py-0.5 rounded text-indigo-700 font-mono font-semibold">bdata scraper heal</code> to restore data extraction in-place.
          </p>
        </div>

        {/* 1-Click Sabotage & Heal Button */}
        <Button
          size="lg"
          onClick={onSimulateBreakAndHeal}
          disabled={isHealing}
          className="flex items-center gap-2 px-6 py-6 rounded-xl font-mono text-xs font-bold bg-purple-600 hover:bg-purple-700 text-white shadow-md cursor-pointer transition-all active:scale-[0.98] disabled:opacity-50"
        >
          {isHealing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>DIAGNOSING & HEALING VIA BDATA CLI...</span>
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 fill-current" />
              <span>SIMULATE WEBSITE BREAK & AUTO-HEAL</span>
            </>
          )}
        </Button>
      </div>

      {/* Main 2-Column Grid: Selector Diff (Left) + Live Bright Data Console (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Side: Before/After Diff & Architecture (Col-Span 7) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Selector Diff Card */}
          <Card className="p-6 rounded-xl border-slate-200 bg-white shadow-xs space-y-4 font-mono text-xs">
            <h3 className="font-bold text-slate-900 text-sm tracking-tight">
              Visual Selector Mutation & Repair Diff
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Broken Selector (Red) */}
              <div className="p-4 rounded-lg bg-rose-50/80 border border-rose-200 space-y-2">
                <div className="flex items-center justify-between text-rose-800 font-bold text-[11px]">
                  <span className="flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-rose-600" />
                    MUTATED / BROKEN SELECTOR
                  </span>
                  <Badge variant="destructive" className="text-[10px] bg-rose-600">FAILED</Badge>
                </div>
                <div className="p-2.5 rounded bg-white border border-rose-200 text-rose-900 font-mono text-xs overflow-x-auto">
                  <code>{diagnosis.brokenSelector || 'table.cve-grid tr td.cve-id'}</code>
                </div>
                <p className="text-[11px] text-rose-700 font-sans">
                  Target feed altered HTML container structure, returning 0 records.
                </p>
              </div>

              {/* Repaired Selector (Green) */}
              <div className="p-4 rounded-lg bg-emerald-50/80 border border-emerald-200 space-y-2">
                <div className="flex items-center justify-between text-emerald-800 font-bold text-[11px]">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    AI REPAIRED SELECTOR
                  </span>
                  <Badge className="text-[10px] bg-emerald-600 hover:bg-emerald-600 text-white">BDATA HEALED</Badge>
                </div>
                <div className="p-2.5 rounded bg-white border border-emerald-200 text-emerald-900 font-mono text-xs overflow-x-auto">
                  <code>{diagnosis.healedSelector || 'div.exploit-card span.cve-tag'}</code>
                </div>
                <p className="text-[11px] text-emerald-700 font-sans">
                  Gemini 3.7 mapped AOM tree $\rightarrow$ executed <code className="font-semibold text-emerald-800">bdata scraper heal</code> in-place.
                </p>
              </div>
            </div>
          </Card>

          {/* Autonomous Step Flow Badges */}
          <Card className="p-5 rounded-xl border-slate-200 bg-white shadow-xs space-y-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-600" />
              <h4 className="font-mono text-xs font-bold text-slate-900 uppercase">
                5-Stage Autonomous Self-Healing Pipeline
              </h4>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 font-mono text-[11px] text-slate-700 text-center">
              <div className="p-2 rounded bg-slate-50 border border-slate-200 font-medium">
                1. Detect 0 Rows
              </div>
              <div className="p-2 rounded bg-slate-50 border border-slate-200 font-medium">
                2. AOM Inspect
              </div>
              <div className="p-2 rounded bg-slate-50 border border-slate-200 font-medium">
                3. Gemini AI Diag
              </div>
              <div className="p-2 rounded bg-indigo-50 border border-indigo-200 text-indigo-800 font-semibold">
                4. bdata heal
              </div>
              <div className="p-2 rounded bg-emerald-50 border border-emerald-200 text-emerald-800 font-semibold">
                5. 100% Repaired
              </div>
            </div>
          </Card>
        </div>

        {/* Right Side: Live Terminal (Col-Span 5) */}
        <div className="lg:col-span-5 h-[520px]">
          <BrightDataTerminal
            logs={terminalLogs}
            collectorId={collectorId}
            targetUrl={targetUrl}
          />
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <Button
          variant="outline"
          onClick={onBack}
          className="flex items-center gap-2 font-mono text-xs cursor-pointer border-slate-300 text-slate-700"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>BACK TO THREAT DATA GRID</span>
        </Button>

        <Button
          onClick={onRestart}
          className="flex items-center gap-2 px-6 py-5 rounded-xl font-mono text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white shadow-md cursor-pointer"
        >
          <RotateCcw className="w-4 h-4" />
          <span>RESTART SCANNER WORKFLOW</span>
        </Button>
      </div>
    </div>
  );
}
