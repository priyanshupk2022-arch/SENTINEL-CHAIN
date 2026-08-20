'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Copy, Check, Sparkles, RefreshCw } from 'lucide-react';

interface TerminalLog {
  id: string;
  timestamp: string;
  command: string;
  output?: string;
  status: 'running' | 'success' | 'failed' | 'healed';
  durationMs?: number;
}

interface BrightDataTerminalProps {
  logs: TerminalLog[];
  collectorId?: string;
  targetUrl?: string;
}

export function BrightDataTerminal({
  logs,
  collectorId = 'c_sentinel_cve_threats',
  targetUrl = 'http://127.0.0.1:8000/api/proxy/target'
}: BrightDataTerminalProps) {
  const [copied, setCopied] = useState(false);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleCopy = () => {
    const text = logs.map((l) => `[${l.timestamp}] $ ${l.command}\n${l.output || ''}`).join('\n\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-[#1E293B] rounded-xl border border-slate-700 shadow-md overflow-hidden font-mono text-xs text-slate-200">
      {/* Terminal Titlebar */}
      <div className="bg-[#0F172A] px-4 py-2.5 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block" />
            <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
          </div>
          <span className="text-slate-400 font-semibold ml-2 text-[11px]">
            Bright Data Scraper Studio Console
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-900/60 text-indigo-300 border border-indigo-700 font-semibold">
            ID: {collectorId}
          </span>
          <button
            onClick={handleCopy}
            className="text-slate-400 hover:text-slate-200 transition-colors p-1 cursor-pointer"
            title="Copy Terminal Logs"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Terminal Body */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 font-mono select-text">
        {/* Welcome banner */}
        <div className="text-slate-400 text-[11px] leading-relaxed pb-2 border-b border-slate-700/60">
          <p className="text-emerald-400 font-semibold">
            Bright Data Scraper Studio Engine initialized.
          </p>
          <p className="text-slate-400 text-[10px] mt-0.5">
            Zone: <span className="text-slate-200">cli_unlocker</span> | Model: <span className="text-indigo-300">Gemini 3.7 Flash</span>
          </p>
        </div>

        {logs.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-[11px]">
            <p>$ npx -p @brightdata/cli bdata scraper run {collectorId} --url {targetUrl}</p>
            <p className="mt-1 text-[10px]">Waiting for scrape trigger...</p>
          </div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="space-y-1.5 animate-in fade-in duration-200">
              <div className="flex items-start justify-between text-slate-300 text-[11px] gap-2">
                <div className="flex items-center gap-1.5 flex-1 min-w-0">
                  <span className="text-indigo-400 font-bold">$</span>
                  <span className="text-slate-100 break-all">{log.command}</span>
                </div>
                <span className="text-[10px] text-slate-500 shrink-0">{log.timestamp}</span>
              </div>

              {log.output && (
                <div className="bg-[#0F172A]/70 p-2.5 rounded border border-slate-800 text-slate-300 text-[10px] overflow-x-auto whitespace-pre-wrap font-mono max-h-48">
                  {log.output}
                </div>
              )}

              <div className="flex items-center justify-between text-[10px]">
                <div className="flex items-center gap-1.5">
                  {log.status === 'running' && (
                    <span className="text-amber-400 flex items-center gap-1 font-semibold">
                      <RefreshCw className="w-3 h-3 animate-spin" /> EXECUTING
                    </span>
                  )}
                  {log.status === 'success' && (
                    <span className="text-emerald-400 font-semibold flex items-center gap-1">
                      <Check className="w-3 h-3" /> EXIT 0 (CLEAN DATA HARVESTED)
                    </span>
                  )}
                  {log.status === 'healed' && (
                    <span className="text-indigo-300 font-semibold flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> HEALED IN-PLACE VIA BDATA CLI
                    </span>
                  )}
                  {log.status === 'failed' && (
                    <span className="text-rose-400 font-semibold">
                      EXIT 1 (DOM MUTATION DETECTED)
                    </span>
                  )}
                </div>

                {log.durationMs !== undefined && (
                  <span className="text-slate-500 font-mono">
                    {log.durationMs.toFixed(0)}ms
                  </span>
                )}
              </div>
            </div>
          ))
        )}

        <div ref={terminalEndRef} />
      </div>
    </div>
  );
}
