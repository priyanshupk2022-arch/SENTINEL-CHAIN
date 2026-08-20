'use client';

import React from 'react';
import { Globe, Plus, Play, RefreshCw, Activity, ShieldCheck, AlertCircle, ArrowRight, Trash2, Clock } from 'lucide-react';

interface TargetItem {
  id: string;
  name: string;
  url: string;
  domain: string;
  status: string;
  health: number;
  monitoring_enabled: boolean;
  schedule: string;
  last_run?: string;
  is_demo?: boolean;
}

interface TargetListViewProps {
  targets: TargetItem[];
  onSelectTarget: (targetId: string) => void;
  onOpenOnboarding: () => void;
  onRunTarget: (targetId: string) => void;
  onDeleteTarget: (targetId: string) => void;
  runningTargetId?: string | null;
}

export function TargetListView({
  targets,
  onSelectTarget,
  onOpenOnboarding,
  onRunTarget,
  onDeleteTarget,
  runningTargetId
}: TargetListViewProps) {
  const getStatusBadge = (status: string, isDemo: boolean = false) => {
    const s = status.toUpperCase();
    if (s === 'HEALTHY') {
      return 'bg-emerald-950/40 text-emerald-400 border-emerald-800/60';
    } else if (s === 'RUNNING' || s === 'INSPECTING' || s === 'HEALING') {
      return 'bg-indigo-950/40 text-indigo-300 border-indigo-800/60 animate-pulse';
    } else if (s === 'FAILED' || s === 'BROKEN') {
      return 'bg-rose-950/40 text-rose-400 border-rose-800/60';
    } else {
      return 'bg-zinc-800 text-zinc-300 border-zinc-700';
    }
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-[#09090B] font-sans">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-zinc-800/60">
        <div>
          <h2 className="text-xl font-bold font-mono text-[#F4F4F5]">
            Monitored Target Registry ({targets.length})
          </h2>
          <p className="text-xs text-zinc-400 mt-1 font-sans">
            User-configured web targets with autonomous self-healing monitoring and schema extraction.
          </p>
        </div>

        <button
          onClick={onOpenOnboarding}
          className="flex items-center gap-2 px-4 py-2.5 rounded-[8px] font-mono text-xs font-semibold bg-[#6366F1] text-white hover:bg-indigo-500 active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(99,102,241,0.25)] cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>ONBOARD NEW TARGET</span>
        </button>
      </div>

      {/* Target Cards Grid */}
      {targets.length === 0 ? (
        <div className="py-20 flex flex-col items-center justify-center text-center rounded-[12px] bg-[#121215] border border-dashed border-zinc-800 p-8 space-y-4">
          <Globe className="w-10 h-10 text-zinc-600" />
          <div className="space-y-1">
            <h3 className="font-mono text-sm font-semibold text-zinc-200">
              No Targets Configured
            </h3>
            <p className="text-xs text-zinc-500 font-sans max-w-sm">
              Click "+ ONBOARD NEW TARGET" to inspect a public URL, generate an extraction schema, and deploy a self-healing scraper.
            </p>
          </div>
          <button
            onClick={onOpenOnboarding}
            className="flex items-center gap-1.5 px-4 py-2 rounded-[8px] font-mono text-xs font-semibold bg-[#6366F1] text-white hover:bg-indigo-500 transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>ADD YOUR FIRST TARGET</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {targets.map((target) => {
            const isRunning = runningTargetId === target.id;
            return (
              <div
                key={target.id}
                className="rounded-[12px] bg-[#121215] border border-zinc-800/60 p-5 flex flex-col justify-between hover:border-zinc-700 transition-all duration-150 shadow-[0_8px_30px_rgb(0,0,0,0.4)] space-y-4"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-[4px] border ${getStatusBadge(target.status, target.is_demo)}`}>
                      {target.status}
                    </span>

                    {target.is_demo && (
                      <span className="text-[10px] font-mono text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/60 font-semibold">
                        DEMO / TEST
                      </span>
                    )}
                  </div>

                  {/* Target Title & URL */}
                  <h3 className="font-mono text-sm font-bold text-zinc-200 truncate">
                    {target.name}
                  </h3>
                  <a
                    href={target.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-zinc-500 hover:text-indigo-400 truncate block mt-0.5 transition-colors font-mono"
                  >
                    {target.url}
                  </a>
                </div>

                {/* Metadata Row */}
                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-zinc-800/60 font-mono text-xs">
                  <div>
                    <span className="text-zinc-500 text-[10px] block">HEALTH SCORE</span>
                    <span className="text-emerald-400 font-semibold">
                      {(target.health * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-zinc-500 text-[10px] block">MONITOR</span>
                    <span className="text-zinc-300 font-medium">
                      {target.schedule || 'MANUAL'}
                    </span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-3 border-t border-zinc-800/40 font-mono text-xs">
                  <button
                    onClick={() => onSelectTarget(target.id)}
                    className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-semibold cursor-pointer"
                  >
                    <span>OPEN WORKSPACE</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onRunTarget(target.id)}
                      disabled={isRunning}
                      className="p-1.5 rounded-[6px] bg-[#18181B] border border-zinc-800 hover:text-white text-zinc-300 transition-colors cursor-pointer disabled:opacity-50"
                      title="Run Scraper Now"
                    >
                      {isRunning ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                    </button>

                    {!target.is_demo && (
                      <button
                        onClick={() => onDeleteTarget(target.id)}
                        className="p-1.5 rounded-[6px] bg-[#18181B] border border-zinc-800 hover:text-rose-400 text-zinc-500 transition-colors cursor-pointer"
                        title="Delete Target"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
