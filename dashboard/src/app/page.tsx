// @ts-nocheck
/* eslint-disable */
"use client";

import FloatingLines from '@/components/FloatingLines';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { AlertCircle, ShieldAlert, Activity, Users, Database, Zap, ChevronDown, CreditCard, Phone, MapPin, Mail, DollarSign } from 'lucide-react';
import SpotlightCard from '@/components/SpotlightCard';
import PixelCard from '@/components/PixelCard';
import { useAuth } from '@/components/AuthContext';
import TextType from '@/components/TextType';

interface ExactSignal {
  signal: string;
  type: 'card' | 'address' | 'device' | 'phone';
  label: string;
  value: string;
}

interface LinkedAccountDetail {
  account_id: string;
  email: string;
  phone: string;
  card_label: string;
  order_id: string;
  amount: number;
  status: string;
  order_time: string;
}

interface Cluster {
  cluster_id: string;
  account_ids: string[];
  shared_signals: string[];
  num_accounts: number;
  score: number;
  flagged_for_review: boolean;
  breakdown: {
    signal_overlap: number;
    cluster_size: number;
    timing_tightness: number;
    behavior_abuse: number;
  };
  exact_shared_signals?: ExactSignal[];
  linked_accounts_detail?: LinkedAccountDetail[];
  total_volume?: number;
  currency?: string;
  emails?: string[];
  phones?: string[];
}

const LINES_GRADIENT = ["#94a3b8", "#6a6a6a", "#000000"];

export default function Home() {
  const { merchantId, merchantName, isAuthenticated } = useAuth();
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [explaining, setExplaining] = useState<string | null>(null);
  const [explanations, setExplanations] = useState<Record<string, string>>(() => {
    if (typeof window !== 'undefined') {
      try {
        const cached = sessionStorage.getItem('sentinel_explanations');
        return cached ? JSON.parse(cached) : {};
      } catch { return {}; }
    }
    return {};
  });
  const [aiSummary, setAiSummary] = useState('');
  const [shouldAnimateSummary, setShouldAnimateSummary] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [expandedCluster, setExpandedCluster] = useState<string | null>(null);

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    if (isAuthenticated && merchantId) {
      fetchClusters();
    }
  }, [isAuthenticated, merchantId]);

  useEffect(() => {
    const handleSyncEvent = () => {
      fetchClusters();
    };
    window.addEventListener('sentinel-data-synced', handleSyncEvent);
    return () => window.removeEventListener('sentinel-data-synced', handleSyncEvent);
  }, [merchantId]);

  const handleManualRefresh = () => {
    setShouldAnimateSummary(true);
    setRefreshKey(prev => prev + 1);
    fetchClusters();
  };

  const fetchClusters = async () => {
    try {
      setLoading(true);
      const url = merchantId
        ? `${API_BASE}/clusters/flagged?merchant_id=${merchantId}`
        : `${API_BASE}/clusters/flagged`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch clusters');
      const data = await res.json();
      setClusters(data.clusters || []);
      generateSummary(data.clusters || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateSummary = (clusterData: Cluster[]) => {
    const cacheKey = `sentinel_last_cluster_count_${merchantId || 'default'}`;
    
    if (clusterData.length === 0) {
      setAiSummary('Scan Complete: No suspicious activity or fraud rings detected in the latest scan.');
      localStorage.setItem(cacheKey, '0');
    } else {
      const lastCountStr = localStorage.getItem(cacheKey);
      const lastCount = lastCountStr ? parseInt(lastCountStr, 10) : null;
      
      const totalAccounts = clusterData.reduce((acc, c) => acc + c.num_accounts, 0);
      const signalCounts: Record<string, number> = {};
      
      clusterData.forEach(c => {
        c.shared_signals.forEach(s => {
          signalCounts[s] = (signalCounts[s] || 0) + 1;
        });
      });
      
      const signalLabels: Record<string, string> = {
        device_hash: 'shared devices',
        address_hash: 'shared addresses',
        card_hash: 'shared payment methods',
      };

      const topSignals = Object.entries(signalCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 2)
        .map(s => signalLabels[s[0]] || s[0]);
      
      let signalsText = '';
      if (topSignals.length > 0) {
        signalsText = ` Primary indicators include ${topSignals.join(' and ')}.`;
      }
      
      if (lastCount !== null && lastCount === clusterData.length) {
        setAiSummary(`No new detections since last scan. Previous analytics: ${clusterData.length} abuse rings involving ${totalAccounts} accounts.${signalsText}`);
      } else {
        setAiSummary(`Analysis Complete: Detected ${clusterData.length} abuse rings involving ${totalAccounts} accounts.${signalsText}`);
      }
      
      localStorage.setItem(cacheKey, clusterData.length.toString());
    }
    
    if (sessionStorage.getItem('sentinel_animate_summary') === 'true') {
      setShouldAnimateSummary(true);
      sessionStorage.removeItem('sentinel_animate_summary');
    }
  };

  const handleExplain = async (clusterId: string) => {
    if (explanations[clusterId]) return;
    try {
      setExplaining(clusterId);
      const res = await fetch(`${API_BASE}/clusters/${clusterId}/explain`);
      if (!res.ok) throw new Error('Failed to get explanation');
      const data = await res.json();
      setExplanations(prev => {
        const updated = { ...prev, [clusterId]: data.explanation };
        sessionStorage.setItem('sentinel_explanations', JSON.stringify(updated));
        return updated;
      });
    } catch (err: any) {
      console.error(err);
      setExplanations(prev => {
        const updated = { ...prev, [clusterId]: `Error: ${err.message}` };
        sessionStorage.setItem('sentinel_explanations', JSON.stringify(updated));
        return updated;
      });
    } finally {
      setExplaining(null);
    }
  };

  return (
    <div className="min-h-screen bg-transparent text-[#e2e8f0] p-8 font-sans selection:bg-[#EBF5FF] selection:text-[#0D94FB] relative overflow-hidden">
      {/* Background layer */}
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
      
      {/* Header */}
      <header className="flex items-center justify-between mb-12">
        <div className="flex-1 mr-8">
          {aiSummary && (
            <div className="text-base font-medium text-white flex items-center min-h-[54px]">
              {shouldAnimateSummary ? (
                <TextType 
                  key={refreshKey}
                  text={aiSummary} 
                  loop={false}
                  typingSpeed={30}
                  cursorBlinkDuration={0.8}
                />
              ) : (
                <span>{aiSummary}</span>
              )}
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-4">
          <button onClick={handleManualRefresh} className="px-5 py-2.5 bg-white/10 hover:bg-white/20 border border-white/20 backdrop-blur-md rounded-xl text-sm font-medium text-white transition-colors flex items-center gap-2 whitespace-nowrap shadow-sm">
            <Activity className="w-4 h-4 text-[#0D94FB]" />
            Refresh Data
          </button>
        </div>
      </header>

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
        <div className="rounded-3xl border border-white/20 shadow-xl bg-white/5 backdrop-blur-md p-6 h-32 flex flex-col justify-between">
          <div className="flex items-center gap-2 text-white/70">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm font-medium">Flagged Clusters</span>
          </div>
          <div className="text-4xl font-bold text-white">{clusters.length}</div>
        </div>
        
        <div className="rounded-3xl border border-white/20 shadow-xl bg-white/5 backdrop-blur-md p-6 h-32 flex flex-col justify-between">
          <div className="flex items-center gap-2 text-white/70">
            <Users className="w-4 h-4" />
            <span className="text-sm font-medium">Affected Accounts</span>
          </div>
          <div className="text-4xl font-bold text-white">
            {clusters.reduce((acc, c) => acc + c.num_accounts, 0)}
          </div>
        </div>
      </div>

      {/* Main Content */}
      {loading ? (
        <div className="text-center py-20 text-white/60 flex flex-col items-center">
          <div className="w-8 h-8 border-4 border-[#0D94FB]/30 border-t-[#0D94FB] rounded-full animate-spin mb-4" />
          Loading clusters...
        </div>
      ) : error ? (
        <div className="bg-red-950/40 backdrop-blur-md border border-red-900 text-red-400 p-6 rounded-3xl shadow-xl">
          Error: {error}
        </div>
      ) : clusters.length === 0 ? (
        <div className="text-center py-16 px-6 text-white/60 bg-white/5 backdrop-blur-md border border-white/20 rounded-3xl shadow-xl flex flex-col items-center max-w-xl mx-auto">
          <ShieldAlert className="w-10 h-10 text-white/30 mb-3" />
          <p className="text-base text-white/90 font-medium">No flagged clusters found for this merchant.</p>
          {merchantName === 'Gamma Groceries' ? (
            <div className="mt-4 flex flex-col sm:flex-row items-center gap-3">
              <button
                onClick={handleManualRefresh}
                className="px-4 py-2 bg-[#0D94FB] hover:bg-[#0b82dc] text-white rounded-xl text-xs font-semibold transition-all shadow-md flex items-center gap-2"
              >
                <Activity className="w-3.5 h-3.5" />
                Refresh Detection
              </button>
              <Link
                href="/payments"
                className="px-4 py-2 bg-white/10 hover:bg-white/15 text-white rounded-xl text-xs font-semibold transition-all border border-white/10 flex items-center gap-1.5"
              >
                View Live Payments
              </Link>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="space-y-2">
          {clusters.map((cluster) => {
            const isExpanded = expandedCluster === cluster.cluster_id;
            return (
              <div key={cluster.cluster_id} className="rounded-2xl border border-white/15 shadow-lg bg-white/[0.03] backdrop-blur-md overflow-hidden">
                {/* Collapsed row */}
                <button
                  onClick={() => {
                    setExpandedCluster(isExpanded ? null : cluster.cluster_id);
                    if (!isExpanded && !explanations[cluster.cluster_id]) {
                      handleExplain(cluster.cluster_id);
                    }
                  }}
                  className="w-full px-5 py-4 text-left hover:bg-white/[0.04] transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <ShieldAlert className="w-5 h-5 text-[#0D94FB] flex-shrink-0" />
                      <div>
                        <div className="flex items-center gap-3">
                          <span className="text-white font-semibold text-[15px]">{cluster.cluster_id}</span>
                          <span className="px-2 py-0.5 bg-[#0D94FB]/15 text-[#0D94FB] border border-[#0D94FB]/30 rounded-full text-xs font-semibold">
                            {cluster.score.toFixed(3)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                          <span className="text-white/40 text-xs">{cluster.num_accounts} accounts</span>
                          <span className="text-white/20">·</span>
                          {cluster.exact_shared_signals && cluster.exact_shared_signals.length > 0 ? (
                            cluster.exact_shared_signals.map((sig, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium bg-[#0D94FB]/10 text-[#0D94FB] border border-[#0D94FB]/20"
                              >
                                {sig.type === 'card' && <CreditCard className="w-3 h-3" />}
                                {sig.type === 'phone' && <Phone className="w-3 h-3" />}
                                {sig.type === 'address' && <MapPin className="w-3 h-3" />}
                                {sig.type === 'device' && <ShieldAlert className="w-3 h-3" />}
                                {sig.label}: {sig.value}
                              </span>
                            ))
                          ) : (
                            <span className="text-white/40 text-xs">{cluster.shared_signals.join(', ')}</span>
                          )}
                          {cluster.total_volume !== undefined && cluster.total_volume > 0 && (
                            <>
                              <span className="text-white/20">·</span>
                              <span className="text-emerald-400 text-xs font-semibold">
                                {cluster.currency === 'INR' ? '₹' : '$'}{cluster.total_volume.toLocaleString()} vol
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <ChevronDown className={`w-4 h-4 text-white/30 flex-shrink-0 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} />
                  </div>
                </button>

                {/* Expanded panel */}
                {isExpanded && (
                  <div className="px-5 pb-5 border-t border-white/10">
                    {/* AI Explanation */}
                    <div className="mt-4 mb-4">
                      {explaining === cluster.cluster_id ? (
                        <div className="flex items-center gap-3 text-white/50 text-sm py-3">
                          <div className="w-4 h-4 border-2 border-[#0D94FB]/30 border-t-[#0D94FB] rounded-full animate-spin" />
                          Analyzing ring pattern...
                        </div>
                      ) : explanations[cluster.cluster_id] ? (
                        <div className="p-4 bg-[#0D94FB]/5 border border-[#0D94FB]/15 text-white/90 text-sm leading-relaxed rounded-xl">
                          <div className="flex items-center gap-1.5 text-[#0D94FB] text-[11px] font-bold uppercase tracking-widest mb-2">
                            <Zap className="w-3 h-3" />
                            AI Analysis
                          </div>
                          {explanations[cluster.cluster_id]}
                        </div>
                      ) : null}
                    </div>

                    {/* Details */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
                      {/* Risk Breakdown */}
                      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 flex flex-col justify-between">
                        <div>
                          <div className="text-[11px] text-white/40 font-bold uppercase tracking-widest mb-3">Risk Breakdown</div>
                          <div className="space-y-2.5">
                            {[
                              { label: 'Signal Overlap', value: cluster.breakdown.signal_overlap },
                              { label: 'Timing Window', value: cluster.breakdown.timing_tightness },
                              { label: 'Behavioral Abuse', value: cluster.breakdown.behavior_abuse },
                            ].map(item => (
                              <div key={item.label}>
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="text-white/50">{item.label}</span>
                                  <span className="text-white font-medium">{(item.value * 100).toFixed(0)}%</span>
                                </div>
                                <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                                  <div className="h-full bg-[#0D94FB] rounded-full transition-all" style={{ width: `${item.value * 100}%` }} />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                        {cluster.total_volume !== undefined && cluster.total_volume > 0 && (
                          <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs">
                            <span className="text-white/40">Total Ring Volume:</span>
                            <span className="text-emerald-400 font-bold text-sm">
                              {cluster.currency === 'INR' ? '₹' : '$'}{cluster.total_volume.toLocaleString()}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Shared Signals */}
                      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
                        <div className="text-[11px] text-white/40 font-bold uppercase tracking-widest mb-3">Exact Shared Signals</div>
                        <div className="space-y-2.5">
                          {cluster.exact_shared_signals && cluster.exact_shared_signals.length > 0 ? (
                            cluster.exact_shared_signals.map((sig, idx) => (
                              <div key={idx} className="p-3 rounded-lg bg-white/5 border border-white/10 flex items-start gap-3">
                                <div className="p-2 rounded-md bg-[#0D94FB]/15 text-[#0D94FB] mt-0.5 flex-shrink-0">
                                  {sig.type === 'card' && <CreditCard className="w-4 h-4" />}
                                  {sig.type === 'phone' && <Phone className="w-4 h-4" />}
                                  {sig.type === 'address' && <MapPin className="w-4 h-4" />}
                                  {sig.type === 'device' && <ShieldAlert className="w-4 h-4" />}
                                </div>
                                <div className="min-w-0 flex-1">
                                  <div className="text-[10px] text-white/40 uppercase font-bold tracking-wider">{sig.label}</div>
                                  <div className="text-xs font-semibold text-white mt-0.5 break-all">{sig.value}</div>
                                </div>
                              </div>
                            ))
                          ) : (
                            <div className="flex flex-wrap gap-2">
                              {cluster.shared_signals.map(sig => (
                                <span key={sig} className="px-2.5 py-1 bg-white/10 text-xs text-white rounded-lg border border-white/10">
                                  {sig}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Linked Accounts */}
                      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 flex flex-col">
                        <div className="flex items-center justify-between mb-3">
                          <div className="text-[11px] text-white/40 font-bold uppercase tracking-widest">
                            Linked Accounts ({cluster.num_accounts})
                          </div>
                        </div>
                        <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                          {cluster.linked_accounts_detail && cluster.linked_accounts_detail.length > 0 ? (
                            cluster.linked_accounts_detail.map((acct) => (
                              <div key={acct.account_id} className="p-2.5 rounded-lg bg-white/5 border border-white/10 text-xs">
                                <div className="flex items-center justify-between gap-2">
                                  <span className="font-mono text-[11px] text-[#0D94FB] font-semibold">{acct.account_id}</span>
                                  <span className="text-emerald-400 font-bold text-xs whitespace-nowrap">
                                    {cluster.currency === 'INR' ? '₹' : '$'}{acct.amount.toFixed(2)}
                                  </span>
                                </div>
                                <div className="text-[11px] text-white/70 truncate mt-1" title={acct.email}>{acct.email}</div>
                                <div className="flex items-center justify-between mt-1.5 text-[10px] text-white/40">
                                  <span className="font-mono truncate max-w-[130px]" title={acct.order_id}>{acct.order_id}</span>
                                  <span>{acct.order_time ? new Date(acct.order_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
                                </div>
                              </div>
                            ))
                          ) : (
                            <div className="flex flex-wrap gap-1.5">
                              {cluster.account_ids.map(id => (
                                <span key={id} className="text-[11px] font-mono text-white/70 bg-white/5 border border-white/10 rounded-md px-2 py-0.5">{id}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
      </div>
    </div>
  );
}
