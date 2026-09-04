// @ts-nocheck
/* eslint-disable */
"use client";

import React, { useState, useRef } from 'react';
import { useAuth } from '@/components/AuthContext';
import { Save, User, KeyRound, Upload, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import FloatingLines from '@/components/FloatingLines';

const LINES_GRADIENT = ["#94a3b8", "#6a6a6a", "#000000"];

export default function ProfilePage() {
  const { merchantName, merchantAvatar, updateProfile } = useAuth();
  
  const [name, setName] = useState(merchantName || '');
  const [password, setPassword] = useState('');
  const [avatarPreview, setAvatarPreview] = useState<string | null>(merchantAvatar);
  const [avatarData, setAvatarData] = useState<string | null>(null);
  const [avatarFilename, setAvatarFilename] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setMessage({ type: 'error', text: 'Please select an image file.' });
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setMessage({ type: 'error', text: 'Image must be less than 5MB.' });
      return;
    }

    setAvatarFilename(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const base64 = event.target?.result as string;
      setAvatarPreview(base64);
      setAvatarData(base64);
    };
    reader.readAsDataURL(file);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage(null);

    try {
      await updateProfile(
        name,
        password || undefined,
        avatarData || undefined,
        avatarFilename || undefined
      );
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      setPassword(''); // Clear password field after save
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to update profile.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-transparent text-[#e2e8f0] pt-24 px-8 pb-12 font-sans selection:bg-[#EBF5FF] selection:text-[#0D94FB] relative overflow-hidden">
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

      <div className="relative z-10 max-w-2xl mx-auto">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-white/60 hover:text-white transition-colors mb-6">
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
        
        <div className="bg-white/5 backdrop-blur-md rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
          <div className="px-8 py-6 border-b border-white/10 bg-white/5">
            <h1 className="text-2xl font-bold text-white">Profile Settings</h1>
            <p className="text-sm text-white/60 mt-1">Manage your account details and profile picture.</p>
          </div>
          
          <form onSubmit={handleSave} className="p-8">
            {message && (
              <div className={`mb-6 p-4 rounded-xl text-sm font-medium ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                {message.text}
              </div>
            )}

            <div className="flex flex-col md:flex-row gap-8 mb-8">
              {/* Avatar Section */}
              <div className="flex flex-col items-center gap-4">
                <div className="relative w-32 h-32 rounded-full overflow-hidden border-4 border-white/10 shadow-lg bg-white/5 group">
                  {avatarPreview ? (
                    <img src={avatarPreview} alt="Avatar" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <User className="w-16 h-16" />
                    </div>
                  )}
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                  >
                    <Upload className="w-6 h-6 text-white" />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-sm font-medium text-[#0D94FB] hover:text-blue-700 transition-colors"
                >
                  Change Picture
                </button>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleImageChange} 
                  accept="image/*" 
                  className="hidden" 
                />
              </div>

              {/* Form Fields */}
              <div className="flex-1 space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-white/80 mb-1.5">Full Name</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                      <User className="w-4 h-4 text-white/40" />
                    </div>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      className="block w-full pl-10 pr-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:ring-2 focus:ring-[#0D94FB]/50 focus:border-[#0D94FB] transition-all outline-none placeholder-white/30"
                      placeholder="Your Name"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-white/80 mb-1.5">New Password</label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                      <KeyRound className="w-4 h-4 text-white/40" />
                    </div>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="block w-full pl-10 pr-3.5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:ring-2 focus:ring-[#0D94FB]/50 focus:border-[#0D94FB] transition-all outline-none placeholder-white/30"
                      placeholder="Leave blank to keep current"
                    />
                  </div>
                  <p className="mt-1.5 text-xs text-white/50">Only fill this if you want to change your password.</p>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-6 border-t border-white/10">
              <button
                type="submit"
                disabled={isLoading || (!name && !password && !avatarData)}
                className="flex items-center gap-2 px-6 py-2.5 bg-[#0D94FB] hover:bg-[#0D94FB]/90 text-white text-sm font-medium rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-[#0D94FB]/20 hover:shadow-lg hover:shadow-[#0D94FB]/30"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {isLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
