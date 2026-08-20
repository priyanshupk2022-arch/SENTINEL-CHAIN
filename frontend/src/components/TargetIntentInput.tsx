'use client';

import React from 'react';
import { Globe, Sparkles, Play, RefreshCw, ShieldCheck, ArrowRight, Zap, CheckCircle2 } from 'lucide-react';

interface TargetIntentInputProps {
  targetUrl: string;
  setTargetUrl: (url: string) => void;
  targetName: string;
  setTargetName: (name: string) => void;
  intentPrompt: string;
  setIntentPrompt: (intent: string) => void;
  isScraping: boolean;
  onRunScraper: () => void;
}

export function TargetIntentInput({
  targetUrl,
  setTargetUrl,
  targetName,
  setTargetName,
  intentPrompt,
  setIntentPrompt,
  isScraping,
  onRunScraper
}: TargetIntentInputProps) {
  const quickTargets = [
    {
      name: 'Exploit-DB Security Advisories',
      url: 'http://127.0.0.1:8000/api/proxy/target',
      intent: 'Extract CVE ID, vulnerability title, severity, and publication date'
    },
    {
      name: 'Books to Scrape Catalog',
      url: 'http://books.toscrape.com/',
      intent: 'Extract book title, price, rating, and stock availability'
    },
    {
      name: 'Quotes to Scrape Directory',
      url: 'http://quotes.toscrape.com/',
      intent: 'Extract quote text, author name, and associated tags'
    },
    {
      name: 'Hacker News Front Page',
      url: 'https://news.ycombinator.com/',
      intent: 'Extract story title, points score, author username, and comment count'
    }
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="w-5 h-5 rounded-full bg-indigo-600 text-white font-mono text-xs flex items-center justify-center font-bold">
            1
          </span>
          <h2 className="text-base font-bold text-slate-900 font-mono tracking-tight">
            Target Website & Extraction Intent
          </h2>
        </div>
        <p className="text-xs text-slate-500 font-sans">
          Provide any public website URL. Bright Data Scraper Studio will unlock and extract structured data automatically.
        </p>
      </div>

      <div className="space-y-4">
        {/* URL Input */}
        <div className="space-y-1.5">
          <label className="text-xs font-mono font-semibold text-slate-700 uppercase">
            TARGET WEBSITE URL
          </label>
          <div className="relative">
            <Globe className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="url"
              placeholder="https://example.com/catalog or http://127.0.0.1:8000/api/proxy/target"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-slate-50 border border-slate-300 text-xs font-mono text-slate-900 placeholder-slate-400 focus:border-indigo-600 focus:bg-white outline-none transition-all"
            />
          </div>
        </div>

        {/* Quick Discovery Cards */}
        <div className="space-y-2">
          <span className="text-[11px] font-mono font-medium text-slate-500 uppercase tracking-wider block">
            Quick Select Public Targets:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 font-mono text-xs">
            {quickTargets.map((qt) => (
              <button
                key={qt.name}
                type="button"
                onClick={() => {
                  setTargetName(qt.name);
                  setTargetUrl(qt.url);
                  setIntentPrompt(qt.intent);
                }}
                className={`p-3 rounded-lg text-left border transition-all cursor-pointer ${
                  targetUrl === qt.url
                    ? 'bg-indigo-50/70 border-indigo-300 shadow-xs text-slate-900'
                    : 'bg-slate-50/80 border-slate-200 hover:border-slate-300 hover:bg-slate-100/60 text-slate-700'
                }`}
              >
                <div className="font-semibold text-xs flex items-center justify-between text-indigo-900">
                  <span>{qt.name}</span>
                  {targetUrl === qt.url && <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />}
                </div>
                <div className="text-[10px] text-slate-500 truncate mt-0.5">{qt.url}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Extraction Intent Prompt Input */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-mono font-semibold text-slate-700 uppercase">
              EXTRACTION INTENT (WHAT DATA SHOULD BE COLLECTED?)
            </label>
            <span className="text-[10px] font-mono text-indigo-600 flex items-center gap-1 font-medium">
              <Sparkles className="w-3 h-3" /> Powered by Gemini 3.7 Flash
            </span>
          </div>
          <input
            type="text"
            placeholder="e.g. Extract title, current price, rating, and stock status"
            value={intentPrompt}
            onChange={(e) => setIntentPrompt(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-lg bg-slate-50 border border-slate-300 text-xs font-mono text-slate-900 placeholder-slate-400 focus:border-indigo-600 focus:bg-white outline-none transition-all"
          />
        </div>

        {/* Big Action CTA */}
        <button
          onClick={onRunScraper}
          disabled={isScraping || !targetUrl.trim()}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-lg font-mono text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 active:scale-[0.99] transition-all shadow-md cursor-pointer disabled:opacity-50"
        >
          {isScraping ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>RUNNING BRIGHT DATA SCRAPER STUDIO...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>SCRAPE CLEAN DATA WITH BRIGHT DATA</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
