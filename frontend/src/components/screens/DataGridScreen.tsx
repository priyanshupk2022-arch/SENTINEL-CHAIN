'use client';

import React, { useState } from 'react';
import { Database, Search, Download, Code, ArrowLeft, ArrowRight, Table as TableIcon, Copy, Check, Terminal, ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { BrightDataTerminal } from '@/components/BrightDataTerminal';

interface DataGridScreenProps {
  records: any[];
  isLoading: boolean;
  terminalLogs: any[];
  collectorId: string;
  targetUrl: string;
  onExportCSV: () => void;
  onBack: () => void;
  onNext: () => void;
}

export function DataGridScreen({
  records,
  isLoading,
  terminalLogs,
  collectorId,
  targetUrl,
  onExportCSV,
  onBack,
  onNext
}: DataGridScreenProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isJsonOpen, setIsJsonOpen] = useState(false);
  const [copiedJson, setCopiedJson] = useState(false);

  // Extract columns dynamically
  const sample = records.length > 0 ? (records[0].data || records[0]) : {};
  const allKeys = Object.keys(sample).filter((k) => !['id', 'run_id', 'target_id', 'timestamp', 'is_simulated'].includes(k));

  // Filter records
  const filteredRecords = records.filter((r) => {
    if (!searchTerm.trim()) return true;
    const dataObj = r.data || r;
    return JSON.stringify(dataObj).toLowerCase().includes(searchTerm.toLowerCase());
  });

  const handleCopyJSON = () => {
    navigator.clipboard.writeText(JSON.stringify(records.map((r) => r.data || r), null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const getSeverityBadge = (sev: string = '') => {
    const s = String(sev).toUpperCase();
    if (s.includes('CRIT')) {
      return <Badge className="bg-rose-100 text-rose-800 border-rose-200 hover:bg-rose-200">CRITICAL</Badge>;
    } else if (s.includes('HIGH')) {
      return <Badge className="bg-amber-100 text-amber-800 border-amber-200 hover:bg-amber-200">HIGH</Badge>;
    } else if (s.includes('MED')) {
      return <Badge className="bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-200">MEDIUM</Badge>;
    } else {
      return <Badge className="bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200">{sev || 'INFO'}</Badge>;
    }
  };

  return (
    <div className="flex-1 max-w-7xl mx-auto w-full p-6 lg:p-8 flex flex-col justify-between space-y-6 animate-in fade-in duration-200 font-sans">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white font-mono text-xs flex items-center justify-center font-bold">
              2
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 font-mono tracking-tight">
              Harvested Cyber Threat Intelligence ({records.length} Records)
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 font-sans mt-0.5">
            Structured vulnerability, bug, and exploit dataset unlocked via Bright Data Scraper Studio.
          </p>
        </div>

        {/* Search, JSON Toggle & CSV Export */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <Input
              type="text"
              placeholder="Search vulnerabilities..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 h-9 font-mono text-xs w-48 sm:w-60 bg-white border-slate-300"
            />
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsJsonOpen(true)}
            className="flex items-center gap-1.5 font-mono text-xs border-slate-300 text-slate-700 cursor-pointer"
          >
            <Code className="w-3.5 h-3.5" />
            <span>VIEW JSON</span>
          </Button>

          {records.length > 0 && (
            <Button
              size="sm"
              onClick={onExportCSV}
              className="flex items-center gap-1.5 font-mono text-xs bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer shadow-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>EXPORT CSV</span>
            </Button>
          )}
        </div>
      </div>

      {/* Main Content Grid: Table (Left 65%) + Bright Data Console (Right 35%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Table Area (Col-Span 7) */}
        <div className="lg:col-span-7">
          <Card className="rounded-xl border-slate-200 bg-white shadow-xs overflow-hidden">
            {records.length === 0 ? (
              <div className="py-20 text-center text-slate-400 font-mono text-xs flex flex-col items-center justify-center space-y-3">
                <Database className="w-10 h-10 text-slate-300 stroke-[1.5]" />
                <p className="text-slate-600 font-semibold">No records extracted yet.</p>
                <p className="text-slate-400 text-xs max-w-sm">
                  Click 'Back to Target Selection' to run Bright Data Scraper Studio.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto max-h-[520px]">
                <Table className="font-mono text-xs">
                  <TableHeader className="bg-slate-50/80 sticky top-0 z-10">
                    <TableRow className="border-b border-slate-200">
                      <TableHead className="w-10 font-bold text-slate-800">#</TableHead>
                      <TableHead className="font-bold text-slate-800">CVE / Bug ID</TableHead>
                      <TableHead className="font-bold text-slate-800">Title / Software</TableHead>
                      <TableHead className="font-bold text-slate-800">Severity</TableHead>
                      <TableHead className="font-bold text-slate-800">Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody className="divide-y divide-slate-100">
                    {filteredRecords.map((r, idx) => {
                      const d = r.data || r;
                      const cveId = d.cve_id || d.id || d.title || `VULN-${idx + 1}`;
                      const title = d.title || d.vulnerability_title || d.name || d.product_name || 'Vulnerability Advisory';
                      const severity = d.severity || d.rating || 'HIGH';
                      const date = d.published_date || d.date || '2026-08-20';

                      return (
                        <TableRow key={idx} className="hover:bg-slate-50/80 transition-colors">
                          <TableCell className="text-slate-400 font-medium">{idx + 1}</TableCell>
                          <TableCell className="font-bold text-indigo-700">{cveId}</TableCell>
                          <TableCell className="text-slate-800 truncate max-w-xs">{title}</TableCell>
                          <TableCell>{getSeverityBadge(severity)}</TableCell>
                          <TableCell className="text-slate-500">{date}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </Card>
        </div>

        {/* Live Terminal Console (Col-Span 5) */}
        <div className="lg:col-span-5 h-[520px]">
          <BrightDataTerminal
            logs={terminalLogs}
            collectorId={collectorId}
            targetUrl={targetUrl}
          />
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <Button
          variant="outline"
          onClick={onBack}
          className="flex items-center gap-2 font-mono text-xs cursor-pointer border-slate-300 text-slate-700"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>BACK TO TARGET SELECTION</span>
        </Button>

        <Button
          onClick={onNext}
          className="flex items-center gap-2 px-6 py-5 rounded-xl font-mono text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-md cursor-pointer"
        >
          <span>PROCEED TO SELF-HEALING LAB</span>
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>

      {/* JSON Viewer Modal Dialog */}
      <Dialog open={isJsonOpen} onOpenChange={setIsJsonOpen}>
        <DialogContent className="max-w-3xl bg-slate-900 border-slate-800 text-slate-100 font-mono text-xs">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle className="text-sm font-mono text-slate-200">
                Harvested Structured JSON Payload ({records.length} Records)
              </DialogTitle>
              <Button
                size="sm"
                variant="outline"
                onClick={handleCopyJSON}
                className="flex items-center gap-1.5 bg-slate-800 border-slate-700 text-slate-200 hover:bg-slate-700 text-xs font-mono"
              >
                {copiedJson ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedJson ? 'COPIED' : 'COPY JSON'}</span>
              </Button>
            </div>
          </DialogHeader>
          <pre className="p-4 bg-slate-950 rounded-lg overflow-x-auto max-h-96 text-slate-300 text-[11px] leading-relaxed">
            {JSON.stringify(records.map((r) => r.data || r), null, 2)}
          </pre>
        </DialogContent>
      </Dialog>
    </div>
  );
}
