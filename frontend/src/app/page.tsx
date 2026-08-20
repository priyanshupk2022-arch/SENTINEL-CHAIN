'use client';

import React, { useState, useEffect } from 'react';
import { TopHUDBar } from '@/components/TopHUDBar';
import { ExecutionDAG } from '@/components/ExecutionDAG';
import { ChaosPanel } from '@/components/ChaosPanel';
import { LiveThreatFeed, ThreatItem } from '@/components/LiveThreatFeed';
import { DiagnosisDiffInspector } from '@/components/DiagnosisDiffInspector';
import { useTelemetryStream } from '@/hooks/useTelemetryStream';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function MissionControlPage() {
  const { frames, latestFrame, connectionStatus, activeNodes } = useTelemetryStream();
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

  return (
    <div className="flex flex-col h-screen w-screen bg-[#080B11] text-slate-100 overflow-hidden font-sans">
      {/* Top HUD Navigation Bar */}
      <TopHUDBar
        connectionStatus={connectionStatus}
        activeChaosMode={chaosMode}
        totalThreats={threats.length}
        isTriggering={isTriggering}
        onTriggerPipeline={handleTriggerPipeline}
        lastRecoveryMs={lastRecoveryMs}
      />

      {/* Main 3-Column Mission Control Grid */}
      <main className="flex-1 grid grid-cols-[300px_1fr_360px] gap-4 p-4 overflow-hidden">
        {/* Left Column: Chaos Controls & Target Ingestion */}
        <section className="flex flex-col gap-4 overflow-y-auto">
          <ChaosPanel
            currentMode={chaosMode}
            onMutate={handleChaosMutate}
            onReset={handleChaosReset}
            isLoading={isTriggering}
          />
        </section>

        {/* Center Column: Live React Flow DAG & Real-Time Threat Stream */}
        <section className="flex flex-col gap-4 overflow-hidden">
          {/* Top Half: Execution DAG */}
          <div className="flex-[1.1] min-h-[300px] flex flex-col">
            <ExecutionDAG activeNodes={activeNodes} />
          </div>

          {/* Bottom Half: Live CVE Threat Intelligence Feed */}
          <div className="flex-1 min-h-[220px] flex flex-col overflow-hidden">
            <LiveThreatFeed threats={threats} isLoading={isTriggering} />
          </div>
        </section>

        {/* Right Column: AI Diagnoser & Schema Diff Inspector */}
        <section className="flex flex-col overflow-hidden">
          <DiagnosisDiffInspector latestEvent={latestFrame} frames={frames} />
        </section>
      </main>
    </div>
  );
}
