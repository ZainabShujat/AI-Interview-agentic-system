import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Building2, GraduationCap, Moon, Sun, LogOut } from 'lucide-react';

export default function Header() {
  const navigate = useNavigate();
  const [isLight, setIsLight] = useState(() => {
    return document.documentElement.classList.contains('light-theme');
  });

  const toggleTheme = () => {
    const nextThemeLight = !isLight;
    setIsLight(nextThemeLight);
    if (nextThemeLight) {
      document.documentElement.classList.add('light-theme');
      localStorage.setItem('theme', 'light');
    } else {
      document.documentElement.classList.remove('light-theme');
      localStorage.setItem('theme', 'dark');
    }
  };

  const role = localStorage.getItem('user_role');
  const name = localStorage.getItem('user_name');

  // Filter navItems based on logged-in user role
  let navItems: { path: string; label: string }[] = [];
  if (role === 'recruiter') {
    navItems = [
      { path: '/recruiter', label: 'Recruiter Workspace' },
      { path: '/recruiter/create', label: 'Create Assessment' },
    ];
  } else if (role === 'student') {
    navItems = [
      { path: '/student', label: 'Student Path' },
      { path: '/student/leaderboard', label: 'Leaderboard' },
    ];
  }

  const handleLogout = () => {
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_email');
    navigate('/login');
    window.location.reload();
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md border-b border-subtle transition-colors duration-300" style={{ borderColor: 'var(--color-border-subtle)', backgroundColor: 'var(--color-bg-secondary)' }}>
      <div className="max-w-7xl mx-auto px-5 md:px-8 h-20 flex items-center justify-between gap-5">
        <Link to="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-blue-950/20">
            H
          </div>
          <div className="leading-tight">
            <span className="font-bold text-white text-base tracking-tight font-sans block" style={{ color: 'var(--color-text-primary)' }}>
              HireIntel
            </span>
            <span className="hidden sm:block text-[10px] uppercase tracking-widest text-theme-tertiary">
              Agentic hiring OS
            </span>
          </div>
        </Link>

        {role && navItems.length > 0 && (
          <nav className="hidden lg:flex items-center gap-1 rounded-lg border border-subtle p-1" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
            {navItems.map((item) => (
              <Link
                key={item.label}
                to={item.path}
                className="text-xs font-semibold transition-colors duration-200 px-3 py-2 rounded-md hover:bg-white/5"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        )}

        <div className="flex items-center gap-2 md:gap-3">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-slate-100/5 transition-colors border border-subtle mr-1"
            style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
            aria-label="Toggle theme"
          >
            {isLight ? (
              <Moon className="w-4.5 h-4.5 text-blue-600" />
            ) : (
              <Sun className="w-4.5 h-4.5 text-amber-400" />
            )}
          </button>

          {role ? (
            <div className="flex items-center gap-2">
              <span className="hidden md:inline-flex items-center gap-1.5 text-xs font-semibold text-white bg-white/5 border border-subtle px-2.5 py-1.5 rounded-md" style={{ color: 'var(--color-text-secondary)', borderColor: 'var(--color-border-subtle)' }}>
                {role === 'recruiter' ? <Building2 className="w-3.5 h-3.5 text-blue-500" /> : <GraduationCap className="w-3.5 h-3.5 text-emerald-500" />}
                {name}
              </span>
              <button
                onClick={handleLogout}
                className="inline-flex items-center justify-center gap-1.5 bg-rose-600/10 border border-rose-500/20 hover:bg-rose-600/20 text-rose-400 text-xs font-bold py-2 px-3 md:px-4 rounded-md transition-colors duration-200"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Log out</span>
              </button>
            </div>
          ) : (
            <>
              <Link
                to="/login?role=student"
                className="hidden sm:inline-flex items-center justify-center gap-1.5 border border-subtle text-white text-xs font-semibold py-2 px-3 rounded-md hover:bg-white/5 transition-colors duration-200"
                style={{ borderColor: 'var(--color-border-subtle)' }}
              >
                <GraduationCap className="w-3.5 h-3.5" />
                Student Portal
              </Link>

              <Link
                to="/login?role=recruiter"
                className="inline-flex items-center justify-center gap-1.5 bg-blue-600 text-white text-xs font-semibold py-2 px-3 md:px-4 rounded-md hover:bg-blue-700 transition-colors duration-200"
              >
                <Building2 className="w-3.5 h-3.5" />
                Recruiter Portal
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
