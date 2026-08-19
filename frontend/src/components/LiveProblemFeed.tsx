import React, { useRef, useEffect, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { motion, AnimatePresence } from 'framer-motion';

interface Problem {
  id: string;
  platform: 'Reddit' | 'G2' | 'Twitter' | 'HN';
  author: string;
  timestamp: string;
  content: string;
  category: string;
  urgency: number;
  wtp: number;
}

const PLATFORM_COLORS = {
  'Reddit': 'text-[#FF4500]',
  'G2': 'text-[#FF492C]',
  'Twitter': 'text-[#1DA1F2]',
  'HN': 'text-[#FF6600]'
};

export function LiveProblemFeed({ problems = [] }: { problems?: Problem[] }) {
  const parentRef = useRef<HTMLDivElement>(null);
  
  // Create some mock data if empty
  const [items, setItems] = useState<Problem[]>(problems.length > 0 ? problems : []);

  useEffect(() => {
    if (problems.length > 0) {
      setItems(problems);
      return;
    }

    // Mock stream simulation
    let counter = 0;
    const interval = setInterval(() => {
      counter++;
      const newProblem: Problem = {
        id: `mock-${Date.now()}-${Math.random()}`,
        platform: ['Reddit', 'G2', 'Twitter', 'HN'][Math.floor(Math.random() * 4)] as any,
        author: `user_${Math.floor(Math.random() * 9999)}`,
        timestamp: new Date().toISOString(),
        content: `I'm struggling with ${['auth', 'database scaling', 'deployment', 'UI state'][Math.floor(Math.random() * 4)]}. It takes hours to fix.`,
        category: ['DevTools', 'FinTech', 'B2B SaaS'][Math.floor(Math.random() * 3)],
        urgency: Math.floor(Math.random() * 50) + 50,
        wtp: Math.floor(Math.random() * 200) * 10 + 50
      };
      setItems(prev => [newProblem, ...prev].slice(0, 1000));
    }, 2000);
    return () => clearInterval(interval);
  }, [problems]);

  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 140, // Estimated card height
    overscan: 5,
  });

  return (
    <div className="w-full h-full overflow-hidden flex flex-col bg-void relative">
      <div 
        ref={parentRef} 
        className="flex-1 overflow-y-auto w-full custom-scrollbar relative"
        style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.1) transparent' }}
      >
        {items.length === 0 ? (
          <div className="p-4 flex flex-col gap-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-[#111827] rounded-md border border-white/5 animate-pulse" />
            ))}
          </div>
        ) : (
          <div
            style={{
              height: `${rowVirtualizer.getTotalSize()}px`,
              width: '100%',
              position: 'relative',
            }}
          >
            <AnimatePresence>
              {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                const item = items[virtualRow.index];
                if (!item) return null;

                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: `${virtualRow.size}px`,
                      transform: `translateY(${virtualRow.start}px)`,
                      padding: '8px 12px',
                    }}
                  >
                    <div className="bg-[#111827] border border-white/10 rounded-md p-3 h-full flex flex-col justify-between shadow-card transition-colors hover:border-white/20">
                      {/* Header */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs font-bold ${PLATFORM_COLORS[item.platform]}`}>
                            {item.platform}
                          </span>
                          <span className="text-zinc-500 font-mono text-[10px]">@{item.author}</span>
                        </div>
                        <span className="text-zinc-600 font-mono text-[10px]">
                          {new Date(item.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      
                      {/* Body */}
                      <div className="text-zinc-300 font-sans text-xs leading-relaxed line-clamp-2 flex-1">
                        {item.content}
                      </div>

                      {/* Footer */}
                      <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/5">
                        <div className="flex items-center gap-2">
                          <span className="bg-white/5 text-zinc-400 text-[10px] font-mono px-1.5 py-0.5 rounded border border-white/10 uppercase">
                            {item.category}
                          </span>
                          <div className="flex items-center gap-1">
                            <div className="w-12 h-1 bg-zinc-800 rounded-full overflow-hidden">
                              <div 
                                className={`h-full ${item.urgency > 80 ? 'bg-red-500' : item.urgency > 50 ? 'bg-amber-500' : 'bg-cyan-500'}`} 
                                style={{ width: `${item.urgency}%` }}
                              />
                            </div>
                          </div>
                        </div>
                        <div className="text-emerald-400 font-mono text-xs font-bold tabular-nums">
                          ${item.wtp.toLocaleString()}/mo
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}
