'use client';

import React, { useState, useEffect } from 'react';
import {
  Globe, Play, RefreshCw, Database, Layers, Activity,
  Clock, ShieldCheck, AlertCircle, FileText, CheckCircle2,
  Settings, ArrowLeft, Download, Sliders, Flame
} from 'lucide-react';
import { ExecutionDAG } from '@/components/ExecutionDAG';
import { DiagnosisDiffInspector } from '@/components/DiagnosisDiffInspector';
import { ChaosPanel } from '@/components/ChaosPanel';
import { TelemetryFrame } from '@/hooks/useTelemetryStream';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface TargetWorkspaceProps {
  targetId: string;
  onBack: () => void;
  activeNodes: Record<string, string>;
  latestFrame: TelemetryFrame | null;
  frames: TelemetryFrame[];
}

export function TargetWorkspace({
  targetId,
  onBack,
  activeNodes,
  latestFrame,
  frames
}: TargetWorkspaceProps) {
  const [target, setTarget] = useState<any>(null);
  const [records, setRecords] = useState<any[]>([]);
  const [schema, setSchema] = useState<any>(null);
  const [inspection, setInspection] = useState<any>(null);
  const [activeSubTab, setActiveSubTab] = useState<'dag' | 'records' | 'schema' | 'inspection' | 'monitor' | 'chaos'>('dag');
  const [isRunning, setIsRunning] = useState(false);
  const [schedule, setSchedule] = useState('MANUAL');
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [chaosMode, setChaosMode] = useState('clean');

  // Load target details
  const loadTargetData = async () => {
    try {
      // 1. Target
      const res = await fetch(`${API_BASE}/api/targets/${targetId}`);
      if (res.ok) {
        const t = await res.json();
        setTarget(t);
        setSchedule(t.schedule || 'MANUAL');
        setIsDemoMode(t.is_demo || false);
      }

      // 2. Records
      const recRes = await fetch(`${API_BASE}/api/targets/${targetId}/records`);
      if (recRes.ok) {
        const recs = await recRes.json();
        setRecords(recs);
      }

      // 3. Schema
      const schemaRes = await fetch(`${API_BASE}/api/targets/${targetId}/schema`);
      if (schemaRes.ok) {
        const s = await schemaRes.json();
        setSchema(s);
      }

      // 4. Inspection
      const inspRes = await fetch(`${API_BASE}/api/targets/${targetId}/inspection/latest`);
      if (inspRes.ok) {
        const insp = await inspRes.json();
        setInspection(insp);
      }

      // 5. Chaos status
      const chaosRes = await fetch(`${API_BASE}/api/chaos/status`);
      if (chaosRes.ok) {
        const c = await chaosRes.json();
        setChaosMode(c.current_mode);
      }
    } catch (e) {
      console.error('Failed to load target data:', e);
    }
  };

  useEffect(() => {
    loadTargetData();
  }, [targetId]);

  // Refresh records when verifier node completes HEALTHY
  useEffect(() => {
    if (latestFrame?.node_id === 'verifier' && latestFrame?.status === 'HEALTHY') {
      loadTargetData();
    }
  }, [latestFrame]);

  // Run Scraper Now
  const handleRunNow = async () => {
    setIsRunning(true);
    try {
      await fetch(`${API_BASE}/api/targets/${targetId}/run`, {
        method: 'POST'
      });
      await loadTargetData();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunning(false);
    }
  };

  // Update Monitoring
  const handleUpdateSchedule = async (newSched: string) => {
    setSchedule(newSched);
    try {
      await fetch(`${API_BASE}/api/targets/${targetId}/monitor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enabled: newSched !== 'MANUAL',
          schedule: newSched
        })
      });
      await loadTargetData();
    } catch (e) {
      console.error(e);
    }
  };

  // Export CSV
  const handleExportCSV = () => {
    if (records.length === 0) return;
    const firstData = records[0].data || {};
    const headers = Object.keys(firstData);
    const rows = records.map((r) =>
      headers.map((h) => `"${(r.data[h] || '').toString().replace(/"/g, '""')}"`)
    );
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${target?.name || 'target'}_records_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col h-full bg-[#09090B] text-slate-100 overflow-hidden font-sans">
      {/* Target Workspace Top Header */}
      <div className="px-6 py-3.5 border-b border-zinc-800/60 bg-[#121215] flex flex-wrap items-center justify-between gap-4 shrink-0 shadow-sm">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] bg-[#18181B] border border-zinc-800 text-xs font-mono text-zinc-300 hover:text-white hover:bg-[#202024] transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>ALL TARGETS</span>
          </button>

          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="font-mono text-sm font-bold text-[#F4F4F5]">
                {target?.name || 'Target Workspace'}
              </h2>
              {isDemoMode && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-[4px] bg-amber-950/40 text-amber-300 border border-amber-800/60 font-semibold animate-pulse">
                  DEMO / TEST MODE
                </span>
              )}
            </div>
            <a
              href={target?.url}
              target="_blank"
              rel="noreferrer"
              className="text-[11px] font-mono text-zinc-500 hover:text-indigo-400 truncate max-w-md block transition-colors"
            >
              {target?.url}
            </a>
          </div>
        </div>

        {/* Actions & Run Now */}
        <div className="flex items-center gap-3">
          {records.length > 0 && (
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] font-mono text-xs text-zinc-300 bg-[#18181B] border border-zinc-800 hover:text-white transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>EXPORT CSV</span>
            </button>
          )}

          <button
            onClick={handleRunNow}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 rounded-[8px] font-mono text-xs font-semibold bg-[#6366F1] text-white hover:bg-indigo-500 active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(99,102,241,0.25)] cursor-pointer disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>EXECUTING...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>RUN SCRAPER NOW</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-2 px-6 py-2 border-b border-zinc-800/40 bg-[#09090B] shrink-0 font-mono text-xs">
        {[
          { id: 'dag', label: 'EXECUTION DAG' },
          { id: 'records', label: `EXTRACTED RECORDS (${records.length})` },
          { id: 'schema', label: 'EXTRACTION SCHEMA' },
          { id: 'inspection', label: 'INSPECTION EVIDENCE' },
          { id: 'monitor', label: 'MONITORING SCHEDULE' },
          ...(isDemoMode ? [{ id: 'chaos', label: 'CHAOS PROXY' }] : [])
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id as any)}
            className={`px-3 py-1.5 rounded-[6px] transition-all cursor-pointer ${
              activeSubTab === tab.id
                ? 'bg-[#18181B] text-indigo-300 border border-indigo-500/40 font-semibold'
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main Workspace Body */}
      <div className="flex-1 grid grid-cols-12 gap-0 overflow-hidden">
        {/* Left / Center Section (Col-Span 8) */}
        <div className="col-span-12 lg:col-span-8 p-4 overflow-y-auto border-r border-zinc-800/40 flex flex-col gap-4">
          {/* TAB 1: Execution DAG */}
          {activeSubTab === 'dag' && (
            <div className="flex-1 flex flex-col min-h-[450px]">
              <ExecutionDAG activeNodes={activeNodes} />
            </div>
          )}

          {/* TAB 2: Dynamic Extracted Records Table */}
          {activeSubTab === 'records' && (
            <div className="flex flex-col rounded-[12px] bg-[#121215] border border-zinc-800/60 p-5 shadow-[0_8px_30px_rgb(0,0,0,0.4)]">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-zinc-800/60">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-emerald-400" />
                  <h3 className="font-mono text-xs font-bold uppercase text-[#F4F4F5]">
                    Harvested Dynamic Records ({records.length})
                  </h3>
                </div>
                {isDemoMode && (
                  <span className="text-[10px] font-mono text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/60">
                    CONTROLLED TEST HARVEST
                  </span>
                )}
              </div>

              {records.length === 0 ? (
                <div className="py-16 text-center text-zinc-500 font-mono text-xs">
                  No records extracted yet. Click "RUN SCRAPER NOW" to harvest data from {target?.domain}.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left font-mono text-xs">
                    <thead>
                      <tr className="border-b border-zinc-800 text-zinc-400 uppercase text-[11px] bg-[#18181B]">
                        <th className="py-3 px-4">#</th>
                        {Object.keys(records[0]?.data || {}).map((col) => (
                          <th key={col} className="py-3 px-4 font-semibold text-zinc-300">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/40">
                      {records.map((r, i) => (
                        <tr key={r.id || i} className="hover:bg-[#18181B]/60 transition-colors">
                          <td className="py-3 px-4 text-zinc-500">{i + 1}</td>
                          {Object.keys(records[0]?.data || {}).map((col) => (
                            <td key={col} className="py-3 px-4 text-zinc-200 truncate max-w-xs">
                              {r.data[col] !== undefined ? String(r.data[col]) : '-'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Extraction Schema View */}
          {activeSubTab === 'schema' && (
            <div className="rounded-[12px] bg-[#121215] border border-zinc-800/60 p-5 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-zinc-800/60">
                <h3 className="font-mono text-xs font-bold uppercase text-[#F4F4F5]">
                  Active Extraction Schema Contract
                </h3>
                <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/40 px-2 py-0.5 rounded border border-indigo-800/60">
                  VERSION {schema?.version || 1}
                </span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                {schema?.fields?.map((f: any, idx: number) => (
                  <div key={idx} className="p-3.5 rounded-[8px] bg-[#18181B] border border-zinc-800 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-indigo-300">{f.name}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#09090B] text-zinc-400 border border-zinc-800">
                          {f.type}
                        </span>
                        {f.required && (
                          <span className="text-[10px] text-rose-400 font-semibold">REQUIRED</span>
                        )}
                      </div>
                      <p className="text-[11px] text-zinc-500 font-sans mt-1">
                        {f.description || 'Target extraction property'}
                      </p>
                    </div>
                    {f.selector_hint && (
                      <span className="text-[11px] text-zinc-400 bg-[#09090B] px-2 py-1 rounded border border-zinc-800">
                        {f.selector_hint}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: Inspection Evidence */}
          {activeSubTab === 'inspection' && inspection && (
            <div className="rounded-[12px] bg-[#121215] border border-zinc-800/60 p-5 space-y-4 font-mono text-xs">
              <h3 className="font-mono text-xs font-bold uppercase text-[#F4F4F5] pb-2 border-b border-zinc-800">
                Deep Target DOM & AOM Evidence
              </h3>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-[8px] bg-[#18181B] border border-zinc-800">
                  <span className="text-zinc-500 block mb-1">Page Type:</span>
                  <span className="text-indigo-400 font-semibold">{inspection.page_type}</span>
                </div>
                <div className="p-3 rounded-[8px] bg-[#18181B] border border-zinc-800">
                  <span className="text-zinc-500 block mb-1">Status Code:</span>
                  <span className="text-emerald-400 font-semibold">{inspection.status_code}</span>
                </div>
              </div>

              <div>
                <span className="text-zinc-500 block mb-2">Candidate Discovered Fields:</span>
                <div className="flex flex-wrap gap-2">
                  {inspection.candidate_fields?.map((f: string) => (
                    <span key={f} className="px-2.5 py-1 rounded bg-[#18181B] border border-zinc-800 text-zinc-300">
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: Monitoring Schedule Configurator */}
          {activeSubTab === 'monitor' && (
            <div className="rounded-[12px] bg-[#121215] border border-zinc-800/60 p-5 space-y-4">
              <h3 className="font-mono text-xs font-bold uppercase text-[#F4F4F5] pb-2 border-b border-zinc-800">
                Autonomous Target Monitoring & Schedule
              </h3>

              <p className="text-xs text-zinc-400 font-sans leading-relaxed">
                Sentinel-Chain will periodically poll the target, harvest fresh records, and trigger the self-healing engine upon failure.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs pt-2">
                {[
                  { id: 'MANUAL', title: 'Manual Only', desc: 'Execute on-demand via API or UI' },
                  { id: 'INTERVAL_5M', title: 'Every 5 Minutes', desc: 'High frequency polling' },
                  { id: 'INTERVAL_15M', title: 'Every 15 Minutes', desc: 'Standard production monitor' },
                  { id: 'HOURLY', title: 'Hourly Cycle', desc: 'Daily intelligence aggregation' }
                ].map((opt) => (
                  <div
                    key={opt.id}
                    onClick={() => handleUpdateSchedule(opt.id)}
                    className={`p-4 rounded-[8px] border cursor-pointer transition-all ${
                      schedule === opt.id
                        ? 'bg-[#18181B] border-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.2)]'
                        : 'bg-[#18181B]/40 border-zinc-800 hover:border-zinc-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-zinc-200">{opt.title}</span>
                      {schedule === opt.id && <CheckCircle2 className="w-4 h-4 text-indigo-400" />}
                    </div>
                    <p className="text-[11px] text-zinc-500 font-sans">{opt.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 6: Chaos Mode */}
          {activeSubTab === 'chaos' && isDemoMode && (
            <ChaosPanel
              currentMode={chaosMode}
              onMutate={async (mode) => {
                await fetch(`${API_BASE}/api/chaos/mutate`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ mode })
                });
                setChaosMode(mode);
              }}
              onReset={async () => {
                await fetch(`${API_BASE}/api/chaos/reset`, { method: 'POST' });
                setChaosMode('clean');
              }}
              isLoading={isRunning}
            />
          )}
        </div>

        {/* Right Details Inspector Panel (Col-Span 4) */}
        <div className="col-span-12 lg:col-span-4 p-4 overflow-hidden bg-[#09090B]">
          <DiagnosisDiffInspector latestEvent={latestFrame} frames={frames} />
        </div>
      </div>
    </div>
  );
}
