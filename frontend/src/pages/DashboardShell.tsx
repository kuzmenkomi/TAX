import { useState, useEffect } from 'react';
import { Dashboard } from '../components/Dashboard';
import { TransactionList } from '../components/TransactionList';
import { TaxOptimizer } from '../components/TaxOptimizer';
import { IssuesCenter } from './IssuesCenter';
import { BlockchainImportPage } from './BlockchainImportPage';
import { ExchangeManager } from '../components/ExchangeManager';
import { SyncSettings } from '../components/SyncSettings';
import { Sidebar } from '../components/Sidebar';
import { Header } from '../components/Header';
import JurisdictionSelector from '../components/JurisdictionSelector';
import { ReconciliationCenter } from '../components/ReconciliationCenter';
import { AIConsultant } from '../components/AIConsultant';
import { PluginManager } from '../components/PluginManager';
import { AuditMode } from '../components/AuditMode';
import { ReportDownloader } from '../components/ReportDownloader';
import { useAppContext } from '../context/AppContext';
import { getApiUrl, auth } from '../api/v1';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';

export function DashboardShell() {
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('activeTab') || 'dashboard';
  });
  const { backendOnline, setBackendOnline } = useAppContext();
  const { token } = useAuth();
  const [checking, setChecking] = useState(true);
  const backendLabel = getApiUrl('').replace(/^https?:\/\//, '').replace(/\/v1\/?$/, '');

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    localStorage.setItem('activeTab', tab);
  };

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
    <div className="min-h-screen font-sans transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      {/* Fixed Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={handleTabChange} />

      {/* Content shifted right by sidebar width */}
      <div className="ml-[220px] flex flex-col min-h-screen">
        <Header setActiveTab={handleTabChange}>
          <JurisdictionSelector />
        </Header>

        {/* Backend status bar */}
        {checking ? (
          <div className="mt-14 border-b px-6 py-1.5 flex items-center gap-2 text-xs" style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text2)' }}>
            <Loader2 className="w-3 h-3 animate-spin" />
            {`Connecting to backend (${backendLabel})...`}
          </div>
        ) : backendOnline ? (
          <div className="mt-14 bg-brand-green-500/5 border-b border-brand-green-500/10 px-6 py-1.5 flex items-center gap-2 text-xs text-brand-green-500 font-medium">
            <Wifi className="w-3 h-3" />
            Backend online — <span className="opacity-60">{backendLabel}</span>
          </div>
        ) : (
          <div className="mt-14 bg-[#f06a6a]/5 border-b border-[#f06a6a]/10 px-6 py-1.5 flex items-center gap-2 text-xs text-[#f06a6a] font-medium">
            <WifiOff className="w-3 h-3" />
            Backend offline. Run:{' '}
            <code className="font-bold bg-[#f06a6a]/10 px-1.5 py-0.5 rounded">
              uvicorn app.api.server:app --reload --port 8000
            </code>
          </div>
        )}

        <main className="flex-1 overflow-y-auto px-8 py-6">
          <div className="max-w-[1280px] mx-auto">
            {activeTab === 'dashboard' && <Dashboard setActiveTab={handleTabChange} />}
            {activeTab === 'transactions' && <TransactionList />}
            {activeTab === 'tax' && <TaxOptimizer />}
            {activeTab === 'reconciliation' && <ReconciliationCenter />}
            {activeTab === 'ai' && <AIConsultant />}
            {activeTab === 'issues' && <IssuesCenter />}
            {activeTab === 'reports' && <ReportDownloader />}
            {activeTab === 'wallets' && <BlockchainImportPage />}
            {activeTab === 'exchanges' && <ExchangeManager />}
            {activeTab === 'plugins' && <PluginManager />}
            {activeTab === 'audit' && <AuditMode />}
            {activeTab === 'sync' && <SyncSettings />}
            {activeTab === 'settings' && <SyncSettings />}
          </div>
        </main>
      </div>
    </div>
  );
}
