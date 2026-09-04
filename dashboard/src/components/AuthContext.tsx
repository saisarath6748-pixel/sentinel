"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';

interface User {
  id: string;
  email: string;
}

interface AuthState {
  user: User | null;
  merchantId: string | null;
  merchantName: string | null;
  merchantAvatar: string | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  updateProfile: (name: string, password?: string, avatarData?: string, avatarFilename?: string) => Promise<void>;
}

const AuthContext = createContext<AuthState>({
  user: null,
  merchantId: null,
  merchantName: null,
  merchantAvatar: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  logout: () => {},
  updateProfile: async () => {},
});

const API_BASE = 'http://localhost:8000';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [merchantName, setMerchantName] = useState<string | null>(null);
  const [merchantAvatar, setMerchantAvatar] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Restore session from sessionStorage on mount
  useEffect(() => {
    try {
      const stored = sessionStorage.getItem('sentinel_auth');
      if (stored) {
        const parsed = JSON.parse(stored);
        setUser(parsed.user);
        setMerchantName(parsed.merchantName);
        setMerchantAvatar(parsed.merchantAvatar || null);
        setToken(parsed.token);
      }
    } catch {
      sessionStorage.removeItem('sentinel_auth');
    }
    setIsLoading(false);
  }, []);

  // Redirect to login if not authenticated (except on login page)
  useEffect(() => {
    if (!isLoading && !token && pathname !== '/login') {
      router.push('/login');
    }
  }, [isLoading, token, pathname, router]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    }

    const data = await res.json();
    const authData = {
      user: data.user,
      merchantName: data.merchant_name,
      merchantAvatar: data.avatar_url,
      token: data.access_token,
    };

    sessionStorage.setItem('sentinel_auth', JSON.stringify(authData));
    sessionStorage.setItem('sentinel_animate_summary', 'true');
    setUser(data.user);
    setMerchantName(data.merchant_name);
    setMerchantAvatar(data.avatar_url);
    setToken(data.access_token);
    router.push('/');
  }, [router]);

  const logout = useCallback(() => {
    sessionStorage.removeItem('sentinel_auth');
    setUser(null);
    setMerchantName(null);
    setMerchantAvatar(null);
    setToken(null);
    router.push('/login');
  }, [router]);

  const updateProfile = useCallback(async (name: string, password?: string, avatarData?: string, avatarFilename?: string) => {
    if (!token) return;
    const res = await fetch(`${API_BASE}/auth/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        name,
        password: password || undefined,
        avatar_data: avatarData || undefined,
        avatar_filename: avatarFilename || undefined,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Profile update failed');
    }

    const data = await res.json();
    
    setMerchantName(name);
    if (data.avatar_url) {
      setMerchantAvatar(data.avatar_url);
    }

    const stored = sessionStorage.getItem('sentinel_auth');
    if (stored) {
      const parsed = JSON.parse(stored);
      parsed.merchantName = name;
      if (data.avatar_url) parsed.merchantAvatar = data.avatar_url;
      sessionStorage.setItem('sentinel_auth', JSON.stringify(parsed));
    }
  }, [token]);

  return (
    <AuthContext.Provider
      value={{
        user,
        merchantId: user?.id || null,
        merchantName,
        merchantAvatar,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
