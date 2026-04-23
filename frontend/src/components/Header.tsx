import { Search, Bell, Plus, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';

interface HeaderProps {
  children?: React.ReactNode;
  setActiveTab?: (tab: string) => void;
}

export function Header({ children, setActiveTab }: HeaderProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();

  return (
    <header
      className="h-16 border-b flex items-center z-[100] fixed top-0 left-0 right-0 transition-all duration-300 backdrop-blur-md"
      style={{ background: 'var(--header-bg)', borderColor: 'var(--border)' }}
    >
      {/* Logo — updated width to match new sidebar (240px) */}
      <div
        className="w-[240px] flex-shrink-0 flex items-center gap-3 px-6 h-full border-r"
        style={{ borderColor: 'var(--border)' }}
      >
        <div className="w-2.5 h-2.5 rounded-full bg-brand-green-500 shadow-[0_0_12px_var(--accent)] animate-pulse" />
        <span className="font-syne font-black text-lg tracking-tight" style={{ color: 'var(--text)' }}>Declairo</span>
      </div>

      {/* Global Search Interface */}
      <div className="flex items-center gap-6 flex-1 px-8">
        <div className="relative w-full max-w-[420px] group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 transition-all opacity-40 group-focus-within:opacity-100 group-focus-within:text-brand-green-500" style={{ color: 'var(--text)' }} />
          <input
            type="text"
            placeholder="Search commands, wallets or audit trails…"
            className="w-full pl-11 pr-5 py-2.5 border rounded-2xl text-[13px] font-bold focus:outline-none focus:border-brand-green-500 transition-all shadow-sm"
            style={{
              background: 'var(--bg2)',
              borderColor: 'var(--border)',
              color: 'var(--text)',
            }}
          />
        </div>
      </div>

      {/* Action Suite */}
      <div className="flex items-center gap-4 pr-6">
        {/* Dynamic Context (Jurisdiction) */}
        <div className="hidden lg:block">
          {children}
        </div>

        <button 
          onClick={() => setActiveTab?.('wallets')}
          className="flex items-center gap-2 bg-brand-green-500 text-brand-dark px-5 py-2.5 rounded-2xl text-[12px] font-black transition-all shadow-xl shadow-brand-green-500/10 hover:bg-brand-green-400 active:scale-95"
        >
          <Plus className="w-4 h-4 stroke-[3px]" />
          CONNECT DATA
        </button>

        <div className="h-6 w-[1px] mx-2" style={{ background: 'var(--border)' }} />

        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          <ThemeToggle />
          
          <button 
            onClick={() => setActiveTab?.('issues')}
            className="w-10 h-10 flex items-center justify-center rounded-xl transition-all relative group border hover:border-brand-green-500/50"
            style={{
              color: 'var(--text2)',
              borderColor: 'var(--border)',
              background: 'var(--bg2)'
            }}
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-3 right-3 w-1.5 h-1.5 bg-brand-green-500 rounded-full shadow-[0_0_8px_var(--accent)]"></span>
          </button>

          {/* User Profile Cluster */}
          <div className="relative group ml-1">
            {/* The invisible landing gear bridge to prevent losing hover */}
            <div className="absolute top-0 right-0 w-full h-[140%] pointer-events-auto z-[-1]" />
            
            <button
              className="flex items-center gap-3 p-1.5 pl-1.5 pr-4 border rounded-2xl transition-all hover:border-brand-green-500/50 shadow-sm"
              style={{
                background: 'var(--bg2)',
                borderColor: 'var(--border)',
              }}
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-green-500 to-accent flex items-center justify-center font-syne text-[11px] font-black text-brand-dark shadow-inner">
                {user?.email?.slice(0, 2).toUpperCase() || 'TF'}
              </div>
              <div className="flex flex-col items-start leading-none">
                <span className="text-[12px] font-black tracking-tight" style={{ color: 'var(--text)' }}>
                  {user?.email?.split('@')[0]}
                </span>
                <span className="text-[9px] font-bold opacity-40 uppercase tracking-widest" style={{ color: 'var(--text)' }}>
                  Active Agent
                </span>
              </div>
            </button>
            
            {/* Expanded User Menu */}
            <div className="absolute top-full left-0 w-full opacity-0 translate-y-2 pointer-events-none group-hover:opacity-100 group-hover:translate-y-0 group-hover:pointer-events-auto transition-all duration-300 z-[120] pt-2">
              <div
                className="border rounded-2xl p-1.5 overflow-hidden"
                style={{ background: 'var(--surface)', borderColor: 'var(--border)', boxShadow: 'var(--card-shadow)' }}
              >
                <div className="px-3 py-2.5 border-b mb-1" style={{ borderColor: 'var(--border)' }}>
                   <p className="text-[8px] font-black opacity-40 uppercase tracking-widest mb-0.5" style={{ color: 'var(--text)' }}>Session</p>
                   <p className="text-[10px] font-bold truncate opacity-80" style={{ color: 'var(--text)' }}>{user?.email}</p>
                </div>
                <button
                  onClick={() => {
                    logout();
                    navigate('/', { replace: true });
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-[10px] font-black text-danger hover:bg-danger/10 transition-all group/exit"
                >
                  <LogOut className="w-3.5 h-3.5 transition-transform group-hover/exit:translate-x-1" />
                  SIGN OUT
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
