import React, { useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  BaseEdge,
  getBezierPath,
  EdgeProps
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { motion } from 'framer-motion';

// --- Custom Nodes ---

const BaseNode = ({ title, children, statusColor = 'bg-cyan-500' }: any) => (
  <div className="bg-[#0B0F17] border border-white/10 rounded-md shadow-card w-[220px] overflow-hidden font-sans text-sm">
    <div className="bg-[#111827] px-3 py-2 border-b border-white/10 flex items-center justify-between">
      <span className="text-zinc-300 font-medium tracking-tight uppercase text-xs">{title}</span>
      <div className={`w-2 h-2 rounded-full ${statusColor} shadow-glow-cyan`} />
    </div>
    <div className="p-3 text-zinc-400 font-mono text-[11px] flex flex-col gap-1">
      {children}
    </div>
    <Handle type="target" position={Position.Top} className="!bg-zinc-600 !w-2 !h-2 !border-none" />
    <Handle type="source" position={Position.Bottom} className="!bg-zinc-600 !w-2 !h-2 !border-none" />
  </div>
);

const SourceNode = ({ data }: any) => (
  <BaseNode title="1. Source" statusColor="bg-emerald-400">
    <div>Target: {data.target || 'r/SaaS'}</div>
    <div>Proxy: Bright Data ASN</div>
  </BaseNode>
);

const IngestNode = ({ data }: any) => (
  <BaseNode title="2. Ingestion" statusColor="bg-cyan-400">
    <div>CDP Stream: Active</div>
    <div>CAPTCHA: Bypassed</div>
  </BaseNode>
);

const DetectionNode = ({ data }: any) => (
  <BaseNode title="3. Detection" statusColor={data.hasError ? 'bg-amber-400' : 'bg-emerald-400'}>
    <div>Hash Validator: {data.hasError ? 'MISMATCH' : 'MATCH'}</div>
  </BaseNode>
);

const HealerNode = ({ data }: any) => (
  <BaseNode title="4. Auto-Healer" statusColor={data.active ? 'bg-amber-400' : 'bg-zinc-600'}>
    <div>Status: {data.active ? 'T2 Escalation' : 'Standby'}</div>
    <div>Algorithm: Spatial IoU</div>
  </BaseNode>
);

const OutputNode = ({ data }: any) => (
  <BaseNode title="5. Output" statusColor="bg-indigo-400">
    <div>Schema: Validated</div>
    <div className="text-emerald-400 font-bold mt-1">WTP: {data.wtp || 'Analyzing...'}</div>
  </BaseNode>
);

// --- Custom Edge ---
const AnimatedEdge = ({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data
}: EdgeProps) => {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetPosition,
    targetX,
    targetY,
  });

  const isHealing = data?.isHealing;
  const isError = data?.isError;

  let strokeColor = 'rgba(6, 182, 212, 0.5)'; // Cyan
  if (isHealing) strokeColor = 'rgba(245, 158, 11, 0.8)'; // Amber
  if (isError) strokeColor = 'rgba(239, 68, 68, 0.8)'; // Red

  return (
    <>
      <BaseEdge path={edgePath} markerEnd={markerEnd} style={{ ...style, strokeWidth: 2, stroke: 'rgba(255,255,255,0.1)' }} />
      <motion.path
        d={edgePath}
        fill="none"
        stroke={strokeColor}
        strokeWidth={3}
        strokeDasharray="5 10"
        initial={{ strokeDashoffset: 20 }}
        animate={{ strokeDashoffset: 0 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      />
    </>
  );
};

const initialNodes = [
  { id: '1', type: 'source', position: { x: 50, y: 50 }, data: { target: 'r/SaaS' } },
  { id: '2', type: 'ingest', position: { x: 50, y: 180 }, data: {} },
  { id: '3', type: 'detection', position: { x: 50, y: 310 }, data: { hasError: false } },
  { id: '4', type: 'healer', position: { x: 50, y: 440 }, data: { active: false } },
  { id: '5', type: 'output', position: { x: 50, y: 570 }, data: { wtp: '$1,200/mo' } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', type: 'animated', data: { isHealing: false } },
  { id: 'e2-3', source: '2', target: '3', type: 'animated', data: { isHealing: false } },
  { id: 'e3-4', source: '3', target: '4', type: 'animated', data: { isHealing: false } },
  { id: 'e4-5', source: '4', target: '5', type: 'animated', data: { isHealing: false } },
];

export function ExecutionDAG() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const nodeTypes = useMemo(() => ({
    source: SourceNode,
    ingest: IngestNode,
    detection: DetectionNode,
    healer: HealerNode,
    output: OutputNode
  }), []);

  const edgeTypes = useMemo(() => ({
    animated: AnimatedEdge
  }), []);

  return (
    <div className="w-full h-full bg-void">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="rgba(255,255,255,0.05)" gap={16} />
      </ReactFlow>
    </div>
  );
}
