import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ZAxis } from 'recharts';
import { motion } from 'framer-motion';

const MOCK_DATA = [
  { id: 1, urgency: 85, wtp: 1200, category: 'DevTools', title: 'Need better CI/CD caching', platform: 'r/devops', z: 200 },
  { id: 2, urgency: 95, wtp: 4500, category: 'FinTech', title: 'Stripe webhook sync failing', platform: 'HackerNews', z: 500 },
  { id: 3, urgency: 60, wtp: 500, category: 'B2B SaaS', title: 'CRM export is too slow', platform: 'G2', z: 100 },
  { id: 4, urgency: 75, wtp: 800, category: 'DevTools', title: 'Local env matches prod', platform: 'r/webdev', z: 150 },
  { id: 5, urgency: 40, wtp: 150, category: 'E-Commerce', title: 'Bulk image upload tool', platform: 'Shopify Forum', z: 80 },
  { id: 6, urgency: 90, wtp: 2500, category: 'FinTech', title: 'Automated ledger reconciliation', platform: 'r/SaaS', z: 350 },
];

const CATEGORY_COLORS: Record<string, string> = {
  'DevTools': '#06B6D4', // Cyan
  'FinTech': '#10B981', // Emerald
  'B2B SaaS': '#6366F1', // Indigo
  'E-Commerce': '#F59E0B', // Amber
};

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-[#111827] border border-white/10 rounded-md p-3 shadow-card font-sans text-xs max-w-[200px]">
        <div className="font-semibold text-white mb-1">{data.title}</div>
        <div className="text-zinc-400 mb-2 flex justify-between">
          <span>{data.platform}</span>
          <span style={{ color: CATEGORY_COLORS[data.category] || '#fff' }}>{data.category}</span>
        </div>
        <div className="font-mono flex justify-between text-zinc-300">
          <span>Urgency: {data.urgency}</span>
          <span className="text-emerald-400 font-bold">${data.wtp}/mo</span>
        </div>
      </div>
    );
  }
  return null;
};

// Custom shape to add a pulse effect
const PulsingDot = (props: any) => {
  const { cx, cy, fill, payload } = props;
  
  if (!cx || !cy) return null;

  // Scale dot size based on Z value (frequency)
  const radius = Math.max(4, Math.min(12, payload.z / 40));

  return (
    <g>
      <motion.circle 
        cx={cx} 
        cy={cy} 
        r={radius} 
        fill={fill} 
        opacity={0.8}
        whileHover={{ scale: 1.5, opacity: 1 }}
        style={{ cursor: 'pointer', filter: `drop-shadow(0 0 4px ${fill})` }}
      />
      {payload.urgency > 80 && (
        <motion.circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke={fill}
          strokeWidth={1}
          animate={{ scale: [1, 2.5], opacity: [0.8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeOut' }}
        />
      )}
    </g>
  );
};

export function OpportunityMatrix() {
  return (
    <div className="w-full h-full p-4 bg-void font-mono">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis 
            type="number" 
            dataKey="urgency" 
            name="Urgency" 
            domain={[0, 100]} 
            stroke="#52525b"
            tick={{ fill: '#a1a1aa', fontSize: 10 }}
            label={{ value: 'Urgency Index (0-100)', position: 'insideBottom', offset: -15, fill: '#52525b', fontSize: 10 }}
          />
          <YAxis 
            type="number" 
            dataKey="wtp" 
            name="WTP" 
            domain={[0, 5000]}
            stroke="#52525b"
            tick={{ fill: '#a1a1aa', fontSize: 10 }}
            tickFormatter={(val) => `$${val}`}
            label={{ value: 'Willingness-to-Pay ($/mo)', angle: -90, position: 'insideLeft', offset: -5, fill: '#52525b', fontSize: 10 }}
          />
          <ZAxis type="number" dataKey="z" range={[50, 400]} />
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3', stroke: 'rgba(255,255,255,0.1)' }} />
          <Scatter data={MOCK_DATA} shape={<PulsingDot />}>
            {MOCK_DATA.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[entry.category] || '#6366F1'} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
