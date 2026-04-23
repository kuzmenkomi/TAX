import { useState, useEffect } from 'react';
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
} from 'lucide-react';
import { cn } from '../utils/cn';
import { useI18n } from '../i18n/I18nContext';
import { useAppContext } from '../context/AppContext';
import apiV1 from '../api/v1';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const { t } = useI18n();
  const { backendOnline } = useAppContext();
  const [txCount, setTxCount] = useState<number>(0);

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
  }, [backendOnline]);

  const renderItem = (item: { id: string; label: string; icon: any }, badge?: number) => (
    <button
      key={item.id}
      onClick={() => setActiveTab(item.id)}
      className={cn(
        "w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-[13px] font-bold transition-all group relative active:scale-95",
        activeTab === item.id
          ? "bg-brand-green-500 text-brand-dark shadow-lg shadow-brand-green-500/20"
          : "hover:bg-brand-green-500/5"
      )}
      style={activeTab !== item.id ? { color: 'var(--text2)' } : undefined}
    >
      <item.icon
        className={cn("w-[18px] h-[18px] flex-shrink-0", activeTab === item.id ? "text-brand-dark" : "opacity-40")}
        style={activeTab !== item.id ? { color: 'var(--text)' } : undefined}
      />
      <span className="tracking-tight">{item.label}</span>
      {badge != null && badge > 0 && (
        <span className={cn(
          "ml-auto text-[10px] font-black px-2 py-0.5 rounded-lg",
          activeTab === item.id ? "bg-brand-dark/20 text-brand-dark" : "bg-brand-green-500/10 text-brand-green-500"
        )}>
          {badge.toLocaleString()}
        </span>
      )}
    </button>
  );

  return (
    <aside
      className="w-[240px] flex flex-col hidden md:flex z-30 fixed top-16 bottom-0 left-0 transition-all duration-300 border-r"
      style={{ 
        background: 'var(--sidebar-bg)', 
        borderColor: 'var(--sidebar-border)',
        boxShadow: 'var(--sidebar-shadow)'
      }}
    >
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-8 custom-scrollbar">

        {/* Main Nav */}
        <div className="space-y-1">
          <p className="px-4 mb-3 text-[10px] font-black uppercase tracking-[2px] opacity-40" style={{ color: 'var(--text)' }}>Primary Hub</p>
          {[
            { id: 'dashboard', label: t('nav.dashboard'), icon: LayoutDashboard },
            { id: 'transactions', label: t('nav.transactions'), icon: Receipt },
            { id: 'tax', label: t('nav.tax'), icon: Percent },
            { id: 'reports', label: 'Tax Reports', icon: FileText },
            { id: 'reconciliation', label: 'Reconciliation', icon: ArrowLeftRight },
          ].map((item) => renderItem(item, item.id === 'transactions' ? txCount : undefined))}
        </div>

        {/* Tools */}
        <div className="space-y-1">
          <p className="px-4 mb-3 text-[10px] font-black uppercase tracking-[2px] opacity-40" style={{ color: 'var(--text)' }}>AI & Compliance</p>
          {[
            { id: 'ai', label: 'AI Fiscal Advisor', icon: Bot },
            { id: 'issues', label: 'Resolution Center', icon: AlertCircle },
          ].map((item) => renderItem(item))}
        </div>

        {/* Connections */}
        <div className="space-y-1">
          <p className="px-4 mb-3 text-[10px] font-black uppercase tracking-[2px] opacity-40" style={{ color: 'var(--text)' }}>Connections</p>
          {[
            { id: 'wallets', label: 'On-chain Wallets', icon: Wallet },
            { id: 'exchanges', label: 'Exchanges (CEX)', icon: ArrowRightLeft },
          ].map((item) => renderItem(item))}
        </div>

        {/* Bottom Utils */}
        <div className="pt-4 border-t" style={{ borderColor: 'var(--border)' }}>
          {renderItem({ id: 'settings', label: 'Control Panel', icon: Settings })}
        </div>

      </div>

      {/* Premium Upgrade Card */}
      <div className="p-4">
        <div className="relative border rounded-[2rem] p-6 overflow-hidden group shadow-xl transition-all hover:scale-[1.02]" 
          style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
          
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-green-500/10 rounded-full -mr-12 -mt-12 blur-2xl group-hover:bg-brand-green-500/20 transition-all" />
          
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="text-brand-green-500" size={16} />
              <p className="text-[10px] font-black text-brand-green-500 uppercase tracking-widest">Tax Efficiency</p>
            </div>
            <p className="text-[13px] font-bold mb-4 italic leading-snug" style={{ color: 'var(--text)' }}>
              "You've minimized <strong className="text-brand-green-500">$1,240</strong> in potential liabilities today."
            </p>
            <button className="w-full bg-brand-green-500 hover:bg-brand-green-400 text-brand-dark py-3 rounded-2xl text-xs font-black transition-all shadow-lg shadow-brand-green-500/20 active:scale-95">
              GO PREMIUM
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
