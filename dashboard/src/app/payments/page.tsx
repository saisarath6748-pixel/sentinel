// @ts-nocheck
/* eslint-disable */
"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  CreditCard, 
  RefreshCcw, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Search, 
  Copy, 
  Check, 
  ShieldAlert, 
  ArrowUpRight,
  ExternalLink,
  Activity,
  Layers,
  ArrowRight
} from 'lucide-react';
import FloatingLines from '@/components/FloatingLines';
import { useAuth } from '@/components/AuthContext';

interface Payment {
  payment_id: string;
  order_id: string;
  amount: number;
  email: string;
  contact: string;
  method: string;
  card_id: string;
  created_at: string;
  status: string;
  account_id: string;
  is_flagged_ring: boolean;
  cluster_id?: string;
}

const LINES_GRADIENT = ["#94a3b8", "#6a6a6a", "#000000"];

export default function PaymentsPage() {
  const { merchantId, merchantName, isAuthenticated, token } = useAuth();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isSyncing, setIsSyncing] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'captured' | 'failed' | 'flagged'>('all');

  const API_BASE = 'http://localhost:8000';
  const isGamma = merchantName === 'Gamma Groceries' || merchantId === '1ed1d417-6ce7-4b1d-ba96-1a08097b591a';

  const fetchPayments = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError('');
      const res = await fetch(`${API_BASE}/razorpay/payments`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to fetch payments');
      }
      const data = await res.json();
      setPayments(data.payments || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && token) {
      if (isGamma) {
        fetchPayments();
      } else {
        setLoading(false);
      }
    }
  }, [isAuthenticated, token, isGamma]);

  const handleSync = async () => {
    if (!token || isSyncing) return;
    setIsSyncing(true);
    try {
      const res = await fetch(`${API_BASE}/razorpay/ingest`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await res.json();
      if (res.ok) {
        await fetchPayments();
      } else {
        alert(`Sync failed: ${data.detail}`);
      }
    } catch (err: any) {
      alert('Error connecting to backend for sync.');
    } finally {
      setIsSyncing(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(text);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Filtered list
  const filteredPayments = payments.filter((p) => {
    const matchesSearch = 
      p.payment_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.contact.includes(searchQuery);

    if (!matchesSearch) return false;

    if (statusFilter === 'captured') return p.status === 'captured';
    if (statusFilter === 'failed') return p.status === 'failed';
    if (statusFilter === 'flagged') return p.is_flagged_ring;

    return true;
  });

  const totalVolume = payments.reduce((acc, p) => p.status === 'captured' ? acc + p.amount : acc, 0);
  const capturedCount = payments.filter(p => p.status === 'captured').length;
  const failedCount = payments.filter(p => p.status === 'failed').length;
  const flaggedCount = payments.filter(p => p.is_flagged_ring).length;

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

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                Live Payments
              </h1>
              {isGamma && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  Razorpay Test Mode Connected
                </span>
              )}
            </div>
            <p className="text-white/60 text-sm mt-1">
              {isGamma 
                ? 'Real-time test payments ingested from Razorpay API and analyzed for coordinated ring activity.' 
                : `Viewing transactions for ${merchantName || 'Merchant'}.`}
            </p>
          </div>

          {isGamma && (
            <div className="flex items-center gap-3">
              <button 
                onClick={handleSync}
                disabled={isSyncing}
                className="px-4 py-2.5 bg-[#0D94FB] hover:bg-[#0b82dc] disabled:opacity-50 text-white rounded-xl text-sm font-semibold transition-all flex items-center gap-2 shadow-lg shadow-[#0D94FB]/20"
              >
                <RefreshCcw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
                {isSyncing ? 'Syncing from Razorpay...' : 'Sync Razorpay'}
              </button>
            </div>
          )}
        </header>

        {/* Non-Gamma warning */}
        {!isGamma && (
          <div className="mb-8 p-6 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-md">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0 text-[#0D94FB]">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-base">Live Razorpay Test Sync is enabled on Gamma Groceries</h3>
                <p className="text-white/60 text-sm mt-1">
                  <strong>Alpha Electronics</strong> and <strong>Beta Fashion</strong> use pre-calculated multi-merchant synthetic data to showcase cross-merchant rings. 
                  To test real-time Razorpay test-mode payment syncing, switch to the <strong>Gamma Groceries</strong> demo merchant account.
                </p>
                <div className="mt-4 flex items-center gap-3">
                  <Link
                    href="/"
                    className="inline-flex items-center gap-2 text-xs font-semibold text-[#0D94FB] hover:underline"
                  >
                    View Ring Detector <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {isGamma && (
          <>
            {/* Stats Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
              <div className="rounded-2xl border border-white/15 bg-white/[0.04] backdrop-blur-md p-5 flex flex-col justify-between shadow-xl">
                <div className="flex items-center justify-between text-white/60 text-xs font-medium uppercase tracking-wider">
                  <span>Total Payments</span>
                  <CreditCard className="w-4 h-4 text-[#0D94FB]" />
                </div>
                <div className="mt-3">
                  <div className="text-3xl font-bold text-white">{payments.length}</div>
                  <div className="text-xs text-white/40 mt-1">From Razorpay Test API</div>
                </div>
              </div>

              <div className="rounded-2xl border border-white/15 bg-white/[0.04] backdrop-blur-md p-5 flex flex-col justify-between shadow-xl">
                <div className="flex items-center justify-between text-white/60 text-xs font-medium uppercase tracking-wider">
                  <span>Captured Volume</span>
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="mt-3">
                  <div className="text-3xl font-bold text-emerald-400">
                    ₹{totalVolume.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                  <div className="text-xs text-white/40 mt-1">{capturedCount} successful payments</div>
                </div>
              </div>

              <div className="rounded-2xl border border-white/15 bg-white/[0.04] backdrop-blur-md p-5 flex flex-col justify-between shadow-xl">
                <div className="flex items-center justify-between text-white/60 text-xs font-medium uppercase tracking-wider">
                  <span>Failed Attempts</span>
                  <XCircle className="w-4 h-4 text-rose-400" />
                </div>
                <div className="mt-3">
                  <div className="text-3xl font-bold text-rose-400">{failedCount}</div>
                  <div className="text-xs text-white/40 mt-1">Card testing / auth failures</div>
                </div>
              </div>

              <div className="rounded-2xl border border-red-500/30 bg-red-500/[0.05] backdrop-blur-md p-5 flex flex-col justify-between shadow-xl">
                <div className="flex items-center justify-between text-red-400 text-xs font-medium uppercase tracking-wider">
                  <span>Ring Flagged</span>
                  <ShieldAlert className="w-4 h-4 text-red-400" />
                </div>
                <div className="mt-3">
                  <div className="text-3xl font-bold text-white">{flaggedCount}</div>
                  <div className="text-xs text-red-300/60 mt-1">Linked to coordinated ring</div>
                </div>
              </div>
            </div>

            {/* Filter and Search Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
              {/* Search input */}
              <div className="relative w-full sm:w-80">
                <Search className="w-4 h-4 text-white/40 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search ID, email, or phone..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/15 rounded-xl text-sm text-white placeholder-white/30 focus:outline-none focus:border-[#0D94FB] transition-colors"
                />
              </div>

              {/* Status filter tabs */}
              <div className="flex items-center gap-1.5 p-1 bg-white/5 border border-white/15 rounded-xl text-xs self-stretch sm:self-auto overflow-x-auto">
                <button
                  onClick={() => setStatusFilter('all')}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                    statusFilter === 'all' 
                      ? 'bg-[#0D94FB] text-white shadow' 
                      : 'text-white/60 hover:text-white hover:bg-white/5'
                  }`}
                >
                  All ({payments.length})
                </button>
                <button
                  onClick={() => setStatusFilter('captured')}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                    statusFilter === 'captured' 
                      ? 'bg-emerald-500 text-white shadow' 
                      : 'text-white/60 hover:text-white hover:bg-white/5'
                  }`}
                >
                  Captured ({capturedCount})
                </button>
                <button
                  onClick={() => setStatusFilter('failed')}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                    statusFilter === 'failed' 
                      ? 'bg-rose-500 text-white shadow' 
                      : 'text-white/60 hover:text-white hover:bg-white/5'
                  }`}
                >
                  Failed ({failedCount})
                </button>
                <button
                  onClick={() => setStatusFilter('flagged')}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                    statusFilter === 'flagged' 
                      ? 'bg-red-600 text-white shadow' 
                      : 'text-white/60 hover:text-white hover:bg-white/5'
                  }`}
                >
                  Abuse Rings ({flaggedCount})
                </button>
              </div>
            </div>

            {/* Payments Table */}
            {loading ? (
              <div className="text-center py-20 text-white/60 flex flex-col items-center">
                <div className="w-8 h-8 border-4 border-[#0D94FB]/30 border-t-[#0D94FB] rounded-full animate-spin mb-4" />
                Loading recent payments from Razorpay...
              </div>
            ) : error ? (
              <div className="bg-red-950/40 backdrop-blur-md border border-red-900 text-red-400 p-6 rounded-3xl shadow-xl">
                Error loading payments: {error}
              </div>
            ) : filteredPayments.length === 0 ? (
              <div className="text-center py-20 text-white/60 bg-white/5 backdrop-blur-md border border-white/20 rounded-3xl shadow-xl">
                {searchQuery || statusFilter !== 'all' 
                  ? 'No payments match the active filter or search query.' 
                  : 'No payments found. Click "Sync Razorpay" to fetch test payments.'}
              </div>
            ) : (
              <div className="rounded-2xl border border-white/15 bg-white/[0.03] backdrop-blur-md shadow-2xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-white/10 bg-white/[0.02] text-xs font-semibold uppercase tracking-wider text-white/50">
                        <th className="py-3.5 px-4">Payment ID</th>
                        <th className="py-3.5 px-4">Customer</th>
                        <th className="py-3.5 px-4">Amount</th>
                        <th className="py-3.5 px-4">Method & Card</th>
                        <th className="py-3.5 px-4">Status</th>
                        <th className="py-3.5 px-4">Abuse Ring Risk</th>
                        <th className="py-3.5 px-4">Created</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5 font-normal">
                      {filteredPayments.map((p) => {
                        return (
                          <tr 
                            key={p.payment_id}
                            className={`hover:bg-white/[0.04] transition-colors ${
                              p.is_flagged_ring ? 'bg-red-500/[0.02]' : ''
                            }`}
                          >
                            {/* Payment ID */}
                            <td className="py-3.5 px-4 whitespace-nowrap">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-xs text-white font-medium">
                                  {p.payment_id}
                                </span>
                                <button
                                  onClick={() => copyToClipboard(p.payment_id)}
                                  className="text-white/40 hover:text-white transition-colors"
                                  title="Copy payment ID"
                                >
                                  {copiedId === p.payment_id ? (
                                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                                  ) : (
                                    <Copy className="w-3.5 h-3.5" />
                                  )}
                                </button>
                              </div>
                            </td>

                            {/* Customer Email & Phone */}
                            <td className="py-3.5 px-4">
                              <div className="flex flex-col">
                                <span className="text-white text-xs font-medium truncate max-w-[200px]" title={p.email}>
                                  {p.email}
                                </span>
                                <span className="text-white/40 text-[11px] font-mono mt-0.5">
                                  {p.contact || 'No contact'}
                                </span>
                              </div>
                            </td>

                            {/* Amount */}
                            <td className="py-3.5 px-4 whitespace-nowrap">
                              <span className="text-white font-semibold text-sm">
                                ₹{p.amount.toFixed(2)}
                              </span>
                            </td>

                            {/* Method & Card */}
                            <td className="py-3.5 px-4 whitespace-nowrap">
                              <div className="flex items-center gap-2">
                                <span className="text-white/70 text-xs capitalize">
                                  {p.method}
                                </span>
                                {p.card_id && (
                                  <span className="font-mono text-[10px] bg-white/10 text-white/70 px-1.5 py-0.5 rounded border border-white/10">
                                    {p.card_id.slice(-8)}
                                  </span>
                                )}
                              </div>
                            </td>

                            {/* Status */}
                            <td className="py-3.5 px-4 whitespace-nowrap">
                              {p.status === 'captured' ? (
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                  <CheckCircle2 className="w-3 h-3" />
                                  Captured
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                                  <XCircle className="w-3 h-3" />
                                  {p.status}
                                </span>
                              )}
                            </td>

                            {/* Abuse Ring Risk */}
                            <td className="py-3.5 px-4 whitespace-nowrap">
                              {p.is_flagged_ring ? (
                                <Link
                                  href="/"
                                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/15 text-red-400 border border-red-500/30 hover:bg-red-500/25 transition-all group"
                                  title="Click to view ring in detector"
                                >
                                  <ShieldAlert className="w-3.5 h-3.5 text-red-400 animate-pulse" />
                                  <span>Ring Flagged</span>
                                  {p.cluster_id && (
                                    <span className="text-[10px] text-red-300 font-mono">({p.cluster_id})</span>
                                  )}
                                  <ArrowUpRight className="w-3 h-3 text-red-400 opacity-70 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                                </Link>
                              ) : (
                                <span className="inline-flex items-center gap-1.5 text-xs text-white/40">
                                  <span className="w-1.5 h-1.5 rounded-full bg-white/30" />
                                  Normal
                                </span>
                              )}
                            </td>

                            {/* Created At */}
                            <td className="py-3.5 px-4 whitespace-nowrap text-xs text-white/50">
                              {p.created_at ? new Date(p.created_at).toLocaleString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                                hour12: true
                              }) : '—'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
