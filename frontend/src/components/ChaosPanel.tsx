'use client';

import React, { useState } from 'react';
import { Flame, RefreshCcw, Layers, Sliders, ExternalLink, ShieldAlert, CheckCircle2 } from 'lucide-react';

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
    badgeColor: 'text-emerald-400 bg-emerald-950/40 border-emerald-800'
  },
  {
    id: 'class_renamed',
    title: 'Class Renaming',
    desc: 'Renames .cve-id to .vulnerability-badge and .cve-title to .vulnerability-summary.',
    badge: 'SABOTAGE L1',
    badgeColor: 'text-amber-400 bg-amber-950/40 border-amber-800'
  },
  {
    id: 'table_to_cards',
    title: 'Table to Cards Redesign',
    desc: 'Table markup completely removed. Replaced by nested <article class="exploit-card"> elements.',
    badge: 'SABOTAGE L2',
    badgeColor: 'text-orange-400 bg-orange-950/40 border-orange-800'
  },
  {
    id: 'deep_nesting',
    title: 'Deep Nested Architecture',
    desc: 'Wraps threat tokens inside arbitrary section and header wrappers with .cve-ref-label.',
    badge: 'SABOTAGE L3',
    badgeColor: 'text-rose-400 bg-rose-950/40 border-rose-800'
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
    <div className="bg-[#0D131F] border border-slate-800 rounded-lg p-4 flex flex-col gap-4 text-slate-200">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Flame className="w-4 h-4 text-amber-400" />
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200">
            Transparent Chaos Proxy
          </h3>
        </div>
        <a
          href="http://localhost:8000/api/proxy/target"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 text-[11px] font-mono text-sky-400 hover:text-sky-300 transition-colors"
        >
          <span>Inspect Target</span>
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed font-sans">
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
              className={`p-3 rounded border cursor-pointer transition-all ${
                isActive
                  ? 'bg-slate-900 border-sky-500 shadow-md shadow-sky-500/10'
                  : 'bg-slate-950/50 border-slate-800/80 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${isActive ? 'bg-sky-400 shadow-sm shadow-sky-400' : 'bg-slate-700'}`} />
                  <span className="font-mono text-xs font-semibold text-white">
                    {mode.title}
                  </span>
                </div>
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${mode.badgeColor}`}>
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

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2 border-t border-slate-800">
        <button
          onClick={() => onReset()}
          disabled={isLoading}
          className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded bg-slate-900 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 text-xs font-mono transition-all disabled:opacity-50"
        >
          <RefreshCcw className="w-3.5 h-3.5" />
          <span>Reset Baseline</span>
        </button>
      </div>
    </div>
  );
}
