"use client";

import React from 'react';
import { usePathname } from 'next/navigation';
import { AuthProvider, useAuth } from './AuthContext';
import TopNav from './TopNav';

function LayoutInner({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const pathname = usePathname();
  const isLoginPage = pathname === '/login';

  // Show nothing while checking auth state (prevents flash)
  if (isLoading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[#0D94FB]/20 border-t-[#0D94FB] rounded-full animate-spin" />
      </div>
    );
  }

  // Login page - no sidebar
  if (isLoginPage) {
    return <>{children}</>;
  }

  // Authenticated pages - with sidebar
  if (isAuthenticated) {
    return (
      <div className="flex flex-col min-h-screen relative z-10">
        <TopNav />
        <main className="flex-1 w-full">{children}</main>
      </div>
    );
  }

  // Not authenticated, not on login — show loading spinner while redirect happens
  return (
    <div className="min-h-screen bg-white flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-[#0D94FB]/20 border-t-[#0D94FB] rounded-full animate-spin" />
    </div>
  );
}

export function AuthLayoutWrapper({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <LayoutInner>{children}</LayoutInner>
    </AuthProvider>
  );
}
