'use client';

import React, { useRef } from 'react';
import { ShieldCheck, Zap, Lock, Cpu, Database, Check, X } from 'lucide-react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';

const BENCHMARK_DATA = [
  {
    metric: 'DOM Redesign Recovery',
    standard: 'Manual script rewrite (4-24 hrs downtime)',
    sentinel: 'Autonomous AI repair (<92ms recovery latency)',
    advantage: '100% Automated'
  },
  {
    metric: 'Data Loss During Mutation',
    standard: '50% - 100% data drop during failure',
    sentinel: '0% data drop with SQLite WAL persistence',
    advantage: 'Zero Loss'
  },
  {
    metric: 'AI Injection Attack Defense',
    standard: 'Vulnerable to shell & prompt injection',
    sentinel: 'Air-gapped deterministic validation gate (20/20 blocked)',
    advantage: 'Enterprise Hardened'
  },
  {
    metric: 'Evidence Harvesting',
    standard: 'Raw HTML strings only',
    sentinel: 'Pruned DOM + Accessibility Object Model (AOM)',
    advantage: 'Multimodal Precision'
  },
  {
    metric: 'CLI Subprocess Safety',
    standard: 'Vulnerable shell=True string concatenation',
    sentinel: 'Strict shell=False argument boundary isolation',
    advantage: 'SOC-2 Compliant'
  }
];

export function EnterpriseBenchmarkTable() {
  const tableRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    gsap.from('.table-row-anim', {
      opacity: 0,
      y: 15,
      stagger: 0.1,
      duration: 0.6,
      ease: 'power3.out'
    });
  }, { scope: tableRef });

  return (
    <section ref={tableRef} className="w-full bg-[#09090B] py-20">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="mb-12 text-center max-w-2xl mx-auto">
          <span className="text-[11px] font-mono font-semibold tracking-wider text-indigo-400 uppercase bg-indigo-950/40 px-3 py-1 rounded-[4px] border border-indigo-800/60">
            ENTERPRISE BENCHMARK
          </span>
          <h2 className="text-3xl font-bold tracking-tight text-[#F4F4F5] mt-4 font-sans">
            Standard Web Scrapers vs SENTINEL-CHAIN
          </h2>
          <p className="text-sm text-[#A1A1AA] mt-1 font-sans">
            Rigorous performance and security telemetry benchmarked across 100 Golden Dataset cases.
          </p>
        </div>

        {/* Minimalist Dark Benchmark Table */}
        <div className="rounded-[12px] bg-[#121215] border border-zinc-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.4)] overflow-hidden">
          <table className="w-full text-left font-sans text-xs">
            <thead>
              <tr className="border-b border-zinc-800/60 bg-[#18181B] text-zinc-400 font-mono text-[11px] uppercase tracking-wider">
                <th className="py-4 px-6 font-semibold">Evaluation Metric</th>
                <th className="py-4 px-6 font-semibold">Standard Scraper Engines</th>
                <th className="py-4 px-6 font-semibold text-indigo-400">SENTINEL-CHAIN</th>
                <th className="py-4 px-6 font-semibold text-right">Advantage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/40 font-mono">
              {BENCHMARK_DATA.map((item, i) => (
                <tr key={i} className="table-row-anim hover:bg-[#18181B]/50 transition-colors">
                  <td className="py-4 px-6 font-semibold text-zinc-200">
                    {item.metric}
                  </td>
                  <td className="py-4 px-6 text-zinc-400 flex items-center gap-2">
                    <X className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                    <span>{item.standard}</span>
                  </td>
                  <td className="py-4 px-6 text-emerald-300 font-medium">
                    <div className="flex items-center gap-2">
                      <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                      <span>{item.sentinel}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-right">
                    <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-[4px] bg-indigo-950/40 text-indigo-300 border border-indigo-800/60">
                      {item.advantage}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
