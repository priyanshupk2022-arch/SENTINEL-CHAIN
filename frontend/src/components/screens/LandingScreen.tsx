'use client';

import React from 'react';
import { Shield, ArrowRight, Sparkles, Terminal, Activity, Zap, CheckCircle2, Lock, Cpu, Globe } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

interface LandingScreenProps {
  onLaunch: () => void;
}

export function LandingScreen({ onLaunch }: LandingScreenProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-between min-h-[calc(100vh-4rem)] p-6 lg:p-12 max-w-6xl mx-auto space-y-12 animate-in fade-in duration-300 font-sans">
      {/* Top Banner Badge */}
      <div className="flex items-center gap-2">
        <Badge variant="outline" className="px-3.5 py-1.5 bg-indigo-50 border-indigo-200 text-indigo-700 font-mono text-xs flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>INTO THE SCRAPE-VERSE HACKATHON 2026 // BRIGHT DATA</span>
        </Badge>
      </div>

      {/* Main Hero Header */}
      <div className="text-center space-y-5 max-w-3xl">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900 font-mono leading-tight">
          Autonomous Cyber Threat & Vulnerability Harvester
        </h1>
        <p className="text-base sm:text-lg text-slate-600 font-sans leading-relaxed">
          <span className="font-semibold text-slate-900">SENTINEL-CHAIN</span> scrapes zero-day vulnerabilities, bugs, and software package exploits in real-time. Built with <span className="font-semibold text-indigo-600">Bright Data Scraper Studio</span> and <span className="font-semibold text-indigo-600">Gemini 3.7 Flash</span>, it automatically self-heals when target websites change their layout.
        </p>

        {/* Primary CTA */}
        <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
          <Button
            size="lg"
            onClick={onLaunch}
            className="px-8 py-6 rounded-xl font-mono text-sm font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg cursor-pointer transition-all active:scale-[0.98] flex items-center gap-3"
          >
            <span>LAUNCH SENTINEL SCANNER</span>
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* 3 Core Architecture Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full pt-4">
        {/* Pillar 1 */}
        <Card className="p-6 rounded-xl border-slate-200 bg-white/80 shadow-xs space-y-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <Globe className="w-5 h-5" />
          </div>
          <h3 className="font-mono text-sm font-bold text-slate-900">
            1. Universal Threat Feeds
          </h3>
          <p className="text-xs text-slate-500 font-sans leading-relaxed">
            Scrapes Exploit-DB, NIST NVD, and GitHub Security Advisories through Bright Data Web Unlocker proxy with zero IP blocks.
          </p>
        </Card>

        {/* Pillar 2 */}
        <Card className="p-6 rounded-xl border-slate-200 bg-white/80 shadow-xs space-y-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="font-mono text-sm font-bold text-slate-900">
            2. Gemini 3.7 Flash AOM
          </h3>
          <p className="text-xs text-slate-500 font-sans leading-relaxed">
            Maps semantic Accessibility Object Model (AOM) trees to automatically diagnose broken CSS selectors and synthesize repair prompts.
          </p>
        </Card>

        {/* Pillar 3 */}
        <Card className="p-6 rounded-xl border-slate-200 bg-white/80 shadow-xs space-y-3">
          <div className="w-10 h-10 rounded-lg bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
            <Zap className="w-5 h-5" />
          </div>
          <h3 className="font-mono text-sm font-bold text-slate-900">
            3. Zero-Downtime Self-Healing
          </h3>
          <p className="text-xs text-slate-500 font-sans leading-relaxed">
            Executes <code className="text-purple-700 font-mono font-semibold">bdata scraper heal</code> in-place to restore 100% data extraction in under 100ms.
          </p>
        </Card>
      </div>

      {/* Live System Status Bar */}
      <div className="w-full py-3 px-5 rounded-lg bg-slate-100/80 border border-slate-200 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-600">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Bright Data Scraper Studio: <strong>CONNECTED</strong> (Zone: cli_unlocker)</span>
        </div>
        <div>
          <span>Engine: <strong>FastAPI + SQLite WAL + Playwright</strong></span>
        </div>
      </div>
    </div>
  );
}
