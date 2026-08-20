'use client';

import React, { useState } from 'react';
import { Flame, RefreshCcw, ExternalLink, ShieldCheck } from 'lucide-react';

interface ChaosPanelProps {
  currentMode: string;
  onMutate: (mode: string) => Promise<void>;
  onReset: () => Promise<void>;
  isLoading?: boolean;
}

const CHAOS_MODES = [
  {
    id: 'clean',
    title: 'Clean Baseline',
    desc: 'Standard HTML table with valid .cve-id and .cve-row selectors.',
    badge: 'HEALTHY',
    badgeColor: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/60'
  },
  {
    id: 'class_renamed',
    title: 'Class Renaming',
    desc: 'Renames .cve-id to .vulnerability-badge and .cve-title to .vulnerability-summary.',
    badge: 'SABOTAGE L1',
    badgeColor: 'text-amber-400 bg-amber-950/40 border-amber-800/60'
  },
  {
    id: 'table_to_cards',
    title: 'Table to Cards Redesign',
    desc: 'Table markup removed. Converted to nested <article class="exploit-card"> cards.',
    badge: 'SABOTAGE L2',
    badgeColor: 'text-orange-400 bg-orange-950/40 border-orange-800/60'
  },
  {
    id: 'deep_nesting',
    title: 'Deep Nested Architecture',
    desc: 'Wraps threat tokens inside arbitrary section and header wrappers with .cve-ref-label.',
    badge: 'SABOTAGE L3',
    badgeColor: 'text-rose-400 bg-rose-950/40 border-rose-800/60'
  }
];

export function ChaosPanel({
  currentMode,
  onMutate,
  onReset,
  isLoading = false
}: ChaosPanelProps) {
  const [selectedMode, setSelectedMode] = useState(currentMode);

  const handleApply = async (mode: string) => {
    setSelectedMode(mode);
    await onMutate(mode);
  };

  return (
    <div className="bg-[#0F131C] border border-white/[0.07] rounded-[12px] p-5 flex flex-col gap-4 text-slate-200 shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-white/[0.07] pb-3">
        <div className="flex items-center gap-2.5">
          <Flame className="w-4 h-4 text-amber-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200">
            Transparent Chaos Proxy
          </h3>
        </div>
        <a
          href="http://localhost:8000/api/proxy/target"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-emerald-400 transition-colors"
        >
          <span>Inspect Target</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed font-sans">
        Inject server-side DOM mutations into the target page to test autonomous self-healing in real-time.
      </p>

      {/* Mutation Modes List */}
      <div className="flex flex-col gap-2.5">
        {CHAOS_MODES.map((mode) => {
          const isActive = currentMode === mode.id;
          return (
            <div
              key={mode.id}
              onClick={() => !isLoading && handleApply(mode.id)}
              className={`p-3.5 rounded-[8px] border cursor-pointer transition-all duration-150 ${
                isActive
                  ? 'bg-[#151B27] border-emerald-500/60 shadow-[0_0_15px_rgba(16,185,129,0.08)]'
                  : 'bg-[#080B11]/60 border-white/[0.06] hover:border-white/[0.14] hover:bg-[#121620]'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full transition-colors ${isActive ? 'bg-emerald-400' : 'bg-slate-700'}`} />
                  <span className="font-mono text-xs font-semibold text-slate-100">
                    {mode.title}
                  </span>
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-[6px] border ${mode.badgeColor}`}>
                  {mode.badge}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 pl-4 font-sans leading-snug">
                {mode.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* Action Reset Button */}
      <div className="pt-2 border-t border-white/[0.07]">
        <button
          onClick={() => onReset()}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-[8px] bg-[#080B11] border border-white/[0.08] text-slate-300 hover:text-white hover:bg-[#151B27] text-xs font-mono transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer"
        >
          <RefreshCcw className="w-3.5 h-3.5" />
          <span>Reset Baseline</span>
        </button>
      </div>
    </div>
  );
}
