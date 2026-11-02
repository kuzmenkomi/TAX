import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Receipt,
  Wallet,
  Settings,
  ArrowRightLeft,
  Bot,
  AlertCircle,
  Percent,
  ArrowLeftRight,
  TrendingUp,
  FileText,
  CreditCard,
  Zap,
  Link as LinkIcon,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import { cn } from '../utils/cn';
import { useI18n } from '../i18n/I18nContext';
import { useAppContext } from '../context/AppContext';
import { useAuth } from '../auth/AuthContext';
import apiV1 from '../api/v1';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string, subTab?: any) => void;
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
  /** Top offset under fixed header (50px base + optional impersonation strip). */
  headerOffsetPx?: number;
  mobileSidebarOpen?: boolean;
  setMobileSidebarOpen?: (v: boolean) => void;
}

export function Sidebar({
  activeTab,
  setActiveTab,
  collapsed,
  setCollapsed,
  headerOffsetPx = 50,
  mobileSidebarOpen,
  setMobileSidebarOpen,
}: SidebarProps) {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { backendOnline, dataVersion } = useAppContext();
  const [txCount, setTxCount] = useState<number>(0);

  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768);
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Swipe-left to close (mobile only)
  const touchStartX = useRef<number | null>(null);
  const touchStartY = useRef<number | null>(null);

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null || touchStartY.current === null) return;
    const dx = e.changedTouches[0].clientX - touchStartX.current;
    const dy = Math.abs(e.changedTouches[0].clientY - touchStartY.current);
    // Close when swiped left ≥ 60px and horizontal direction dominates
    if (dx <= -60 && dy < Math.abs(dx)) {
      setMobileSidebarOpen?.(false);
    }
    touchStartX.current = null;
    touchStartY.current = null;
  };

  const isCollapsed = collapsed && !isMobile;

  const userInitials = user?.email?.slice(0, 2).toUpperCase() || 'TE';
  const userName = user?.email?.split('@')[0]?.charAt(0).toUpperCase() + (user?.email?.split('@')[0]?.slice(1) || 'User');

  // Fetch real transaction count
  useEffect(() => {
    if (!backendOnline) return;
    (async () => {
      try {
        const txs = await apiV1.wallet.getTransactions(undefined, 10000);
        setTxCount(txs.length);
      } catch {
        // No transactions yet
      }
    })();
  }, [backendOnline, dataVersion]);

  const renderItem = (item: { id: string; label: string; icon: any }, badge?: number) => (
    <button
      key={item.id}
      onClick={() => {
        if (item.id === 'integrations') {
          setActiveTab('integrations', 'EXCHANGES');
        } else {
          setActiveTab(item.id);
        }
      }}
      title={isCollapsed ? item.label : undefined}
      className={cn(
        "menu-item w-full flex items-center gap-3 rounded-[12px] text-[12px] font-bold transition-all group relative active:scale-95",
        isCollapsed ? "justify-center px-0 py-2.5" : "px-4 py-[14px] md:py-2.5",
        activeTab === item.id
          ? "active bg-brand-green-legacy-500 text-brand-dark shadow-lg shadow-brand-green-legacy-500/20"
          : "hover:bg-[var(--accent-dim)] text-[var(--text2)] hover:text-[var(--text)]"
      )}
    >
      <item.icon
        className={cn("flex-shrink-0", isCollapsed ? "w-[18px] h-[18px]" : "w-[16px] h-[16px]", activeTab === item.id ? "text-brand-dark" : "opacity-50")}
      />
      {!isCollapsed && (
        <>
          <span className="tracking-tight uppercase menu-label">{item.label}</span>
          {badge != null && badge > 0 && (
            <span className={cn(
              "ml-auto text-[9px] font-black px-2 py-0.5 rounded-lg",
              activeTab === item.id ? "bg-brand-dark/20 text-brand-dark" : "bg-brand-green-legacy-500/10 text-brand-green-legacy-500"
            )}>
              {badge.toLocaleString()}
            </span>
          )}
        </>
      )}
      {isCollapsed && badge != null && badge > 0 && (
        <span className="absolute top-1 right-1 w-[6px] h-[6px] rounded-full bg-brand-green-legacy-500" />
      )}
    </button>
  );

  return (
    <aside
      className={cn(
        'sidebar app-sidebar flex flex-col z-30 fixed bottom-0 left-0 transition-all duration-300 border-r',
        isCollapsed ? 'w-[64px]' : 'w-[212px]',
        mobileSidebarOpen && 'open'
      )}
      onTouchStart={isMobile ? handleTouchStart : undefined}
      onTouchEnd={isMobile ? handleTouchEnd : undefined}
      style={{
        top: headerOffsetPx,
        background: 'var(--sidebar-bg)',
        borderColor: 'var(--sidebar-border)',
        boxShadow: 'var(--sidebar-shadow)',
      }}
    >
      {/* Mobile-only Sidebar Header */}
      <div className="flex items-center justify-between px-4 py-3 md:hidden border-b border-[var(--border)] mb-4">
        <div className="flex items-center gap-2.5">
          <img 
            src="/logo.webp" 
            alt="Declairo Logo" 
            className="w-8 h-8 object-contain" 
          />
          <span className="font-syne font-extrabold text-[17px] tracking-tight text-[var(--text)]">
            Declairo
          </span>
        </div>
        <button
          type="button"
          onClick={() => setMobileSidebarOpen?.(false)}
          className="flex h-11 w-11 items-center justify-center rounded-xl border text-[var(--text2)] transition-all hover:bg-[var(--accent-dim)]"
          style={{ borderColor: 'var(--border)' }}
          aria-label="Close sidebar"
        >
          <X size={20} />
        </button>
      </div>

      {/* Collapse toggle button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className={cn(
          "absolute -right-[14px] top-[24px] z-50 w-7 h-7 rounded-full flex items-center justify-center transition-all shadow-md hidden md:flex",
          "bg-[var(--card)] border border-[var(--border2)] text-[var(--text2)] hover:text-[var(--accent)] hover:border-[var(--accent)]"
        )}
        title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {isCollapsed ? <ChevronRight size={13} strokeWidth={2.5} /> : <ChevronLeft size={13} strokeWidth={2.5} />}
      </button>

      <div className={cn("sidebar-content flex-1 overflow-y-auto py-6 space-y-7 md:space-y-5 custom-scrollbar", isCollapsed ? "px-2" : "px-4")}>
        
        {/* Section 1: Core Navigation */}
        <div className="menu-section space-y-1">
          {!isCollapsed && (
            <p className="menu-section-title px-4 mb-3 text-[9px] font-black uppercase tracking-[2px] text-[var(--text3)] opacity-40">
              {t('nav.section.navigation') || 'NAVIGATION'}
            </p>
          )}
          {isCollapsed && <div className="h-px bg-[var(--border)] opacity-30 mb-3" />}
          {[
            { id: 'dashboard', label: t('nav.dashboard') || 'Dashboard', icon: LayoutDashboard },
            { id: 'integrations', label: t('nav.connections') || 'Integrations', icon: LinkIcon },
            { id: 'transactions', label: t('nav.transactions') || 'Transactions', icon: Receipt },
          ].map((item) => renderItem(item, item.id === 'transactions' ? txCount : undefined))}
        </div>

        <div className="h-px bg-[var(--border)] mx-4 opacity-50" />

        {/* Section 2: Analysis & Tax */}
        <div className="menu-section space-y-1">
          {!isCollapsed && (
            <p className="menu-section-title px-4 mb-3 text-[9px] font-black uppercase tracking-[2px] text-[var(--text3)] opacity-40">
              {t('nav.section.tax') || 'TAX & COMPLIANCE'}
            </p>
          )}
          {[
            { id: 'tax', label: t('nav.taxCenter') || 'Tax Center', icon: Percent },
            { id: 'health', label: t('nav.audit') || 'Audit & Issues', icon: AlertCircle },
          ].map((item) => renderItem(item))}
        </div>

        <div className="h-px bg-[var(--border)] mx-4 opacity-50" />

        {/* Section 3: Intelligence */}
        <div className="menu-section space-y-1">
          {!isCollapsed && (
            <p className="menu-section-title px-4 mb-3 text-[9px] font-black uppercase tracking-[2px] text-[var(--text3)] opacity-40">
              {t('nav.section.intelligence') || 'INTELLIGENCE'}
            </p>
          )}
          {/* AI Fiscal Advisor — Coming Soon, disabled for all plans */}
          <div
            title={isCollapsed ? `${t('nav.aiAdvisor') || 'AI Fiscal Advisor'} — Coming Soon` : 'Coming Soon'}
            className={cn(
              "menu-item w-full flex items-center gap-3 rounded-[12px] text-[12px] font-bold relative cursor-not-allowed select-none text-[var(--text2)]",
              isCollapsed ? "justify-center px-0 py-2.5" : "px-4 py-[14px] md:py-2.5",
            )}
          >
            <Bot className={cn("flex-shrink-0 opacity-50", isCollapsed ? "w-[18px] h-[18px]" : "w-[16px] h-[16px]")} />
            {!isCollapsed && (
              <>
                <span className="tracking-tight uppercase menu-label">{t('nav.aiAdvisor') || 'AI Fiscal Advisor'}</span>
                <span className="ml-auto text-[8px] font-black px-2 py-0.5 rounded-lg bg-amber-500/15 text-amber-400 border border-amber-500/20 uppercase tracking-wider">
                  Soon
                </span>
              </>
            )}
            {isCollapsed && (
              <span className="absolute top-0.5 right-0.5 text-[6px] font-black px-1 py-0 rounded bg-amber-500/20 text-amber-400 uppercase leading-tight">
                S
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="h-px bg-[var(--border)] mx-4 opacity-50" />

      {/* Footer Area: Premium + Profile */}
      <div className={cn("sidebar-footer mt-auto flex flex-col gap-4", isCollapsed ? "p-2" : "p-4")}>
        
        {/* Compact Tax Efficiency Card — hidden when collapsed */}
        {!isCollapsed && (
          <div className="relative rounded-[16px] p-4 overflow-hidden border transition-all hidden md:block" 
            style={{ background: 'var(--card2)', borderColor: 'var(--border)' }}>
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="text-[var(--accent)]" size={12} />
                <p className="text-[8px] font-black text-[var(--accent)] uppercase tracking-widest">
                  {t('common.taxEfficiency') || 'TAX EFFICIENCY'}
                </p>
              </div>
              <p className="text-[10px] font-bold mb-3 text-[var(--text2)] leading-tight italic">
                Minimized <strong className="text-[var(--accent)]">$1,240</strong> today.
              </p>
              <button 
                onClick={() => setActiveTab('billing')}
                className="w-full bg-brand-green-legacy-500 hover:bg-brand-green-legacy-600 text-brand-dark py-1.5 rounded-lg text-[9px] font-black transition-all shadow-md shadow-brand-green-legacy-500/25"
              >
                {t('common.upgrade') || 'UPGRADE'}
              </button>
            </div>
          </div>
        )}

        {/* User Profile Footer */}
        <div className={cn(
          "flex items-center group pt-4 border-t",
          isCollapsed ? "justify-center" : "justify-between"
        )} style={{ borderColor: 'var(--border)' }}>
          <div
            className={cn("flex items-center", isCollapsed ? "justify-center" : "gap-3")}
            title={isCollapsed ? userName : undefined}
          >
            <div className="w-9 h-9 rounded-full border border-[var(--border2)] flex items-center justify-center bg-[var(--card2)] text-[var(--accent)] text-[10px] font-black shadow-inner flex-shrink-0">
               {userInitials}
            </div>
            {!isCollapsed && (
              <div className="flex flex-col">
                <span className="text-[11px] font-bold text-[var(--text)] leading-tight">{userName}</span>
                <span className="text-[8px] text-[var(--text3)] font-medium">
                  {t('common.personalAccount') || 'Personal Account'}
                </span>
              </div>
            )}
          </div>
          
          {!isCollapsed && (
            <button 
              onClick={() => setActiveTab('settings')}
              className={cn(
                "p-2 rounded-lg transition-all hover:bg-[var(--accent-dim)]",
                activeTab === 'settings' ? "text-[var(--accent)]" : "text-[var(--text3)] hover:text-[var(--text)]"
              )}
            >
              <Settings size={18} />
            </button>
          )}
        </div>

        {/* Settings button in collapsed mode */}
        {isCollapsed && (
          <button
            onClick={() => setActiveTab('settings')}
            title="Settings"
            className={cn(
              "w-full flex justify-center p-2 rounded-lg transition-all hover:bg-[var(--accent-dim)]",
              activeTab === 'settings' ? "text-[var(--accent)]" : "text-[var(--text3)] hover:text-[var(--text)]"
            )}
          >
            <Settings size={18} />
          </button>
        )}
      </div>
    </aside>
  );
}
