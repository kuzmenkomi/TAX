import { useState, useEffect, useMemo } from 'react';
import { Search, ChevronDown, Plus, Wallet, ArrowRight, SlidersHorizontal, Download, RefreshCw } from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { useToast } from '../context/ToastContext';
import apiV1, { Transaction, ExchangeConnection } from '../api/v1';
import { cn } from '../utils/cn';
import { getDisplayTransactionType } from '../utils/transactionCategory';
import { buildCsvImportSources, CsvImportSource } from '../utils/importSources';

const PER_PAGE = 10;

const TypeIcons = {
  buy: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="11" height="11"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>,
  sell: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="11" height="11"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>,
  transfer: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="11" height="11"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>,
  income: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="11" height="11"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
};

type WalletRow = {
  id: number | string;
  chain?: string;
  blockchain?: string;
  address: string;
  label?: string | null;
  transaction_count?: number;
  sync_status?: string;
};

function getAssetColors(asset: string) {
  const a = asset.toLowerCase();
  if (a === 'ada') return 'bg-[rgba(0,51,173,.15)] text-[#4070e0]';
  if (a === 'btc') return 'bg-[rgba(247,147,26,.15)] text-[#f7931a]';
  if (a === 'sol') return 'bg-[rgba(153,69,255,.15)] text-[#9945ff]';
  if (a === 'eth') return 'bg-[rgba(98,126,234,.15)] text-[#627eea]';
  return 'bg-[var(--tx-panel-muted)] text-[var(--tx-text-muted)]';
}

function getExchangeColors(ex: string) {
  const e = ex.toLowerCase();
  if (e.includes('binance')) return 'bg-[rgba(243,186,47,.12)] text-[#c89c18]';
  if (e.includes('coinbase')) return 'bg-[rgba(22,82,240,.12)] text-[#4d7af5]';
  if (e.includes('kraken')) return 'bg-[rgba(87,65,217,.12)] text-[#8b7cf5]';
  if (e.includes('okx')) return 'bg-[var(--tx-panel-muted)] text-[var(--tx-text-muted)]';
  if (e.includes('bybit')) return 'bg-[rgba(247,166,0,.12)] text-[var(--tx-amber)]';
  if (e.includes('csv')) return 'bg-[rgba(240,165,0,.12)] text-[var(--tx-amber)]';
  return 'bg-[var(--tx-panel-muted)] text-[var(--tx-text-muted)]';
}

function getExchangeIcon(ex: string) {
  const e = ex.toLowerCase();
  if (e.includes('binance')) return 'B';
  if (e.includes('coinbase')) return 'C';
  if (e.includes('kraken')) return 'K';
  if (e.includes('okx')) return 'OKX';
  if (e.includes('bybit')) return 'BY';
  if (e.includes('eth') || e.includes('ethereum')) {
    return (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-[13px] h-[13px]">
        <path d="M12 2L4 12.5 12 16l8-3.5L12 2zm0 14l-8-3.5L12 22l8-6.5L12 16z" opacity=".8" />
      </svg>
    );
  }
  if (e.includes('btc') || e.includes('bitcoin')) {
    return (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-[13px] h-[13px]">
        <path d="M17.2 10.3c.3-.9.1-2-.6-2.7-.7-.7-1.8-1-2.7-.8V5h-1.5v1.6H11V5H9.5v1.6H7V8h1.5v8H7v1.4h2.5V19H11v-1.6h1.4V19H15.5v-1.6c1 0 1.9-.4 2.6-1.1.7-.7 1.1-1.7.9-2.7-.2-.8-.7-1.5-1.3-1.9.5-.5.8-1.2.6-1.9z" />
      </svg>
    );
  }
  if (e.includes('sol') || e.includes('solana')) {
    return (
      <svg viewBox="0 0 24 24" fill="currentColor" className="w-[13px] h-[13px]">
        <path d="M18.6 7H5.4C5 7 4.8 7.5 5 7.8l2.6 3c.2.2.5.2.8.2h13.2c.4 0 .6-.5.4-.8l-2.6-3c-.2-.2-.5-.2-.8-.2zm-13.2 4H18.6c.4 0 .6.5.4.8l-2.6 3c-.2.2-.5.2-.8.2H5.4c-.4 0-.6-.5-.4-.8l2.6-3c.2-.2.5-.2.8-.2zm13.2 4H5.4c-.4 0-.6.5-.4.8l2.6 3c.2.2.5.2.8.2h13.2c.4 0 .6-.5.4-.8l-2.6-3c-.2-.2-.5-.2-.8-.2z" />
      </svg>
    );
  }
  return e.charAt(0).toUpperCase();
}

function formatProviderLabel(provider: string): string {
  const key = provider.trim().toLowerCase();
  if (!key || key === 'native' || key === 'csv') return 'CSV Import';
  return key.charAt(0).toUpperCase() + key.slice(1);
}

function txMatchesConnection(tx: Transaction, conn: ExchangeConnection): boolean {
  const provider = String(conn.exchange_name || conn.exchange || '').trim().toLowerCase();
  if (!provider) return false;
  if (tx.connection_id != null && String(tx.connection_id) === String(conn.id)) return true;
  const fmt = String(tx.import_format || '').toLowerCase();
  return fmt === provider || fmt.includes(provider);
}

function txMatchesCsv(tx: Transaction, csv: CsvImportSource): boolean {
  if (csv.runId != null) {
    return tx.run_id != null && tx.run_id === csv.runId;
  }
  const fmt = String(tx.import_format || '').toLowerCase();
  return fmt === csv.provider;
}

function txMatchesWallet(tx: Transaction, walletId: string | number): boolean {
  return tx.wallet_id != null && String(tx.wallet_id) === String(walletId);
}

function countForConnection(txs: Transaction[], conn: ExchangeConnection): number {
  if (conn.transaction_count != null && conn.transaction_count > 0) {
    return conn.transaction_count;
  }
  return txs.filter((tx) => txMatchesConnection(tx, conn)).length;
}

function countForCsv(txs: Transaction[], csv: CsvImportSource): number {
  const matched = txs.filter((tx) => txMatchesCsv(tx, csv)).length;
  if (matched > 0) return matched;
  return csv.transaction_count;
}

function shortenAddress(address: string): string {
  if (address.length <= 12) return address;
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

function walletStatusDot(wallet: WalletRow, txCount: number) {
  if (txCount > 0) return 'bg-[var(--tx-accent)]';
  if (wallet.sync_status === 'syncing' || wallet.sync_status === 'pending') return 'bg-[var(--tx-amber)]';
  return 'bg-[var(--tx-text-faint)]';
}

type ExchangeGroup = {
  key: string;
  name: string;
  connections: ExchangeConnection[];
  csvSources: CsvImportSource[];
};

interface TransactionListProps {
  setActiveTab?: (tab: string, subTab?: 'EXCHANGES' | 'WALLETS') => void;
}

type LoadedTransactionData = {
  txs: Transaction[];
  exData: ExchangeConnection[];
  walletRows: WalletRow[];
  csv: CsvImportSource[];
  hasNoSources: boolean;
  hasFailures: boolean;
};

async function loadTransactionData(): Promise<LoadedTransactionData> {
  const [txResult, exResult, connResult, runsResult] = await Promise.allSettled([
    apiV1.wallet.getTransactions(undefined, 10000),
    apiV1.exchange.listMy(),
    apiV1.wallet.list(),
    apiV1.analysis.listRuns(),
  ]);

  const txs =
    txResult.status === 'fulfilled' && Array.isArray(txResult.value) ? txResult.value : [];
  const exData =
    exResult.status === 'fulfilled' && Array.isArray(exResult.value) ? exResult.value : [];
  const connData = connResult.status === 'fulfilled' ? connResult.value : null;
  const runsData = runsResult.status === 'fulfilled' ? runsResult.value : { runs: [] };
  const walletRows: WalletRow[] = Array.isArray(connData)
    ? connData
    : (connData?.wallets ?? []);
  const csv = buildCsvImportSources(runsData.runs ?? []);
  const hasNoSources = walletRows.length === 0 && exData.length === 0 && csv.length === 0;
  const hasFailures = [txResult, exResult, connResult, runsResult].some((r) => r.status === 'rejected');

  return { txs, exData, walletRows, csv, hasNoSources, hasFailures };
}

export function TransactionList({ setActiveTab }: TransactionListProps) {
  const { backendOnline, dataVersion } = useAppContext();
  const { addToast } = useToast();

  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const [activeType, setActiveType] = useState<'all' | 'buy' | 'sell' | 'transfer' | 'income'>('all');
  const [activeSourceId, setActiveSourceId] = useState('all');
  const [sortKey, setSortKey] = useState('date-desc');
  const [filterSheetOpen, setFilterSheetOpen] = useState(false);

  const [allTransactions, setAllTransactions] = useState<Transaction[]>([]);
  const [exchanges, setExchanges] = useState<ExchangeConnection[]>([]);
  const [wallets, setWallets] = useState<WalletRow[]>([]);
  const [csvSources, setCsvSources] = useState<CsvImportSource[]>([]);
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!backendOnline) return;
    let cancelled = false;

    const fetchData = async () => {
      setLoading(true);
      try {
        const { txs, exData, walletRows, csv, hasNoSources, hasFailures } = await loadTransactionData();
        if (cancelled) return;
        setAllTransactions(txs);
        setExchanges(exData);
        setWallets(walletRows);
        setCsvSources(csv);
        if (hasFailures && !hasNoSources) {
          addToast('Failed to load transactions', 'error');
        }
      } catch (err) {
        if (cancelled) return;
        console.error('Failed to fetch transactions data', err);
        addToast('Failed to load transactions', 'error');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void fetchData();
    return () => {
      cancelled = true;
    };
  }, [backendOnline, dataVersion, addToast]);

  const exchangeGroups = useMemo(() => {
    const map = new Map<string, ExchangeGroup>();

    exchanges.forEach((conn) => {
      const key = String(conn.exchange_name || conn.exchange || 'exchange').trim().toLowerCase();
      if (!map.has(key)) {
        map.set(key, {
          key,
          name: formatProviderLabel(key),
          connections: [],
          csvSources: [],
        });
      }
      map.get(key)!.connections.push(conn);
    });

    csvSources.forEach((csv) => {
      const provider = csv.provider.trim().toLowerCase();
      const key = provider === 'native' || provider === 'csv' ? 'csv-import' : provider;
      if (!map.has(key)) {
        map.set(key, {
          key,
          name: formatProviderLabel(provider === 'native' || provider === 'csv' ? 'csv' : provider),
          connections: [],
          csvSources: [],
        });
      }
      map.get(key)!.csvSources.push(csv);
    });

    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [exchanges, csvSources]);

  const groupedWallets = useMemo(() => {
    const groups: Record<string, { items: WalletRow[]; count: number }> = {};
    wallets.forEach((w) => {
      const chain = (w.chain || w.blockchain || 'Unknown').trim();
      if (!groups[chain]) groups[chain] = { items: [], count: 0 };
      groups[chain].items.push(w);
      const fromApi = w.transaction_count ?? 0;
      groups[chain].count += fromApi > 0
        ? fromApi
        : allTransactions.filter((tx) => txMatchesWallet(tx, w.id)).length;
    });
    return groups;
  }, [wallets, allTransactions]);

  useEffect(() => {
    const defaults: Record<string, boolean> = {};
    exchangeGroups.forEach((g) => {
      defaults[`g-${g.key}`] = true;
    });
    Object.keys(groupedWallets).forEach((chain) => {
      defaults[`g-${chain}`] = true;
    });
    setOpenGroups((prev) => ({ ...defaults, ...prev }));
  }, [exchangeGroups, groupedWallets]);

  const toggleGroup = (id: string) => {
    setOpenGroups((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const selectSource = (sourceId: string) => {
    setActiveSourceId(sourceId);
    setPage(0);
  };

  const handleRefresh = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const { txs, exData, walletRows, csv, hasNoSources, hasFailures } = await loadTransactionData();
      setAllTransactions(txs);
      setExchanges(exData);
      setWallets(walletRows);
      setCsvSources(csv);
      if (hasFailures && !hasNoSources) {
        addToast('Failed to refresh transactions', 'error');
      } else {
        addToast('Transactions updated', 'success');
      }
    } catch {
      addToast('Failed to refresh transactions', 'error');
    } finally {
      setLoading(false);
    }
  };

  const hasNoSources =
    !loading && wallets.length === 0 && exchanges.length === 0 && csvSources.length === 0;

  const filtered = useMemo(() => {
    let res = allTransactions.filter((tx) => {
      const displayType = getDisplayTransactionType(tx);
      if (activeType !== 'all' && displayType !== activeType) return false;

      if (activeSourceId !== 'all') {
        if (activeSourceId.startsWith('ex_')) {
          const connId = Number(activeSourceId.replace('ex_', ''));
          const conn = exchanges.find((c) => c.id === connId);
          if (!conn || !txMatchesConnection(tx, conn)) return false;
        } else if (activeSourceId.startsWith('w_')) {
          const walletId = activeSourceId.replace('w_', '');
          if (!txMatchesWallet(tx, walletId)) return false;
        } else if (activeSourceId.startsWith('csv_')) {
          const csv = csvSources.find((c) => c.id === activeSourceId);
          if (!csv || !txMatchesCsv(tx, csv)) return false;
        }
      }

      if (search) {
        const q = search.toLowerCase();
        const conn = exchanges.find((c) => txMatchesConnection(tx, c));
        const sourceName = conn?.exchange_name || conn?.exchange || tx.import_format || tx.blockchain || '';
        return (
          tx.token?.toLowerCase().includes(q) ||
          tx.blockchain?.toLowerCase().includes(q) ||
          tx.type?.toLowerCase().includes(q) ||
          sourceName.toLowerCase().includes(q)
        );
      }
      return true;
    });

    res.sort((a, b) => {
      const vA = a.value_usd || 0;
      const vB = b.value_usd || 0;
      const tA = new Date(a.timestamp || 0).getTime();
      const tB = new Date(b.timestamp || 0).getTime();
      if (sortKey === 'date-desc') return tB - tA;
      if (sortKey === 'date-asc') return tA - tB;
      if (sortKey === 'val-desc') return vB - vA;
      return vA - vB;
    });

    return res;
  }, [allTransactions, activeType, activeSourceId, search, sortKey, exchanges, csvSources]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const safePage = Math.min(page, totalPages - 1);
  const paged = filtered.slice(safePage * PER_PAGE, (safePage + 1) * PER_PAGE);

  useEffect(() => {
    if (page !== safePage) setPage(safePage);
  }, [page, safePage]);

  const handleExportCSV = () => {
    if (filtered.length === 0) return;
    const headers = ['Type', 'Asset', 'Amount', 'Value USD', 'Source', 'Date'];
    const rows = filtered.map((tx) => {
      const conn = exchanges.find((c) => txMatchesConnection(tx, c));
      const source = conn?.exchange_name || conn?.exchange || tx.blockchain || 'Import';
      return [
        getDisplayTransactionType(tx),
        tx.token,
        tx.amount,
        tx.value_usd,
        source,
        tx.timestamp ? new Date(tx.timestamp).toISOString() : '',
      ];
    });
    const csvContent = [headers, ...rows].map((r) => r.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', `transactions_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    addToast('CSV exported', 'success');
  };

  const activeSourceMeta = useMemo(() => {
    if (activeSourceId === 'all') return null;
    if (activeSourceId.startsWith('ex_')) {
      const conn = exchanges.find((c) => `ex_${c.id}` === activeSourceId);
      if (!conn) return null;
      return {
        logo: conn.exchange_name || conn.exchange || 'EX',
        title: conn.exchange_name || conn.exchange || 'Exchange',
        method: 'API',
        subtitle: conn.label || undefined,
      };
    }
    if (activeSourceId.startsWith('w_')) {
      const wallet = wallets.find((w) => `w_${w.id}` === activeSourceId);
      if (!wallet) return null;
      return {
        logo: wallet.chain || wallet.blockchain || 'Chain',
        title: shortenAddress(wallet.address),
        method: 'Chain',
        subtitle: wallet.label || undefined,
      };
    }
    const csv = csvSources.find((c) => c.id === activeSourceId);
    if (!csv) return null;
    return {
      logo: formatProviderLabel(csv.provider),
      title: csv.name,
      method: 'CSV',
    };
  }, [activeSourceId, exchanges, wallets, csvSources]);

  const resolveRowSource = (tx: Transaction) => {
    const conn = exchanges.find((c) => txMatchesConnection(tx, c));
    if (conn) {
      return {
        shortName: conn.exchange_name || conn.exchange || 'Exchange',
        method: 'api' as const,
      };
    }
    if (tx.wallet_id != null) {
      const wallet = wallets.find((w) => String(w.id) === String(tx.wallet_id));
      return {
        shortName: wallet?.chain || wallet?.blockchain || tx.blockchain || 'Wallet',
        method: 'wallet' as const,
      };
    }
    if (tx.source === 'csv' || tx.run_id) {
      return {
        shortName: formatProviderLabel(tx.import_format || 'csv'),
        method: 'csv' as const,
      };
    }
    return {
      shortName: tx.blockchain || 'Import',
      method: (tx.source_method === 'wallet' ? 'wallet' : 'csv') as 'csv' | 'wallet',
    };
  };

  const pageNumbers = useMemo(() => {
    if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i);
    const nums = new Set<number>([0, safePage - 1, safePage, safePage + 1, totalPages - 1]);
    const sorted = Array.from(nums).filter((n) => n >= 0 && n < totalPages).sort((a, b) => a - b);
    const out: (number | 'ellipsis')[] = [];
    sorted.forEach((n, idx) => {
      if (idx > 0 && n - sorted[idx - 1] > 1) out.push('ellipsis');
      out.push(n);
    });
    return out;
  }, [totalPages, safePage]);

  const countLabel = activeSourceId === 'all' && activeType === 'all' && !search
    ? `${allTransactions.length} total`
    : `${filtered.length} total`;

  const groupTotalCount = (group: ExchangeGroup) =>
    allTransactions.filter(
      (tx) =>
        group.connections.some((c) => txMatchesConnection(tx, c)) ||
        group.csvSources.some((c) => txMatchesCsv(tx, c)),
    ).length;

  const walletTxCount = (w: WalletRow) => {
    if (w.transaction_count != null && w.transaction_count > 0) return w.transaction_count;
    return allTransactions.filter((tx) => txMatchesWallet(tx, w.id)).length;
  };

  const mobileSourceOptions = useMemo(() => {
    const options: Array<{ id: string; label: string; count: number }> = [
      { id: 'all', label: `All sources`, count: allTransactions.length },
    ];

    exchangeGroups.forEach((group) => {
      group.connections.forEach((conn) => {
        options.push({
          id: `ex_${conn.id}`,
          label: conn.label || conn.exchange_name || conn.exchange || 'Exchange',
          count: countForConnection(allTransactions, conn),
        });
      });
      group.csvSources.forEach((csv) => {
        options.push({
          id: csv.id,
          label: csv.name,
          count: countForCsv(allTransactions, csv),
        });
      });
    });

    Object.values(groupedWallets).forEach((group) => {
      group.items.forEach((wallet) => {
        options.push({
          id: `w_${wallet.id}`,
          label: wallet.label || shortenAddress(wallet.address),
          count: walletTxCount(wallet),
        });
      });
    });

    return options;
  }, [allTransactions.length, exchangeGroups, groupedWallets]);

  return (
    <div className="tx-pro flex flex-col flex-1 min-h-0 w-full bg-[var(--tx-page-bg)] overflow-hidden font-manrope text-[13px] text-[var(--tx-text)]">

      {/* ── MOBILE COMPACT HEADER ── */}
      <div className="md:hidden flex-shrink-0 border-b border-[var(--tx-border)] bg-[var(--tx-surface)]">
        {/* Row 1: Title + action icons */}
        <div className="flex items-center gap-2 px-4 pt-3 pb-2">
          <span className="font-syne text-[17px] font-bold tracking-[-0.3px] flex-1">Transactions</span>
          <span className="bg-[var(--tx-panel-muted)] border border-[var(--tx-border-strong)] rounded-[20px] px-2 py-0.5 text-[11px] font-semibold text-[var(--tx-text-muted)] font-mono">{countLabel}</span>
          <button
            type="button"
            onClick={handleExportCSV}
            disabled={filtered.length === 0}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-[var(--tx-text-muted)] hover:bg-[var(--tx-panel-muted)] transition-all disabled:opacity-40"
            aria-label="Export CSV"
          >
            <Download size={15} />
          </button>
          <button
            type="button"
            onClick={handleRefresh}
            disabled={loading}
            className={cn(
              'w-8 h-8 flex items-center justify-center rounded-lg text-[var(--tx-text-muted)] hover:bg-[var(--tx-panel-muted)] transition-all disabled:opacity-50',
              loading && 'animate-spin',
            )}
            aria-label="Refresh"
          >
            <RefreshCw size={15} />
          </button>
        </div>

        {/* Row 2: Search + Filter icon */}
        <div className="flex items-center gap-2 px-4 pb-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--tx-text-faint)]" />
            <input
              type="text"
              placeholder="Search asset, exchange..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              className="h-9 w-full rounded-xl border border-[var(--tx-border-strong)] bg-[var(--tx-page-bg)] pl-9 pr-3 text-[13px] text-[var(--tx-text)] outline-none placeholder:text-[var(--tx-text-faint)]"
            />
          </div>
          <button
            type="button"
            onClick={() => setFilterSheetOpen(true)}
            className={cn(
              'h-9 w-9 flex items-center justify-center rounded-xl border transition-all flex-shrink-0',
              filterSheetOpen || activeSourceId !== 'all' || sortKey !== 'date-desc'
                ? 'border-[var(--tx-accent)] bg-[var(--tx-accent-dim)] text-[var(--tx-accent)]'
                : 'border-[var(--tx-border-strong)] bg-[var(--tx-page-bg)] text-[var(--tx-text-muted)]',
            )}
            aria-label="Filters"
          >
            <SlidersHorizontal size={14} />
          </button>
        </div>

        {/* Row 3: Type pills */}
        <div className="no-scrollbar flex gap-1.5 overflow-x-auto px-4 pb-3" style={{ WebkitOverflowScrolling: 'touch' }}>
          {(['all', 'buy', 'sell', 'transfer', 'income'] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => { setActiveType(t); setPage(0); }}
              className={cn(
                'shrink-0 rounded-full px-3 py-1.5 text-[11px] font-bold capitalize transition-all',
                activeType === t
                  ? 'bg-[var(--tx-accent)] text-[var(--tx-accent-on)]'
                  : 'bg-[var(--tx-panel-muted)] text-[var(--tx-text-muted)]',
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* ── DESKTOP TOP BAR ── */}
      <div className="hidden md:block border-b border-[var(--tx-border)] bg-[var(--tx-surface)] px-6 flex-shrink-0" style={{ height: '56px' }}>
        <div className="flex h-full items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="font-syne text-[18px] font-bold tracking-[-0.3px]">Transactions</span>
            <span className="bg-[var(--tx-panel-muted)] border border-[var(--tx-border-strong)] rounded-[20px] px-2.5 py-1 text-[12px] font-semibold text-[var(--tx-text-muted)] font-mono">{countLabel}</span>
          </div>
          <div className="flex items-center gap-2">
            <button type="button" onClick={handleExportCSV} disabled={filtered.length === 0} className="flex min-h-[36px] items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-[12px] font-bold border border-[var(--tx-border-strong)] text-[var(--tx-text-muted)] hover:bg-[var(--tx-panel-muted)] hover:text-[var(--tx-text)] transition-all disabled:opacity-40">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[13px] h-[13px]"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Export CSV
            </button>
            <button type="button" onClick={handleRefresh} disabled={loading} className="flex min-h-[36px] items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-[12px] font-bold bg-[var(--tx-accent)] text-[var(--tx-accent-on)] hover:bg-[var(--tx-accent-hover)] transition-all disabled:opacity-60">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[13px] h-[13px]"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* ── FILTER BOTTOM SHEET (mobile) ── */}
      <div
        className={cn(
          'md:hidden fixed inset-0 z-[60] transition-opacity duration-300',
          filterSheetOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
        )}
      >
        {/* Backdrop */}
        <div
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={() => setFilterSheetOpen(false)}
        />
        {/* Sheet */}
        <div
          className={cn(
            'absolute bottom-0 left-0 right-0 rounded-t-3xl border-t border-[var(--tx-border)] shadow-2xl transition-transform duration-300 ease-out',
            filterSheetOpen ? 'translate-y-0' : 'translate-y-full',
          )}
          style={{ background: '#0B0E11' }}
        >
          {/* Handle */}
          <div className="flex justify-center pt-3 pb-1">
            <div className="w-10 h-1 rounded-full bg-[var(--tx-border-strong)]" />
          </div>
          <div className="px-5 pb-2 pt-1">
            <h3 className="text-[13px] font-bold text-[var(--tx-text)] tracking-tight">Filters &amp; Sort</h3>
          </div>

          <div className="px-5 pb-8 space-y-4">
            {/* Source */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-[0.1em] text-[var(--tx-text-faint)]">Source</label>
              <select
                value={activeSourceId}
                onChange={(e) => { selectSource(e.target.value); }}
                className="h-11 w-full rounded-xl border border-[var(--tx-border-strong)] bg-[var(--tx-page-bg)] px-4 text-[13px] font-semibold text-[var(--tx-text)] outline-none"
              >
                {mobileSourceOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label} ({option.count})
                  </option>
                ))}
              </select>
            </div>

            {/* Sort */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold uppercase tracking-[0.1em] text-[var(--tx-text-faint)]">Sort by</label>
              <select
                value={sortKey}
                onChange={(e) => setSortKey(e.target.value)}
                className="h-11 w-full rounded-xl border border-[var(--tx-border-strong)] bg-[var(--tx-page-bg)] px-4 text-[13px] font-semibold text-[var(--tx-text)] outline-none"
              >
                <option value="date-desc">Newest first</option>
                <option value="date-asc">Oldest first</option>
                <option value="val-desc">Value: High → Low</option>
                <option value="val-asc">Value: Low → High</option>
              </select>
            </div>

            {/* Export */}
            <button
              type="button"
              onClick={() => { handleExportCSV(); setFilterSheetOpen(false); }}
              disabled={filtered.length === 0}
              className="flex h-11 w-full items-center justify-center gap-2 rounded-xl border border-[var(--tx-border-strong)] text-[13px] font-bold text-[var(--tx-text-muted)] hover:text-[var(--tx-text)] transition-all disabled:opacity-40"
            >
              <Download size={15} />
              Export CSV ({filtered.length})
            </button>

            {/* Apply */}
            <button
              type="button"
              onClick={() => setFilterSheetOpen(false)}
              className="flex h-11 w-full items-center justify-center rounded-xl bg-[var(--tx-accent)] text-[13px] font-bold text-[var(--tx-accent-on)] transition-all active:scale-[0.98]"
            >
              Apply
            </button>
          </div>
        </div>
      </div>

      {/* ── MOBILE TRANSACTION LIST ── */}
      <div className="md:hidden flex-1 overflow-y-auto px-4 pt-3 pb-4 space-y-2.5 custom-scrollbar">
        {loading && paged.length === 0 && (
          <div className="py-16 text-center text-[var(--tx-text-faint)]">Loading...</div>
        )}
        {!loading && hasNoSources && (
          <div className="rounded-2xl border border-[var(--tx-border)] bg-[var(--tx-surface)] px-6 py-12 text-center">
            <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--tx-accent-dim)] text-[var(--tx-accent)]">
              <Wallet size={28} />
            </div>
            <h3 className="mb-2 font-syne text-lg font-bold text-[var(--tx-text)]">No data sources yet</h3>
            <p className="mb-6 text-[13px] text-[var(--tx-text-muted)]">Connect a wallet or exchange to import transactions.</p>
            <button
              type="button"
              onClick={() => setActiveTab?.('integrations', 'WALLETS')}
              className="inline-flex min-h-[48px] items-center gap-2 rounded-xl bg-[var(--tx-accent)] px-6 py-3 font-bold text-white"
            >
              <Plus size={14} strokeWidth={2.5} />
              Connect data
            </button>
          </div>
        )}
        {!loading && !hasNoSources && paged.length === 0 && (
          <div className="py-16 text-center text-[var(--tx-text-faint)]">No transactions found</div>
        )}

        {!loading && !hasNoSources && paged.map((tx) => {
          const displayType = getDisplayTransactionType(tx);
          const typeClass =
            displayType === 'buy' ? 'bg-[var(--tx-accent-dim)] text-[var(--tx-accent)]' :
            displayType === 'sell' ? 'bg-[var(--tx-red-dim)] text-[var(--tx-red)]' :
            displayType === 'transfer' ? 'bg-[var(--tx-blue-dim)] text-[var(--tx-blue)]' :
            displayType === 'income' ? 'bg-[var(--tx-purple-dim)] text-[var(--tx-purple)]' :
            'bg-[var(--tx-panel-muted)] text-[var(--tx-text-muted)]';
          const srcInfo = resolveRowSource(tx);
          const valueUsd = `$${(tx.value_usd || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
          return (
            <div key={tx.id} className="rounded-2xl border border-[var(--tx-border)] bg-[var(--tx-surface)] p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span className={cn('inline-flex min-h-[32px] items-center gap-[5px] rounded-[8px] px-[10px] py-1 text-[11px] font-bold capitalize whitespace-nowrap', typeClass)}>
                    {TypeIcons[displayType as keyof typeof TypeIcons] || TypeIcons.transfer}
                    {displayType}
                  </span>
                  <div className="flex items-center gap-[9px] min-w-0">
                    <div className={cn('flex h-8 w-8 rounded-full items-center justify-center text-[10px] font-extrabold flex-shrink-0', getAssetColors(tx.token || 'UNK'))}>
                      {(tx.token || 'U').slice(0, 3).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <div className="truncate text-[14px] font-bold tracking-[0.3px]">{tx.token?.toUpperCase()}</div>
                      <div className="truncate text-[11px] text-[var(--tx-text-faint)] capitalize">{tx.blockchain || '—'}</div>
                    </div>
                  </div>
                </div>
                <div className="text-right text-[14px] font-bold font-mono text-[var(--tx-text)]">{valueUsd}</div>
              </div>

              <div className="mt-3 grid grid-cols-3 gap-2 text-[11px] text-[var(--tx-text-faint)]">
                <div className="truncate font-mono">{Number(tx.amount || 0).toFixed(6)} {tx.token?.toUpperCase()}</div>
                <div className="truncate text-center">{srcInfo.shortName}</div>
                <div className="truncate text-right font-mono">{tx.timestamp ? new Date(tx.timestamp).toLocaleDateString('en-GB').replace(/\//g, '.') : '—'}</div>
              </div>
            </div>
          );
        })}

        {!loading && !hasNoSources && filtered.length > 0 && (
          <div className="flex items-center justify-between gap-3 rounded-2xl border border-[var(--tx-border)] bg-[var(--tx-surface)] p-3">
            <button
              type="button"
              disabled={safePage === 0}
              onClick={() => setPage((p) => p - 1)}
              className="min-h-[44px] rounded-xl border border-[var(--tx-border-strong)] px-4 text-[12px] font-semibold text-[var(--tx-text-muted)] disabled:opacity-30"
            >
              Назад
            </button>
            <span className="text-[12px] font-mono text-[var(--tx-text-faint)]">
              {safePage + 1} из {totalPages}
            </span>
            <button
              type="button"
              disabled={safePage >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              className="min-h-[44px] rounded-xl border border-[var(--tx-border-strong)] px-4 text-[12px] font-semibold text-[var(--tx-text-muted)] disabled:opacity-30"
            >
              Вперед
            </button>
          </div>
        )}
      </div>

      <div className="hidden md:flex flex-1 overflow-hidden">
        <div className="w-[260px] border-r border-[var(--tx-border)] bg-[var(--tx-surface)] flex flex-col overflow-y-auto flex-shrink-0 custom-scrollbar">
          <div className="p-3.5 pb-2">
            <div
              onClick={() => selectSource('all')}
              className={cn(
                'flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer mb-1 transition-all border border-transparent hover:bg-[var(--tx-panel-elevated)]',
                activeSourceId === 'all' && 'bg-[var(--tx-accent-dim)] border-[var(--tx-accent-border)]',
              )}
            >
              <div className={cn('w-7 h-7 rounded-md flex items-center justify-center text-[var(--tx-text-muted)]', activeSourceId === 'all' ? 'bg-[var(--tx-accent-dim)] text-[var(--tx-accent)]' : 'bg-[var(--tx-panel-muted)]')}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-3.5 h-3.5"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
              </div>
              <span className={cn('font-semibold text-[13px] flex-1', activeSourceId === 'all' && 'text-[var(--tx-accent)]')}>All sources</span>
              <span className="text-[11px] text-[var(--tx-text-faint)] font-mono">{allTransactions.length}</span>
            </div>
          </div>
          <div className="h-px bg-[var(--tx-border)] mx-3.5 my-2" />
          <div className="p-3.5 pt-4 pb-2">
            <div className="text-[10px] font-bold uppercase tracking-[1px] text-[var(--tx-text-faint)] px-1.5 mb-1.5 flex items-center justify-between">
              CEX Exchanges
              <button type="button" className="text-[var(--tx-accent)] normal-case tracking-normal hover:underline" onClick={() => selectSource('all')}>Clear</button>
            </div>
            {exchangeGroups.length === 0 && <p className="px-2.5 py-2 text-[12px] text-[var(--tx-text-faint)]">No exchange connections yet</p>}
            {exchangeGroups.map((group) => {
              const groupId = `g-${group.key}`;
              return (
                <div key={group.key} className="mb-1">
                  <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg cursor-pointer hover:bg-[var(--tx-panel-elevated)] transition-colors" onClick={() => toggleGroup(groupId)}>
                    <div className={cn('w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-extrabold flex-shrink-0', getExchangeColors(group.name))}>{getExchangeIcon(group.name)}</div>
                    <span className="text-[12px] font-bold flex-1 text-[var(--tx-text-muted)]">{group.name}</span>
                    <span className="text-[11px] text-[var(--tx-text-faint)] font-mono">{groupTotalCount(group)}</span>
                    <span className="text-[var(--tx-text-faint)] flex items-center"><ChevronDown size={12} className={cn('transition-transform', !openGroups[groupId] && '-rotate-90')} /></span>
                  </div>
                  {openGroups[groupId] && (
                    <div className="pl-3.5">
                      {group.csvSources.map((csv) => {
                        const sid = csv.id;
                        const active = activeSourceId === sid;
                        const count = countForCsv(allTransactions, csv);
                        return (
                          <div key={csv.id} onClick={() => selectSource(sid)} className={cn('flex items-center gap-2 px-2.5 py-1.5 rounded-lg cursor-pointer transition-all border border-transparent mb-0.5 relative', active ? 'bg-[var(--tx-accent-dim-soft)] border-[var(--tx-accent-border-soft)]' : 'hover:bg-[var(--tx-panel-elevated)]')}>
                            <div className="absolute left-[-6px] top-1/2 -translate-y-1/2 w-px h-[60%] bg-[var(--tx-border-strong)]" />
                            <div className="w-5 h-5 rounded-[5px] flex items-center justify-center flex-shrink-0 bg-[var(--tx-amber-dim)] text-[var(--tx-amber)]">
                              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[11px] h-[11px]"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                            </div>
                            <span className={cn('text-[12px] font-semibold flex-1 truncate', active && 'text-[var(--tx-accent)]')}>{csv.name}</span>
                            <div className="flex flex-col items-end gap-[1px]">
                              <span className="text-[10px] text-[var(--tx-text-faint)] font-mono">{count}</span>
                              <span className="text-[9px] font-bold px-1 rounded-[3px] tracking-[0.3px] bg-[var(--tx-amber-dim)] text-[var(--tx-amber)]">CSV</span>
                            </div>
                            <div className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0 ml-2', count > 0 ? 'bg-[var(--tx-accent)]' : 'bg-[var(--tx-amber)]')} />
                          </div>
                        );
                      })}
                      {group.connections.map((conn) => {
                        const sid = `ex_${conn.id}`;
                        const active = activeSourceId === sid;
                        const count = countForConnection(allTransactions, conn);
                        const label = conn.label || `API · ${conn.exchange_name || conn.exchange || 'Account'}`;
                        return (
                          <div key={conn.id} onClick={() => selectSource(sid)} className={cn('flex items-center gap-2 px-2.5 py-1.5 rounded-lg cursor-pointer transition-all border border-transparent mb-0.5 relative', active ? 'bg-[var(--tx-accent-dim-soft)] border-[var(--tx-accent-border-soft)]' : 'hover:bg-[var(--tx-panel-elevated)]')}>
                            <div className="absolute left-[-6px] top-1/2 -translate-y-1/2 w-px h-[60%] bg-[var(--tx-border-strong)]" />
                            <div className="w-5 h-5 rounded-[5px] flex items-center justify-center flex-shrink-0 bg-[var(--tx-blue-dim)] text-[var(--tx-blue)]">
                              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[11px] h-[11px]"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
                            </div>
                            <span className={cn('text-[12px] font-semibold flex-1 truncate', active && 'text-[var(--tx-accent)]')}>{label}</span>
                            <div className="flex flex-col items-end gap-[1px]">
                              <span className="text-[10px] text-[var(--tx-text-faint)] font-mono">{count}</span>
                              <span className="text-[9px] font-bold px-1 rounded-[3px] tracking-[0.3px] bg-[var(--tx-blue-dim)] text-[var(--tx-blue)]">API</span>
                            </div>
                            <div className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0 ml-2', count > 0 ? 'bg-[var(--tx-accent)]' : 'bg-[var(--tx-text-faint)]')} />
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <div className="h-px bg-[var(--tx-border)] mx-3.5 my-2" />
          <div className="p-3.5 pt-4 pb-6">
            <div className="text-[10px] font-bold uppercase tracking-[1px] text-[var(--tx-text-faint)] px-1.5 mb-1.5">On-chain Wallets</div>
            {Object.keys(groupedWallets).length === 0 && <p className="px-2.5 py-2 text-[12px] text-[var(--tx-text-faint)]">No wallets connected yet</p>}
            {Object.entries(groupedWallets).map(([chain, data]) => {
              const groupId = `g-${chain}`;
              return (
                <div key={chain} className="mb-1">
                  <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg cursor-pointer hover:bg-[var(--tx-panel-elevated)] transition-colors" onClick={() => toggleGroup(groupId)}>
                    <div className={cn('w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-extrabold flex-shrink-0', getAssetColors(chain))}>{getExchangeIcon(chain)}</div>
                    <span className="text-[12px] font-bold flex-1 text-[var(--tx-text-muted)] capitalize">{chain}</span>
                    <span className="text-[11px] text-[var(--tx-text-faint)] font-mono">{data.count}</span>
                    <span className="text-[var(--tx-text-faint)] flex items-center"><ChevronDown size={12} className={cn('transition-transform', !openGroups[groupId] && '-rotate-90')} /></span>
                  </div>
                  {openGroups[groupId] && (
                    <div className="pl-3.5">
                      {data.items.map((w) => {
                        const sid = `w_${w.id}`;
                        const active = activeSourceId === sid;
                        const count = walletTxCount(w);
                        return (
                          <div key={w.id} onClick={() => selectSource(sid)} className={cn('flex items-center gap-2 px-2.5 py-1.5 rounded-lg cursor-pointer transition-all border border-transparent mb-0.5 relative', active ? 'bg-[var(--tx-accent-dim-soft)] border-[var(--tx-accent-border-soft)]' : 'hover:bg-[var(--tx-panel-elevated)]')}>
                            <div className="absolute left-[-6px] top-1/2 -translate-y-1/2 w-px h-[60%] bg-[var(--tx-border-strong)]" />
                            <div className="w-5 h-5 rounded-[5px] flex items-center justify-center flex-shrink-0 bg-[var(--tx-purple-dim)] text-[var(--tx-purple)]">
                              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[11px] h-[11px]"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
                            </div>
                            <span className={cn('text-[12px] font-semibold flex-1 truncate', active && 'text-[var(--tx-accent)]')}>{w.label || shortenAddress(w.address)}</span>
                            <div className="flex flex-col items-end gap-[1px]">
                              <span className="text-[10px] text-[var(--tx-text-faint)] font-mono">{count}</span>
                              <span className="text-[9px] font-bold px-1 rounded-[3px] tracking-[0.3px] bg-[var(--tx-purple-dim)] text-[var(--tx-purple)]">Chain</span>
                            </div>
                            <div className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0 ml-2', walletStatusDot(w, count))} />
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        <div className="flex-1 flex flex-col overflow-hidden relative">
          <div className="flex items-center gap-2 px-5 py-2.5 border-b border-[var(--tx-border)] bg-[var(--tx-surface)] flex-shrink-0 min-h-[44px]">
            {!activeSourceMeta ? (
              <span className="text-[12px] text-[var(--tx-text-muted)] font-medium">Showing all sources</span>
            ) : (
              <>
                <span className="text-[12px] text-[var(--tx-text-muted)] font-medium">Filtered by</span>
                <div className="flex items-center gap-1.5 bg-[var(--tx-panel-muted)] border border-[var(--tx-border-strong)] rounded-[20px] px-2.5 py-1 text-[12px] font-semibold">
                  <div className={cn('w-4 h-4 rounded-[4px] flex items-center justify-center text-[8px] font-extrabold', getExchangeColors(activeSourceMeta.logo))}>{getExchangeIcon(activeSourceMeta.logo)}</div>
                  {activeSourceMeta.title}
                  <span className="text-[var(--tx-text-faint)] ml-1">{activeSourceMeta.method}</span>
                  <div className="w-3.5 h-3.5 rounded-full bg-[var(--tx-border-strong)] flex items-center justify-center cursor-pointer ml-0.5 text-[var(--tx-text-faint)] hover:bg-[var(--tx-red-hover)] hover:text-[var(--tx-red)] transition-colors" onClick={() => selectSource('all')}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="w-2 h-2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className="flex items-center gap-2.5 px-5 py-2.5 border-b border-[var(--tx-border)] bg-[var(--tx-panel)] flex-shrink-0">
            <div className="flex bg-[var(--tx-surface)] border border-[var(--tx-border)] rounded-lg p-[3px] gap-[2px]">
              {(['all', 'buy', 'sell', 'transfer', 'income'] as const).map((t) => (
                <div
                  key={t}
                  onClick={() => { setActiveType(t); setPage(0); }}
                  className={cn(
                    'px-3.5 py-1.5 rounded-[6px] cursor-pointer text-[12px] font-bold transition-all tracking-[0.3px] capitalize',
                    activeType === t ? 'bg-[var(--tx-panel-muted)] text-[var(--tx-text)]' : 'text-[var(--tx-text-faint)] hover:text-[var(--tx-text-muted)]',
                  )}
                >
                  {t}
                </div>
              ))}
            </div>
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--tx-text-faint)]" />
              <input
                type="text"
                placeholder="Search asset, exchange..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(0); }}
                className="w-full bg-[var(--tx-surface)] border border-[var(--tx-border-strong)] rounded-lg pl-[34px] pr-3.5 py-1.5 text-[13px] text-[var(--tx-text)] outline-none focus:border-[var(--tx-accent)] transition-colors placeholder:text-[var(--tx-text-faint)]"
              />
            </div>
            <select
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value)}
              className="bg-[var(--tx-surface)] border border-[var(--tx-border-strong)] rounded-lg px-3 py-1.5 text-[var(--tx-text-muted)] text-[12px] font-semibold outline-none cursor-pointer"
            >
              <option value="date-desc">Newest first</option>
              <option value="date-asc">Oldest first</option>
              <option value="val-desc">Value: High → Low</option>
              <option value="val-asc">Value: Low → High</option>
            </select>
          </div>

          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <table className="w-full border-collapse">
              <thead className="sticky top-0 z-10">
                <tr className="bg-[var(--tx-panel)] border-b border-[var(--tx-border)]">
                  <th className="p-2.5 px-4 text-[10px] font-bold uppercase tracking-[0.8px] text-[var(--tx-text-faint)] text-left">Type</th>
                  <th className="p-2.5 px-4 text-[10px] font-bold uppercase tracking-[0.8px] text-[var(--tx-text-faint)] text-left">Asset</th>
                  <th className="p-2.5 px-4 text-[10px] font-bold uppercase tracking-[0.8px] text-[var(--tx-text-faint)] text-left">Amount</th>
                  <th className="p-2.5 px-4 text-[10px] font-bold uppercase tracking-[0.8px] text-[var(--tx-accent)] text-left">Value</th>
                  <th className="p-2.5 px-4 text-[10px] font-bold uppercase tracking-[0.8px] text-[var(--tx-text-faint)] text-left">Source</th>
                  <th className="p-2.5 px-4 text-[10px] font-bold uppercase tracking-[0.8px] text-[var(--tx-text-faint)] text-left">Date</th>
                </tr>
              </thead>
              <tbody>
                {loading && paged.length === 0 && (
                  <tr><td colSpan={6} className="text-center py-20 text-[var(--tx-text-faint)]">Loading...</td></tr>
                )}
                {!loading && hasNoSources && (
                  <tr>
                    <td colSpan={6}>
                      <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
                        <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-5 bg-[var(--tx-accent-dim)] text-[var(--tx-accent)]">
                          <Wallet size={28} />
                        </div>
                        <h3 className="font-syne font-bold text-lg text-[var(--tx-text)] mb-2">No data sources yet</h3>
                        <p className="text-[13px] text-[var(--tx-text-muted)] max-w-[400px] mb-6">
                          Connect a wallet or exchange to import transactions. Nothing will appear here until you add a source.
                        </p>
                        <button
                          type="button"
                          onClick={() => setActiveTab?.('integrations', 'WALLETS')}
                          className="inline-flex items-center gap-2 bg-[var(--tx-accent)] text-white font-bold px-6 py-2.5 rounded-lg transition-all hover:brightness-95 shadow-[0_2px_6px_rgba(16,185,129,0.3)]"
                        >
                          <Plus size={14} strokeWidth={2.5} />
                          Connect data
                          <ArrowRight size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                )}
                {!loading && !hasNoSources && paged.length === 0 && (
                  <tr><td colSpan={6} className="text-center py-20 text-[var(--tx-text-faint)]">No transactions found</td></tr>
                )}
                {paged.map((tx, i) => {
                  const displayType = getDisplayTransactionType(tx);
                  const typeClass =
                    displayType === 'buy' ? 'bg-[var(--tx-accent-dim)] text-[var(--tx-accent)]' :
                    displayType === 'sell' ? 'bg-[var(--tx-red-dim)] text-[var(--tx-red)]' :
                    displayType === 'transfer' ? 'bg-[var(--tx-blue-dim)] text-[var(--tx-blue)]' :
                    displayType === 'income' ? 'bg-[var(--tx-purple-dim)] text-[var(--tx-purple)]' :
                    'bg-[var(--tx-panel-muted)] text-[var(--tx-text-muted)]';
                  const srcInfo = resolveRowSource(tx);
                  const valClass = displayType === 'sell' ? 'text-[var(--tx-red)]' : displayType === 'transfer' ? 'text-[var(--tx-text-muted)]' : 'text-[var(--tx-accent)]';
                  return (
                    <tr key={tx.id} className="border-b border-[var(--tx-border)] hover:bg-[var(--tx-panel-elevated)] transition-colors" style={{ animationDelay: `${i * 30}ms` }}>
                      <td className="p-3 px-4">
                        <span className={cn('inline-flex items-center gap-[5px] text-[11px] font-bold px-[9px] py-1 rounded-[6px] tracking-[0.3px] capitalize whitespace-nowrap', typeClass)}>
                          {TypeIcons[displayType as keyof typeof TypeIcons] || TypeIcons.transfer}
                          {displayType}
                        </span>
                      </td>
                      <td className="p-3 px-4">
                        <div className="flex items-center gap-[9px]">
                          <div className={cn('w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-extrabold flex-shrink-0', getAssetColors(tx.token || 'UNK'))}>
                            {(tx.token || 'U').slice(0, 3).toUpperCase()}
                          </div>
                          <div>
                            <div className="text-[13px] font-bold tracking-[0.3px]">{tx.token?.toUpperCase()}</div>
                            <div className="text-[11px] text-[var(--tx-text-faint)] mt-[1px] capitalize">{tx.blockchain || '—'}</div>
                          </div>
                        </div>
                      </td>
                      <td className="p-3 px-4 font-mono text-[12px] text-[var(--tx-text-muted)]">{Number(tx.amount || 0).toFixed(6)}</td>
                      <td className={cn('p-3 px-4 font-mono text-[12px] font-semibold', valClass)}>
                        ${(tx.value_usd || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td className="p-3 px-4">
                        <div className="flex items-center gap-[7px]">
                          <div className={cn('w-5 h-5 rounded-[5px] flex items-center justify-center text-[9px] font-extrabold flex-shrink-0', getExchangeColors(srcInfo.shortName))}>
                            {getExchangeIcon(srcInfo.shortName)}
                          </div>
                          <span className="text-[12px] font-semibold text-[var(--tx-text-muted)]">{srcInfo.shortName}</span>
                          <span className={cn(
                            'text-[9px] font-bold px-1.5 py-0.5 rounded-[3px] tracking-[0.3px] uppercase',
                            srcInfo.method === 'api' ? 'bg-[var(--tx-blue-dim)] text-[var(--tx-blue)]' :
                            srcInfo.method === 'wallet' ? 'bg-[var(--tx-purple-dim)] text-[var(--tx-purple)]' :
                            'bg-[var(--tx-amber-dim)] text-[var(--tx-amber)]',
                          )}>{srcInfo.method}</span>
                        </div>
                      </td>
                      <td className="p-3 px-4 font-mono text-[11px] text-[var(--tx-text-faint)]">
                        {tx.timestamp ? new Date(tx.timestamp).toLocaleDateString('en-GB').replace(/\//g, '.') : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between p-3 px-5 border-t border-[var(--tx-border)] bg-[var(--tx-panel)] flex-shrink-0">
            <span className="text-[12px] text-[var(--tx-text-faint)]">Showing {paged.length} of {filtered.length}</span>
            <div className="flex gap-[3px]">
              <button type="button" disabled={safePage === 0} onClick={() => setPage((p) => p - 1)} className="w-7 h-7 rounded-[6px] border border-[var(--tx-border-strong)] bg-transparent text-[var(--tx-text-faint)] text-[12px] font-semibold flex items-center justify-center hover:border-[var(--tx-accent)] hover:text-[var(--tx-accent)] transition-all font-mono disabled:opacity-30">‹</button>
              {pageNumbers.map((item, idx) =>
                item === 'ellipsis' ? (
                  <span key={`e-${idx}`} className="text-[var(--tx-text-faint)] px-1 font-mono">…</span>
                ) : (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setPage(item)}
                    className={cn(
                      'w-7 h-7 rounded-[6px] border text-[12px] font-semibold flex items-center justify-center transition-all font-mono',
                      safePage === item ? 'bg-[var(--tx-accent)] text-[var(--tx-accent-on)] border-[var(--tx-accent)]' : 'bg-transparent border-[var(--tx-border-strong)] text-[var(--tx-text-faint)] hover:border-[var(--tx-accent)] hover:text-[var(--tx-accent)]',
                    )}
                  >
                    {item + 1}
                  </button>
                ),
              )}
              <button type="button" disabled={safePage >= totalPages - 1} onClick={() => setPage((p) => p + 1)} className="w-7 h-7 rounded-[6px] border border-[var(--tx-border-strong)] bg-transparent text-[var(--tx-text-faint)] text-[12px] font-semibold flex items-center justify-center hover:border-[var(--tx-accent)] hover:text-[var(--tx-accent)] transition-all font-mono disabled:opacity-30">›</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
