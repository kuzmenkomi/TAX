import { Suspense, lazy, useState, useEffect, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { Header } from '../components/Header';
import { useAppContext } from '../context/AppContext';
import { useAuth } from '../auth/AuthContext';
import { getApiUrl, auth } from '../api/v1';
import { SUPPORT_IMPERSONATION_STRIP_H_PX } from '../components/SupportImpersonationStrip';
import { SyncJurisdictionFromUser } from '../components/SyncJurisdictionFromUser';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import { cn } from '../utils/cn';

const Dashboard = lazy(() => import('../components/Dashboard').then((module) => ({ default: module.Dashboard })));
const TransactionList = lazy(() =>
  import('../components/TransactionList').then((module) => ({ default: module.TransactionList })),
);
const IntegrationsHub = lazy(() => import('../components/IntegrationsHub').then((module) => ({ default: module.IntegrationsHub })));
const TaxHub = lazy(() => import('../components/TaxHub').then((module) => ({ default: module.TaxHub })));
const AuditHub = lazy(() => import('../components/AuditHub').then((module) => ({ default: module.AuditHub })));
const AIConsultant = lazy(() => import('../components/AIConsultant').then((module) => ({ default: module.AIConsultant })));
const SyncSettings = lazy(() => import('../components/SyncSettings').then((module) => ({ default: module.SyncSettings })));
const SettingsHub = lazy(() => import('../components/SettingsHub').then((module) => ({ default: module.SettingsHub })));
const PluginManager = lazy(() => import('../components/PluginManager').then((module) => ({ default: module.PluginManager })));
const BillingPage = lazy(() => import('./BillingPage').then((module) => ({ default: module.BillingPage })));

function TabFallback() {
  return (
    <div className="rounded-[2rem] border p-8 text-sm font-bold animate-pulse" style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)' }}>
      Loading module...
    </div>
  );
}

export function DashboardShell() {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');
    if (tab === 'exchanges') return 'integrations';
    return localStorage.getItem('activeTab') || 'dashboard';
  });
  const [integrationsSubTab, setIntegrationsSubTab] = useState<'EXCHANGES' | 'WALLETS' | undefined>(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('tab') === 'exchanges' ? 'EXCHANGES' : undefined;
  });
  const [auditSubTab, setAuditSubTab] = useState<'reconciliation' | 'issues' | undefined>();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    return localStorage.getItem('sidebarCollapsed') === 'true';
  });

  const handleSetCollapsed = (v: boolean) => {
    setSidebarCollapsed(v);
    localStorage.setItem('sidebarCollapsed', String(v));
  };
  
  const { backendOnline, setBackendOnline } = useAppContext();
  const { user } = useAuth();
  const [checking, setChecking] = useState(true);
  const backendLabel = getApiUrl('').replace(/^https?:\/\//, '').replace(/\/v1\/?$/, '');

  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768);
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const headerStackPx = useMemo(
    () => (isMobile ? 56 : 50) + (user?.impersonation ? SUPPORT_IMPERSONATION_STRIP_H_PX : 0),
    [isMobile, user?.impersonation],
  );

  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Lock scroll when sidebar is open on mobile
  useEffect(() => {
    if (mobileSidebarOpen && isMobile) {
      document.body.classList.add('sidebar-open');
    } else {
      document.body.classList.remove('sidebar-open');
    }
    return () => {
      document.body.classList.remove('sidebar-open');
    };
  }, [mobileSidebarOpen, isMobile]);

  // Close sidebar on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setMobileSidebarOpen(false);
      }
    };
    if (mobileSidebarOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [mobileSidebarOpen]);

  const handleTabChange = (tab: string, subTab?: any) => {
    setActiveTab(tab);
    if (tab === 'integrations' && subTab) {
      setIntegrationsSubTab(subTab);
    }
    if (tab === 'health' && subTab) {
      setAuditSubTab(subTab);
    }
    localStorage.setItem('activeTab', tab);
    setMobileSidebarOpen(false);
  };

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tab = params.get('tab');
    if (tab === 'exchanges') {
      setActiveTab('integrations');
      setIntegrationsSubTab('EXCHANGES');
      localStorage.setItem('activeTab', 'integrations');
    }
  }, [location.search]);

  // Health check every 5 seconds
  useEffect(() => {
    const check = async () => {
      try {
        await auth.health();
        setBackendOnline(true);
      } catch {
        setBackendOnline(false);
      } finally {
        setChecking(false);
      }
    };

    check();
    const interval = setInterval(check, 5000);
    return () => clearInterval(interval);
  }, [setBackendOnline]);

  return (
    <div className="min-h-screen overflow-x-hidden font-sans transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      <SyncJurisdictionFromUser />
      {/* Page Overlay for Mobile Sidebar */}
      {mobileSidebarOpen && (
        <div
          className="overlay page-overlay md:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Fixed Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        collapsed={sidebarCollapsed}
        setCollapsed={handleSetCollapsed}
        headerOffsetPx={headerStackPx}
        mobileSidebarOpen={mobileSidebarOpen}
        setMobileSidebarOpen={setMobileSidebarOpen}
      />

      {/* Content shifted right by sidebar width */}
      <div className={`flex min-h-screen flex-col transition-all duration-300 md:h-screen main-content ${sidebarCollapsed ? 'md:ml-[64px]' : 'md:ml-[212px]'}`}>
        <Header
          activeTab={activeTab}
          setActiveTab={handleTabChange}
          sidebarCollapsed={sidebarCollapsed}
          setSidebarCollapsed={handleSetCollapsed}
          mobileSidebarOpen={mobileSidebarOpen}
          setMobileSidebarOpen={setMobileSidebarOpen}
        />

        {/* Main Content Area */}
        <main
          className={cn(
            'flex-1 min-h-0',
            activeTab === 'transactions'
              ? 'overflow-hidden flex flex-col'
              : 'overflow-y-auto overflow-x-hidden px-4 py-4 pb-28 md:px-8 md:py-6 md:pb-6 custom-scrollbar',
          )}
          style={{ marginTop: headerStackPx }}
        >
          <div
            className={cn(
              activeTab === 'transactions' ? 'flex-1 min-h-0 flex flex-col' : 'max-w-[1400px] mx-auto space-y-6',
            )}
          >
            <Suspense fallback={<TabFallback />}>
              {activeTab === 'dashboard' && <Dashboard setActiveTab={handleTabChange} />}
              {activeTab === 'transactions' && <TransactionList setActiveTab={handleTabChange} />}
              {activeTab === 'tax' && <TaxHub setActiveTab={handleTabChange} />}
              {activeTab === 'health' && <AuditHub setActiveTab={handleTabChange} initialSubTab={auditSubTab} />}
              {activeTab === 'integrations' && <IntegrationsHub initialTab={integrationsSubTab} />}
              {activeTab === 'ai' && <AIConsultant />}
              {activeTab === 'plugins' && <PluginManager />}
              {activeTab === 'settings' && <SettingsHub setActiveTab={handleTabChange} />}
              {activeTab === 'billing' && <BillingPage setActiveTab={handleTabChange} />}
            </Suspense>
          </div>
        </main>

        {(activeTab === 'dashboard' || activeTab === 'integrations') && (
          <button
            type="button"
            onClick={() => handleTabChange('integrations')}
            className={cn(
              "fixed bottom-5 right-4 z-[110] flex h-14 w-14 items-center justify-center rounded-full bg-[var(--accent)] text-black shadow-[0_18px_40px_rgba(16,185,129,0.28)] md:hidden",
              mobileSidebarOpen ? "fab sidebar-open" : "fab"
            )}
            aria-label="Connect data"
          >
            <span className="text-3xl font-semibold leading-none">+</span>
          </button>
        )}
      </div>
    </div>
  );
}
