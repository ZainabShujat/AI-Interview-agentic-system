import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Building2, GraduationCap, ArrowRight, ShieldCheck, Mail, Lock, User } from 'lucide-react';
import { supabase } from '../supabaseClient';
import { useAuth } from '../AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const defaultRole = searchParams.get('role') === 'student' ? 'student' : 'recruiter';
  const pickRoleMode = searchParams.get('pick_role') === 'true';

  const { user, role: currentRole, setRole: setAuthRole, loading: authLoading } = useAuth();

  const [role, setRole] = useState<'recruiter' | 'student'>(defaultRole);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);

  // If user is already authenticated and has a role, redirect
  useEffect(() => {
    if (authLoading) return;
    if (user && currentRole && !pickRoleMode) {
      navigate(currentRole === 'recruiter' ? '/recruiter' : '/student', { replace: true });
    }
  }, [user, currentRole, authLoading, pickRoleMode, navigate]);

  // If user just came from OAuth and needs to pick a role
  const handleRoleConfirm = () => {
    setAuthRole(role);
    navigate(role === 'recruiter' ? '/recruiter' : '/student', { replace: true });
    window.location.reload();
  };

  // Email/password login or signup
  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email.trim()) {
      setError('Email address is required.');
      return;
    }
    if (!password.trim()) {
      setError('Password is required.');
      return;
    }

    setLoading(true);

    try {
      if (isSignUp) {
        const { error: signUpError } = await supabase.auth.signUp({
          email: email.trim(),
          password: password.trim(),
          options: {
            data: {
              full_name: name.trim() || undefined,
            },
          },
        });

        if (signUpError) {
          setError(signUpError.message);
          setLoading(false);
          return;
        }

        // Set role after sign up
        setAuthRole(role);
        setLoading(false);
        navigate(role === 'recruiter' ? '/recruiter' : '/student', { replace: true });
        window.location.reload();
      } else {
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password: password.trim(),
        });

        if (signInError) {
          setError(signInError.message);
          setLoading(false);
          return;
        }

        // Set role after sign in
        setAuthRole(role);
        setLoading(false);
        navigate(role === 'recruiter' ? '/recruiter' : '/student', { replace: true });
        window.location.reload();
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
      setLoading(false);
    }
  };

  // If the user is authed but needs to pick a role (post-OAuth first login)
  if (user && pickRoleMode) {
    return (
      <div className="layout-container max-w-lg mx-auto py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="card-premium p-8"
        >
          <div className="text-center space-y-3 mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-emerald-500/20 bg-emerald-600/10 text-emerald-400 text-xs font-bold uppercase tracking-widest">
              <ShieldCheck className="w-3.5 h-3.5" />
              Almost There
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white font-sans">
              Choose Your Portal
            </h2>
            <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
              Welcome, {user.user_metadata?.full_name || user.email}! Select how you'll use HireIntel.
            </p>
          </div>

          {/* Role Toggle */}
          <div className="grid grid-cols-2 gap-2 p-1.5 rounded-lg border border-subtle mb-6" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
            <button
              type="button"
              onClick={() => setRole('recruiter')}
              className="flex items-center justify-center gap-2 py-3 rounded-md text-xs font-semibold transition-all"
              style={{
                backgroundColor: role === 'recruiter' ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
                color: role === 'recruiter' ? 'white' : 'var(--color-text-secondary)',
                border: role === 'recruiter' ? '1px solid var(--color-border-subtle)' : '1px solid transparent',
              }}
            >
              <Building2 className="w-4 h-4" />
              <span>Recruiter Portal</span>
            </button>
            <button
              type="button"
              onClick={() => setRole('student')}
              className="flex items-center justify-center gap-2 py-3 rounded-md text-xs font-semibold transition-all"
              style={{
                backgroundColor: role === 'student' ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
                color: role === 'student' ? 'white' : 'var(--color-text-secondary)',
                border: role === 'student' ? '1px solid var(--color-border-subtle)' : '1px solid transparent',
              }}
            >
              <GraduationCap className="w-4 h-4" />
              <span>Student Portal</span>
            </button>
          </div>

          <button
            onClick={handleRoleConfirm}
            className="w-full btn-base btn-primary py-3 text-xs font-bold gap-2 justify-center"
          >
            <span>Continue as {role === 'recruiter' ? 'Recruiter' : 'Student'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="layout-container max-w-lg mx-auto py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="card-premium p-8"
      >
        <div className="text-center space-y-3 mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-blue-500/20 bg-blue-600/10 text-blue-400 text-xs font-bold uppercase tracking-widest">
            <ShieldCheck className="w-3.5 h-3.5" />
            Secure Platform Login
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white font-sans">
            Welcome to HireIntel
          </h2>
          <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            Select your workspace portal below to access the OS.
          </p>
        </div>

        {/* Role Toggle Tabs */}
        <div className="grid grid-cols-2 gap-2 p-1.5 rounded-lg border border-subtle mb-6" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
          <button
            type="button"
            onClick={() => {
              setRole('recruiter');
              setError('');
            }}
            className="flex items-center justify-center gap-2 py-2.5 rounded-md text-xs font-semibold transition-all"
            style={{
              backgroundColor: role === 'recruiter' ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
              color: role === 'recruiter' ? 'white' : 'var(--color-text-secondary)',
              border: role === 'recruiter' ? '1px solid var(--color-border-subtle)' : '1px solid transparent',
            }}
          >
            <Building2 className="w-4 h-4" />
            <span>Recruiter Portal</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setRole('student');
              setError('');
            }}
            className="flex items-center justify-center gap-2 py-2.5 rounded-md text-xs font-semibold transition-all"
            style={{
              backgroundColor: role === 'student' ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
              color: role === 'student' ? 'white' : 'var(--color-text-secondary)',
              border: role === 'student' ? '1px solid var(--color-border-subtle)' : '1px solid transparent',
            }}
          >
            <GraduationCap className="w-4 h-4" />
            <span>Student Portal</span>
          </button>
        </div>

        {/* Email/Password Login Form */}
        <form onSubmit={handleEmailAuth} className="space-y-5">
          {error && (
            <div className="p-3 text-xs bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-md font-semibold">
              {error}
            </div>
          )}

          {isSignUp && (
            <div className="space-y-1.5">
              <label className="text-[10px] uppercase font-bold tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-tertiary)' }} />
                <input
                  type="text"
                  placeholder="Full Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input-base !pl-10 text-xs w-full"
                />
              </div>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-tertiary)' }} />
              <input
                type="email"
                placeholder={role === 'recruiter' ? 'recruiter@company.com' : 'student@university.edu'}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-base !pl-10 text-xs w-full"
                required
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-tertiary)' }} />
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-base !pl-10 text-xs w-full"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-base btn-primary py-3 text-xs font-bold gap-2 justify-center mt-2"
          >
            {loading ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <span>{isSignUp ? 'Create Account' : `Enter ${role === 'recruiter' ? 'Recruiter' : 'Student'} Workspace`}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Toggle Sign Up / Sign In */}
        <div className="mt-5 text-center">
          <button
            type="button"
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError('');
            }}
            className="text-xs font-semibold transition-colors"
            style={{ color: 'var(--color-accent)' }}
            onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-accent-hover)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-accent)'; }}
          >
            {isSignUp ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
