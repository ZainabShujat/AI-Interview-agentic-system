import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from './supabaseClient';
import type { User, Session, AuthChangeEvent } from '@supabase/supabase-js';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  role: 'recruiter' | 'student' | null;
  setRole: (role: 'recruiter' | 'student') => void;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [role, setRoleState] = useState<'recruiter' | 'student' | null>(null);

  // Load persisted role from localStorage
  useEffect(() => {
    const storedRole = localStorage.getItem('user_role') as 'recruiter' | 'student' | null;
    if (storedRole === 'recruiter' || storedRole === 'student') {
      setRoleState(storedRole);
    }
  }, []);

  // Set role and persist it
  const setRole = (newRole: 'recruiter' | 'student') => {
    setRoleState(newRole);
    localStorage.setItem('user_role', newRole);

    // Also persist basic user info for Header and other components that read localStorage
    if (user) {
      const displayName =
        user.user_metadata?.full_name ||
        user.user_metadata?.name ||
        user.email?.split('@')[0] ||
        (newRole === 'recruiter' ? 'Recruiter' : 'Student');
      localStorage.setItem('user_name', displayName);
      localStorage.setItem('user_email', user.email || '');
    }
  };

  // Sign out
  const signOut = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
    setRoleState(null);
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_email');
  };

  // Listen for auth state changes
  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session: currentSession } }: { data: { session: Session | null } }) => {
      setSession(currentSession);
      setUser(currentSession?.user ?? null);

      // Sync localStorage for components that still read it directly
      if (currentSession?.user) {
        const u = currentSession.user;
        const displayName =
          u.user_metadata?.full_name ||
          u.user_metadata?.name ||
          u.email?.split('@')[0] ||
          'User';
        localStorage.setItem('user_name', displayName);
        localStorage.setItem('user_email', u.email || '');
      }

      setLoading(false);
    });

    // Subscribe to auth changes (login, logout, token refresh)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event: AuthChangeEvent, newSession: Session | null) => {
      setSession(newSession);
      setUser(newSession?.user ?? null);

      if (newSession?.user) {
        const u = newSession.user;
        const displayName =
          u.user_metadata?.full_name ||
          u.user_metadata?.name ||
          u.email?.split('@')[0] ||
          'User';
        localStorage.setItem('user_name', displayName);
        localStorage.setItem('user_email', u.email || '');
      }

      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  return (
    <AuthContext.Provider value={{ user, session, loading, role, setRole, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
