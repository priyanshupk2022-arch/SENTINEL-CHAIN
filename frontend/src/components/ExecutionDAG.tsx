'use client';

import React, { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  Edge,
  Node,
  Position,
  Handle
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Shield, Activity, Sparkles, Terminal, CheckCircle2, AlertOctagon, Wrench, ShieldCheck } from 'lucide-react';

interface ExecutionDAGProps {
  activeNodes: Record<string, string>;
}

const nodeTypes = {
  customStage: ({ data }: any) => {
    const status = data.status || 'IDLE';
    let borderColor = 'border-white/[0.08]';
    let bgColor = 'bg-[#0F131C]';
    let textColor = 'text-slate-400';
    let pulse = false;

    if (status === 'RUNNING' || status === 'EVIDENCE_COLLECTING' || status === 'DIAGNOSING' || status === 'HEALING' || status === 'APPROVING') {
      borderColor = 'border-emerald-400/80 shadow-[0_0_20px_rgba(16,185,129,0.15)]';
      bgColor = 'bg-[#151B27]';
      textColor = 'text-emerald-300';
      pulse = true;
    } else if (status === 'HEALTHY' || status === 'VALIDATED' || status === 'APPROVED' || status === 'EVIDENCE_COLLECTED' || status === 'DIAGNOSED') {
      borderColor = 'border-emerald-500/60 shadow-[0_0_12px_rgba(16,185,129,0.10)]';
      bgColor = 'bg-emerald-950/20';
      textColor = 'text-emerald-300';
    } else if (status === 'BROKEN' || status === 'FAILED' || status === 'REJECTED') {
      borderColor = 'border-rose-500/80 shadow-[0_0_20px_rgba(239,68,68,0.15)]';
      bgColor = 'bg-rose-950/30';
      textColor = 'text-rose-300';
      pulse = true;
    }

    return (
      <div className={`px-4 py-3 rounded-[10px] border ${borderColor} ${bgColor} min-w-[170px] text-center transition-all duration-200 relative`}>
        <Handle type="target" position={Position.Left} className="!bg-slate-500 !w-2 !h-2" />
        
        <div className="flex items-center justify-center gap-2 mb-1">
          {data.icon && <data.icon className={`w-3.5 h-3.5 ${textColor}`} />}
          <span className="font-mono text-xs font-semibold text-slate-100 tracking-wide">
            {data.label}
          </span>
        </div>

        <div className="flex items-center justify-center gap-1.5 mt-1">
          {pulse && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />}
          <span className={`text-[10px] font-mono font-medium uppercase ${textColor}`}>
            {status}
          </span>
        </div>

        <Handle type="source" position={Position.Right} className="!bg-slate-500 !w-2 !h-2" />
      </div>
    );
  }
};

export function ExecutionDAG({ activeNodes }: ExecutionDAGProps) {
  const nodes: Node[] = useMemo(() => [
    {
      id: 'runner',
      type: 'customStage',
      position: { x: 30, y: 120 },
      data: { label: '1. Runner (CLI)', icon: Terminal, status: activeNodes['runner'] || 'IDLE' }
    },
    {
      id: 'detector',
      type: 'customStage',
      position: { x: 240, y: 120 },
      data: { label: '2. Failure Detector', icon: AlertOctagon, status: activeNodes['detector'] || 'IDLE' }
    },
    {
      id: 'evidence',
      type: 'customStage',
      position: { x: 450, y: 40 },
      data: { label: '3. AOM Harvester', icon: Activity, status: activeNodes['evidence'] || 'IDLE' }
    },
    {
      id: 'diagnoser',
      type: 'customStage',
      position: { x: 660, y: 40 },
      data: { label: '4. Gemini 3.7 Flash', icon: Sparkles, status: activeNodes['diagnoser'] || 'IDLE' }
    },
    {
      id: 'validator',
      type: 'customStage',
      position: { x: 870, y: 40 },
      data: { label: '5. Deterministic Gate', icon: Shield, status: activeNodes['validator'] || 'IDLE' }
    },
    {
      id: 'healer',
      type: 'customStage',
      position: { x: 660, y: 200 },
      data: { label: '6. bdata heal', icon: Wrench, status: activeNodes['healer'] || 'IDLE' }
    },
    {
      id: 'approval',
      type: 'customStage',
      position: { x: 870, y: 200 },
      data: { label: '7. bdata approve', icon: CheckCircle2, status: activeNodes['approval'] || 'IDLE' }
    },
    {
      id: 'verifier',
      type: 'customStage',
      position: { x: 1080, y: 120 },
      data: { label: '8. Health Verifier', icon: ShieldCheck, status: activeNodes['verifier'] || 'IDLE' }
    }
  ], [activeNodes]);

  const edges: Edge[] = useMemo(() => [
    { id: 'e1-2', source: 'runner', target: 'detector', animated: true, style: { stroke: '#94a3b8' } },
    { id: 'e2-3', source: 'detector', target: 'evidence', animated: true, style: { stroke: '#f59e0b' } },
    { id: 'e3-4', source: 'evidence', target: 'diagnoser', animated: true, style: { stroke: '#10b981' } },
    { id: 'e4-5', source: 'diagnoser', target: 'validator', animated: true, style: { stroke: '#0ea5e9' } },
    { id: 'e5-6', source: 'validator', target: 'healer', animated: true, style: { stroke: '#10b981' } },
    { id: 'e6-7', source: 'healer', target: 'approval', animated: true, style: { stroke: '#10b981' } },
    { id: 'e7-8', source: 'approval', target: 'verifier', animated: true, style: { stroke: '#10b981' } },
    { id: 'e2-8', source: 'detector', target: 'verifier', style: { stroke: '#10b981', strokeDasharray: '4,4' } }
  ], []);

  return (
    <div className="w-full h-full min-h-[340px] bg-[#0F131C] relative rounded-[12px] border border-white/[0.07] overflow-hidden shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        attributionPosition="bottom-left"
      >
        <Background color="#1e293b" gap={16} size={1} />
        <Controls className="!bg-[#0F131C] !border-white/[0.08] !text-slate-300" />
      </ReactFlow>
    </div>
  );
}
