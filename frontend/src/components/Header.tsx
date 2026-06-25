import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Sun, Moon } from 'lucide-react';

export default function Header() {
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

  const navItems = [
    { path: '#product', label: 'Product' },
    { path: '#how-it-works', label: 'How it works' },
    { path: '#enterprise', label: 'Enterprise' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-slate-950/60 dark:bg-slate-950/40 backdrop-blur-md border-b border-subtle transition-colors duration-300" style={{ borderColor: 'var(--color-border-subtle)', backgroundColor: 'rgba(var(--color-bg-primary), 0.7)' }}>
      <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Logo / Brand */}
        <Link to="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
          <div className="w-6 h-6 rounded-md bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
            H
          </div>
          <span className="font-bold text-white text-base tracking-tight font-sans" style={{ color: 'var(--color-text-primary)' }}>
            HireIntel
          </span>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-8">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.path}
              className="text-sm font-medium transition-colors duration-200"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {item.label}
            </a>
          ))}
        </nav>

        {/* CTA & Theme Toggle */}
        <div className="flex items-center gap-4">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-full hover:bg-slate-800/10 dark:hover:bg-slate-100/5 transition-colors border border-subtle"
            style={{ borderColor: 'var(--color-border-subtle)', color: 'var(--color-text-primary)' }}
            aria-label="Toggle theme"
          >
            {isLight ? (
              <Moon className="w-4.5 h-4.5 text-blue-600" />
            ) : (
              <Sun className="w-4.5 h-4.5 text-amber-400" />
            )}
          </button>
          
          <Link
            to="/upload"
            className="inline-flex items-center justify-center bg-blue-600 text-white text-xs font-semibold py-2 px-4 rounded-md hover:bg-blue-700 transition-colors duration-200"
          >
            Start screening
          </Link>
        </div>
      </div>
    </header>
  );
}

