import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="w-9 h-9 flex items-center justify-center rounded-lg transition-all border shadow-[var(--card-shadow)]"
      style={{
        background: 'var(--input-bg)',
        borderColor: 'var(--border)',
        color: 'var(--text2)',
      }}
      title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {theme === 'dark' ? (
        <Sun className="w-4 h-4 hover:text-amber-400 transition-colors" />
      ) : (
        <Moon className="w-4 h-4 hover:text-brand-blue-500 transition-colors" />
      )}
    </button>
  );
}
