"use client";

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { ShieldAlert, ScanLine, LogOut } from 'lucide-react';
import { useAuth } from './AuthContext';

const navItems = [
  { href: '/', label: 'Ring Detector', icon: ShieldAlert },
  { href: '/key-scanner', label: 'Key Scanner', icon: ScanLine },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { merchantName, logout } = useAuth();

  return (
    <aside className="fixed top-0 left-0 h-full w-60 bg-[#121C2D] flex flex-col z-50">
      {/* Logo */}
      <div className="px-4 py-8 flex justify-center items-center w-full">
        <Image src="/logo.png" alt="Sentinel Logo" width={220} height={80} style={{ width: 'auto', height: 'auto' }} className="w-52 h-auto object-contain" priority />
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-6 py-3 rounded-none text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-[#1A56F0] text-white'
                  : 'text-white/60 hover:text-white hover:bg-white/10'
              }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Merchant info + logout */}
      <div className="p-4 mt-auto">
        <div className="mb-3 px-3">
          <p className="text-[10px] text-white/50 uppercase tracking-widest mb-1">Logged in as</p>
          <p className="text-sm text-white font-medium truncate">{merchantName || 'Merchant'}</p>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm text-white/60 hover:text-white hover:bg-white/10 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Log out
        </button>
      </div>
    </aside>
  );
}
