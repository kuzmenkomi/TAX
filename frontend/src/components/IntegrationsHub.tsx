import { useState, useEffect, type ReactNode } from 'react';
import { Wallet, Plus, Trash2, Link as LinkIcon, ShieldCheck, Zap, Globe, Upload, ArrowRight, Lock, RefreshCw } from 'lucide-react';
import apiV1 from '../api/v1';
import { cn } from '../utils/cn';
import { ConnectExchangeModal, AddWalletModal } from './ConnectionModals';
import { useAppContext } from '../context/AppContext';
import { useToast } from '../context/ToastContext';
import { buildCsvImportSources } from '../utils/importSources';
import type { ExchangeConnection } from '../api/v1';
import { SkeletonCard, SkeletonText } from './ui/Skeleton';
import { maskValue } from '../utils/privacy';

function normalizeBridgeExchange(raw: Record<string, unknown>): ExchangeConnection {
  return {
    id: Number(raw.id),
    exchange_name: String(raw.exchange_name || raw.provider || 'Exchange'),
    exchange: String(raw.provider || raw.exchange_name || ''),
    label: (raw.label as string | null) ?? null,
    status: String(raw.status || 'pending'),
    last_sync_at: (raw.last_sync_at || raw.last_synced_at) as string | null,
    last_synced: (raw.last_synced_at || raw.last_sync_at) as string | null,
    transaction_count: Number(raw.transaction_count ?? 0),
    balance: Number(raw.balance ?? 0),
  };
}

function mergeExchangeConnections(
  fromApi: ExchangeConnection[],
  fromBridge: Record<string, unknown>[],
): ExchangeConnection[] {
  const byId = new Map<number, ExchangeConnection>();
  fromApi.forEach((conn) => byId.set(conn.id, conn));
  fromBridge.forEach((raw) => {
    const normalized = normalizeBridgeExchange(raw);
    const existing = byId.get(normalized.id);
    if (existing) {
      byId.set(normalized.id, {
        ...existing,
        ...normalized,
        transaction_count: Math.max(existing.transaction_count ?? 0, normalized.transaction_count ?? 0),
      });
    } else {
      byId.set(normalized.id, normalized);
    }
  });
  return Array.from(byId.values());
}

function ExLogo({ id }: { id: string }) {
  const cls = 'w-[28px] h-[28px]';
  if (id === 'binance') return (
    <svg className={cls} viewBox="0 0 32 32" fill="none">
      <path d="M16 9.5l2.4 2.4-5.8 5.8-2.4-2.4L16 9.5z M10.4 15.2l2.4 2.4-2.4 2.4-2.4-2.4 2.4-2.4z M21.6 15.2l2.4 2.4-2.4 2.4-2.4-2.4 2.4-2.4z M16 20.9l2.4 2.4-2.4 2.4-2.4-2.4 2.4-2.4z M16 15.2l2.4 2.4-2.4 2.4-2.4-2.4 2.4-2.4z" fill="#F3BA2F"/>
    </svg>
  );
  if (id === 'coinbase') return (
    <svg className={cls} viewBox="0 0 32 32" fill="none">
      <circle cx="16" cy="16" r="9" fill="white"/>
      <circle cx="16" cy="16" r="4" fill="#0052FF"/>
    </svg>
  );
  if (id === 'kraken') return (
    <svg className={cls} viewBox="0 0 32 32" fill="none">
      <path d="M10 8h3v7.5l7.5-7.5h3.8L15 17.2l9.3 8.8H20l-7-6.8V26h-3V8z" fill="white"/>
    </svg>
  );
  if (id === 'okx') return (
    <svg className={cls} viewBox="0 0 32 32" fill="none">
      <rect x="8.5" y="8.5" width="6" height="6" rx="1.5" fill="white"/>
      <rect x="17.5" y="8.5" width="6" height="6" rx="1.5" fill="white"/>
      <rect x="8.5" y="17.5" width="6" height="6" rx="1.5" fill="white"/>
      <rect x="17.5" y="17.5" width="6" height="6" rx="1.5" fill="white"/>
    </svg>
  );
  if (id === 'bybit') return (
    <svg className={cls} viewBox="0 0 32 32" fill="none">
      <path d="M5 10h5c3 0 4.5 1.5 4.5 3.5S13 17 10 17H8v5H5V10zm3 5h1.5c1 0 1.5-.5 1.5-1.5S10.5 12 9.5 12H8v3z" fill="#FFB11A"/>
      <path d="M16 10h5c3 0 4.5 1.5 4.5 3.5 0 1.2-.6 2.2-1.7 2.8L27 22h-3.8l-1.9-4.5H19V22h-3V10zm3 5h1.5c1 0 1.5-.5 1.5-1.5S21.5 12 20.5 12H19v3z" fill="#FFB11A"/>
    </svg>
  );
  return null;
}

const EXCHANGES = [
  { id: 'binance', name: 'Binance', bg: '#181818' },
  { id: 'coinbase', name: 'Coinbase', bg: '#0052FF' },
  { id: 'kraken', name: 'Kraken', bg: '#5741D9' },
  { id: 'okx', name: 'OKX', bg: '#151515' },
  { id: 'bybit', name: 'Bybit', bg: '#181818' },
];

const CHAINS = [
  { id: 'eth', name: 'Ethereum', icon: <svg className="w-[26px] h-[26px]" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="16" fill="#627EEA" opacity=".2"/><path d="M16 5.5l-8 10.3 8-4.4 8 4.4L16 5.5z" fill="#627EEA"/><path d="M8 15.8l8 4.8 8-4.8-8 4.4L8 15.8z" fill="#627EEA" opacity=".6"/><path d="M16 22.2l-8-4.8L16 26.5l8-9.1-8 4.8z" fill="#627EEA"/></svg> },
  { id: 'btc', name: 'Bitcoin', icon: <svg className="w-[26px] h-[26px]" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="16" fill="#F7931A" opacity=".2"/><path d="M21.2 14.2c.3-1.8-1.1-2.8-3-3.4l.6-2.5-1.5-.4-.6 2.4-1.2-.3.6-2.4-1.5-.4-.6 2.5-2.4-.6-.4 1.6 1.1.3c.6.2.7.5.7.8l-1.7 7c-.1.3-.4.7-.9.5l-1.1-.3-.7 1.8 2.3.6-.6 2.5 1.5.4.6-2.5 1.2.3-.6 2.4 1.5.4.6-2.5c2.6.5 4.5.3 5.3-2.1.6-1.9 0-3 0-3 1.1-.5 1.7-1.4 1.35-2.9z" fill="#F7931A"/></svg> },
  { id: 'sol', name: 'Solana', icon: <svg className="w-[26px] h-[26px]" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="16" fill="#9945FF" opacity=".2"/><path d="M9 20.5h11.5l2.5-2.5H11.5L9 20.5z" fill="#9945FF"/><path d="M9 13.5h11.5L23 11H11.5L9 13.5z" fill="#9945FF"/><path d="M11.5 17H23l-2.5-2.5H9L11.5 17z" fill="#14F195"/></svg> },
  { id: 'pol', name: 'Polygon', icon: <svg className="w-[26px] h-[26px]" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="16" fill="#8247E5" opacity=".2"/><path d="M20.5 12.5l-5.5 3.2v6.4l5.5-3.2v-6.4z" fill="#8247E5"/><path d="M15 15.7l-4.5 2.6v5.2l4.5-2.6v-5.2z" fill="#8247E5" opacity=".7"/><path d="M20.5 12.5L17 10.5 9.5 14.8l4.5 2.6 6.5-4.9z" fill="#8247E5" opacity=".5"/></svg> },
  { id: 'arb', name: 'Arbitrum', icon: <svg className="w-[26px] h-[26px]" viewBox="0 0 32 32" fill="none"><circle cx="16" cy="16" r="16" fill="#28A0F0" opacity=".2"/><path d="M16 7l8 4.6v9.2L16 25l-8-4.6v-9.2L16 7z" fill="none" stroke="#28A0F0" strokeWidth="2"/><path d="M13 20l3-8 3 8M13 17h6" stroke="#28A0F0" strokeWidth="1.5" strokeLinecap="round"/></svg> },
];

function PillRow({ pills }: { pills: { icon: ReactNode; label: string }[] }) {
  return (
    <div className="flex items-center justify-center gap-[6px] flex-wrap">
      {pills.map((p, i) => (
        <div key={p.label} className="contents">
          <div className="flex items-center gap-[5px] text-[11px]" style={{ color: 'var(--text2)' }}>
            {p.icon}{p.label}
          </div>
          {i < pills.length - 1 && <span className="w-[3px] h-[3px] rounded-full" style={{ background: 'var(--text3)' }} />}
        </div>
      ))}
    </div>
  );
}

function SupportedGrid({ items }: { items: { id: string; name: string; bg: string; icon: ReactNode }[] }) {
  return (
    <div className="flex justify-center gap-[20px] flex-wrap">
      {items.map((item) => (
        <div key={item.id} className="flex flex-col items-center gap-[8px]">
          <div className="w-[52px] h-[52px] rounded-full flex items-center justify-center transition-all" style={{ background: item.bg, border: '1.5px solid rgba(255,255,255,0.08)' }}>
            {item.icon}
          </div>
          <span className="text-[10px] font-semibold" style={{ color: 'var(--text2)' }}>{item.name}</span>
        </div>
      ))}
    </div>
  );
}

export function IntegrationsHub({ initialTab }: { initialTab?: 'EXCHANGES' | 'WALLETS' }) {
  const { addToast } = useToast();
  const [activeTab, setActiveTab] = useState<'EXCHANGES' | 'WALLETS'>(initialTab || 'EXCHANGES');
  const [connections, setConnections] = useState<any[]>([]);
  const [wallets, setWallets] = useState<any[]>([]);
  const [csvImports, setCsvImports] = useState<any[]>([]);
  const [selectedChain, setSelectedChain] = useState('eth');
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [showConnectExchange, setShowConnectExchange] = useState(false);
  const [exchangeModalTab, setExchangeModalTab] = useState<'api' | 'csv'>('api');
  const [showAddWallet, setShowAddWallet] = useState(false);
  const [totalTransactions, setTotalTransactions] = useState(0);
  const [portfolioValueUsd, setPortfolioValueUsd] = useState(0);
  const { bumpDataVersion, dataVersion, isPrivacyMode } = useAppContext();

  useEffect(() => {
    if (initialTab) setActiveTab(initialTab);
  }, [initialTab]);

  useEffect(() => {
    fetchAll();
  }, [dataVersion]);

  async function fetchAll() {
    setLoading(true);
    try {
      const [exData, wData, runsData, txData, portData] = await Promise.allSettled([
        apiV1.exchange.listMy(),
        apiV1.wallet.list(),
        apiV1.analysis.listRuns(),
        apiV1.wallet.getTransactions(undefined, 10000),
        apiV1.portfolio.getSummary(),
      ]);

      const apiConnections = exData.status === 'fulfilled' ? (exData.value || []) : [];
      let bridgeExchanges: Record<string, unknown>[] = [];
      if (wData.status === 'fulfilled') {
        const payload = wData.value;
        if (Array.isArray(payload)) {
          setWallets(payload);
        } else {
          setWallets(payload?.wallets ?? []);
          bridgeExchanges = Array.isArray(payload?.exchanges) ? payload.exchanges : [];
        }
      }
      setConnections(mergeExchangeConnections(apiConnections, bridgeExchanges));

      if (runsData.status === 'fulfilled') {
        setCsvImports(buildCsvImportSources(runsData.value?.runs ?? []));
      }
      if (txData.status === 'fulfilled' && Array.isArray(txData.value)) {
        setTotalTransactions(txData.value.length);
      }
      if (portData.status === 'fulfilled' && portData.value) {
        const p = portData.value;
        setPortfolioValueUsd(Number(p.total_current_value_usd ?? p.total_value_usd ?? 0));
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  async function deleteExchange(id: number | string) {
    try {
      const target = exchangeSources.find((conn) => conn.id === id);
      const targetName = target?.exchange_name || target?.exchange || target?.name || target?.provider || 'this connection';
      if (typeof id === 'string' && id.startsWith('csv_')) {
        // CSV import: extract runId and delete the run
        const csvItem = csvImports.find((c) => c.id === id);
        if (csvItem?.runId) {
          await apiV1.analysis.deleteRun(csvItem.runId);
        }
        setCsvImports((prev) => prev.filter((c) => c.id !== id));
      } else {
        await apiV1.exchange.disconnect(id as number);
        setConnections((prev) => prev.filter((conn) => conn.id !== id));
      }
      await fetchAll();
      bumpDataVersion();
      addToast(`${targetName} deleted successfully.`, 'success');
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to delete connection.', 'error');
    }
  }

  async function syncExchange(id: number | string) {
    if (typeof id === 'string') return; // CSV imports can't be synced
    setSyncing(String(id));
    try {
      await apiV1.exchange.sync(id as number);
      await fetchAll();
      bumpDataVersion();
    } catch {
      // ignore
    } finally {
      setSyncing(null);
    }
  }

  async function syncWallet(walletId: number) {
    setSyncing(`wallet_${walletId}`);
    try {
      await apiV1.wallet.sync(walletId);
      await fetchAll();
      bumpDataVersion();
    } catch {
      // ignore
    } finally {
      setSyncing(null);
    }
  }

  async function deleteWallet(walletId: number) {
    const wallet = wallets.find((item) => item.id === walletId);
    const walletName = wallet?.label || wallet?.address || 'this wallet';
    try {
      await apiV1.wallet.disconnect(walletId);
      setWallets((prev) => prev.filter((item) => item.id !== walletId));
      await fetchAll();
      bumpDataVersion();
      addToast(`${walletName} deleted successfully.`, 'success');
    } catch (err) {
      addToast(err instanceof Error ? err.message : 'Failed to delete wallet.', 'error');
    }
  }

  function openExchangeModal(tab: 'api' | 'csv' = 'api') { 
    setExchangeModalTab(tab);
    setShowConnectExchange(true); 
  }
  function openWalletModal() { setShowAddWallet(true); }

  const exchangeSources = [...connections, ...csvImports];
  const sourcesTxTotal = exchangeSources.reduce((acc, c) => acc + (c.transaction_count || 0), 0);
  const summaryTxTotal = Math.max(sourcesTxTotal, totalTransactions);
  const sourcesBalanceTotal = exchangeSources.reduce((acc, c) => acc + (c.balance || 0), 0);
  const summaryPortfolioValue = Math.max(sourcesBalanceTotal, portfolioValueUsd);
  const apiConnectionCount = connections.length;
  const csvImportCount = csvImports.length;
  const openIssuesCount = exchangeSources.filter(
    (c) => c.sourceType !== 'csv' && c.status !== 'connected' && c.status !== 'synced' && !c.last_sync_at,
  ).length;
  const exItems = [
    ...EXCHANGES.map((e) => ({ id: e.id, name: e.name, bg: e.bg, icon: <ExLogo id={e.id} /> })),
    { id: '__more', name: '+15', bg: 'var(--card2)', icon: <span className="text-[13px] font-black" style={{ color: 'var(--text2)' }}>+15</span> },
  ];
  const chainItems = [
    ...CHAINS.map((c) => ({ id: c.id, name: c.name, bg: 'var(--card2)', icon: c.icon })),
    { id: '__more', name: '+20', bg: 'var(--card2)', icon: <span className="text-[13px] font-black" style={{ color: 'var(--text2)' }}>+20</span> },
  ];

  if (loading && connections.length === 0 && wallets.length === 0 && csvImports.length === 0) {
    return (
      <div className="space-y-[16px] animate-fade-in">
        <div className="flex items-center justify-between gap-4">
          <SkeletonText lines={2} className="w-[320px]" />
          <div className="w-[160px] h-[42px] rounded-xl animate-pulse" style={{ background: 'var(--card2)' }} />
        </div>
        <div className="grid grid-cols-2 gap-[12px]">
          <div className="h-[44px] rounded-[12px] animate-pulse" style={{ background: 'var(--card2)' }} />
          <div className="h-[44px] rounded-[12px] animate-pulse" style={{ background: 'var(--card2)' }} />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, idx) => (
            <SkeletonCard key={idx} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-[16px] animate-fade-in">
      {/* Header */}
      <div className="mb-[20px] flex flex-col gap-4 md:mb-[28px] md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-[22px] font-bold tracking-[-0.3px] font-syne">{activeTab === 'EXCHANGES' ? 'Exchange Accounts' : 'On-chain Wallets'}</h1>
          <p className="text-[13px] text-[var(--text2)] mt-[4px]">
            {activeTab === 'EXCHANGES'
              ? 'Manage your CEX API keys and automated trading history imports'
              : `Track wallet balances and auto-import on-chain transactions · ${wallets.length} wallets connected`}
          </p>
        </div>
        <button className="btn-primary flex min-h-[48px] w-full items-center justify-center gap-[7px] md:w-auto" onClick={activeTab === 'EXCHANGES' ? () => openExchangeModal('api') : openWalletModal}>
          <Plus size={14} strokeWidth={2.5} /> {activeTab === 'EXCHANGES' ? 'Add Connection' : 'Add Wallet'}
        </button>
      </div>

      {/* Tabs */}
      <div className="conn-tabs">
        <div 
          onClick={() => setActiveTab('EXCHANGES')} 
          className={cn('conn-tab', activeTab === 'EXCHANGES' && 'active')}
        >
          Exchanges (CEX) <span className={cn('conn-tab-badge', exchangeSources.length === 0 && 'muted')}>{exchangeSources.length}</span>
        </div>
        <div 
          onClick={() => setActiveTab('WALLETS')} 
          className={cn('conn-tab', activeTab === 'WALLETS' && 'active')}
        >
          On-chain Wallets <span className={cn('conn-tab-badge', wallets.length === 0 && 'muted')}>{wallets.length}</span>
        </div>
      </div>

      {/* Exchanges View */}
      {activeTab === 'EXCHANGES' && (
        <>
          {exchangeSources.length === 0 ? (
            <div className="conn-empty-card" style={{ backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.035) 1px, transparent 1px)', backgroundSize: '22px 22px' }}>
              <div className="conn-empty-icon"><Zap size={28} className="text-[var(--accent)]" /></div>
              <h2 className="conn-empty-title">No exchanges connected</h2>
              <p className="conn-empty-sub">
                Connect your CEX accounts via API or upload CSV exports<br />to automatically import your trading history.
              </p>
              <div className="conn-empty-btns">
                <button className="conn-cta-primary" onClick={() => openExchangeModal('api')}>
                  <LinkIcon size={16} /> Connect Your First Exchange <ArrowRight size={15} />
                </button>
                <button className="conn-cta-secondary" onClick={() => openExchangeModal('csv')}>
                  <Upload size={15} /> Upload CSV
                </button>
              </div>
              <p className="conn-section-label">SUPPORTED EXCHANGES</p>
              <SupportedGrid items={exItems} />
              <div className="conn-pills">
                <PillRow pills={[
                  { icon: <span className="w-[7px] h-[7px] rounded-full bg-[var(--accent)] inline-block" />, label: 'Read-only access' },
                  { icon: <Lock size={11} />, label: 'No withdrawal permissions' },
                  { icon: <Zap size={11} className="text-[var(--accent)]" />, label: 'Auto-sync' },
                ]} />
              </div>
            </div>
          ) : (
            <div className="conn-layout">
              {/* Left: Connected Accounts */}
              <div>
                <div className="card">
                  <div className="card-hd">
                    <span className="card-title">Connected Accounts</span>
                    <span className="text-[12px] text-[var(--text2)] font-mono">{exchangeSources.length} Total</span>
                  </div>
                  <div className="divide-y divide-[var(--border)]">
                    {exchangeSources.map((conn, idx) => {
                      // Exchange connections use exchange_name/provider; CSV imports use name/provider
                      const exId = (conn.exchange_name || conn.exchange || conn.name || conn.provider || '').toLowerCase();
                      // isSynced: API connections have status; CSV are always 'imported'
                      const isSynced = conn.sourceType === 'csv'
                        ? true
                        : (conn.status === 'connected' || conn.status === 'synced' || !!conn.last_sync_at);
                      const isSyncing = syncing === String(conn.id);
                      const syncLabel = conn.sourceType === 'csv'
                        ? 'Imported'
                        : (isSyncing ? 'Syncing...' : isSynced ? 'Synced' : 'Pending');
                      const syncChip = conn.sourceType === 'csv'
                        ? 'synced'
                        : (isSyncing ? 'syncing' : isSynced ? 'synced' : 'error');

                      // Date display
                      const dateStr = conn.sourceType === 'csv'
                        ? (conn.createdAt ? `Imported · ${new Date(conn.createdAt).toLocaleDateString()}` : 'Imported')
                        : (conn.last_sync_at ? `Last sync: ${new Date(conn.last_sync_at).toLocaleString()}` : 'Not synced yet');

                      const txCount = conn.transaction_count ?? 0;
                      const balance = conn.balance ?? 0;

                      return (
                        <div key={conn.id} className="flex flex-col items-start p-[14px_16px] gap-[12px] hover:bg-[var(--card2)] transition-all cursor-pointer animate-fade-up md:flex-row md:items-center md:p-[14px_20px] md:gap-[14px]" style={{ animationDelay: `${idx * 0.05}s` }}>
                          <div className="status-dot w-[8px] h-[8px] rounded-full flex-shrink-0" style={{ background: isSynced ? 'var(--green)' : 'var(--orange)', boxShadow: `0 0 6px ${isSynced ? 'var(--green)' : 'var(--orange)'}` }} />
                          <div className={cn('ex-logo-box', exId)}>
                            {['binance', 'coinbase', 'kraken', 'okx', 'bybit'].includes(exId) ? <ExLogo id={exId} /> : (conn.exchange_name || conn.exchange || conn.name || '?').charAt(0).toUpperCase()}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-[14px] font-semibold">{conn.exchange_name || conn.exchange || conn.name || conn.provider}</div>
                            <div className="text-[12px] text-[var(--text2)] mt-[2px]">
                              {conn.sourceType === 'csv' ? 'CSV Import' : 'API'} · {dateStr}
                            </div>
                          </div>
                          <div className="flex items-center gap-[20px] flex-shrink-0">
                            <div className="text-right">
                              <div className="text-[13px] font-semibold font-mono text-[var(--text)]">{txCount > 0 ? txCount.toLocaleString() : '—'}</div>
                              <div className="text-[11px] text-[var(--text2)] mt-[1px]">Transactions</div>
                            </div>
                            <div className="text-right">
                              <div className="text-[13px] font-semibold font-mono text-[var(--green)]">{balance > 0 ? `$${balance.toLocaleString()}` : '—'}</div>
                              <div className="text-[11px] text-[var(--text2)] mt-[1px]">Portfolio</div>
                            </div>
                          </div>
                          <span className={cn('sync-chip', syncChip)}>{syncLabel}</span>
                          <div className="flex items-center gap-[4px]">
                            {conn.sourceType !== 'csv' && (
                              <button onClick={(e) => { e.stopPropagation(); syncExchange(conn.id); }} className="w-[30px] h-[30px] rounded-[7px] border border-[var(--border2)] flex items-center justify-center text-[var(--text2)] hover:bg-[var(--card3)] hover:text-[var(--text)] transition-all">
                                <RefreshCw size={13} className={isSyncing ? 'animate-spin' : ''} />
                              </button>
                            )}
                            <button onClick={(e) => { e.stopPropagation(); deleteExchange(conn.id); }} className="w-[30px] h-[30px] rounded-[7px] border border-[var(--border2)] flex items-center justify-center text-[var(--text2)] hover:bg-[var(--card3)] hover:text-[var(--danger)] transition-all">
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Security Bar */}
                <div className="bg-[var(--card)] border border-[var(--border)] rounded-[12px] p-[16px_20px] flex items-center gap-[14px] mt-[20px]">
                  <ShieldCheck className="text-[var(--green)] flex-shrink-0" size={20} />
                  <div>
                    <div className="text-[13px] font-semibold">Data Security & Privacy</div>
                    <div className="text-[12px] text-[var(--text2)] mt-[2px]">We use read-only API access. Your credentials are encrypted with hardware-level security modules and are never exposed to third parties.</div>
                  </div>
                </div>
              </div>

              {/* Right Sidebar */}
              <div className="space-y-[16px]">
                {/* Summary */}
                <div className="card">
                  <div className="card-hd"><span className="card-title">Portfolio Summary</span></div>
                  <div className="summary-grid">
                    <div className="summary-cell">
                      <div className="summary-val green">
                        {summaryPortfolioValue > 0 ? `$${summaryPortfolioValue.toLocaleString()}` : '$0'}
                      </div>
                      <div className="summary-lbl">Total Value</div>
                    </div>
                    <div className="summary-cell">
                      <div className="summary-val">{summaryTxTotal.toLocaleString()}</div>
                      <div className="summary-lbl">Transactions</div>
                    </div>
                    <div className="summary-cell">
                      <div className="summary-val">{exchangeSources.length}</div>
                      <div className="summary-lbl">
                        Accounts
                        {(apiConnectionCount > 0 || csvImportCount > 0) && (
                          <span className="block text-[10px] font-normal text-[var(--text3)] mt-0.5">
                            {apiConnectionCount > 0 ? `${apiConnectionCount} API` : ''}
                            {apiConnectionCount > 0 && csvImportCount > 0 ? ' · ' : ''}
                            {csvImportCount > 0 ? `${csvImportCount} CSV` : ''}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="summary-cell">
                      <div className="summary-val" style={{ color: 'var(--orange)' }}>
                        {openIssuesCount}
                      </div>
                      <div className="summary-lbl">Open Issues</div>
                    </div>
                  </div>
                </div>

                {/* Quick Guide */}
                <div className="card">
                  <div className="card-hd"><span className="card-title">Quick Guide</span></div>
                  <div className="guide-row">
                    <div className="guide-num">1</div>
                    <div><div className="guide-title">Generate Keys</div><div className="guide-sub">Go to exchange API settings and create read-only keys</div></div>
                  </div>
                  <div className="guide-row">
                    <div className="guide-num">2</div>
                    <div><div className="guide-title">Set Permissions</div><div className="guide-sub">Disable Transfer. Only Read is required</div></div>
                  </div>
                  <div className="guide-row">
                    <div className="guide-num">3</div>
                    <div><div className="guide-title">Paste & Connect</div><div className="guide-sub">We handle everything else</div></div>
                  </div>
                </div>

                {/* Supported */}
                <div className="card">
                  <div className="card-hd"><span className="card-title">Supported</span></div>
                  {EXCHANGES.map((ex) => (
                    <div key={ex.id} className="supported-row">
                      <div className={cn('sup-logo', ex.id)}><ExLogo id={ex.id} /></div>
                      <div className="flex-1">
                        <div className="sup-name">{ex.name}</div>
                        <div className="sup-sub">CEX · API</div>
                      </div>
                      <span className="sup-badge high">HIGH</span>
                    </div>
                  ))}
                  <div className="supported-row">
                    <div className="sup-logo manual">?</div>
                    <div className="flex-1">
                      <div className="sup-name">Manual import</div>
                      <div className="sup-sub">CEX · CSV</div>
                    </div>
                    <span className="sup-badge csv">CSV ready</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Wallets View */}
      {activeTab === 'WALLETS' && (
        <>
          {wallets.length === 0 ? (
            <div className="conn-empty-card" style={{ backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.035) 1px, transparent 1px)', backgroundSize: '22px 22px' }}>
              <div className="conn-empty-icon"><LinkIcon size={28} className="text-[var(--accent)]" /></div>
              <h2 className="conn-empty-title">No wallets connected</h2>
              <p className="conn-empty-sub">
                Add your wallet addresses to automatically import<br />on-chain transactions from all major blockchains.
              </p>
              <div className="conn-empty-btns">
                <button className="conn-cta-primary conn-cta-full" onClick={openWalletModal}>
                  <Wallet size={16} /> Add Your First Wallet <ArrowRight size={15} />
                </button>
              </div>
              <p className="conn-section-label">SUPPORTED CHAINS</p>
              <SupportedGrid items={chainItems} />
              <div className="conn-pills">
                <PillRow pills={[
                  { icon: <span className="w-[7px] h-[7px] rounded-full bg-[var(--accent)] inline-block" />, label: 'Read-only access' },
                  { icon: <Lock size={11} />, label: 'No private keys required' },
                  { icon: <Zap size={11} className="text-[var(--accent)]" />, label: 'Auto-sync' },
                ]} />
              </div>
            </div>
          ) : (
            <div className="conn-layout">
              {/* Left: Wallets Panel */}
              <div>
                <div className="card">
                  <div className="card-hd">
                    <span className="card-title">Connected Wallets</span>
                    <span className="text-[12px] text-[var(--text2)] font-mono">{wallets.length} Total</span>
                  </div>
                  <div className="divide-y divide-[var(--border)]">
                    {wallets.map((wallet, idx) => {
                      const chainInfo = CHAINS.find(c => c.id === wallet.chain);
                      const isSynced = wallet.sync_status === 'completed' || !!wallet.last_synced_at;
                      const isSyncing = syncing === `wallet_${wallet.id}`;
                      const txCount = wallet.transaction_count ?? 0;
                      return (
                        <div key={wallet.id} className="flex items-center p-[14px_20px] gap-[14px] hover:bg-[var(--card2)] transition-all cursor-pointer animate-fade-up" style={{ animationDelay: `${idx * 0.05}s` }}>
                          <div className="status-dot w-[8px] h-[8px] rounded-full flex-shrink-0" style={{ background: isSynced ? 'var(--green)' : 'var(--orange)', boxShadow: `0 0 6px ${isSynced ? 'var(--green)' : 'var(--orange)'}` }} />
                          <div className={cn('chain-icon-box', wallet.chain)}>
                            {chainInfo?.icon || <Wallet size={20} />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-[14px] font-semibold">{wallet.label || wallet.name || `${chainInfo?.name || wallet.chain} Wallet`}</div>
                            <div className="wallet-addr-text">
                              {wallet.address} · {chainInfo?.name || wallet.chain}
                            </div>
                          </div>
                          <div className="flex items-center gap-[20px] flex-shrink-0">
                            <div className="text-right">
                              <div className="text-[13px] font-semibold font-mono text-[var(--text)]">{txCount > 0 ? txCount.toLocaleString() : '—'}</div>
                              <div className="text-[11px] text-[var(--text2)] mt-[1px]">Transactions</div>
                            </div>
                            <div className="text-right">
                              <div className="text-[13px] font-semibold font-mono text-[var(--green)]">{wallet.balance != null && wallet.balance > 0 ? `$${wallet.balance.toLocaleString()}` : '—'}</div>
                              <div className="text-[11px] text-[var(--text2)] mt-[1px]">Balance</div>
                            </div>
                          </div>
                          <span className={cn('sync-chip', isSynced ? 'synced' : 'error')}>{isSynced ? 'Synced' : 'Pending'}</span>
                          <div className="flex items-center gap-[4px]">
                            <button onClick={() => syncWallet(wallet.id)} className="w-[30px] h-[30px] rounded-[7px] border border-[var(--border2)] flex items-center justify-center text-[var(--text2)] hover:bg-[var(--card3)] hover:text-[var(--text)] transition-all">
                              <RefreshCw size={13} className={isSyncing ? 'animate-spin' : ''} />
                            </button>
                            <button onClick={() => deleteWallet(wallet.id)} className="w-[30px] h-[30px] rounded-[7px] border border-[var(--border2)] flex items-center justify-center text-[var(--text2)] hover:bg-[var(--card3)] hover:text-[var(--danger)] transition-all">
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="bg-[var(--card)] border border-[var(--border)] rounded-[12px] p-[16px_20px] flex items-center gap-[14px] mt-[20px]">
                  <ShieldCheck className="text-[var(--green)] flex-shrink-0" size={20} />
                  <div>
                    <div className="text-[13px] font-semibold">Data Security & Privacy</div>
                    <div className="text-[12px] text-[var(--text2)] mt-[2px] leading-[1.4]">We use read-only API access. Your credentials are encrypted with hardware-level security modules and are never exposed to third parties.</div>
                  </div>
                </div>
              </div>

              {/* Right Sidebar */}
              <div className="space-y-[16px]">
                <div className="card">
                  <div className="card-hd"><span className="card-title">Wallet Summary</span></div>
                  <div className="summary-grid">
                    <div className="summary-cell">
                      <div className="summary-val green">${wallets.reduce((acc, w) => acc + (w.balance || 0), 0).toLocaleString()}</div>
                      <div className="summary-lbl">Total Value</div>
                    </div>
                    <div className="summary-cell">
                      <div className="summary-val">{wallets.reduce((acc, w) => acc + (w.transaction_count || 0), 0).toLocaleString()}</div>
                      <div className="summary-lbl">Transactions</div>
                    </div>
                    <div className="summary-cell">
                      <div className="summary-val">{wallets.length}</div>
                      <div className="summary-lbl">Wallets</div>
                    </div>
                    <div className="summary-cell">
                      <div className="summary-val">{new Set(wallets.map(w => w.chain)).size}</div>
                      <div className="summary-lbl">Chains</div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <div className="card-hd"><span className="card-title">Supported Chains</span></div>
                  <div className="chains-pill-grid">
                    <div className="chain-pill-item"><div className="chain-dot eth" />Ethereum</div>
                    <div className="chain-pill-item"><div className="chain-dot btc" />Bitcoin</div>
                    <div className="chain-pill-item"><div className="chain-dot sol" />Solana</div>
                    <div className="chain-pill-item"><div className="chain-dot poly" />Polygon</div>
                    <div className="chain-pill-item"><div className="chain-dot arb" />Arbitrum</div>
                    <div className="chain-pill-item"><div className="chain-dot more" />+20 more</div>
                  </div>
                  <div className="features-strip">
                    <div className="feat-item"><div className="feat-item-dot" />Read-only</div>
                    <div className="feat-item"><div className="feat-item-dot" />No private keys</div>
                    <div className="feat-item"><div className="feat-item-dot" />Auto-sync</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {showConnectExchange && <ConnectExchangeModal onClose={() => setShowConnectExchange(false)} onSuccess={fetchAll} initialTab={exchangeModalTab} />}
      {showAddWallet && <AddWalletModal onClose={() => setShowAddWallet(false)} onSuccess={fetchAll} />}
    </div>
  );
}
