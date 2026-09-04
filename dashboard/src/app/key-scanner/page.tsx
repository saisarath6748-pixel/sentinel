// @ts-nocheck
/* eslint-disable */
"use client";

import { useState, useEffect } from 'react';
import { ScanLine, FolderSearch, GitBranch, AlertTriangle, CheckCircle2, Shield, FileWarning } from 'lucide-react';
import SpotlightCard from '@/components/SpotlightCard';
import PixelCard from '@/components/PixelCard';
import FloatingLines from '@/components/FloatingLines';

const LINES_GRADIENT = ["#94a3b8", "#6a6a6a", "#000000"];

interface Finding {
  file: string;
  line: number;
  name: string;
  matched?: string;
  confidence: number;
  fix: string;
}

interface ScanResult {
  findings: Finding[];
  total: number;
  scanned_path: string;
  summary: { high: number; medium: number; low: number };
}

function SeverityBadge({ confidence }: { confidence: number }) {
  if (confidence >= 0.85) {
    return (
      <span className="px-2 py-0.5 rounded-full bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-medium">
        HIGH
      </span>
    );
  }
  if (confidence >= 0.60) {
    return (
      <span className="px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-medium">
        MEDIUM
      </span>
    );
  }
  return (
    <span className="px-2 py-0.5 rounded-full bg-white/10 border border-white/20 text-white/70 text-xs font-medium">
      LOW
    </span>
  );
}

export default function KeyScannerPage() {
  const [repoPath, setRepoPath] = useState('');
  const [scanHistory, setScanHistory] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState('');

  const API_BASE = 'http://localhost:8000';

  const handleScan = async () => {
    if (!repoPath.trim()) return;
    setError('');
    setResult(null);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_path: repoPath.trim(), scan_history: scanHistory }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Scan failed');
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-transparent text-[#e2e8f0] p-8 font-sans selection:bg-[#EBF5FF] selection:text-[#0D94FB] relative overflow-hidden">
      {/* Background Floating Lines */}
      <div className="fixed inset-0 z-0 pointer-events-none bg-black">
        <FloatingLines
          linesGradient={LINES_GRADIENT}
          animationSpeed={1}
          interactive={false}
          bendRadius={8}
          bendStrength={-2}
          mouseDamping={0.05}
          parallax
          parallaxStrength={0.2}
        />
      </div>

      <div className="relative z-10">
      {/* Scan input */}
      <div className="rounded-3xl border border-white/20 shadow-2xl bg-white/5 backdrop-blur-md p-6 mb-8">
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1">
            <label className="block text-xs text-white/50 mb-1.5 font-medium uppercase tracking-wider">
              Repository Path
            </label>
            <div className="relative">
              <FolderSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
              <input
                type="text"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="C:\path\to\your\repo"
                onKeyDown={(e) => e.key === 'Enter' && handleScan()}
                className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/20 rounded-xl text-white text-sm font-mono placeholder-white/30 focus:outline-none focus:border-[#0D94FB] focus:ring-1 focus:ring-[#0D94FB] transition-colors shadow-inner"
              />
            </div>
          </div>

          <label className="flex items-center gap-2 cursor-pointer px-4 py-3 rounded-xl border border-white/20 bg-white/5 hover:bg-white/10 transition-colors shadow-sm">
            <input
              type="checkbox"
              checked={scanHistory}
              onChange={(e) => setScanHistory(e.target.checked)}
              className="w-4 h-4 rounded border-white/20 bg-white/10 text-[#0D94FB] focus:ring-[#0D94FB]/20"
            />
            <GitBranch className="w-4 h-4 text-white/50" />
            <span className="text-sm text-white/90 whitespace-nowrap">Git history</span>
          </label>

          <button
            onClick={handleScan}
            disabled={loading || !repoPath.trim()}
            className="flex items-center gap-2 px-6 py-3 bg-[#0D94FB] hover:bg-[#0D94FB]/90 text-white text-sm font-medium rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap shadow-md"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Scanning...
              </>
            ) : (
              <>
                <Shield className="w-4 h-4" />
                Scan Repository
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 bg-red-950/40 backdrop-blur-md border border-red-900 text-red-400 text-sm p-4 rounded-2xl mb-8 shadow-xl">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Stats row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <PixelCard
              colors={result.total > 0 ? "#dc2626,#f87171,#7f1d1d" : "#22c55e,#4ade80,#14532d"}
              speed={30}
              gap={6}
              className="h-28 p-5 bg-white/5 backdrop-blur-md border border-white/20 shadow-xl rounded-3xl"
            >
              <div className="flex flex-col h-full justify-between">
                <div className="flex items-center gap-2 text-white/70">
                  <FileWarning className="w-4 h-4" />
                  <span className="text-xs font-medium uppercase tracking-wider">Total</span>
                </div>
                <div className="text-3xl font-bold text-white">{result.total}</div>
              </div>
            </PixelCard>

            <div className="rounded-3xl border border-white/20 shadow-xl bg-white/5 backdrop-blur-md p-5 h-28 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-red-400">
                <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
                <span className="text-xs font-medium uppercase tracking-wider">High</span>
              </div>
              <div className="text-3xl font-bold text-red-400">{result.summary.high}</div>
            </div>

            <div className="rounded-3xl border border-white/20 shadow-xl bg-white/5 backdrop-blur-md p-5 h-28 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-amber-400">
                <span className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]" />
                <span className="text-xs font-medium uppercase tracking-wider">Medium</span>
              </div>
              <div className="text-3xl font-bold text-amber-400">{result.summary.medium}</div>
            </div>

            <div className="rounded-3xl border border-white/20 shadow-xl bg-white/5 backdrop-blur-md p-5 h-28 flex flex-col justify-between">
              <div className="flex items-center gap-2 text-white/50">
                <span className="w-2 h-2 rounded-full bg-white/50 shadow-[0_0_8px_rgba(255,255,255,0.4)]" />
                <span className="text-xs font-medium uppercase tracking-wider">Low</span>
              </div>
              <div className="text-3xl font-bold text-white/70">{result.summary.low}</div>
            </div>
          </div>

          {/* Scanned path */}
          <div className="text-xs text-white/50 mb-4 font-mono">
            Scanned: {result.scanned_path}
          </div>

          {/* Findings */}
          {result.total === 0 ? (
            <div className="text-center py-16 bg-white/5 backdrop-blur-md border border-white/20 rounded-3xl shadow-xl">
              <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-4 drop-shadow-[0_0_8px_rgba(74,222,128,0.5)]" />
              <p className="text-green-400 font-medium text-lg">Repository looks clean!</p>
              <p className="text-white/60 text-sm mt-1">No leaked keys or secrets detected.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {result.findings.map((finding, i) => (
                <SpotlightCard
                  key={`${finding.file}-${finding.line}-${i}`}
                  spotlightColor={
                    finding.confidence >= 0.85
                      ? "rgba(239, 68, 68, 0.1)"
                      : finding.confidence >= 0.60
                      ? "rgba(245, 158, 11, 0.1)"
                      : "rgba(13, 148, 251, 0.1)"
                  }
                  className="p-0 bg-white/5 backdrop-blur-md border-white/20 shadow-2xl !rounded-3xl"
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <SeverityBadge confidence={finding.confidence} />
                        <h3 className="text-sm font-semibold text-white">{finding.name}</h3>
                      </div>
                      <span className="text-xs text-white/50 font-mono">
                        {(finding.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                      <div>
                        <span className="text-xs text-white/40 uppercase tracking-wider">File</span>
                        <p className="text-sm text-white/90 font-mono mt-0.5">
                          {finding.file}
                          {finding.line > 0 && <span className="text-[#0D94FB]">:{finding.line}</span>}
                        </p>
                      </div>
                      {finding.matched && (
                        <div>
                          <span className="text-xs text-white/40 uppercase tracking-wider">Match</span>
                          <p className="text-sm text-white/60 font-mono mt-0.5 truncate bg-white/5 px-2 py-0.5 rounded border border-white/10 inline-block">
                            {finding.matched}
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="rounded-xl border border-white/10 bg-white/5 p-4 mt-3 shadow-inner">
                      <span className="text-xs text-white/40 uppercase tracking-wider">Suggested Fix</span>
                      <p className="text-sm text-white/90 mt-1.5 leading-relaxed">{finding.fix}</p>
                    </div>
                  </div>
                </SpotlightCard>
              ))}
            </div>
          )}
        </>
      )}

      {/* Empty state (no scan yet) */}
      {!result && !error && !loading && (
        <div className="text-center py-20 text-white/60 bg-white/5 backdrop-blur-md border border-white/20 rounded-3xl shadow-xl">
          <FolderSearch className="w-12 h-12 mx-auto mb-4 text-white/40" />
          <p className="text-lg font-medium text-white">Enter a repository path to scan</p>
          <p className="text-sm mt-1">The scanner checks for leaked API keys, secrets, and .gitignore coverage</p>
        </div>
      )}
      </div>
    </div>
  );
}
