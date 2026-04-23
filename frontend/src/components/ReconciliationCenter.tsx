import { useState, useEffect, useCallback } from 'react';
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
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';

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
  { key: 'PURCHASE', label: 'Purchase', icon: ShoppingCart, color: 'text-[#4d7aff] bg-[#4d7aff]/10 border-[#4d7aff]/20' },
  { key: 'GIFT', label: 'Gift / Airdrop', icon: Gift, color: 'text-[#f0a86a] bg-[#f0a86a]/10 border-[#f0a86a]/20' },
  { key: 'INTERNAL_TRANSFER', label: 'Internal Transfer', icon: Wallet, color: 'text-[#6af0c8] bg-[#6af0c8]/10 border-[#6af0c8]/20' },
  { key: 'STAKING_REWARD', label: 'Staking Reward', icon: Zap, color: 'text-[#a78bfa] bg-[#a78bfa]/10 border-[#a78bfa]/20' },
  { key: 'IGNORE', label: 'Ignore', icon: XCircle, color: 'text-text3 bg-brand-green-500/5 border-border' },
];

function severityIcon(sev: string) {
  if (sev === 'error') return <AlertOctagon className="w-4 h-4 text-[#f06a6a]" />;
  if (sev === 'warning') return <AlertTriangle className="w-4 h-4 text-[#f0a86a]" />;
  return <Info className="w-4 h-4 text-[#4d7aff]" />;
}

function severityBadgeClass(sev: string) {
  if (sev === 'error') return 'bg-[#f06a6a]/10 text-[#f06a6a] border-[#f06a6a]/15';
  if (sev === 'warning') return 'bg-[#f0a86a]/10 text-[#f0a86a] border-[#f0a86a]/15';
  return 'bg-[#4d7aff]/10 text-[#4d7aff] border-[#4d7aff]/15';
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
  const color = pct >= 80 ? 'bg-[#6af0c8]' : pct >= 50 ? 'bg-[#f0a86a]' : 'bg-[#f06a6a]';
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1 rounded-full overflow-hidden" style={{ background: 'var(--bg2)' }}>
        <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] font-medium" style={{ color: 'var(--text3)' }}>{pct}%</span>
    </div>
  );
}


export function ReconciliationCenter() {
  const { analyzeResult } = useAppContext();
  const runId = analyzeResult?.analysis_run_id;

  const [issues, setIssues] = useState<ReconciliationIssue[]>([]);
  const [stats, setStats] = useState<ReconciliationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [autoMatching, setAutoMatching] = useState(false);
  const [resolving, setResolving] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [filter, setFilter] = useState<'all' | 'unresolved' | 'resolved'>('all');

  const loadIssues = useCallback(async () => {
    if (!runId) return;
    setLoading(true);
    try {
      const resolvedParam = filter === 'all' ? undefined : filter === 'resolved';
      const res = await fetch(`/api/v1/reconciliation/issues/${runId}${resolvedParam !== undefined ? `?resolved=${resolvedParam}` : ''}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
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

  const handleScan = async () => {
    if (!runId) return;
    setScanning(true);
    try {
      await fetch(`/api/v1/reconciliation/scan/${runId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      await loadIssues();
    } catch (err) {
      console.error('Scan failed', err);
    } finally {
      setScanning(false);
    }
  };

  const handleAutoMatch = async () => {
    if (!runId) return;
    setAutoMatching(true);
    try {
      await fetch(`/api/v1/reconciliation/auto-match/${runId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
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
      await fetch('/api/v1/reconciliation/resolve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ issue_id: issueId, resolution }),
      });
      await loadIssues();
    } catch (err) {
      console.error('Resolve failed', err);
    } finally {
      setResolving(null);
    }
  };

  if (!runId) {
    return (
      <div className="text-center py-24">
        <div className="w-20 h-20 mx-auto mb-5 rounded-2xl border flex items-center justify-center" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
          <ArrowRightLeft className="w-8 h-8" style={{ color: 'var(--text3)' }} />
        </div>
        <h2 className="text-2xl font-syne font-bold mb-2" style={{ color: 'var(--text)' }}>Transaction Reconciliation</h2>
        <p className="text-[14px] max-w-md mx-auto" style={{ color: 'var(--text3)' }}>
          Upload and analyze your transactions first. Then come here to resolve any issues with missing data.
        </p>
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
                className="h-full bg-gradient-to-r from-brand-green-500 to-[#6af0c8] rounded-full"
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
