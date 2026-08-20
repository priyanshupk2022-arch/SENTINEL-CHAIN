'use client';

import React, { useState } from 'react';
import { Flame, RefreshCcw, ExternalLink, ShieldCheck, Sliders } from 'lucide-react';

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
    <div className="bg-[#121215] border border-zinc-800/60 rounded-[12px] p-5 flex flex-col gap-4 text-slate-200 shadow-[0_8px_30px_rgb(0,0,0,0.4)]">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-zinc-800/40 pb-3">
        <div className="flex items-center gap-2.5">
          <Flame className="w-4 h-4 text-amber-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#F4F4F5]">
            Transparent Chaos Proxy
          </h3>
        </div>
        <a
          href="http://localhost:8000/api/proxy/target"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-[11px] font-mono text-zinc-400 hover:text-indigo-400 transition-colors"
        >
          <span>Inspect Target</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      <p className="text-xs text-[#A1A1AA] leading-relaxed font-sans">
        Inject real server-side DOM redesigns into the target page to test autonomous self-healing in real-time.
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
                  ? 'bg-[#18181B] border-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.15)]'
                  : 'bg-[#18181B]/40 border-zinc-800/60 hover:border-zinc-700 hover:bg-[#18181B]'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full transition-colors ${isActive ? 'bg-indigo-400' : 'bg-zinc-700'}`} />
                  <span className="font-mono text-xs font-semibold text-zinc-200">
                    {mode.title}
                  </span>
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-[4px] border ${mode.badgeColor} font-semibold`}>
                  {mode.badge}
                </span>
              </div>
              <p className="text-[11px] text-zinc-400 pl-4 font-sans leading-snug">
                {mode.desc}
              </p>
            </div>
          );
        })}
      </div>

      {/* Action Reset Button */}
      <div className="pt-2 border-t border-zinc-800/40">
        <button
          onClick={() => onReset()}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-[8px] bg-[#18181B] border border-zinc-800 text-zinc-300 hover:text-white hover:bg-[#202024] text-xs font-mono transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer"
        >
          <RefreshCcw className="w-3.5 h-3.5" />
          <span>Reset Baseline</span>
        </button>
      </div>
    </div>
  );
}
