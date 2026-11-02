import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  AlertOctagon,
  Info,
  CheckCircle2,
  Search,
  Zap,
  Loader2,
  ShoppingCart,
  Gift,
  Wallet,
  ArrowRightLeft,
  XCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  RefreshCw,
  Link as LinkIcon,
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import apiV1, { apiFetch } from '../api/v1';
import { SkeletonCard, SkeletonTable, SkeletonText } from './ui/Skeleton';

interface SuggestedMatch {
  source_run_id: number;
  tx_index: number;
  asset: string;
  amount: number;
  timestamp: string;
  wallet: string;
  confidence: number;
  reason: string;
}

interface ReconciliationIssue {
  id: number;
  run_id: number;
  tx_index: number;
  tx_hash: string | null;
  asset: string | null;
  amount: number | null;
  timestamp: string | null;
  issue_type: string;
  severity: string;
  description: string | null;
  suggested_matches: SuggestedMatch[];
  resolved: boolean;
  resolved_as: string | null;
}

interface ReconciliationStats {
  total: number;
  resolved: number;
  unresolved: number;
  progress_pct: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
}

const RESOLUTION_OPTIONS = [
  { key: 'PURCHASE', label: 'Purchase', icon: ShoppingCart, color: 'text-[#0077ff] bg-[#0077ff]/10 border-[#0077ff]/20' },
  { key: 'GIFT', label: 'Gift / Airdrop', icon: Gift, color: 'text-[#f59e0b] bg-[#f59e0b]/10 border-[#f59e0b]/20' },
  { key: 'INTERNAL_TRANSFER', label: 'Internal Transfer', icon: Wallet, color: 'text-[var(--accent)] bg-[var(--accent)]/10 border-[var(--accent)]/20' },
  { key: 'STAKING_REWARD', label: 'Staking Reward', icon: Zap, color: 'text-[#a78bfa] bg-[#a78bfa]/10 border-[#a78bfa]/20' },
  { key: 'IGNORE', label: 'Ignore', icon: XCircle, color: 'text-[var(--text3)] bg-[var(--accent-dim)] border-[var(--border)]' },
];

function severityIcon(sev: string) {
  if (sev === 'error') return <AlertOctagon className="w-4 h-4" style={{ color: 'var(--danger)' }} />;
  if (sev === 'warning') return <AlertTriangle className="w-4 h-4" style={{ color: 'var(--warning)' }} />;
  return <Info className="w-4 h-4" style={{ color: 'var(--info)' }} />;
}

function severityBadgeClass(sev: string) {
  if (sev === 'error') return 'bg-[rgba(255,77,106,0.1)] text-[#ff4d6a] border-[#ff4d6a]/15';
  if (sev === 'warning') return 'bg-[rgba(245,158,11,0.1)] text-[#f59e0b] border-[#f59e0b]/15';
  return 'bg-[rgba(0,119,255,0.1)] text-[#0077ff] border-[#0077ff]/15';
}

function issueTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    MISSING_COST_BASIS: 'Missing Cost Basis',
    UNKNOWN_SOURCE: 'Unknown Source',
    ORPHAN_RECEIVE: 'Orphan Receive',
    POSSIBLE_INTERNAL_TRANSFER: 'Possible Internal Transfer',
    POSSIBLE_AIRDROP: 'Possible Airdrop',
    DUPLICATE_SUSPECT: 'Duplicate Suspect',
  };
  return labels[type] || type;
}

function issueSmartHint(type: string, asset: string | null): string {
  const hints: Record<string, string> = {
    MISSING_COST_BASIS: `We couldn't find the purchase price for ${asset || 'this asset'}. If you bought it on an exchange we haven't linked yet, please add that connection.`,
    UNKNOWN_SOURCE: `This ${asset || 'deposit'} has no clear origin. Was it a gift, mining reward, or a transfer from your own wallet?`,
    ORPHAN_RECEIVE: `We see ${asset || 'funds'} arriving, but don't know where from. Marking this as a 'Gift' is the safest conservative option if you're unsure.`,
    POSSIBLE_INTERNAL_TRANSFER: `This looks like a transfer from one of your other wallets. Labeling it as 'Internal Transfer' will ensure it's not taxed as a sale.`,
    POSSIBLE_AIRDROP: `Is this a surprise drop? Airdrops are usually taxed as ordinary income at the time of receipt.`,
    DUPLICATE_SUSPECT: `This looks identical to another transaction. We might have imported it twice (e.g. via both API and CSV).`,
  };
  return hints[type] || "We need a bit more info to categorize this correctly.";
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? 'bg-[var(--accent)]' : pct >= 50 ? 'bg-[#f59e0b]' : 'bg-[#ff4d6a]';
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1 rounded-full overflow-hidden" style={{ background: 'var(--bg2)' }}>
        <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] font-medium" style={{ color: 'var(--text3)' }}>{pct}%</span>
    </div>
  );
}


export function ReconciliationCenter({ setActiveTab, onScanReady }: {
  setActiveTab?: (tab: string, subTab?: any) => void;
  onScanReady?: (fn: () => void) => void;
}) {
  const { analyzeResult, dataVersion } = useAppContext();
  const [fallbackRunId, setFallbackRunId] = useState<number | null>(null);
  const [runLookupLoading, setRunLookupLoading] = useState(true);
  const runId = analyzeResult?.analysis_run_id ?? fallbackRunId;

  const [issues, setIssues] = useState<ReconciliationIssue[]>([]);
  const [stats, setStats] = useState<ReconciliationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [autoMatching, setAutoMatching] = useState(false);
  const [resolving, setResolving] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [filter, setFilter] = useState<'all' | 'unresolved' | 'resolved'>('all');

  useEffect(() => {
    let active = true;

    async function loadLatestRunId() {
      if (analyzeResult?.analysis_run_id) {
        setFallbackRunId(null);
        setRunLookupLoading(false);
        return;
      }

      setRunLookupLoading(true);
      try {
        const runData = await apiV1.analysis.listRuns();
        const latestRunId = Number(runData?.runs?.[0]?.run_id ?? 0) || null;
        if (active) setFallbackRunId(latestRunId);
      } catch {
        if (active) setFallbackRunId(null);
      } finally {
        if (active) setRunLookupLoading(false);
      }
    }

    loadLatestRunId();
    return () => { active = false; };
  }, [analyzeResult?.analysis_run_id, dataVersion]);

  const loadIssues = useCallback(async () => {
    if (!runId) return;
    setLoading(true);
    try {
      const resolvedParam = filter === 'all' ? undefined : filter === 'resolved';
      const res = await apiFetch(
        `/reconciliation/issues/${runId}${resolvedParam !== undefined ? `?resolved=${resolvedParam}` : ''}`,
      );
      const data = await res.json();
      setIssues(data.issues || []);
      setStats(data.stats || null);
    } catch (err) {
      console.error('Failed to load issues', err);
    } finally {
      setLoading(false);
    }
  }, [runId, filter]);

  useEffect(() => { loadIssues(); }, [loadIssues]);

  const handleScan = useCallback(async () => {
    if (!runId) return;
    setScanning(true);
    try {
      await apiFetch(`/reconciliation/scan/${runId}`, { method: 'POST' });
      await loadIssues();
    } catch (err) {
      console.error('Scan failed', err);
    } finally {
      setScanning(false);
    }
  }, [runId, loadIssues]);

  // Register handleScan with parent (for "Re-scan All" button)
  useEffect(() => { onScanReady?.(handleScan); }, [handleScan, onScanReady]);

  // Auto-scan when new data is imported (dataVersion bumped)
  // Use a ref to skip the very first mount (initial scan handled by loadIssues)
  const isFirstRun = React.useRef(true);
  useEffect(() => {
    if (isFirstRun.current) { isFirstRun.current = false; return; }
    if (!runId) return;
    // Small delay so the backend has time to process the import
    const timer = setTimeout(() => handleScan(), 800);
    return () => clearTimeout(timer);
  }, [dataVersion]);

  const handleAutoMatch = async () => {
    if (!runId) return;
    setAutoMatching(true);
    try {
      await apiFetch(`/reconciliation/auto-match/${runId}`, { method: 'POST' });
      await loadIssues();
    } catch (err) {
      console.error('Auto-match failed', err);
    } finally {
      setAutoMatching(false);
    }
  };

  const handleResolve = async (issueId: number, resolution: string) => {
    setResolving(issueId);
    try {
      await apiFetch('/reconciliation/resolve', {
        method: 'POST',
        body: JSON.stringify({ issue_id: issueId, resolution }),
      });
      await loadIssues();
    } catch (err) {
      console.error('Resolve failed', err);
    } finally {
      setResolving(null);
    }
  };

  if (runLookupLoading || (runId && loading && issues.length === 0 && !stats)) {
    return (
      <div className="space-y-6 animate-in fade-in duration-500">
        <SkeletonText lines={2} className="w-[320px]" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-[16px]">
          {Array.from({ length: 3 }).map((_, idx) => (
            <SkeletonCard key={idx} />
          ))}
        </div>
        <SkeletonTable rows={4} />
      </div>
    );
  }

  if (!runId) {
    return (
      <div className="space-y-[32px] animate-in fade-in duration-700">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-[16px]">
           <div className="p-[20px] rounded-[16px] flex items-center justify-between" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-[12px]">
                 <div className="w-[32px] h-[32px] rounded-full bg-[rgba(16, 185, 129,0.1)] flex items-center justify-center">
                    <CheckCircle2 size={16} className="text-[var(--accent)]" />
                 </div>
                 <div>
                    <p className="text-[14px] font-black" style={{ color: 'var(--text)' }}> — </p>
                    <p className="text-[10px] uppercase font-bold" style={{ color: 'var(--text3)' }}>Matched</p>
                 </div>
              </div>
           </div>
           <div className="p-[20px] rounded-[16px] flex items-center justify-between" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-[12px]">
                  <div className="w-[32px] h-[32px] rounded-full bg-[rgba(245,158,11,0.1)] flex items-center justify-center">
                     <AlertTriangle size={16} style={{ color: 'var(--warning)' }} />
                 </div>
                 <div>
                    <p className="text-[14px] font-black" style={{ color: 'var(--text)' }}> — </p>
                    <p className="text-[10px] uppercase font-bold" style={{ color: 'var(--text3)' }}>Unmatched</p>
                 </div>
              </div>
           </div>
           <div className="p-[20px] rounded-[16px] flex items-center justify-between" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-[12px]">
                 <div className="w-[32px] h-[32px] rounded-full flex items-center justify-center" style={{ background: 'var(--card2)' }}>
                    <ArrowRightLeft size={16} style={{ color: 'var(--text3)' }} />
                 </div>
                 <div>
                    <p className="text-[14px] font-black" style={{ color: 'var(--text)' }}> — </p>
                    <p className="text-[10px] uppercase font-bold" style={{ color: 'var(--text3)' }}>Missing</p>
                 </div>
              </div>
           </div>
        </div>

        <div className="flex flex-col items-center justify-center py-[60px] text-center max-w-[600px] mx-auto">
           <div className="w-[80px] h-[80px] rounded-[24px] flex items-center justify-center mb-[24px] shadow-2xl" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
              <ArrowRightLeft size={32} className="opacity-40" style={{ color: 'var(--text2)' }} />
           </div>
           
           <h2 className="font-syne font-black text-[28px] mb-[12px]" style={{ color: 'var(--text)' }}>No data to reconcile</h2>
           <p className="text-[14px] leading-relaxed mb-[32px]" style={{ color: 'var(--text2)' }}>
              Connect your wallets and exchanges so Declairo can automatically match on-chain transactions with exchange records and flag discrepancies.
           </p>
           
           <div className="flex gap-[12px]">
              <button 
                onClick={() => setActiveTab?.('integrations', 'WALLETS')}
                className="flex items-center gap-[12px] p-[16px] rounded-[16px] transition-all group w-[220px]"
                style={{ background: 'var(--card)', border: '1px solid var(--border)' }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(16, 185, 129,0.4)')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
              >
                 <div className="w-[36px] h-[36px] rounded-[10px] bg-[rgba(16, 185, 129,0.1)] flex items-center justify-center">
                    <LinkIcon size={18} className="text-[var(--accent)]" />
                 </div>
                 <div className="text-left">
                    <p className="text-[13px] font-bold" style={{ color: 'var(--text)' }}>Connect Wallet</p>
                    <p className="text-[10px]" style={{ color: 'var(--text3)' }}>ETH, BTC, SOL, and more</p>
                 </div>
                 <ChevronDown size={14} className="ml-auto group-hover:text-[var(--accent)] -rotate-90" style={{ color: 'var(--text3)' }} />
              </button>
              
              <button 
                onClick={() => setActiveTab?.('integrations', 'EXCHANGES')}
                className="flex items-center gap-[12px] p-[16px] rounded-[16px] transition-all group w-[220px]"
                style={{ background: 'var(--card)', border: '1px solid var(--border)' }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(16, 185, 129,0.4)')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
              >
                 <div className="w-[36px] h-[36px] rounded-[10px] bg-[rgba(16, 185, 129,0.1)] flex items-center justify-center">
                    <Zap size={18} className="text-[var(--accent)]" />
                 </div>
                 <div className="text-left">
                    <p className="text-[13px] font-bold" style={{ color: 'var(--text)' }}>Import Transactions</p>
                    <p className="text-[10px]" style={{ color: 'var(--text3)' }}>CSV or API sync</p>
                 </div>
                 <ChevronDown size={14} className="ml-auto group-hover:text-[var(--accent)] -rotate-90" style={{ color: 'var(--text3)' }} />
              </button>
           </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      {/* Header Container */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>Reconciliation</h1>
          <p className="text-[13px] mt-1" style={{ color: 'var(--text3)' }}>Resolve missing cost basis and unknown transaction sources</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleScan}
            disabled={scanning}
            className="flex items-center gap-2 px-4 py-2 border rounded-xl text-[12px] font-bold transition-all hover:bg-brand-green-500/5 disabled:opacity-50"
            style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text2)' }}
          >
            {scanning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
            Scan for Issues
          </button>
          <button
            onClick={handleAutoMatch}
            disabled={autoMatching}
            className="flex items-center gap-2 px-4 py-2 bg-brand-green-500 text-brand-dark rounded-xl text-[12px] font-black shadow-lg shadow-brand-green-500/20 hover:bg-brand-green-400 disabled:opacity-50 transition-all"
          >
            {autoMatching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            Auto-Match
          </button>
        </div>
      </div>

      {/* Stats Dashboard */}
      {stats && stats.total > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="md:col-span-3 border rounded-[2rem] p-8 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <CheckCircle2 className={`w-5 h-5 ${stats.progress_pct === 100 ? 'text-brand-green-500' : 'text-brand-green-500/40'}`} />
                <h3 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Tax Readiness Status</h3>
              </div>
              <span className={`text-2xl font-black ${stats.progress_pct === 100 ? 'text-brand-green-500' : 'text-brand-green-500/80'}`}>{stats.progress_pct}%</span>
            </div>
            <div className="w-full h-2 rounded-full overflow-hidden mb-8" style={{ background: 'var(--bg2)' }}>
              <motion.div
                className="h-full bg-gradient-to-r from-brand-green-500 to-[var(--accent)] rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${stats.progress_pct}%` }}
                transition={{ duration: 1, ease: 'easeOut' }}
              />
            </div>
            <div className="grid grid-cols-3 gap-8">
              <div className="text-center md:text-left">
                <p className="text-2xl font-black" style={{ color: 'var(--text)' }}>{stats.total}</p>
                <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color: 'var(--text3)' }}>Total Issues</p>
              </div>
              <div className="text-center md:text-left border-l pl-8" style={{ borderColor: 'var(--border)' }}>
                <p className="text-2xl font-black text-brand-green-500">{stats.resolved}</p>
                <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color: 'var(--text3)' }}>Resolved</p>
              </div>
              <div className="text-center md:text-left border-l pl-8" style={{ borderColor: 'var(--border)' }}>
                <p className="text-2xl font-black text-danger">{stats.unresolved}</p>
                <p className="text-[10px] font-bold uppercase tracking-wider" style={{ color: 'var(--text3)' }}>Pending Action</p>
              </div>
            </div>
          </div>
          
          <div className="border rounded-[2rem] p-8 flex flex-col justify-center text-center shadow-lg" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
            <div className="w-12 h-12 bg-brand-green-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Sparkles className="text-brand-green-500" size={24} />
            </div>
            <p className="text-sm font-bold mb-2" style={{ color: 'var(--text)' }}>AI Assist</p>
            <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text3)' }}>
              Our engine found possible matches for your orphan transactions.
            </p>
          </div>
        </div>
      )}

      {/* Filter Options */}
      <div className="flex gap-2 p-1 border rounded-2xl w-fit" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
        {(['all', 'unresolved', 'resolved'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-6 py-2 rounded-xl text-xs font-bold capitalize transition-all ${
              filter === f
                ? 'bg-brand-green-500 text-brand-dark shadow-md'
                : 'hover:bg-brand-green-500/5'
            }`}
            style={filter !== f ? { color: 'var(--text2)' } : undefined}
          >
            {f}
          </button>
        ))}
      </div>

      {/* List Container */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-brand-green-500 animate-spin" />
          </div>
        ) : issues.length === 0 ? (
          <div className="text-center py-24 border rounded-[2rem]" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <CheckCircle2 className="w-16 h-16 text-brand-green-500 mx-auto mb-6" />
            <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--text)' }}>All Clear!</h2>
            <p className="max-w-md mx-auto mb-8" style={{ color: 'var(--text3)' }}>
              No reconciliation issues found. Your data is consistent and ready for export.
            </p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {issues.map((issue, i) => (
              <motion.div
                key={issue.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.3 }}
                className={`border rounded-[1.5rem] overflow-hidden transition-all shadow-sm ${
                  issue.resolved ? 'opacity-50' : 'hover:border-brand-green-500/30'
                }`}
                style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
              >
                <div
                  className="p-6 cursor-pointer"
                  onClick={() => setExpandedId(expandedId === issue.id ? null : issue.id)}
                >
                  <div className="flex items-start gap-4">
                    <div className="mt-1">{severityIcon(issue.severity)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <span className={`text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded border ${severityBadgeClass(issue.severity)}`}>
                          {issue.severity}
                        </span>
                        <span className="text-[9px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider" style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text3)' }}>
                          {issueTypeLabel(issue.issue_type)}
                        </span>
                        {issue.resolved && (
                          <span className="text-[9px] font-black text-brand-green-500 bg-brand-green-500/10 px-2 py-0.5 rounded border border-brand-green-500/20 flex items-center gap-1 uppercase tracking-widest">
                            <CheckCircle2 className="w-3 h-3" />
                            {issue.resolved_as}
                          </span>
                        )}
                      </div>
                      <p className="text-[14px] font-bold mb-1" style={{ color: 'var(--text)' }}>{issue.description}</p>
                      <p className="text-[12px] mb-3 opacity-70" style={{ color: 'var(--text2)' }}>
                        <span className="font-semibold text-brand-green-500">Hint:</span> {issueSmartHint(issue.issue_type, issue.asset)}
                      </p>
                      <div className="flex flex-wrap gap-4 text-[11px]" style={{ color: 'var(--text3)' }}>
                        {issue.asset && <span>Asset: <strong style={{ color: 'var(--text)' }}>{issue.asset}</strong></span>}
                        {issue.amount != null && <span>Amount: <strong style={{ color: 'var(--text)' }}>{issue.amount.toFixed(6)}</strong></span>}
                        {issue.tx_hash && <span className="font-mono">Hash: {issue.tx_hash.slice(0, 10)}...</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {issue.suggested_matches.length > 0 && !issue.resolved && (
                        <span className="text-[10px] font-bold text-[#a78bfa] bg-[#a78bfa]/10 px-2.5 py-1 rounded-full border border-[#a78bfa]/20 shadow-sm animate-pulse">
                          {issue.suggested_matches.length} Match Suggestion{issue.suggested_matches.length > 1 ? 's' : ''}
                        </span>
                      )}
                      <div className="w-8 h-8 rounded-full flex items-center justify-center transition-colors" style={{ background: 'var(--bg2)', color: 'var(--text2)' }}>
                        {expandedId === issue.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Expanded Section */}
                {expandedId === issue.id && !issue.resolved && (
                  <div className="px-6 pb-6 border-t pt-6 space-y-6 animate-in slide-in-from-top-2" style={{ borderColor: 'var(--border)' }}>
                    {/* Suggested Matches */}
                    {issue.suggested_matches.length > 0 && (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2 mb-3">
                          <Sparkles size={14} className="text-[#a78bfa]" />
                          <h4 className="text-[10px] font-bold text-[#a78bfa] uppercase tracking-[2px]">AI Match Recommendations</h4>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {issue.suggested_matches.map((match, mi) => (
                            <div key={mi} className="flex items-center justify-between p-4 rounded-2xl border transition-all hover:scale-[1.01]" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                              <div className="flex-1 min-w-0">
                                <p className="text-[13px] font-bold" style={{ color: 'var(--text)' }}>
                                  {match.asset} · {match.amount.toFixed(6)}
                                </p>
                                <p className="text-[10px] mt-1 italic" style={{ color: 'var(--text3)' }}>{match.reason}</p>
                              </div>
                              <ConfidenceBar confidence={match.confidence} />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Resolution Buttons */}
                    <div className="space-y-3">
                      <h4 className="text-[10px] font-bold uppercase tracking-[2px]" style={{ color: 'var(--text3)' }}>Classify this acquisition</h4>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                        {RESOLUTION_OPTIONS.map((opt) => (
                          <button
                            key={opt.key}
                            onClick={() => handleResolve(issue.id, opt.key)}
                            disabled={resolving === issue.id}
                            className={`flex flex-col items-center justify-center gap-2 p-4 rounded-2xl border text-[11px] font-bold transition-all hover:scale-[1.02] ${opt.color}`}
                          >
                            {resolving === issue.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <opt.icon className="w-5 h-5" />
                            )}
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
