'use client';

import React, { useRef } from 'react';
import { Layers, Terminal, Sparkles, ShieldCheck, ArrowRight, Code2, Database } from 'lucide-react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';

export function ArchitectureBento() {
  const bentoRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    gsap.from('.bento-card', {
      opacity: 0,
      y: 30,
      stagger: 0.2,
      duration: 0.8,
      ease: 'power3.out'
    });
  }, { scope: bentoRef });

  return (
    <section ref={bentoRef} id="how-it-works" className="w-full border-b border-zinc-800/40 bg-[#09090B] py-20">
      <div className="max-w-7xl mx-auto px-6">
        {/* Section Header */}
        <div className="mb-14 text-center max-w-2xl mx-auto">
          <span className="text-[11px] font-mono font-semibold tracking-wider text-indigo-400 uppercase bg-indigo-950/40 px-3 py-1 rounded-[4px] border border-indigo-800/60">
            HOW IT WORKS // ARCHITECTURE
          </span>
          <h2 className="text-3xl font-bold tracking-tight text-[#F4F4F5] mt-4 font-sans">
            Three-Stage Autonomous Resilience Pipeline
          </h2>
          <p className="text-sm text-[#A1A1AA] mt-2 font-sans">
            From DOM failure detection to unattended model synthesis and deterministic verification.
          </p>
        </div>

        {/* 3-Step Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Target Harvester & Breakdown */}
          <div className="bento-card flex flex-col justify-between p-6 rounded-[12px] bg-[#121215] border border-zinc-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.4)]">
            <div>
              <div className="w-10 h-10 rounded-[8px] bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 mb-5">
                <Terminal className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-mono font-semibold text-zinc-500 uppercase tracking-wider">
                STAGE 01
              </span>
              <h3 className="text-lg font-semibold text-[#F4F4F5] mt-1 font-sans">
                Target Harvester & Failure Detection
              </h3>
              <p className="text-xs text-[#A1A1AA] mt-2.5 leading-relaxed font-sans">
                Scraper runs scheduled CLI extractions. When target HTML undergoes layout redesigns or class renaming, Sentinel-Chain detects empty payloads or structural mismatch within 10ms.
              </p>
            </div>

            {/* Code Snippet */}
            <div className="mt-6 p-3 rounded-[8px] bg-[#09090B] border border-zinc-800 font-mono text-[11px] text-zinc-400">
              <span className="text-rose-400 font-semibold block mb-1">[DETECTED FAILURE]</span>
              <span className="text-zinc-500">Selector:</span> <span className="text-rose-300">.cve-id (0 matches)</span><br />
              <span className="text-zinc-500">Status:</span> <span className="text-amber-400">Harvesting AOM Tree...</span>
            </div>
          </div>

          {/* Card 2: Gemini 3.7 AI Diagnosis */}
          <div className="bento-card flex flex-col justify-between p-6 rounded-[12px] bg-[#121215] border border-indigo-500/40 shadow-[0_0_30px_rgba(99,102,241,0.08)]">
            <div>
              <div className="w-10 h-10 rounded-[8px] bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-5">
                <Sparkles className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-mono font-semibold text-indigo-400 uppercase tracking-wider">
                STAGE 02
              </span>
              <h3 className="text-lg font-semibold text-[#F4F4F5] mt-1 font-sans">
                Gemini 3.7 Flash Root-Cause Diagnosis
              </h3>
              <p className="text-xs text-[#A1A1AA] mt-2.5 leading-relaxed font-sans">
                Playwright extracts the semantic DOM & Accessibility Object Model. Gemini 3.7 Flash analyzes the mutation, synthesizes the correct selector, and writes the `bdata scraper heal` prompt.
              </p>
            </div>

            {/* Code Snippet */}
            <div className="mt-6 p-3 rounded-[8px] bg-[#09090B] border border-indigo-900/40 font-mono text-[11px] text-zinc-400">
              <span className="text-indigo-400 font-semibold block mb-1">[AI SYNTHESIS]</span>
              <span className="text-zinc-500">Proposal:</span> <span className="text-emerald-300">&lt;td.vulnerability-badge&gt;</span><br />
              <span className="text-zinc-500">Confidence:</span> <span className="text-indigo-300">0.98 (Gate Approved)</span>
            </div>
          </div>

          {/* Card 3: Bypass Execution & Zero Data Loss */}
          <div className="bento-card flex flex-col justify-between p-6 rounded-[12px] bg-[#121215] border border-zinc-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.4)]">
            <div>
              <div className="w-10 h-10 rounded-[8px] bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mb-5">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="text-[11px] font-mono font-semibold text-zinc-500 uppercase tracking-wider">
                STAGE 03
              </span>
              <h3 className="text-lg font-semibold text-[#F4F4F5] mt-1 font-sans">
                Bypass Execution & Persistence
              </h3>
              <p className="text-xs text-[#A1A1AA] mt-2.5 leading-relaxed font-sans">
                Air-gapped validation gate verifies shell safety. Scraper executes auto-approve and re-runs immediately, persisting clean CVE records into SQLite WAL without single-frame downtime.
              </p>
            </div>

            {/* Code Snippet */}
            <div className="mt-6 p-3 rounded-[8px] bg-[#09090B] border border-emerald-900/40 font-mono text-[11px] text-zinc-400">
              <span className="text-emerald-400 font-semibold block mb-1">[VERIFIED HEALTHY]</span>
              <span className="text-zinc-500">Extracted:</span> <span className="text-emerald-300">100% Threat Records</span><br />
              <span className="text-zinc-500">DB State:</span> <span className="text-zinc-300">SQLite WAL Synced</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
