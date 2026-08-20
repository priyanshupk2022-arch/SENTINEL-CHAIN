'use client';

import React, { useState } from 'react';
import { Database, Search, Download, Code, Table as TableIcon, Copy, Check } from 'lucide-react';

interface CleanDataGridProps {
  records: any[];
  isLoading: boolean;
  onExportCSV: () => void;
}

export function CleanDataGrid({ records, isLoading, onExportCSV }: CleanDataGridProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [viewFormat, setViewFormat] = useState<'table' | 'json'>('table');
  const [copiedJson, setCopiedJson] = useState(false);

  // Extract keys dynamically from records
  const sampleData = records.length > 0 ? (records[0].data || records[0]) : {};
  const columns = Object.keys(sampleData).filter((k) => !['id', 'run_id', 'target_id', 'timestamp', 'is_simulated'].includes(k));

  // Filter records based on search query
  const filteredRecords = records.filter((r) => {
    if (!searchTerm.trim()) return true;
    const dataObj = r.data || r;
    const str = JSON.stringify(dataObj).toLowerCase();
    return str.includes(searchTerm.toLowerCase());
  });

  const handleCopyJSON = () => {
    const rawData = records.map((r) => r.data || r);
    navigator.clipboard.writeText(JSON.stringify(rawData, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
      {/* Header Bar */}
      <div className="p-5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50/50">
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <span className="w-5 h-5 rounded-full bg-emerald-600 text-white font-mono text-xs flex items-center justify-center font-bold">
              2
            </span>
            <h3 className="font-mono text-sm font-bold text-slate-900">
              Clean Structured Data Output ({records.length} Records)
            </h3>
          </div>
          <p className="text-xs text-slate-500 font-sans">
            Unlocked and formatted in real-time from Bright Data Scraper Studio.
          </p>
        </div>

        {/* Search & Actions */}
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search records..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 rounded-lg bg-white border border-slate-300 text-xs font-mono text-slate-800 placeholder-slate-400 focus:border-indigo-600 outline-none w-48"
            />
          </div>

          <div className="flex items-center bg-slate-200/80 p-0.5 rounded-lg border border-slate-300 font-mono text-xs">
            <button
              onClick={() => setViewFormat('table')}
              className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer flex items-center gap-1 ${
                viewFormat === 'table' ? 'bg-white text-slate-900 font-semibold shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <TableIcon className="w-3 h-3" />
              <span>TABLE</span>
            </button>
            <button
              onClick={() => setViewFormat('json')}
              className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer flex items-center gap-1 ${
                viewFormat === 'json' ? 'bg-white text-slate-900 font-semibold shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Code className="w-3 h-3" />
              <span>JSON</span>
            </button>
          </div>

          {records.length > 0 && (
            <button
              onClick={onExportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-300 text-emerald-800 hover:bg-emerald-100 text-xs font-mono font-medium transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>EXPORT CSV</span>
            </button>
          )}
        </div>
      </div>

      {/* Body Area */}
      <div className="p-0 overflow-y-auto max-h-[500px]">
        {records.length === 0 ? (
          <div className="py-20 text-center text-slate-400 font-mono text-xs flex flex-col items-center justify-center space-y-2">
            <Database className="w-8 h-8 text-slate-300 stroke-[1.5]" />
            <p className="text-slate-600 font-medium">No records collected yet.</p>
            <p className="text-slate-400 text-[11px] max-w-sm">
              Enter a URL above and click "Scrape Clean Data with Bright Data" to start harvesting.
            </p>
          </div>
        ) : viewFormat === 'table' ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-100/70 text-slate-700 uppercase text-[11px]">
                  <th className="py-3 px-4 font-semibold">#</th>
                  {columns.map((col) => (
                    <th key={col} className="py-3 px-4 font-semibold text-slate-800">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {filteredRecords.map((r, idx) => {
                  const dataObj = r.data || r;
                  return (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="py-2.5 px-4 text-slate-400 font-medium">{idx + 1}</td>
                      {columns.map((col) => (
                        <td key={col} className="py-2.5 px-4 text-slate-800 truncate max-w-xs">
                          {dataObj[col] !== undefined ? String(dataObj[col]) : '-'}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-4 bg-slate-900 text-slate-200 font-mono text-xs overflow-x-auto relative">
            <button
              onClick={handleCopyJSON}
              className="absolute top-4 right-4 flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-300 text-[11px] transition-colors cursor-pointer"
            >
              {copiedJson ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedJson ? 'COPIED' : 'COPY JSON'}</span>
            </button>
            <pre className="p-2">
              {JSON.stringify(records.map((r) => r.data || r), null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
