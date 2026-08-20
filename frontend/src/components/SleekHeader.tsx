'use client';

import React from 'react';
import { Shield, Terminal, CheckCircle2, ArrowRight, Activity, Zap, Download } from 'lucide-react';

interface SleekHeaderProps {
  currentStep: number;
  onSelectStep: (step: number) => void;
  totalRecords: number;
  isScraping: boolean;
  onExportCSV: () => void;
}

export function SleekHeader({
  currentStep,
  onSelectStep,
  totalRecords,
  isScraping,
  onExportCSV
}: SleekHeaderProps) {
  const steps = [
    { id: 1, label: '1. Target & Intent' },
    { id: 2, label: `2. Clean Data (${totalRecords})` },
    { id: 3, label: '3. Self-Healing Lab' }
  ];

  return (
    <header className="w-full bg-white border-b border-slate-200 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-40 shadow-xs">
      {/* Brand & Bright Data Auth Badge */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-xs">
            <Shield className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-sm text-slate-900 tracking-tight font-mono">
                SENTINEL-CHAIN
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold">
                SCRAPER STUDIO
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-sans">
              Autonomous Web Harvester & AI Self-Healing Engine
            </p>
          </div>
        </div>

        {/* Bright Data CLI Connection Status */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-medium">Bright Data CLI Connected</span>
          <span className="text-[10px] text-emerald-600">(Zone: cli_unlocker)</span>
        </div>
      </div>

      {/* 3-Step Linear Workflow Stepper */}
      <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 font-mono text-xs">
        {steps.map((step) => {
          const isActive = currentStep === step.id;
          return (
            <button
              key={step.id}
              onClick={() => onSelectStep(step.id)}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer flex items-center gap-1.5 font-medium ${
                isActive
                  ? 'bg-white text-indigo-700 shadow-xs border border-slate-200 font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <span>{step.label}</span>
            </button>
          );
        })}
      </div>

      {/* Export / Status CTA */}
      <div className="flex items-center gap-3">
        {totalRecords > 0 && (
          <button
            onClick={onExportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-100 border border-slate-300 text-slate-700 hover:bg-slate-200 text-xs font-mono font-medium transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>EXPORT CSV</span>
          </button>
        )}

        <div className="flex items-center gap-2 text-xs font-mono text-slate-500">
          <Activity className="w-3.5 h-3.5 text-indigo-600" />
          <span>Gemini 3.7 Flash Active</span>
        </div>
      </div>
    </header>
  );
}
