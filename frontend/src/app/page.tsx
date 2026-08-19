'use client';

import React from 'react';
import { TopHUDBar } from '@/components/TopHUDBar';
import { ExecutionDAG } from '@/components/ExecutionDAG';
import { OpportunityMatrix } from '@/components/OpportunityMatrix';
import { LiveProblemFeed } from '@/components/LiveProblemFeed';
import { useTelemetryStream } from '@/hooks/useTelemetryStream';

export default function Page() {
  const { frames, connectionStatus } = useTelemetryStream();

  return (
    <div className="flex flex-col h-full bg-void text-white">
      {/* Top HUD Bar */}
      <TopHUDBar 
        connectionStatus={connectionStatus} 
        activeWorkers={16} 
        latencyMs={382} 
        totalProblems={142890} 
        failedCount={0} 
      />

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden grid grid-cols-[280px_1fr_380px] gap-px bg-white/5">
        {/* Left Panel */}
        <section className="bg-void flex flex-col p-4 gap-4 overflow-y-auto">
          <div className="bg-[#0B0F17] border border-white/10 p-3 rounded-md shadow-card">
            <h2 className="font-sans text-[14px] uppercase tracking-[-0.01em] text-zinc-400 font-medium mb-2">1. Target Ingestion</h2>
            <div className="h-20 bg-[#111827] rounded-sm border border-white/10 border-dashed flex items-center justify-center text-xs text-zinc-500 font-mono">
              [ TargetPanel.tsx ]
            </div>
          </div>
          
          <div className="bg-[#0B0F17] border border-white/10 p-3 rounded-md shadow-card flex-1">
            <h2 className="font-sans text-[14px] uppercase tracking-[-0.01em] text-zinc-400 font-medium mb-2">2. Chaos Slider</h2>
            <div className="h-32 bg-[#111827] rounded-sm border border-white/10 border-dashed mb-4 flex items-center justify-center text-xs text-zinc-500 font-mono">
              [ Slider Level 1-3 ]
            </div>
            <button className="w-full bg-[#111827] border border-white/10 text-amber-400 font-mono text-[12px] py-2 rounded-sm hover:border-amber-400/50 transition-colors">
              💥 INJECT MUTATION
            </button>
          </div>

          <div className="bg-[#0B0F17] border border-white/10 p-3 rounded-md shadow-card flex-1">
            <h2 className="font-sans text-[14px] uppercase tracking-[-0.01em] text-zinc-400 font-medium mb-2">3. Platform Health</h2>
            <div className="h-full min-h-[100px] bg-[#111827] rounded-sm border border-white/10 border-dashed flex items-center justify-center text-xs text-zinc-500 font-mono">
              [ Health Radar ]
            </div>
          </div>
        </section>

        {/* Center Stage */}
        <section className="bg-void flex flex-col overflow-hidden">
          <div className="flex-[1.5] bg-[#0B0F17] border-b border-white/10 flex flex-col relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full p-3 border-b border-white/10 shrink-0 bg-[#0B0F17] z-10">
              <h2 className="font-sans text-[14px] uppercase tracking-[-0.01em] text-zinc-400 font-medium">1. Interactive Execution DAG</h2>
            </div>
            <div className="flex-1 w-full h-full pt-12">
              <ExecutionDAG />
            </div>
          </div>
          <div className="flex-1 flex border-b border-white/10 bg-[#0B0F17]">
            <div className="flex-1 border-r border-white/10 flex flex-col relative">
              <div className="absolute top-0 left-0 w-full p-3 border-b border-white/10 shrink-0 z-10 bg-[#0B0F17]">
                <h2 className="font-sans text-[14px] uppercase tracking-[-0.01em] text-zinc-400 font-medium">2. Opportunity Matrix</h2>
              </div>
              <div className="flex-1 pt-12">
                <OpportunityMatrix />
              </div>
            </div>
            <div className="flex-1 flex flex-col">
              <div className="p-3 border-b border-white/10 shrink-0">
                <h2 className="font-sans text-[14px] uppercase tracking-[-0.01em] text-zinc-400 font-medium">3. DOM Diff Inspector</h2>
              </div>
              <div className="flex-1 bg-[#111827]/50 flex items-center justify-center font-mono text-zinc-500 text-sm">
                [ react-diff-viewer ]
              </div>
            </div>
          </div>
        </section>

        {/* Right Stream Panel */}
        <section className="bg-void flex flex-col">
          <div className="flex-[2] border-b border-white/10 p-3 flex flex-col bg-[#0B0F17] overflow-hidden relative">
            <h2 className="font-sans text-[14px] uppercase tracking-[-0.01em] text-zinc-400 font-medium mb-2 shrink-0 z-10 bg-[#0B0F17]">1. Live Problem Stream</h2>
            <div className="flex-1 overflow-hidden -mx-3 -mb-3 px-3 pb-3">
              <LiveProblemFeed />
            </div>
          </div>
          <div className="h-[200px] border-b border-white/10 p-3 flex flex-col bg-[#0B0F17] shrink-0">
            <h2 className="font-sans text-[14px] uppercase tracking-[-0.01em] text-zinc-400 font-medium mb-2 shrink-0">2. Telemetry Logs</h2>
            <div className="flex-1 bg-[#111827] rounded-sm border border-white/10 p-2 overflow-y-auto font-mono text-[10px] text-zinc-400 flex flex-col gap-1">
              {frames.length === 0 && <p className="text-zinc-600">Waiting for stream...</p>}
              {frames.map((frame, i) => (
                <div key={i} className="flex gap-2">
                  <span className="text-cyan-400">[{new Date(frame.timestamp).toLocaleTimeString()}]</span>
                  <span className="text-emerald-400">{frame.event}</span>
                  <span className="text-zinc-500">{JSON.stringify(frame.data)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="h-[150px] p-3 flex flex-col bg-[#0B0F17] shrink-0">
            <h2 className="font-sans text-[14px] uppercase tracking-[-0.01em] text-zinc-400 font-medium mb-2 shrink-0 text-red-400">3. Dead Letter Queue</h2>
            <div className="flex-1 bg-[#111827] rounded-sm border border-red-500/20 border-dashed p-2 overflow-y-auto font-mono text-[10px] text-zinc-500 flex items-center justify-center">
              [ Empty ]
            </div>
          </div>
        </section>
      </main>

      {/* Stretch Goal Footer */}
      <footer className="h-8 bg-[#0B0F17] border-t border-white/10 flex items-center px-4 shrink-0">
         <span className="font-mono text-[10px] text-zinc-500 tracking-tight">BOTTOM BAR: Time-Travel DOM Flight Recorder (0.25x to 10x Playback)</span>
      </footer>
    </div>
  );
}
