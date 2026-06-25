

export default function Footer() {
  return (
    <footer className="border-t border-subtle bg-dark-950/20 py-8" style={{ borderColor: 'var(--color-border-subtle)' }}>
      <div className="layout-container flex flex-col md:flex-row items-center justify-between gap-4 text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
        <div>
          &copy; {new Date().getFullYear()} HireIntel AI. All rights reserved.
        </div>
        <div className="flex gap-6">
          <a href="#" className="hover:text-blue-600 dark:hover:text-white transition-colors" style={{ color: 'var(--color-text-secondary)' }}>Privacy</a>
          <a href="#" className="hover:text-blue-600 dark:hover:text-white transition-colors" style={{ color: 'var(--color-text-secondary)' }}>Terms</a>
          <a href="#" className="hover:text-blue-600 dark:hover:text-white transition-colors" style={{ color: 'var(--color-text-secondary)' }}>Security</a>
        </div>
      </div>
    </footer>
  );
}
