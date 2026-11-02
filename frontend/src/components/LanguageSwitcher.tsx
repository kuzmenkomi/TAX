import { useState, useRef, useEffect } from 'react';
import { useI18n, type Locale } from '../i18n/I18nContext';
import { Globe, ChevronDown } from 'lucide-react';

export function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const languages: { code: Locale; name: string; flag: string; color: string }[] = [
    { code: 'en', name: 'English',   flag: 'EN', color: '#f59e0b' },
    { code: 'pt', name: 'Português', flag: 'PT', color: '#22c55e' },
    { code: 'es', name: 'Español',   flag: 'ES', color: '#3b82f6' },
  ];

  const current = languages.find(l => l.code === locale)!;

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2.5 h-9 px-3 border rounded-lg transition-all focus:ring-2 focus:ring-brand-green-500/20 outline-none shadow-sm"
        style={{ background: 'var(--card2)', borderColor: 'var(--border)', color: 'var(--text)' }}
        title="Change language"
      >
        <Globe className="w-4 h-4" />
        <span className="text-[11px] font-bold uppercase tracking-wider">{current.code}</span>
        <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-48 border rounded-xl p-1 animate-fade-in origin-top-right shadow-2xl"
          style={{
            zIndex: 9999,
            background: 'var(--card)',
            borderColor: 'var(--border)',
            boxShadow: 'var(--card-shadow), 0 0 0 1px var(--border)',
          }}
        >
          {languages.map(lang => (
            <button
              key={lang.code}
              onClick={() => {
                setLocale(lang.code);
                setIsOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${locale === lang.code
                ? 'bg-brand-green-500/10 text-brand-green-500'
                : 'hover:bg-brand-green-500/5'
                }`}
              style={locale !== lang.code ? { color: 'var(--text2)' } : undefined}
            >
              <span
                className="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0"
                style={{ background: lang.color }}
              >
                {lang.flag}
              </span>
              <div className="text-left">
                <div className="font-bold text-[11px] uppercase tracking-wider">{lang.name}</div>
              </div>
              {locale === lang.code && (
                <div className="ml-auto w-1 h-1 rounded-full bg-brand-green-500 shadow-[0_0_8px_var(--accent)]" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
