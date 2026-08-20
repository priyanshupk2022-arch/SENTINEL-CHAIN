'use client';

import React, { useState, useEffect } from 'react';
import { TopHUDBar } from '@/components/TopHUDBar';
import { SidebarNav } from '@/components/SidebarNav';
import { ExecutionDAG } from '@/components/ExecutionDAG';
import { ChaosPanel } from '@/components/ChaosPanel';
import { LiveThreatFeed, ThreatItem } from '@/components/LiveThreatFeed';
import { DiagnosisDiffInspector } from '@/components/DiagnosisDiffInspector';
import { LandingHero } from '@/components/LandingHero';
import { ArchitectureBento } from '@/components/ArchitectureBento';
import { SandboxPlayground } from '@/components/SandboxPlayground';
import { EnterpriseBenchmarkTable } from '@/components/EnterpriseBenchmarkTable';
import { useTelemetryStream } from '@/hooks/useTelemetryStream';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function App() {
  const { frames, latestFrame, connectionStatus, activeNodes } = useTelemetryStream();
  const [viewMode, setViewMode] = useState<'cockpit' | 'landing'>('cockpit');
  const [activeTab, setActiveTab] = useState<string>('harvests');
  const [threats, setThreats] = useState<ThreatItem[]>([]);
  const [chaosMode, setChaosMode] = useState<string>('clean');
  const [isTriggering, setIsTriggering] = useState<boolean>(false);
  const [lastRecoveryMs, setLastRecoveryMs] = useState<number>(0);

  // Fetch initial threat records
  const fetchThreats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/threats?limit=50`);
      if (res.ok) {
        const data = await res.json();
        setThreats(data);
      }
    } catch (err) {
      console.error('Failed to fetch threats:', err);
    }
  };

  // Fetch initial chaos status
  const fetchChaosStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/chaos/status`);
      if (res.ok) {
        const data = await res.json();
        setChaosMode(data.current_mode);
      }
    } catch (err) {
      console.error('Failed to fetch chaos status:', err);
    }
  };

  useEffect(() => {
    fetchThreats();
    fetchChaosStatus();
  }, []);

  // Refresh threats whenever verifier finishes with HEALTHY
  useEffect(() => {
    if (latestFrame?.node_id === 'verifier' && latestFrame?.status === 'HEALTHY') {
      fetchThreats();
    }
  }, [latestFrame]);

  // Handle pipeline trigger
  const handleTriggerPipeline = async () => {
    setIsTriggering(true);
    const start = performance.now();
    try {
      const res = await fetch(`${API_BASE}/api/scraper/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collector_id: 'c_sentinel_cve_threats',
          auto_heal: true
        })
      });
      const data = await res.json();
      if (data?.result?.duration_ms) {
        setLastRecoveryMs(data.result.duration_ms);
      } else {
        setLastRecoveryMs(performance.now() - start);
      }
      await fetchThreats();
    } catch (err) {
      console.error('Pipeline trigger failed:', err);
    } finally {
      setIsTriggering(false);
    }
  };

  // Fast Judge "Aha!" Demo: Injects Chaos Sabotage and immediately triggers healing
  const handleInjectSabotage = async () => {
    try {
      setIsTriggering(true);
      await fetch(`${API_BASE}/api/chaos/mutate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'table_to_cards' })
      });
      setChaosMode('table_to_cards');
      // Immediately run the pipeline to demonstrate the autonomous recovery flow
      await handleTriggerPipeline();
    } catch (err) {
      console.error('Sabotage trigger error:', err);
    } finally {
      setIsTriggering(false);
    }
  };

  // Handle Chaos mutation
  const handleChaosMutate = async (mode: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/chaos/mutate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      if (res.ok) {
        const data = await res.json();
        setChaosMode(data.current_mode);
      }
    } catch (err) {
      console.error('Chaos mutation failed:', err);
    }
  };

  // Handle Chaos reset
  const handleChaosReset = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/chaos/reset`, { method: 'POST' });
      if (res.ok) {
        setChaosMode('clean');
      }
    } catch (err) {
      console.error('Chaos reset failed:', err);
    }
  };

  // Export harvested threat records to CSV
  const handleExportCSV = () => {
    if (threats.length === 0) return;
    const headers = ['CVE_ID', 'Title', 'Severity', 'Published_Date', 'Source'];
    const rows = threats.map((t) => [
      `"${t.cve_id}"`,
      `"${(t.title || '').replace(/"/g, '""')}"`,
      `"${t.severity}"`,
      `"${t.published_date || ''}"`,
      `"${t.source || ''}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `sentinel_threat_harvest_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col min-h-screen w-screen bg-[#09090B] text-slate-100 font-sans select-none overflow-x-hidden">
      {/* Top HUD Navigation Bar */}
      <TopHUDBar
        connectionStatus={connectionStatus}
        activeChaosMode={chaosMode}
        totalThreats={threats.length}
        isTriggering={isTriggering}
        onTriggerPipeline={handleTriggerPipeline}
        onInjectSabotage={handleInjectSabotage}
        onExportCSV={handleExportCSV}
        lastRecoveryMs={lastRecoveryMs}
        currentView={viewMode}
        onToggleView={() => setViewMode(viewMode === 'cockpit' ? 'landing' : 'cockpit')}
      />

      {viewMode === 'landing' ? (
        /* ========================================================================= */
        /* LANDING PAGE VIEW (Section 3: 12-Column Editorial Showcase)               */
        /* ========================================================================= */
        <div className="flex-1 flex flex-col overflow-y-auto">
          <LandingHero
            onLaunchPlayground={() => setViewMode('cockpit')}
            onScrollToDocs={() => {
              const el = document.getElementById('how-it-works');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
            }}
          />
          <ArchitectureBento />
          <SandboxPlayground />
          <EnterpriseBenchmarkTable />

          {/* Minimalist Dark Footer */}
          <footer className="w-full border-t border-zinc-800/40 bg-[#09090B] py-8 text-center text-xs font-mono text-zinc-500">
            SENTINEL-CHAIN // WE-MAKE-DEVS SCRAPE-VERSE HACKATHON 2026 // POWERED BY BRIGHT DATA & GEMINI 3.7 FLASH
          </footer>
        </div>
      ) : (
        /* ========================================================================= */
        /* SECOPS COCKPIT VIEW (Section 4: High-Density Split-Pane Workspace)         */
        /* ========================================================================= */
        <main className="flex-1 grid grid-cols-12 gap-0 overflow-hidden h-[calc(100vh-3.5rem)]">
          {/* Left Navigation Sidebar (Col-Span 2) */}
          <div className="col-span-2 hidden md:flex flex-col h-full border-r border-zinc-800/40">
            <SidebarNav
              activeTab={activeTab}
              onSelectTab={(tab) => {
                setActiveTab(tab);
                if (tab === 'chaos') {
                  // highlight chaos
                }
              }}
              totalThreats={threats.length}
            />
          </div>

          {/* Center Workspace (Col-Span 7): DAG + Threat Feed */}
          <div className="col-span-12 md:col-span-7 flex flex-col gap-3 p-3 overflow-hidden border-r border-zinc-800/40">
            {/* Top 60%: Interactive Active Reactor DAG */}
            <div className="flex-[1.2] min-h-[300px] flex flex-col">
              <ExecutionDAG activeNodes={activeNodes} />
            </div>

            {/* Bottom 40%: Threat Stream or Chaos Controller depending on Tab */}
            <div className="flex-1 min-h-[220px] flex flex-col overflow-hidden">
              {activeTab === 'chaos' ? (
                <ChaosPanel
                  currentMode={chaosMode}
                  onMutate={handleChaosMutate}
                  onReset={handleChaosReset}
                  isLoading={isTriggering}
                />
              ) : (
                <LiveThreatFeed threats={threats} isLoading={isTriggering} />
              )}
            </div>
          </div>

          {/* Right Details Inspector Panel (Col-Span 3) */}
          <div className="col-span-12 md:col-span-3 flex flex-col p-3 overflow-hidden bg-[#09090B]">
            <DiagnosisDiffInspector latestEvent={latestFrame} frames={frames} />
          </div>
        </main>
      )}
    </div>
  );
}
