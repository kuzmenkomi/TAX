import { useState, useEffect } from 'react';
import {
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Download,
  Filter,
  MoreVertical,
  ChevronRight,
  ChevronLeft,
  ShieldCheck,
  Search,
  Upload,
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { MatchEntry } from '../api/client';
import { FiltersPanel, type FilterState } from './FiltersPanel';
import { useToast } from '../context/ToastContext';
import apiV1 from '../api/v1';
import { BulkActionBar } from './ui/BulkActionBar';
import { AuditTrailModal } from './AuditTrailModal';
import { MatchEntry } from '../api/client';

function fmt(n: unknown): string {
  const num = Number(n);
  if (isNaN(num)) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(num);
}

function fmtNum(n: unknown, decimals = 6): string {
  const num = Number(n);
  if (isNaN(num)) return String(n ?? '—');
  return num.toFixed(decimals);
}

// Convert a backend match to a themed table row
function MatchToRow({ 
  match, 
  index, 
  isSelected, 
  onToggle,
  onAudit
}: { 
  match: any; 
  index: number; 
  isSelected: boolean;
  onToggle: () => void;
  onAudit: () => void;
}) {
  const gl = Number(match.gain_loss ?? 0);
  const isGain = gl >= 0;

  return (
    <tr 
      className={`hover:bg-brand-green-500/5 transition-colors border-b last:border-0 ${isSelected ? 'bg-brand-green-500/10' : ''}`} 
      style={{ borderColor: 'var(--border)' }}
    >
      <td className="px-5 py-4 w-4">
        <input 
          type="checkbox" 
          checked={isSelected}
          onChange={onToggle}
          className="w-4 h-4 rounded border-gray-300 text-brand-green-500 focus:ring-brand-green-500 cursor-pointer"
        />
      </td>
      <td className="px-5 py-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isGain ? 'bg-[#6af0c8]/10 text-[#6af0c8]' : 'bg-[#f06a6a]/10 text-[#f06a6a]'}`}>
            {isGain ? <ArrowDownRight className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
          </div>
          <span className="font-medium text-[13px]" style={{ color: 'var(--text)' }}>{isGain ? 'Realized Gain' : 'Realized Loss'}</span>
        </div>
      </td>
      <td className="px-5 py-4">
        <div className="flex flex-col">
          <span className="text-[13px] font-semibold tracking-tight uppercase" style={{ color: 'var(--text)' }}>
            {String(match.asset ?? match.symbol ?? `Match #${index + 1}`).toUpperCase()}
          </span>
          <span className="text-[11px] mt-0.5" style={{ color: 'var(--text3)' }}>{String(match.sell_timestamp ?? match.sell_date ?? '—').slice(0, 10)}</span>
        </div>
      </td>
      <td className="hidden sm:table-cell px-5 py-4">
        <span className="text-[11px] px-2 py-1 rounded-md" style={{ background: 'var(--bg2)', color: 'var(--text2)' }}>
          {String(match.buy_timestamp ?? match.buy_date ?? '—').slice(0, 10)}
        </span>
      </td>
      <td className="px-5 py-4">
        <span className="text-[13px] font-semibold" style={{ color: 'var(--text)' }}>{fmtNum(match.amount, 4)}</span>
      </td>
      <td className="px-5 py-4">
        <span className={`text-[13px] font-semibold ${isGain ? 'text-[#6af0c8]' : 'text-[#f06a6a]'}`}>
          {isGain ? '+' : ''}{fmt(gl)}
        </span>
      </td>
      <td className="hidden md:table-cell px-5 py-4">
        <button 
          onClick={(e) => { e.stopPropagation(); onAudit(); }}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider bg-brand-green-500/10 text-brand-green-500 border border-brand-green-500/15 hover:bg-brand-green-500/20 transition-all"
        >
          <ShieldCheck className="w-3 h-3" />
          Audit Trail
        </button>
      </td>
      <td className="px-5 py-4 text-right">
        <button className="p-1.5 transition-colors rounded-lg hover:bg-white/5" style={{ color: 'var(--text3)' }}>
          <MoreVertical className="w-4 h-4" />
        </button>
      </td>
    </tr>
  );
}

export function TransactionList() {
  const { analyzeResult, backendOnline } = useAppContext();
  const { addToast } = useToast();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const [apiTransactions, setApiTransactions] = useState<any[]>([]);
  const [loadingApi, setLoadingApi] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    sortBy: 'ascending',
    accounts: [],
    assets: [],
    dateRange: null,
    blockchainAddresses: [],
    transactionTypes: [],
  });
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  
  // Audit Trail State
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);
  const [selectedTx, setSelectedTx] = useState<{ id?: number | string; asset?: string; amount?: number } | null>(null);

  const openAuditTrail = (match: any) => {
    setSelectedTx({
      id: match.sell_tx_id,
      asset: match.asset,
      amount: match.amount
    });
    setIsAuditModalOpen(true);
  };

  const PER_PAGE = 15;

  const toggleSelect = (id: number) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  const handleBulkAction = async (action: string) => {
    const ids = Array.from(selectedIds);
    addToast(`Processing ${ids.length} items...`, 'info');
    
    try {
      // Mapping local UI actions to backend resolution types
      const resolutionMap: Record<string, string> = {
        'TRANSFER': 'INTERNAL_TRANSFER',
        'IGNORE': 'IGNORE',
        'TAG': 'GIFT', // Example
      };
      
      const resolution = resolutionMap[action] || 'IGNORE';
      
      await apiV1.reconciliation.bulkResolve({
        issue_ids: ids,
        resolution
      });
      
      addToast(`Successfully updated ${ids.length} transactions`, 'success');
      setSelectedIds(new Set());
      handleRefresh();
    } catch {
      addToast('Failed to perform bulk action', 'error');
    }
  };

  // Fetch transactions from API
  useEffect(() => {
    if (!backendOnline) return;
    (async () => {
      setLoadingApi(true);
      try {
        const txs = await apiV1.wallet.getTransactions(undefined, 10000);
        setApiTransactions(txs);
      } catch { /* no transactions yet */ }
      finally { setLoadingApi(false); }
    })();
  }, [backendOnline]);

  // Merge: prefer analyzeResult matches if available, else show API transactions
  const hasAnalyzeData = analyzeResult && (analyzeResult.lot_matches?.length > 0);

  const filteredMatches = hasAnalyzeData
    ? (analyzeResult.lot_matches || [])
        .filter((m) => {
          const q = search.toLowerCase();
          if (q && !String(m.asset ?? m.symbol ?? '').toLowerCase().includes(q) &&
              !String(m.buy_date ?? '').includes(q) &&
              !String(m.sell_date ?? '').includes(q)) {
            return false;
          }
          return true;
        })
        .sort((a, b) => {
          const aVal = Number(a.gain_loss ?? 0);
          const bVal = Number(b.gain_loss ?? 0);
          return filters.sortBy === 'ascending' ? aVal - bVal : bVal - aVal;
        })
    : [];

  const filteredApiTxs = apiTransactions.filter((tx) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      String(tx.token ?? '').toLowerCase().includes(q) ||
      String(tx.blockchain ?? '').toLowerCase().includes(q) ||
      String(tx.type ?? '').toLowerCase().includes(q)
    );
  });

  const totalItems = hasAnalyzeData ? filteredMatches.length : filteredApiTxs.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / PER_PAGE));
  const pageMatches = hasAnalyzeData
    ? filteredMatches.slice(page * PER_PAGE, (page + 1) * PER_PAGE)
    : [];
  const pageApiTxs = !hasAnalyzeData
    ? filteredApiTxs.slice(page * PER_PAGE, (page + 1) * PER_PAGE)
    : [];

  const handleExport = () => {
    addToast('Exporting transactions as CSV...', 'info');
  };

  const handleRefresh = async () => {
    addToast('Refreshing transactions...', 'info');
    try {
      const txs = await apiV1.wallet.getTransactions(undefined, 10000);
      setApiTransactions(txs);
      addToast(`Loaded ${txs.length} transactions`, 'success');
    } catch {
      addToast('Failed to refresh', 'error');
    }
  };

  const noData = !hasAnalyzeData && filteredApiTxs.length === 0 && !loadingApi;

  return (
    <div className="space-y-5 animate-in fade-in slide-in-from-bottom-4 duration-500">

      {/* Header Container */}
      <div className="border rounded-[14px] p-6 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-5">
          <div>
            <h2 className="text-xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>Transactions</h2>
            <p className="text-[13px] mt-0.5" style={{ color: 'var(--text3)' }}>
              {hasAnalyzeData
                ? `${analyzeResult.matches_found} matches from ${analyzeResult.filename}`
                : totalItems > 0
                  ? `${totalItems} transactions synced`
                  : 'No transactions yet — import a wallet or connect an exchange'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              className="flex items-center gap-2 px-3.5 py-2 border rounded-lg text-[12px] transition-all hover:bg-brand-green-500/5"
              style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text2)' }}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-3.5 py-2 bg-brand-green-500/10 border border-brand-green-500/20 rounded-lg text-[12px] text-brand-green-500 hover:bg-brand-green-500/15 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1 max-w-[400px] group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 transition-all" style={{ color: 'var(--text3)' }} />
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              placeholder="Search by asset, date, or type..."
              className="w-full pl-9 pr-4 py-2 border rounded-lg text-[12px] transition-all focus:outline-none focus:border-brand-green-500/30"
              style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-[12px] transition-all border ${
              showFilters ? 'bg-brand-green-500/10 text-brand-green-500 border-brand-green-500/20' : 'hover:bg-brand-green-500/5'
            }`}
            style={!showFilters ? { color: 'var(--text2)', borderColor: 'var(--border)' } : undefined}
          >
            <Filter className="w-3.5 h-3.5" />
            Filters
          </button>
        </div>
      </div>

      {/* Empty State */}
      {noData && (
        <div className="border rounded-[14px] p-16 text-center shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl border flex items-center justify-center" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
            <Upload className="w-7 h-7" style={{ color: 'var(--text3)' }} />
          </div>
          <h3 className="text-lg font-syne font-semibold mb-2" style={{ color: 'var(--text)' }}>No transactions yet</h3>
          <p className="text-[13px] max-w-md mx-auto" style={{ color: 'var(--text3)' }}>
            Import a wallet or connect an exchange to see your transaction history here.
          </p>
        </div>
      )}

      {/* Table Container */}
      {totalItems > 0 && (
        <div className="border rounded-[14px] overflow-hidden shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                  <th className="px-5 py-3.5 w-4">
                    <input 
                      type="checkbox" 
                      onChange={(e) => {
                        if (e.target.checked) {
                          const ids = new Set(pageMatches.map((_, i) => i)); // Simplified matching for now
                          setSelectedIds(ids);
                        } else {
                          setSelectedIds(new Set());
                        }
                      }}
                      className="w-4 h-4 rounded border-gray-300 text-brand-green-500 focus:ring-brand-green-500 cursor-pointer"
                    />
                  </th>
                  <th className="px-5 py-3.5 text-[10px] font-semibold uppercase tracking-[1.5px]" style={{ color: 'var(--text3)' }}>Type</th>
                  <th className="px-5 py-3.5 text-[10px] font-semibold uppercase tracking-[1.5px]" style={{ color: 'var(--text3)' }}>Asset</th>
                  <th className="hidden sm:table-cell px-5 py-3.5 text-[10px] font-semibold uppercase tracking-[1.5px]" style={{ color: 'var(--text3)' }}>Date</th>
                  <th className="px-5 py-3.5 text-[10px] font-semibold uppercase tracking-[1.5px]" style={{ color: 'var(--text3)' }}>Amount</th>
                  <th className="px-5 py-3.5 text-[10px] font-semibold uppercase tracking-[1.5px]" style={{ color: 'var(--text3)' }}>Gain / Loss</th>
                  <th className="hidden md:table-cell px-5 py-3.5 text-[10px] font-semibold uppercase tracking-[1.5px]" style={{ color: 'var(--text3)' }}>Status</th>
                  <th className="px-5 py-3.5"></th>
                </tr>
              </thead>
              <tbody>
                {/* Analyze matches */}
                {hasAnalyzeData && pageMatches.map((match, i) => (
                  <MatchToRow 
                    key={i} 
                    match={match} 
                    index={page * PER_PAGE + i} 
                    isSelected={selectedIds.has(i)}
                    onToggle={() => toggleSelect(i)}
                    onAudit={() => openAuditTrail(match)}
                  />
                ))}

                {/* API transactions */}
                {!hasAnalyzeData && pageApiTxs.map((tx, i) => (
                  <tr key={tx.id || i} className="hover:bg-brand-green-500/5 transition-colors border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${
                          tx.type === 'receive' ? 'bg-[#6af0c8]/10 text-[#6af0c8]' :
                          tx.type === 'send' ? 'bg-[#f06a6a]/10 text-[#f06a6a]' :
                          tx.type === 'swap' ? 'bg-[#4d7aff]/10 text-[#4d7aff]' :
                          'bg-[#f0a86a]/10 text-[#f0a86a]'
                        }`}>
                          {tx.type === 'receive' ? <ArrowDownRight className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
                        </div>
                        <span className="font-medium text-[13px] capitalize" style={{ color: 'var(--text)' }}>{tx.type}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-col">
                        <span className="text-[13px] font-semibold" style={{ color: 'var(--text)' }}>{String(tx.token ?? '—').toUpperCase()}</span>
                        <span className="text-[11px] mt-0.5" style={{ color: 'var(--text3)' }}>{tx.blockchain}</span>
                      </div>
                    </td>
                    <td className="hidden sm:table-cell px-5 py-4">
                      <span className="text-[11px]" style={{ color: 'var(--text2)' }}>
                        {tx.timestamp ? new Date(tx.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—'}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-[13px] font-medium" style={{ color: 'var(--text)' }}>{Number(tx.amount).toFixed(4)}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-[13px] font-medium" style={{ color: 'var(--text)' }}>{fmt(tx.value_usd)}</span>
                    </td>
                    <td className="hidden md:table-cell px-5 py-4">
                      <span className={`text-[10px] font-semibold uppercase tracking-wider px-2 py-1 rounded-full ${
                        tx.status === 'completed' ? 'bg-[#6af0c8]/10 text-[#6af0c8]' :
                        tx.status === 'pending' ? 'bg-[#f0a86a]/10 text-[#f0a86a]' :
                        'bg-[#f06a6a]/10 text-[#f06a6a]'
                      }`}>
                        {tx.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <button className="p-1.5 transition-colors rounded-lg hover:bg-white/5" style={{ color: 'var(--text3)' }}>
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Container */}
          <div className="px-5 py-4 border-t flex items-center justify-between" style={{ borderColor: 'var(--border)' }}>
            <span className="text-[12px]" style={{ color: 'var(--text3)' }}>
              Showing {page * PER_PAGE + 1}–{Math.min((page + 1) * PER_PAGE, totalItems)} of {totalItems}
            </span>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 border rounded-lg transition-all hover:bg-brand-green-500/5 disabled:opacity-30"
                style={{ borderColor: 'var(--border)', color: 'var(--text3)' }}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i)}
                  className={`w-8 h-8 rounded-lg text-[12px] font-medium transition-all ${
                    page === i ? 'bg-brand-green-500 text-brand-dark' : 'border hover:bg-brand-green-500/5'
                  }`}
                  style={page !== i ? { borderColor: 'var(--border)', color: 'var(--text2)' } : undefined}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 border rounded-lg transition-all hover:bg-brand-green-500/5 disabled:opacity-30"
                style={{ borderColor: 'var(--border)', color: 'var(--text3)' }}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filters Sidebar */}
      {showFilters && (
        <>
          <div className="fixed inset-0 bg-black/40 z-[110]" onClick={() => setShowFilters(false)} />
          <div className="fixed right-0 top-0 bottom-0 w-96 border-l overflow-y-auto z-[120] animate-in slide-in-from-right" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <div className="sticky top-0 border-b p-5 flex items-center justify-between z-10" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <h3 className="text-base font-syne font-semibold" style={{ color: 'var(--text)' }}>Filters</h3>
              <button
                onClick={() => setShowFilters(false)}
                className="p-1.5 rounded-lg transition-colors hover:bg-white/5"
                style={{ color: 'var(--text3)' }}
              >
                ✕
              </button>
            </div>
            <div className="p-5">
              <FiltersPanel filters={filters} onFiltersChange={setFilters} />
            </div>
          </div>
        </>
      )}

      {/* Bulk Operations Bar */}
      <BulkActionBar 
        selectedCount={selectedIds.size} 
        onClear={() => setSelectedIds(new Set())}
        onAction={handleBulkAction}
      />

      <AuditTrailModal 
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        txId={selectedTx?.id}
        asset={selectedTx?.asset}
        amount={selectedTx?.amount}
      />
    </div>
  );
}
