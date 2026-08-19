import React, { useState } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';

interface TopHUDBarProps {
  connectionStatus?: 'LIVE' | 'MOCK' | 'OFFLINE';
  activeWorkers?: number;
  latencyMs?: number;
  totalProblems?: number;
  failedCount?: number;
}

export function TopHUDBar({
  connectionStatus = 'OFFLINE',
  activeWorkers = 16,
  latencyMs = 382,
  totalProblems = 142890,
  failedCount = 0
}: TopHUDBarProps) {
  const [audioEnabled, setAudioEnabled] = useState(false);

  // Simple number ticker using framer-motion springs
  const springValue = useSpring(totalProblems, { stiffness: 400, damping: 90 });
  
  // Format the number
  const displayTotal = useTransform(springValue, (latest) => Math.floor(latest).toLocaleString());

  const getStatusColor = () => {
    switch(connectionStatus) {
      case 'LIVE': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30 shadow-glow-emerald';
      case 'MOCK': return 'text-amber-400 bg-amber-400/10 border-amber-400/30 shadow-glow-amber';
      case 'OFFLINE': return 'text-red-400 bg-red-400/10 border-red-400/30 shadow-glow-crimson';
    }
  };

  const getStatusPulse = () => {
    switch(connectionStatus) {
      case 'LIVE': return 'bg-emerald-400 shadow-glow-emerald';
      case 'MOCK': return 'bg-amber-400 shadow-glow-amber';
      case 'OFFLINE': return 'bg-red-400 shadow-glow-crimson';
    }
  };

  return (
    <header className="flex h-12 items-center justify-between px-4 border-b border-white/10 bg-[#0B0F17] shrink-0">
      <div className="flex items-center gap-3">
        {/* Live System Pulse Radar */}
        <div className="relative flex items-center justify-center w-4 h-4">
          {connectionStatus !== 'OFFLINE' && (
            <motion.div
              className={`absolute inset-0 rounded-full ${getStatusPulse()} opacity-50`}
              animate={{ scale: [1, 2.5], opacity: [0.5, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'easeOut' }}
            />
          )}
          <div className={`w-2 h-2 rounded-full ${getStatusPulse()}`} />
        </div>
        
        <span className="font-sans font-semibold tracking-tight text-white uppercase text-sm">
          RADAR-X // MARKET INTELLIGENCE OS
        </span>
      </div>

      <div className="flex items-center gap-3 font-mono text-[12px] tabular-nums text-zinc-300">
        <div className="flex items-center gap-2 border border-white/10 rounded-sm px-2 py-1 bg-[#111827]">
          <span className="text-emerald-400">●</span> {activeWorkers} Residential Nodes
        </div>
        
        <div className="flex items-center gap-2 border border-white/10 rounded-sm px-2 py-1 bg-[#111827]">
          <span className="text-cyan-400">⚡</span> {latencyMs}ms P50
        </div>
        
        <div className="flex items-center gap-2 border border-white/10 rounded-sm px-2 py-1 bg-[#111827]">
          <span className="text-indigo-400">🔥</span>
          <motion.span>{displayTotal}</motion.span> Posts
        </div>

        <div className="flex items-center gap-2 border border-white/10 rounded-sm px-2 py-1 bg-[#111827] text-red-400">
          ⚠️ {failedCount} Failed
        </div>

        <button 
          onClick={() => setAudioEnabled(!audioEnabled)}
          className={`flex items-center gap-2 border border-white/10 rounded-sm px-2 py-1 transition-colors ${audioEnabled ? 'text-cyan-400 bg-cyan-400/10' : 'text-zinc-500 hover:text-zinc-300'}`}
        >
          {audioEnabled ? '🔊 ON' : '🔇 OFF'}
        </button>

        <div className={`flex items-center gap-2 border rounded-sm px-2 py-1 ${getStatusColor()}`}>
          {connectionStatus === 'LIVE' ? '🟢' : connectionStatus === 'MOCK' ? '🟡' : '🔴'} {connectionStatus}
        </div>
      </div>
    </header>
  );
}
