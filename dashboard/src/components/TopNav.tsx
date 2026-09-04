"use client";

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { ShieldAlert, ScanLine, LogOut, ChevronDown, User, RefreshCcw } from 'lucide-react';
import { useAuth } from './AuthContext';

const navItems = [
  { href: '/', label: 'Ring Detector', icon: ShieldAlert },
  { href: '/key-scanner', label: 'Key Scanner', icon: ScanLine },
];

export default function TopNav() {
  const pathname = usePathname();
  const { merchantName, merchantAvatar, logout, token } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  const handleSyncRazorpay = async () => {
    if (!token) return;
    setIsSyncing(true);
    try {
      const res = await fetch('http://localhost:8000/razorpay/ingest', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await res.json();
      if (res.ok) {
        if (data.added_accounts > 0 || data.added_orders > 0) {
          // Force a reload of the clusters on the page
          window.location.reload();
        } else {
          alert('No new Razorpay payments found to ingest.');
        }
      } else {
        alert(`Sync failed: ${data.detail}`);
      }
    } catch (e) {
      alert('Error connecting to backend for sync.');
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="px-6 pt-6 relative z-50">
      <header className="bg-white rounded-2xl shadow-xl flex items-center justify-between px-6 py-3">
        {/* Logo */}
        <div className="flex-shrink-0 flex items-center">
          <Image 
            src="/logo.png" 
            alt="Sentinel Logo" 
            width={160} 
            height={50} 
            style={{ width: 'auto', height: 'auto' }}
            className="w-32 sm:w-40 h-auto object-contain invert" 
            priority 
          />
        </div>

        {/* Nav */}
        <nav className="flex items-center gap-2 flex-1 justify-center">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-[#0D94FB] text-white shadow-md'
                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span className="hidden sm:inline">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Merchant info + dropdown */}
        <div className="flex items-center gap-3 relative" ref={dropdownRef}>
          <button 
            onClick={handleSyncRazorpay}
            disabled={isSyncing}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-green-50 text-green-700 hover:bg-green-100 border border-green-200 transition-colors disabled:opacity-50"
          >
            <RefreshCcw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Syncing...' : 'Sync Razorpay'}
          </button>
          
          <div className="h-6 w-px bg-gray-200 hidden md:block"></div>
          
          <button 
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex items-center gap-2 px-2 py-1.5 rounded-full hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-all"
          >
            <div className="w-8 h-8 rounded-full bg-blue-50 text-[#0D94FB] flex items-center justify-center flex-shrink-0 overflow-hidden border border-blue-100">
              {merchantAvatar ? (
                <img src={merchantAvatar} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <User className="w-4 h-4" />
              )}
            </div>
            <span className="hidden md:block text-sm text-gray-700 font-medium max-w-[120px] truncate ml-1">
              {merchantName || 'Merchant'}
            </span>
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ml-1 ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>
          
          {isDropdownOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden py-1 z-50">
              <Link
                href="/profile"
                onClick={() => setIsDropdownOpen(false)}
                className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-600 hover:text-[#0D94FB] hover:bg-blue-50 transition-colors text-left"
              >
                <User className="w-4 h-4" />
                <span>Profile</span>
              </Link>
              <button
                onClick={() => {
                  setIsDropdownOpen(false);
                  logout();
                }}
                className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 transition-colors text-left"
              >
                <LogOut className="w-4 h-4" />
                <span>Log out</span>
              </button>
            </div>
          )}
        </div>
      </header>
    </div>
  );
}
