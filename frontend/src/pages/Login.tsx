import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Building2, GraduationCap, ArrowRight, ShieldCheck, Mail, Lock, User } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const defaultRole = searchParams.get('role') === 'student' ? 'student' : 'recruiter';
  
  const [role, setRole] = useState<'recruiter' | 'student'>(defaultRole);
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email.trim()) {
      setError('Email address is required.');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      // Simulate quick auth login
      localStorage.setItem('user_role', role);
      localStorage.setItem('user_name', name.trim() || (role === 'recruiter' ? 'Arjun V.' : 'Aarav S.'));
      localStorage.setItem('user_email', email.trim());

      setLoading(false);
      if (role === 'recruiter') {
        navigate('/recruiter');
      } else {
        navigate('/student');
      }
      window.location.reload(); // Refresh header layout
    }, 800);
  };

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

        {/* Login Form */}
        <form onSubmit={handleLogin} className="space-y-5">
          {error && (
            <div className="p-3 text-xs bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-md font-semibold">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-[10px] uppercase font-bold tracking-wider" style={{ color: 'var(--color-text-tertiary)' }}>
              Full Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-tertiary)' }} />
              <input
                type="text"
                placeholder={role === 'recruiter' ? 'Arjun V.' : 'Aarav S.'}
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-base !pl-10 text-xs w-full"
              />
            </div>
          </div>

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
              Password / Access Key
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-tertiary)' }} />
              <input
                type="password"
                placeholder="••••••••"
                className="input-base !pl-10 text-xs w-full"
                defaultValue="password123"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-base btn-primary py-3 text-xs font-bold gap-2 justify-center mt-2"
          >
            {loading ? (
              <span>Authenticating Portal...</span>
            ) : (
              <>
                <span>Enter {role === 'recruiter' ? 'Recruiter' : 'Student'} Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </motion.div>
    </div>
  );
}
