'use client';

import React, { useState, useRef } from 'react';
import { Terminal, Play, Flame, RefreshCw, CheckCircle2, AlertOctagon, Sliders, Shield, ArrowRight } from 'lucide-react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';

const INITIAL_LOGS = [
  { id: 1, type: 'info', text: '[INFO] Initializing Sentinel-Chain runtime environment...' },
  { id: 2, type: 'info', text: '[INFO] Loaded Bright Data Scraper Studio contract for c_sentinel_cve_threats' },
  { id: 3, type: 'healthy', text: '[SUCCESS] Scraping baseline Exploit-DB target: 4 CVEs harvested' },
  { id: 4, type: 'healthy', text: '[DB] SQLite WAL record stream persisted to sentinel_chain.db' },
];

export function SandboxPlayground() {
  const [logs, setLogs] = useState(INITIAL_LOGS);
  const [isSimulating, setIsSimulating] = useState(false);
  const [targetSource, setTargetSource] = useState('cve_exploit_advisories.html');
  const [proxyRotate, setProxyRotate] = useState(true);
  const [jsRendering, setJsRendering] = useState(true);
  const [captchaBypass, setCaptchaBypass] = useState(true);
  const terminalRef = useRef<HTMLDivElement>(null);

  const handleSimulateChaos = () => {
    setIsSimulating(true);
    const newLogs = [
      ...INITIAL_LOGS,
      { id: 5, type: 'warn', text: '[CHAOS INJECTED] Target DOM layout mutation active: Table converted to Cards' },
      { id: 6, type: 'error', text: '[CRITICAL FAIL] Selector .cve-id failed to match. Extracted 0 records.' },
      { id: 7, type: 'info', text: '[HARVEST] Playwright extracted semantic DOM & Accessibility Object Tree (2.4ms)' },
      { id: 8, type: 'info', text: '[AI DIAGNOSTIC] Gemini 3.7 Flash synthesized proposal: <article.exploit-card span>' },
      { id: 9, type: 'info', text: '[VALIDATION GATE] Sanitized repair prompt. No shell injection detected. (0.85ms)' },
      { id: 10, type: 'healthy', text: '[HEAL EXECUTION] `bdata scraper heal` & `approve` committed successfully.' },
      { id: 11, type: 'healthy', text: '[RE-RUN VERIFIED] 100% CVE records extracted. Pipeline fully restored!' }
    ];

    setLogs(newLogs);
    setTimeout(() => {
      setIsSimulating(false);
      if (terminalRef.current) {
        terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
      }
    }, 1200);
  };

  return (
    <section className="w-full border-b border-zinc-800/40 bg-[#09090B] py-20">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="mb-12">
          <span className="text-[11px] font-mono font-semibold tracking-wider text-indigo-400 uppercase bg-indigo-950/40 px-3 py-1 rounded-[4px] border border-indigo-800/60">
            INTERACTIVE SHOWCASE
          </span>
          <h2 className="text-3xl font-bold tracking-tight text-[#F4F4F5] mt-4 font-sans">
            Live Sandbox Simulation Playground
          </h2>
          <p className="text-sm text-[#A1A1AA] mt-1 font-sans">
            Trigger a simulated chaos block and watch the self-healing telemetry stream reroute in real-time.
          </p>
        </div>

        {/* 12-Column Sandbox Layout (4 Cols Control, 8 Cols Terminal) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (4 Cols): Control Board */}
          <div className="lg:col-span-4 p-6 rounded-[12px] bg-[#121215] border border-zinc-800/60 flex flex-col justify-between shadow-[0_8px_30px_rgb(0,0,0,0.4)]">
            <div className="space-y-6">
              <div className="flex items-center gap-2 pb-3 border-b border-zinc-800/40">
                <Sliders className="w-4 h-4 text-indigo-400" />
                <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#F4F4F5]">
                  Control Board
                </h3>
              </div>

              {/* Target Source Dropdown */}
              <div className="space-y-2">
                <label className="text-xs font-mono text-zinc-400 block">
                  TARGET ADVISORY SOURCE
                </label>
                <select
                  value={targetSource}
                  onChange={(e) => setTargetSource(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-[8px] bg-[#18181B] border border-zinc-800 text-xs font-mono text-zinc-200 focus:border-indigo-500 outline-none cursor-pointer"
                >
                  <option value="cve_exploit_advisories.html">Exploit-DB Threat Feed (HTML)</option>
                  <option value="nist_nvd_advisories.html">NIST NVD Advisory Table</option>
                  <option value="zero_day_bulletin.html">Zero-Day Intelligence Bulletin</option>
                </select>
              </div>

              {/* Checkboxes List */}
              <div className="space-y-3 font-mono text-xs">
                <label className="flex items-center gap-2.5 cursor-pointer text-zinc-300">
                  <input
                    type="checkbox"
                    checked={proxyRotate}
                    onChange={(e) => setProxyRotate(e.target.checked)}
                    className="accent-indigo-500 rounded"
                  />
                  <span>Bright Data Residential Proxy Rotate</span>
                </label>

                <label className="flex items-center gap-2.5 cursor-pointer text-zinc-300">
                  <input
                    type="checkbox"
                    checked={jsRendering}
                    onChange={(e) => setJsRendering(e.target.checked)}
                    className="accent-indigo-500 rounded"
                  />
                  <span>Playwright Headless DOM Harvester</span>
                </label>

                <label className="flex items-center gap-2.5 cursor-pointer text-zinc-300">
                  <input
                    type="checkbox"
                    checked={captchaBypass}
                    onChange={(e) => setCaptchaBypass(e.target.checked)}
                    className="accent-indigo-500 rounded"
                  />
                  <span>Gemini 3.7 Flash Self-Healing Engine</span>
                </label>
              </div>
            </div>

            {/* Action Trigger Button */}
            <div className="pt-6 border-t border-zinc-800/40">
              <button
                onClick={handleSimulateChaos}
                disabled={isSimulating}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-[8px] font-mono text-xs font-semibold bg-rose-950/40 border border-rose-800/80 text-rose-300 hover:bg-rose-900/60 hover:text-white active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(239,68,68,0.15)] disabled:opacity-50 cursor-pointer"
              >
                {isSimulating ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>HEALING SCRAPER...</span>
                  </>
                ) : (
                  <>
                    <Flame className="w-3.5 h-3.5 text-rose-400" />
                    <span>SIMULATE CHAOS BLOCK</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right Column (8 Cols): Mock Streaming Terminal */}
          <div className="lg:col-span-8 p-6 rounded-[12px] bg-[#121215] border border-zinc-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.4)] flex flex-col h-[400px]">
            {/* Terminal Top Bar */}
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800/40 shrink-0">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-indigo-400" />
                <span className="font-mono text-xs font-semibold text-zinc-300">
                  STREAMING TELEMETRY PIPELINE
                </span>
              </div>
              <span className="text-[10px] font-mono text-zinc-500">
                PORT 8000 // SSE STREAM
              </span>
            </div>

            {/* Terminal Lines Container */}
            <div ref={terminalRef} className="flex-1 overflow-y-auto space-y-2 font-mono text-xs pr-2">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className={`p-2 rounded-[6px] transition-all ${
                    log.type === 'error'
                      ? 'bg-rose-950/30 text-rose-300 border-l-2 border-rose-500'
                      : log.type === 'warn'
                      ? 'bg-amber-950/30 text-amber-300 border-l-2 border-amber-500'
                      : log.type === 'healthy'
                      ? 'bg-emerald-950/30 text-emerald-300 border-l-2 border-emerald-500'
                      : 'text-zinc-400'
                  }`}
                >
                  {log.text}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
