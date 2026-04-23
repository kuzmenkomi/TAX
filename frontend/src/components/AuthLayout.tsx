import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useI18n } from '../i18n/I18nContext';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle: string;
}

export function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  const { t } = useI18n();
  const location = useLocation();
  const isLogin = location.pathname === '/login';

  return (
    <div className="min-h-screen flex flex-col relative z-10 transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      {/* Navigation */}
      <nav 
        className="relative z-20 flex items-center justify-between px-6 md:px-12 py-6 border-b backdrop-blur-md"
        style={{ borderColor: 'var(--border)', background: 'var(--nav-bg)' }}
      >
        <Link to="/" className="flex items-center gap-2 no-underline font-syne font-extrabold text-xl tracking-tight hover:opacity-80 transition-opacity" style={{ color: 'var(--text)' }}>
          <div className="w-2 h-2 rounded-full bg-brand-green-500 shadow-[0_0_10px_var(--accent)]" />
          Declairo
        </Link>
        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
      </nav>

      <main className="flex-1 flex items-center justify-center p-6 md:p-12">
        <div className="w-full max-w-[440px] animate-fade-in">
          
          {/* Auth Card */}
          <div 
            className="border rounded-[20px] overflow-hidden animate-fade-in"
            style={{ background: 'var(--surface)', borderColor: 'var(--border)', boxShadow: 'var(--card-shadow)' }}
          >
            {/* Card Header */}
            <div 
              className="p-[32px_36px_28px] border-b relative overflow-hidden"
              style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}
            >
              <div className="absolute -top-[50px] -right-[50px] w-[180px] h-[180px] bg-brand-green-500/10 rounded-full blur-[60px] pointer-events-none" />
              <h1 className="text-[26px] font-syne font-bold mb-1 tracking-[-0.5px]" style={{ color: 'var(--text)' }}>
                {title}
              </h1>
              <p className="text-sm font-medium" style={{ color: 'var(--text2)' }}>
                {subtitle}
              </p>
            </div>

            {/* Card Body */}
            <div className="p-[32px_36px]">
              {children}
            </div>
          </div>

          {/* Footer Legal */}
          <div className="mt-8 text-center text-xs leading-relaxed max-w-[300px] mx-auto" style={{ color: 'var(--text3)' }}>
            {t('auth.legalPrefix')}{' '}
            <Link to="/terms" className="text-brand-green-500 hover:underline">{t('auth.termsOfService')}</Link>
            {' '}&{' '}
            <Link to="/privacy" className="text-brand-green-500 hover:underline">{t('auth.privacyPolicy')}</Link>
          </div>
        </div>
      </main>
    </div>
  );
}
