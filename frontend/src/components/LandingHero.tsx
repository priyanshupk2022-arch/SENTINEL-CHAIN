'use client';

import React, { useRef } from 'react';
import { Shield, Zap, ArrowRight, Terminal, RefreshCw, CheckCircle2, AlertOctagon, Activity, Sparkles, Cpu, Layers } from 'lucide-react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';

interface LandingHeroProps {
  onLaunchPlayground: () => void;
  onScrollToDocs: () => void;
}

export function LandingHero({ onLaunchPlayground, onScrollToDocs }: LandingHeroProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const heroTextRef = useRef<HTMLDivElement>(null);
  const graphicRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

    tl.from('.hero-badge', { opacity: 0, y: -15, duration: 0.6 })
      .from('.hero-title', { opacity: 0, y: 25, duration: 0.8 }, '-=0.4')
      .from('.hero-desc', { opacity: 0, y: 20, duration: 0.6 }, '-=0.5')
      .from('.hero-terminal', { opacity: 0, y: 20, duration: 0.6 }, '-=0.4')
      .from('.hero-actions', { opacity: 0, y: 20, duration: 0.6 }, '-=0.4')
      .from('.hero-metrics', { opacity: 0, y: 20, duration: 0.6 }, '-=0.4')
      .from(graphicRef.current, { opacity: 0, scale: 0.95, duration: 0.9 }, '-=0.8');
  }, { scope: containerRef });

  return (
    <section ref={containerRef} className="relative w-full border-b border-zinc-800/40 bg-[#09090B] py-16 lg:py-24 overflow-hidden">
      {/* Subtle Ambient Radial Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-indigo-500/[0.04] blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Column (5 Cols): Typography & High-Converting CTAs */}
        <div ref={heroTextRef} className="lg:col-span-5 flex flex-col space-y-6">
          {/* Version Badge */}
          <div className="hero-badge inline-flex items-center gap-2.5 px-3 py-1 rounded-[4px] bg-[#121215] border border-zinc-800/60 w-fit">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
            <span className="text-[11px] font-mono font-semibold tracking-wider text-indigo-300 uppercase">
              ANTIGRAVITY 2.0 // GEMINI 3.7 FLASH
            </span>
          </div>

          {/* H1 Display Headline */}
          <h1 className="hero-title text-4xl sm:text-5xl font-bold tracking-tight text-[#F4F4F5] leading-[1.12]">
            THE SELF-HEALING ENGINE FOR <span className="text-indigo-400">UNBROKEN</span> WEB INTELLIGENCE.
          </h1>

          {/* Description */}
          <p className="hero-desc text-base text-[#A1A1AA] leading-relaxed font-sans">
            Enterprise cyber threat intelligence harvester built on Bright Data Scraper Studio & Google Gemini AI. Automatically detects DOM mutations, harvests visual evidence, and repairs broken scrapers in milliseconds.
          </p>

          {/* Live Terminal Prompt Box */}
          <div className="hero-terminal flex items-center justify-between px-4 py-3 rounded-[8px] bg-[#121215] border border-zinc-800/60 font-mono text-xs text-zinc-300 shadow-[0_8px_30px_rgb(0,0,0,0.4)]">
            <div className="flex items-center gap-2.5">
              <Terminal className="w-4 h-4 text-indigo-400" />
              <span className="text-zinc-500">$</span>
              <span className="text-zinc-200">npx sentinel-chain run --auto-heal</span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-[4px] bg-emerald-950/40 text-emerald-400 border border-emerald-800/60 font-semibold">
              READY
            </span>
          </div>

          {/* Action Buttons */}
          <div className="hero-actions flex flex-wrap items-center gap-4 pt-2">
            <button
              onClick={onLaunchPlayground}
              className="flex items-center gap-2 px-6 py-3.5 rounded-[8px] font-mono text-xs font-semibold bg-[#6366F1] text-white hover:bg-indigo-500 active:scale-[0.98] transition-all shadow-[0_0_25px_rgba(99,102,241,0.25)] cursor-pointer"
            >
              <span>LAUNCH LIVE PLAYGROUND</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={onScrollToDocs}
              className="flex items-center gap-2 px-5 py-3.5 rounded-[8px] font-mono text-xs font-medium bg-[#18181B] border border-zinc-800 text-zinc-300 hover:text-white hover:bg-[#202024] active:scale-[0.98] transition-all cursor-pointer"
            >
              <span>HOW IT WORKS</span>
            </button>
          </div>

          {/* Trust Metrics Row */}
          <div className="hero-metrics grid grid-cols-3 gap-4 pt-6 border-t border-zinc-800/40 font-mono">
            <div>
              <div className="text-xl font-bold text-emerald-400">99.98%</div>
              <div className="text-[11px] text-zinc-500">Unbroken Scrapes</div>
            </div>
            <div>
              <div className="text-xl font-bold text-indigo-400">&lt;92ms</div>
              <div className="text-[11px] text-zinc-500">Recovery Latency</div>
            </div>
            <div>
              <div className="text-xl font-bold text-zinc-200">100%</div>
              <div className="text-[11px] text-zinc-500">Injection Defense</div>
            </div>
          </div>
        </div>

        {/* Right Column (7 Cols): Interactive Simulation Preview Graphic */}
        <div ref={graphicRef} className="lg:col-span-7">
          <div className="relative rounded-[12px] bg-[#121215] border border-zinc-800/60 p-6 shadow-[0_8px_30px_rgb(0,0,0,0.4)] overflow-hidden">
            {/* Header of Simulated Graphic */}
            <div className="flex items-center justify-between pb-4 mb-6 border-b border-zinc-800/40">
              <div className="flex items-center gap-2.5">
                <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                <span className="font-mono text-xs text-zinc-400 ml-2">
                  reactor_pipeline_stream.sh
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-[4px] bg-indigo-950/40 text-indigo-300 border border-indigo-800/60 font-semibold">
                LIVE REACTOR TELEMETRY
              </span>
            </div>

            {/* Interactive Simulated Node Stream */}
            <div className="space-y-4 font-mono text-xs">
              {/* Step 1: Normal Harvester */}
              <div className="flex items-center justify-between p-3 rounded-[8px] bg-[#18181B] border border-zinc-800">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 rounded-[6px] bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                    <Activity className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <span className="text-zinc-200 font-semibold">1. EXPLOIT-DB TARGET HARVESTER</span>
                    <p className="text-[11px] text-zinc-500 font-sans">Scraping live CVE advisories via Bright Data CLI</p>
                  </div>
                </div>
                <span className="text-[10px] text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/60 font-semibold">
                  STATUS: HEALTHY
                </span>
              </div>

              {/* Step 2: Sabotage Proxy Detection */}
              <div className="flex items-center justify-between p-3 rounded-[8px] bg-[#18181B] border border-rose-900/40">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 rounded-[6px] bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
                    <AlertOctagon className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <span className="text-rose-300 font-semibold">2. TARGET DOM MUTATION DETECTED</span>
                    <p className="text-[11px] text-zinc-400 font-sans">Class .cve-id altered to .vulnerability-badge (404 Empty)</p>
                  </div>
                </div>
                <span className="text-[10px] text-rose-400 bg-rose-950/50 px-2 py-0.5 rounded border border-rose-800/80 font-semibold animate-pulse">
                  CRITICAL FAIL
                </span>
              </div>

              {/* Step 3: Autonomous AI Remediation */}
              <div className="flex items-center justify-between p-3.5 rounded-[8px] bg-emerald-950/20 border border-emerald-500/50 shadow-[0_0_25px_rgba(16,185,129,0.15)]">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 rounded-[6px] bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <span className="text-emerald-300 font-semibold">3. GEMINI 3.7 FLASH AUTO-REMEDIATION</span>
                    <p className="text-[11px] text-emerald-400/80 font-sans">Synthesized selector &lt;td.vulnerability-badge&gt; (100% Healed)</p>
                  </div>
                </div>
                <span className="text-[10px] text-emerald-300 bg-emerald-900/60 px-2 py-0.5 rounded border border-emerald-600 font-semibold">
                  SELF-HEALED
                </span>
              </div>
            </div>

            {/* Micro-Interaction CTA to Jump Direct to Live Playground */}
            <div className="mt-6 pt-4 border-t border-zinc-800/40 flex items-center justify-between">
              <span className="text-[11px] text-zinc-500 font-mono">
                Click to inspect active React Flow DAG in SecOps Cockpit:
              </span>
              <button
                onClick={onLaunchPlayground}
                className="flex items-center gap-1.5 text-xs font-mono font-semibold text-indigo-400 hover:text-indigo-300 transition-colors cursor-pointer"
              >
                <span>OPEN COCKPIT</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
