import {
  Bell,
  Plus,
  LogOut,
  Settings,
  Menu,
  X,
  Eye,
  EyeOff,
  LayoutDashboard,
  Receipt,
  Percent,
  AlertCircle,
  Bot,
  Link as LinkIcon,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';
import { useTheme } from '../context/ThemeContext';
import { cn } from '../utils/cn';
import { SupportImpersonationStrip } from './SupportImpersonationStrip';
import { useAppContext } from '../context/AppContext';
import apiV1 from '../api/v1';

interface HeaderProps {
  children?: React.ReactNode;
  setActiveTab?: (tab: string, subTab?: any) => void;
  sidebarCollapsed?: boolean;
  setSidebarCollapsed?: (v: boolean) => void;
  mobileSidebarOpen?: boolean;
  setMobileSidebarOpen?: (v: boolean) => void;
  activeTab?: string;
}

export function Header({
  children,
  setActiveTab,
  sidebarCollapsed,
  setSidebarCollapsed,
  mobileSidebarOpen,
  setMobileSidebarOpen,
  activeTab,
}: HeaderProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();
  const { theme } = useTheme();
  const { backendOnline, dataVersion, isPrivacyMode, togglePrivacyMode } = useAppContext();
  const [txCount, setTxCount] = useState(0);

  const userInitials = user?.email?.slice(0, 2).toUpperCase() || 'TE';
  const userName = useMemo(() => {
    const local = user?.email?.split('@')[0] || 'Test';
    return local.charAt(0).toUpperCase() + local.slice(1);
  }, [user?.email]);

  useEffect(() => {
    if (!backendOnline) return;
    let cancelled = false;
    (async () => {
      try {
        const txs = await apiV1.wallet.getTransactions(undefined, 10000);
        if (!cancelled) setTxCount(txs.length);
      } catch {
        if (!cancelled) setTxCount(0);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [backendOnline, dataVersion]);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'integrations', label: 'Connections', icon: LinkIcon },
    { id: 'transactions', label: 'Transactions', icon: Receipt, badge: txCount > 0 ? txCount : undefined },
    { id: 'tax', label: 'Tax Center', icon: Percent },
    { id: 'health', label: 'Audit & Issues', icon: AlertCircle },
    { id: 'ai', label: 'AI Fiscal Advisor', icon: Bot, badgeLabel: 'SOON', disabled: true },
  ];

  return (
    <header
      className="flex flex-col z-[100] fixed top-0 left-0 right-0 transition-all duration-300 backdrop-blur-md border-b"
      style={{ background: 'var(--nav-bg)', borderColor: 'var(--border)' }}
    >
      <SupportImpersonationStrip />
      <div className="flex h-[56px] md:h-[50px] w-full items-center">
      {/* Mobile Menu Toggle (Left side) */}
      <div className="flex items-center pl-3 md:hidden">
        <button
          type="button"
          onClick={() => setMobileSidebarOpen?.(!mobileSidebarOpen)}
          className="flex h-11 w-11 items-center justify-center rounded-xl text-[var(--text)] transition-all hover:bg-[var(--accent-dim)]"
          aria-label={mobileSidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          {mobileSidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Logo Area */}
      <div 
        className={cn(
          "h-full flex items-center transition-all duration-300 overflow-hidden md:border-r",
          sidebarCollapsed ? "md:w-[64px] md:px-4 pl-1 pr-4" : "md:w-[212px] md:px-6 pl-1 pr-4"
        )} 
        style={{ borderColor: 'var(--border)' }}
      >
        <Link to="/dashboard" className="flex items-center gap-2.5 no-underline hover:opacity-80 transition-all flex-shrink-0">
          <img 
            src="/logo.webp" 
            alt="Declairo Logo" 
            className="w-8 h-8 object-contain" 
          />
          <span className={cn(
            "font-syne font-extrabold text-[17px] tracking-tight text-[var(--text)] whitespace-nowrap",
            sidebarCollapsed ? "hidden" : "block"
          )}>
            Declairo
          </span>
        </Link>
      </div>

      {/* Spacer where search was */}
      <div className="flex-1" />

      {/* Action Suite */}
      <div className="flex items-center gap-[8px] pr-[14px] md:pr-[20px]">

        <button
          onClick={() => setActiveTab?.('integrations')}
          className="hidden md:flex bg-[var(--accent)] hover:brightness-95 text-white px-[13px] py-[6px] rounded-[7px] font-bold text-[11px] tracking-[0.3px] transition-all active:scale-95 items-center gap-2 shadow-[0_2px_6px_rgba(16,185,129,0.3)]"
        >
          <Plus size={14} strokeWidth={3} />
          CONNECT DATA
        </button>

        <div className="hidden md:block w-[1px] h-[18px] bg-[var(--border)] mx-[4px]" />

        <div className="hidden md:flex items-center gap-[8px]">
          <LanguageSwitcher />
          <ThemeToggle />

          <button
            onClick={() => setActiveTab?.('health', 'issues')}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-[var(--accent-dim)] text-[var(--text2)] transition-all"
          >
            <Bell size={16} />
          </button>

          {/* User Profile Cluster (Condensed version as most info is now in sidebar) */}
          <div className="relative group ml-[4px]">
              <div className="flex items-center gap-3 px-2 py-1.5 rounded-xl hover:bg-[var(--accent-dim)] transition-all cursor-pointer">
                <div className="w-[30px] h-[30px] rounded-lg bg-gradient-to-br from-[#0077ff] to-[var(--accent)] flex items-center justify-center font-extrabold text-[10px] text-black shadow-lg">
                {userInitials}
                </div>
              </div>

            {/* User Dropdown */}
            <div className="absolute top-full right-0 opacity-0 translate-y-2 pointer-events-none group-hover:opacity-100 group-hover:translate-y-0 group-hover:pointer-events-auto transition-all duration-300 z-[120] pt-2">
              <div
                className="bg-[var(--surface)] border border-[var(--border)] rounded-[14px] p-[6px] overflow-hidden min-w-[180px] shadow-[var(--card-shadow)]"
              >
                <div className="px-[12px] py-[10px] border-b border-[var(--border)] mb-[4px]">
                  <p className="text-[9px] font-extrabold text-[var(--text3)] uppercase tracking-[1.5px] mb-[2px]">Account</p>
                  <p className="text-[11px] font-bold text-[var(--text)] truncate">{user?.email}</p>
                </div>
                <button
                  onClick={() => setActiveTab?.('settings')}
                  className="w-full flex items-center gap-[8px] px-[12px] py-[10px] rounded-[9px] text-[11px] font-bold text-[var(--text2)] hover:bg-[var(--accent-dim)] hover:text-[var(--text)] transition-all"
                >
                  <Settings size={14} />
                  SETTINGS
                </button>
                <button
                  onClick={() => {
                    void logout().then(() => navigate('/', { replace: true }));
                  }}
                  className="w-full flex items-center gap-[8px] px-[12px] py-[10px] rounded-[9px] text-[11px] font-extrabold text-[var(--red)] hover:bg-[rgba(255,77,106,0.1)] transition-all group/exit"
                >
                  <LogOut className="w-[14px] h-[14px] transition-transform group-hover/exit:translate-x-1" />
                  SIGN OUT
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 md:hidden">
          <button
            type="button"
            onClick={togglePrivacyMode}
            className="flex h-11 w-11 items-center justify-center rounded-xl text-[var(--text2)] transition-all hover:bg-[var(--accent-dim)]"
            aria-label={isPrivacyMode ? 'Show balances' : 'Hide balances'}
          >
            {isPrivacyMode ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab?.('health', 'issues')}
            className="flex h-11 w-11 items-center justify-center rounded-xl text-[var(--text2)] transition-all hover:bg-[var(--accent-dim)]"
            aria-label="Notifications"
          >
            <Bell size={18} />
          </button>
        </div>
      </div>
      </div>


    </header>
  );
}
