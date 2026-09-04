"use client";

import React, { useState } from 'react';
import Image from 'next/image';
import { ShieldAlert, Mail, Lock, ArrowRight, AlertCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthContext';
import FloatingLines from '@/components/FloatingLines';

const LINES_GRADIENT = ["#94a3b8", "#6a6a6a", "#000000"];

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 overflow-hidden bg-[#0A101D]">
      {/* Background Floating Lines */}
      <div className="fixed inset-0 z-0">
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

      <div className="relative z-10 w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-12">
          <Image src="/logo.png" alt="Sentinel Logo" width={400} height={120} style={{ width: 'auto', height: 'auto' }} className="w-96 h-auto object-contain mb-2" priority />
        </div>

        {/* Login Card */}
        <div className="bg-white/5 backdrop-blur-md border border-white/20 shadow-2xl rounded-3xl p-8">
          <h2 className="text-2xl font-bold text-[#e2e8f0] mb-1">Sign in</h2>
          <p className="text-[#cbd5e1] text-sm mb-6 font-medium">Enter your merchant credentials to continue</p>

          {error && (
            <div className="flex items-center gap-2 bg-red-950/30 border border-red-900/50 text-red-400 text-sm p-3 rounded-xl mb-6">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs text-[#94a3b8] mb-1.5 font-bold uppercase tracking-wider">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#94a3b8]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="merchant@demo.sentinel"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white text-sm placeholder-white/40 focus:bg-white/20 focus:outline-none focus:border-[#0D94FB] focus:ring-1 focus:ring-[#0D94FB] transition-all shadow-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-[#94a3b8] mb-1.5 font-bold uppercase tracking-wider">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#94a3b8]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white text-sm placeholder-white/40 focus:bg-white/20 focus:outline-none focus:border-[#0D94FB] focus:ring-1 focus:ring-[#0D94FB] transition-all shadow-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 bg-[#0D94FB] hover:bg-[#0D94FB]/90 text-white text-sm font-medium rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}
