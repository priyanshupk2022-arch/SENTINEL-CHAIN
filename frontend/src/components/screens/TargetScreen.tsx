'use client';

import React from 'react';
import { Globe, ArrowLeft, ArrowRight, Play, RefreshCw, Shield, Sparkles, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

interface TargetScreenProps {
  targetUrl: string;
  setTargetUrl: (url: string) => void;
  targetName: string;
  setTargetName: (name: string) => void;
  intentPrompt: string;
  setIntentPrompt: (intent: string) => void;
  isScraping: boolean;
  onRunScraper: () => void;
  onBack: () => void;
}

export function TargetScreen({
  targetUrl,
  setTargetUrl,
  targetName,
  setTargetName,
  intentPrompt,
  setIntentPrompt,
  isScraping,
  onRunScraper,
  onBack
}: TargetScreenProps) {
  const securityPresets = [
    {
      name: 'Exploit-DB Security Advisories',
      url: 'http://127.0.0.1:8000/api/proxy/target',
      intent: 'Extract CVE ID, vulnerability title, severity, affected software, and published date'
    },
    {
      name: 'NIST Vulnerability Feed (NVD)',
      url: 'https://nvd.nist.gov/vuln/data-feeds',
      intent: 'Extract CVE identifier, CVSS score, bug type, and vulnerable software versions'
    },
    {
      name: 'Open-Source Package Advisories',
      url: 'https://github.com/advisories',
      intent: 'Extract package name, ecosystem (npm/pip), advisory summary, and patched version'
    },
    {
      name: 'Books to Scrape Public Catalog',
      url: 'http://books.toscrape.com/',
      intent: 'Extract book title, price, star rating, and stock availability'
    }
  ];

  return (
    <div className="flex-1 max-w-4xl mx-auto w-full p-6 lg:p-10 flex flex-col justify-between space-y-8 animate-in fade-in duration-200 font-sans">
      {/* Top Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-mono text-xs flex items-center justify-center font-bold">
            1
          </span>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 font-mono tracking-tight">
            Target Website Feed & Extraction Intent
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-slate-500 font-sans">
          Provide any public vulnerability advisory feed, bug tracker, or web catalog. Bright Data Scraper Studio will unlock and extract clean structured data.
        </p>
      </div>

      {/* Main Input Card */}
      <Card className="p-6 rounded-xl border-slate-200 bg-white shadow-xs space-y-6">
        {/* Target URL Input */}
        <div className="space-y-2">
          <label className="text-xs font-mono font-bold text-slate-700 uppercase tracking-wider">
            TARGET WEBSITE URL
          </label>
          <div className="relative">
            <Globe className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <Input
              type="url"
              placeholder="https://... or http://127.0.0.1:8000/api/proxy/target"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              className="pl-10 h-10 font-mono text-xs bg-slate-50 border-slate-300 focus:bg-white"
            />
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Protected by SSRF security gateway. AWS metadata and private networks are automatically filtered.
          </p>
        </div>

        {/* Quick Select Presets */}
        <div className="space-y-2">
          <span className="text-[11px] font-mono font-medium text-slate-500 uppercase tracking-wider block">
            Quick Select Public Feeds:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
            {securityPresets.map((preset) => (
              <button
                key={preset.name}
                type="button"
                onClick={() => {
                  setTargetName(preset.name);
                  setTargetUrl(preset.url);
                  setIntentPrompt(preset.intent);
                }}
                className={`p-3.5 rounded-lg text-left border transition-all cursor-pointer ${
                  targetUrl === preset.url
                    ? 'bg-indigo-50/70 border-indigo-300 shadow-xs text-slate-900'
                    : 'bg-slate-50/80 border-slate-200 hover:border-slate-300 hover:bg-slate-100/60 text-slate-700'
                }`}
              >
                <div className="font-semibold text-xs flex items-center justify-between text-indigo-900">
                  <span>{preset.name}</span>
                  {targetUrl === preset.url && <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />}
                </div>
                <div className="text-[10px] text-slate-500 truncate mt-1">{preset.url}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Natural Language Intent Input */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-mono font-bold text-slate-700 uppercase tracking-wider">
              EXTRACTION INTENT (WHAT BUG / THREAT DATA TO HARVEST?)
            </label>
            <span className="text-[10px] font-mono text-indigo-600 flex items-center gap-1 font-medium">
              <Sparkles className="w-3 h-3" /> Gemini 3.7 Flash
            </span>
          </div>
          <Input
            type="text"
            placeholder="e.g. Extract CVE ID, vulnerability title, severity, affected software, and published date"
            value={intentPrompt}
            onChange={(e) => setIntentPrompt(e.target.value)}
            className="h-10 font-mono text-xs bg-slate-50 border-slate-300 focus:bg-white"
          />
        </div>
      </Card>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <Button
          variant="outline"
          onClick={onBack}
          className="flex items-center gap-2 font-mono text-xs cursor-pointer border-slate-300 text-slate-700"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>BACK TO HOME</span>
        </Button>

        <Button
          onClick={onRunScraper}
          disabled={isScraping || !targetUrl.trim()}
          className="flex items-center gap-2 px-6 py-5 rounded-xl font-mono text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-md cursor-pointer disabled:opacity-50"
        >
          {isScraping ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>HARVESTING WITH BRIGHT DATA...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>HARVEST THREAT INTEL WITH BRIGHT DATA</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
