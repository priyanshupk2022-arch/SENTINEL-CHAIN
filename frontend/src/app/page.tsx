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
import { TargetOnboardingModal } from '@/components/TargetOnboardingModal';
import { TargetListView } from '@/components/TargetListView';
import { TargetWorkspace } from '@/components/TargetWorkspace';
import { useTelemetryStream } from '@/hooks/useTelemetryStream';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function App() {
  const { frames, latestFrame, connectionStatus, activeNodes } = useTelemetryStream();
  const [viewMode, setViewMode] = useState<'cockpit' | 'landing'>('cockpit');
  const [activeTab, setActiveTab] = useState<string>('targets');
  const [selectedTargetId, setSelectedTargetId] = useState<string | null>(null);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState<boolean>(false);
  const [targets, setTargets] = useState<any[]>([]);
  const [threats, setThreats] = useState<ThreatItem[]>([]);
  const [chaosMode, setChaosMode] = useState<string>('clean');
  const [isTriggering, setIsTriggering] = useState<boolean>(false);
  const [lastRecoveryMs, setLastRecoveryMs] = useState<number>(0);

  // Fetch targets list
  const fetchTargets = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/targets`);
      if (res.ok) {
        const data = await res.json();
        setTargets(data);
      }
    } catch (err) {
      console.error('Failed to fetch targets:', err);
    }
  };

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
    fetchTargets();
    fetchThreats();
    fetchChaosStatus();
  }, []);

  // Refresh data when verifier finishes with HEALTHY
  useEffect(() => {
    if (latestFrame?.node_id === 'verifier' && latestFrame?.status === 'HEALTHY') {
      fetchThreats();
      fetchTargets();
    }
  }, [latestFrame]);

  // Handle pipeline trigger
  const handleTriggerPipeline = async (targetId?: string) => {
    setIsTriggering(true);
    const start = performance.now();
    try {
      const endpoint = targetId ? `${API_BASE}/api/targets/${targetId}/run` : `${API_BASE}/api/scraper/trigger`;
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collector_id: 'c_sentinel_cve_threats',
          auto_heal: true
        })
      });
      const data = await res.json();
      if (data?.result?.duration_ms || data?.duration_ms) {
        setLastRecoveryMs(data.result?.duration_ms || data.duration_ms);
      } else {
        setLastRecoveryMs(performance.now() - start);
      }
      await fetchThreats();
      await fetchTargets();
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

  // Delete target
  const handleDeleteTarget = async (targetId: string) => {
    try {
      await fetch(`${API_BASE}/api/targets/${targetId}`, { method: 'DELETE' });
      if (selectedTargetId === targetId) setSelectedTargetId(null);
      await fetchTargets();
    } catch (err) {
      console.error('Failed to delete target:', err);
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
        onTriggerPipeline={() => handleTriggerPipeline()}
        onInjectSabotage={handleInjectSabotage}
        onExportCSV={handleExportCSV}
        lastRecoveryMs={lastRecoveryMs}
        currentView={viewMode}
        onToggleView={() => setViewMode(viewMode === 'cockpit' ? 'landing' : 'cockpit')}
      />

      {/* Target Onboarding Modal */}
      <TargetOnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
        onTargetCreated={(newTargetId) => {
          fetchTargets();
          setSelectedTargetId(newTargetId);
          setActiveTab('targets');
        }}
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

          <footer className="w-full border-t border-zinc-800/40 bg-[#09090B] py-8 text-center text-xs font-mono text-zinc-500">
            SENTINEL-CHAIN // WE-MAKE-DEVS SCRAPE-VERSE HACKATHON 2026 // POWERED BY BRIGHT DATA & GEMINI 3.7 FLASH
          </footer>
        </div>
      ) : (
        /* ========================================================================= */
        /* SECOPS COCKPIT VIEW & TARGET WORKSPACE PLATFORM                            */
        /* ========================================================================= */
        <main className="flex-1 grid grid-cols-12 gap-0 overflow-hidden h-[calc(100vh-3.5rem)]">
          {/* Left Navigation Sidebar (Col-Span 2) */}
          <div className="col-span-2 hidden md:flex flex-col h-full border-r border-zinc-800/40">
            <SidebarNav
              activeTab={activeTab}
              onSelectTab={(tab) => {
                setActiveTab(tab);
                if (tab !== 'targets') {
                  setSelectedTargetId(null);
                }
              }}
              onOpenOnboarding={() => setIsOnboardingOpen(true)}
              totalTargets={targets.length}
              totalThreats={threats.length}
            />
          </div>

          {/* Main Area: Target Workspace, Target Registry, or Mission Control */}
          <div className="col-span-12 md:col-span-10 flex flex-col h-full overflow-hidden">
            {selectedTargetId ? (
              /* Dedicated Target Workspace */
              <TargetWorkspace
                targetId={selectedTargetId}
                onBack={() => setSelectedTargetId(null)}
                activeNodes={activeNodes}
                latestFrame={latestFrame}
                frames={frames}
              />
            ) : activeTab === 'targets' ? (
              /* Target Registry List */
              <TargetListView
                targets={targets}
                onSelectTarget={(id) => setSelectedTargetId(id)}
                onOpenOnboarding={() => setIsOnboardingOpen(true)}
                onRunTarget={(id) => handleTriggerPipeline(id)}
                onDeleteTarget={handleDeleteTarget}
                runningTargetId={isTriggering ? 'active' : null}
              />
            ) : activeTab === 'harvests' ? (
              /* Data Harvest Stream */
              <div className="p-6 h-full overflow-y-auto">
                <LiveThreatFeed threats={threats} isLoading={isTriggering} />
              </div>
            ) : activeTab === 'chaos' ? (
              /* Chaos Sandbox Panel */
              <div className="p-6 max-w-2xl">
                <ChaosPanel
                  currentMode={chaosMode}
                  onMutate={handleChaosMutate}
                  onReset={handleChaosReset}
                  isLoading={isTriggering}
                />
              </div>
            ) : (
              /* Global Mission Control Cockpit */
              <div className="grid grid-cols-12 gap-0 h-full overflow-hidden">
                <div className="col-span-8 flex flex-col gap-3 p-3 overflow-hidden border-r border-zinc-800/40">
                  <div className="flex-[1.2] min-h-[300px] flex flex-col">
                    <ExecutionDAG activeNodes={activeNodes} />
                  </div>
                  <div className="flex-1 min-h-[220px] flex flex-col overflow-hidden">
                    <LiveThreatFeed threats={threats} isLoading={isTriggering} />
                  </div>
                </div>
                <div className="col-span-4 flex flex-col p-3 overflow-hidden bg-[#09090B]">
                  <DiagnosisDiffInspector latestEvent={latestFrame} frames={frames} />
                </div>
              </div>
            )}
          </div>
        </main>
      )}
    </div>
  );
}
