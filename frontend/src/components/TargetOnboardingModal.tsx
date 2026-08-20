'use client';

import React, { useState } from 'react';
import { Globe, Search, Sparkles, ArrowRight, Check, AlertCircle, RefreshCw, X, Plus, Trash2, ShieldCheck, Layers, Terminal } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface TargetOnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTargetCreated: (targetId: string) => void;
}

export function TargetOnboardingModal({ isOpen, onClose, onTargetCreated }: TargetOnboardingModalProps) {
  const [step, setStep] = useState<'url' | 'inspecting' | 'schema' | 'review'>('url');
  const [targetName, setTargetName] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [discoveryResults, setDiscoveryResults] = useState<any[]>([]);
  const [inspection, setInspection] = useState<any>(null);
  const [intentPrompt, setIntentPrompt] = useState('');
  const [schemaFields, setSchemaFields] = useState<any[]>([]);
  const [createdTargetId, setCreatedTargetId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  // Search discovery catalog
  const handleSearchDiscovery = async (q: string) => {
    setSearchQuery(q);
    try {
      const res = await fetch(`${API_BASE}/api/discovery/search?query=${encodeURIComponent(q)}`);
      if (res.ok) {
        const data = await res.json();
        setDiscoveryResults(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // 1. Create Target & Run Inspection
  const handleStartInspection = async () => {
    if (!targetUrl.trim()) {
      setErrorMsg('Please enter a valid website URL');
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);
    setStep('inspecting');

    try {
      // Step 1: Create target in database
      const name = targetName.trim() || new URL(targetUrl).hostname;
      const isDemo = targetUrl.includes('localhost') || targetUrl.includes('127.0.0.1');

      const createRes = await fetch(`${API_BASE}/api/targets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, url: targetUrl, is_demo: isDemo })
      });

      if (!createRes.ok) {
        const err = await createRes.json();
        throw new Error(err.detail || 'Failed to create target');
      }

      const targetData = await createRes.json();
      const targetId = targetData.target.id;
      setCreatedTargetId(targetId);

      // Step 2: Run deep inspection
      const inspRes = await fetch(`${API_BASE}/api/targets/${targetId}/inspect`, {
        method: 'POST'
      });

      if (!inspRes.ok) {
        const err = await inspRes.json();
        throw new Error(err.detail || 'Inspection failed');
      }

      const inspData = await inspRes.json();
      setInspection(inspData);

      // Pre-fill intent suggestion
      if (inspData.candidate_fields?.length > 0) {
        setIntentPrompt(`Extract ${inspData.candidate_fields.slice(0, 4).join(', ')}`);
      } else {
        setIntentPrompt('Extract key data fields from this page');
      }

      setStep('schema');
    } catch (e: any) {
      setErrorMsg(e.message || 'Error occurred during inspection');
      setStep('url');
    } finally {
      setIsLoading(false);
    }
  };

  // 2. Generate Schema via Gemini 3.7 Flash
  const handleGenerateSchema = async () => {
    if (!createdTargetId) return;
    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch(`${API_BASE}/api/targets/${createdTargetId}/schema/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intent_prompt: intentPrompt })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Schema generation failed');
      }

      const schemaData = await res.json();
      setSchemaFields(schemaData.fields || []);
      setStep('review');
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to generate schema');
    } finally {
      setIsLoading(false);
    }
  };

  // 3. Finalize Scraper Creation
  const handleFinalizeScraper = async () => {
    if (!createdTargetId) return;
    setIsLoading(true);

    try {
      // Save reviewed schema
      await fetch(`${API_BASE}/api/targets/${createdTargetId}/schema`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `${targetName || 'Target'} Schema`,
          intent_prompt: intentPrompt,
          fields: schemaFields
        })
      });

      // Create scraper definition
      await fetch(`${API_BASE}/api/targets/${createdTargetId}/scraper`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `${targetName || 'Target'} Scraper`,
          collector_id: 'c_sentinel_cve_threats',
          instructions: intentPrompt
        })
      });

      onTargetCreated(createdTargetId);
      onClose();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to finalize scraper');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddField = () => {
    setSchemaFields([
      ...schemaFields,
      { name: `field_${schemaFields.length + 1}`, type: 'string', description: '', required: true }
    ]);
  };

  const handleRemoveField = (idx: number) => {
    setSchemaFields(schemaFields.filter((_, i) => i !== idx));
  };

  const handleFieldChange = (idx: number, key: string, val: any) => {
    const updated = [...schemaFields];
    updated[idx][key] = val;
    setSchemaFields(updated);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in">
      <div className="w-full max-w-2xl bg-[#121215] border border-zinc-800 rounded-[12px] shadow-[0_8px_30px_rgb(0,0,0,0.6)] overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800/60 bg-[#18181B]">
          <div className="flex items-center gap-2.5">
            <Globe className="w-4 h-4 text-indigo-400" />
            <h2 className="font-mono text-xs font-bold uppercase tracking-wider text-[#F4F4F5]">
              Onboard Target Website
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-500 hover:text-white p-1 rounded transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {errorMsg && (
            <div className="p-3 rounded-[8px] bg-rose-950/40 border border-rose-800 text-rose-300 text-xs font-mono flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* STEP 1: Enter URL & Target Details */}
          {step === 'url' && (
            <div className="space-y-5">
              <div className="space-y-1.5">
                <label className="text-xs font-mono font-medium text-zinc-300">TARGET WEBSITE URL</label>
                <div className="relative">
                  <input
                    type="url"
                    placeholder="https://example.com/catalog or http://127.0.0.1:8000/api/proxy/target"
                    value={targetUrl}
                    onChange={(e) => setTargetUrl(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-[8px] bg-[#09090B] border border-zinc-800 text-xs font-mono text-zinc-200 placeholder-zinc-600 focus:border-indigo-500 outline-none"
                  />
                </div>
                <p className="text-[11px] text-zinc-500 font-sans">
                  Protected by SSRF firewall. Internal hostnames & AWS metadata are automatically blocked.
                </p>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-mono font-medium text-zinc-300">TARGET NAME (OPTIONAL)</label>
                <input
                  type="text"
                  placeholder="e.g. Exploit-DB Security Advisories"
                  value={targetName}
                  onChange={(e) => setTargetName(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-[8px] bg-[#09090B] border border-zinc-800 text-xs font-mono text-zinc-200 placeholder-zinc-600 focus:border-indigo-500 outline-none"
                />
              </div>

              {/* Public Catalog Discovery Helpers */}
              <div className="pt-3 border-t border-zinc-800/40 space-y-2">
                <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider block">
                  Quick Select Public Targets:
                </span>
                <div className="grid grid-cols-2 gap-2 font-mono text-xs">
                  <button
                    onClick={() => {
                      setTargetName('Exploit-DB Vulnerability Feed');
                      setTargetUrl('http://127.0.0.1:8000/api/proxy/target');
                    }}
                    className="text-left p-2.5 rounded-[6px] bg-[#18181B] border border-zinc-800 hover:border-indigo-500/80 transition-colors text-zinc-300 cursor-pointer"
                  >
                    <div className="font-semibold text-indigo-300 text-[11px]">Exploit-DB Live Sandbox</div>
                    <div className="text-[10px] text-zinc-500 truncate">http://127.0.0.1:8000/api/proxy/target</div>
                  </button>

                  <button
                    onClick={() => {
                      setTargetName('Books to Scrape Catalog');
                      setTargetUrl('http://books.toscrape.com/');
                    }}
                    className="text-left p-2.5 rounded-[6px] bg-[#18181B] border border-zinc-800 hover:border-indigo-500/80 transition-colors text-zinc-300 cursor-pointer"
                  >
                    <div className="font-semibold text-emerald-300 text-[11px]">Books to Scrape</div>
                    <div className="text-[10px] text-zinc-500 truncate">http://books.toscrape.com/</div>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Inspecting Loading State */}
          {step === 'inspecting' && (
            <div className="py-12 flex flex-col items-center justify-center space-y-4 text-center">
              <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin" />
              <div className="space-y-1">
                <h3 className="font-mono text-sm font-semibold text-zinc-200">
                  Inspecting Target DOM & Accessibility Model...
                </h3>
                <p className="text-xs text-zinc-500 font-sans max-w-sm">
                  Headless browser is rendering the webpage, mapping semantic structures, and discovering candidate fields.
                </p>
              </div>
            </div>
          )}

          {/* STEP 3: Inspection Results & Extraction Intent */}
          {step === 'schema' && inspection && (
            <div className="space-y-5">
              {/* Inspection Summary Card */}
              <div className="p-4 rounded-[8px] bg-[#18181B] border border-zinc-800 space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between border-b border-zinc-800/60 pb-2">
                  <span className="text-zinc-400 font-medium">DISCOVERED STRUCTURE:</span>
                  <span className="px-2 py-0.5 rounded bg-indigo-950/40 text-indigo-300 border border-indigo-800/60 font-semibold">
                    {inspection.page_type}
                  </span>
                </div>
                <div className="text-zinc-300">
                  <span className="text-zinc-500">Page Title:</span> {inspection.page_title}
                </div>
                <div>
                  <span className="text-zinc-500 block mb-1.5">Candidate Fields Found:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {inspection.candidate_fields?.map((f: string) => (
                      <span key={f} className="px-2 py-0.5 rounded bg-[#09090B] border border-zinc-800 text-zinc-300 text-[11px]">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Extraction Intent Prompt Input */}
              <div className="space-y-1.5">
                <label className="text-xs font-mono font-medium text-zinc-300">
                  WHAT SHOULD SENTINEL EXTRACT? (NATURAL LANGUAGE INTENT)
                </label>
                <textarea
                  rows={3}
                  value={intentPrompt}
                  onChange={(e) => setIntentPrompt(e.target.value)}
                  placeholder="e.g. Extract product name, current price, rating, and stock status."
                  className="w-full p-3 rounded-[8px] bg-[#09090B] border border-zinc-800 text-xs font-mono text-zinc-200 placeholder-zinc-600 focus:border-indigo-500 outline-none"
                />
              </div>
            </div>
          )}

          {/* STEP 4: Review & Edit Schema Fields */}
          {step === 'review' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
                <span className="font-mono text-xs font-bold text-zinc-200 uppercase">
                  Reviewed Extraction Fields ({schemaFields.length})
                </span>
                <button
                  onClick={handleAddField}
                  className="flex items-center gap-1 text-[11px] font-mono text-indigo-400 hover:text-indigo-300 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>ADD FIELD</span>
                </button>
              </div>

              <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1 font-mono text-xs">
                {schemaFields.map((field, idx) => (
                  <div key={idx} className="p-3 rounded-[8px] bg-[#18181B] border border-zinc-800 flex items-center gap-3">
                    <input
                      type="text"
                      value={field.name}
                      onChange={(e) => handleFieldChange(idx, 'name', e.target.value)}
                      className="flex-1 px-2 py-1 rounded bg-[#09090B] border border-zinc-800 text-xs text-zinc-200 focus:border-indigo-500 outline-none"
                      placeholder="Field name"
                    />

                    <select
                      value={field.type}
                      onChange={(e) => handleFieldChange(idx, 'type', e.target.value)}
                      className="px-2 py-1 rounded bg-[#09090B] border border-zinc-800 text-xs text-zinc-300 focus:border-indigo-500 outline-none cursor-pointer"
                    >
                      <option value="string">string</option>
                      <option value="number">number</option>
                      <option value="currency">currency</option>
                      <option value="date">date</option>
                      <option value="url">url</option>
                      <option value="boolean">boolean</option>
                    </select>

                    <label className="flex items-center gap-1.5 text-zinc-400 text-[11px] cursor-pointer">
                      <input
                        type="checkbox"
                        checked={field.required}
                        onChange={(e) => handleFieldChange(idx, 'required', e.target.checked)}
                        className="accent-indigo-500 rounded"
                      />
                      <span>Req</span>
                    </label>

                    <button
                      onClick={() => handleRemoveField(idx)}
                      className="text-zinc-600 hover:text-rose-400 p-1 cursor-pointer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-zinc-800/60 bg-[#18181B] flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-[8px] font-mono text-xs text-zinc-400 hover:text-white transition-colors cursor-pointer"
          >
            CANCEL
          </button>

          {step === 'url' && (
            <button
              onClick={handleStartInspection}
              disabled={isLoading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-[8px] font-mono text-xs font-semibold bg-[#6366F1] text-white hover:bg-indigo-500 transition-all shadow-[0_0_20px_rgba(99,102,241,0.25)] cursor-pointer"
            >
              <span>INSPECT TARGET</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}

          {step === 'schema' && (
            <button
              onClick={handleGenerateSchema}
              disabled={isLoading || !intentPrompt.trim()}
              className="flex items-center gap-2 px-5 py-2.5 rounded-[8px] font-mono text-xs font-semibold bg-[#6366F1] text-white hover:bg-indigo-500 transition-all shadow-[0_0_20px_rgba(99,102,241,0.25)] cursor-pointer disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>GENERATE SCHEMA WITH GEMINI 3.7</span>
            </button>
          )}

          {step === 'review' && (
            <button
              onClick={handleFinalizeScraper}
              disabled={isLoading || schemaFields.length === 0}
              className="flex items-center gap-2 px-5 py-2.5 rounded-[8px] font-mono text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-500 transition-all shadow-[0_0_20px_rgba(16,185,129,0.25)] cursor-pointer disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              <span>CREATE SCRAPER & LAUNCH</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
