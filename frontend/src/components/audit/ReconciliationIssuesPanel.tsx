import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  AlertOctagon,
  Info,
  Zap,
  Loader2,
  ShoppingCart,
  Gift,
  Wallet,
  XCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';
import type { ReconciliationIssueRow } from '../../hooks/useAuditData';
import { issueTypeLabel } from './auditUtils';

const RESOLUTION_OPTIONS = [
  { key: 'PURCHASE', label: 'Purchase', icon: ShoppingCart, color: 'text-[#0077ff] bg-[#0077ff]/10 border-[#0077ff]/20' },
  { key: 'GIFT', label: 'Gift / Airdrop', icon: Gift, color: 'text-[var(--warning)] bg-[rgba(245,158,11,0.1)] border-[rgba(245,158,11,0.2)]' },
  { key: 'INTERNAL_TRANSFER', label: 'Internal Transfer', icon: Wallet, color: 'text-[var(--accent)] bg-[var(--accent-dim)] border-[var(--accent)]/20' },
  { key: 'STAKING_REWARD', label: 'Staking Reward', icon: Zap, color: 'text-[#a78bfa] bg-[#a78bfa]/10 border-[#a78bfa]/20' },
  { key: 'IGNORE', label: 'Ignore', icon: XCircle, color: 'text-[var(--text3)] bg-[var(--card2)] border-[var(--border)]' },
];

function severityIcon(sev: string) {
  if (sev === 'error') return <AlertOctagon className="w-4 h-4 text-[var(--danger)]" />;
  if (sev === 'warning') return <AlertTriangle className="w-4 h-4 text-[var(--warning)]" />;
  return <Info className="w-4 h-4 text-[var(--info)]" />;
}

function severityBadgeClass(sev: string) {
  if (sev === 'error') return 'bg-[rgba(255,77,106,0.1)] text-[var(--danger)] border-[rgba(255,77,106,0.15)]';
  if (sev === 'warning') return 'bg-[rgba(245,158,11,0.1)] text-[var(--warning)] border-[rgba(245,158,11,0.15)]';
  return 'bg-[rgba(0,119,255,0.1)] text-[var(--info)] border-[rgba(0,119,255,0.15)]';
}

function issueSmartHint(type: string, asset: string | null): string {
  const hints: Record<string, string> = {
    MISSING_COST_BASIS: `We couldn't find the purchase price for ${asset || 'this asset'}.`,
    UNKNOWN_SOURCE: `This ${asset || 'deposit'} has no clear origin.`,
    ORPHAN_RECEIVE: `Funds arrived without a known source.`,
    POSSIBLE_INTERNAL_TRANSFER: `This may be a transfer between your wallets.`,
    POSSIBLE_AIRDROP: `This may be an airdrop or reward.`,
    DUPLICATE_SUSPECT: `This may be a duplicate import.`,
  };
  return hints[type] || 'Additional classification may be required.';
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? 'bg-[var(--accent)]' : pct >= 50 ? 'bg-[var(--warning)]' : 'bg-[var(--danger)]';
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1 rounded-full overflow-hidden bg-[var(--card3)]">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] font-medium text-[var(--text3)]">{pct}%</span>
    </div>
  );
}

type Props = {
  issues: ReconciliationIssueRow[];
  onResolve: (issueId: number, resolution: string) => Promise<void>;
};

export function ReconciliationIssuesPanel({ issues, onResolve }: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [resolving, setResolving] = useState<number | null>(null);

  const unresolved = issues.filter((i) => !i.resolved);
  if (unresolved.length === 0) return null;

  const handleResolve = async (issueId: number, resolution: string) => {
    setResolving(issueId);
    try {
      await onResolve(issueId, resolution);
      setExpandedId(null);
    } finally {
      setResolving(null);
    }
  };

  return (
    <div className="audit-panel" style={{ marginTop: 18 }}>
      <div className="audit-panel-hd">
        <div className="audit-ph-icon">⚙</div>
        <div>
          <div className="audit-ph-title">Resolve issues</div>
          <div className="audit-ph-sub">{unresolved.length} open item{unresolved.length !== 1 ? 's' : ''}</div>
        </div>
      </div>
      <div style={{ padding: 16 }}>
        <AnimatePresence mode="popLayout">
          {unresolved.map((issue) => (
            <motion.div
              key={issue.id}
              layout
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="border rounded-xl overflow-hidden mb-3"
              style={{ background: 'var(--card)', borderColor: 'var(--border)' }}
            >
              <div className="p-4 cursor-pointer" onClick={() => setExpandedId(expandedId === issue.id ? null : issue.id)}>
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">{severityIcon(issue.severity)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className={`text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded border ${severityBadgeClass(issue.severity)}`}>
                        {issue.severity}
                      </span>
                      <span className="text-[9px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider bg-[var(--card2)] border-[var(--border)] text-[var(--text3)]">
                        {issueTypeLabel(issue.issue_type)}
                      </span>
                    </div>
                    <p className="text-[13px] font-bold text-[var(--text)]">{issue.description}</p>
                    <p className="text-[11px] text-[var(--text2)] mt-1">{issueSmartHint(issue.issue_type, issue.asset)}</p>
                  </div>
                  {expandedId === issue.id ? <ChevronUp size={16} className="text-[var(--text3)]" /> : <ChevronDown size={16} className="text-[var(--text3)]" />}
                </div>
              </div>
              {expandedId === issue.id && (
                <div className="px-4 pb-4 border-t border-[var(--border)] pt-4 space-y-4">
                  {(issue.suggested_matches as { asset: string; amount: number; reason: string; confidence: number }[]).length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-[#a78bfa]">
                        <Sparkles size={12} /> Suggested matches
                      </div>
                      {(issue.suggested_matches as { asset: string; amount: number; reason: string; confidence: number }[]).map((match, mi) => (
                        <div key={mi} className="flex items-center justify-between p-3 rounded-lg border border-[var(--border)] bg-[var(--card2)]">
                          <div>
                            <p className="text-[12px] font-bold text-[var(--text)]">
                              {match.asset} · {match.amount.toFixed(6)}
                            </p>
                            <p className="text-[10px] text-[var(--text3)]">{match.reason}</p>
                          </div>
                          <ConfidenceBar confidence={match.confidence} />
                        </div>
                      ))}
                    </div>
                  )}
                  <div>
                    <h4 className="text-[10px] font-bold uppercase tracking-wider text-[var(--text3)] mb-2">Classify</h4>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                      {RESOLUTION_OPTIONS.map((opt) => (
                        <button
                          key={opt.key}
                          type="button"
                          onClick={() => handleResolve(issue.id, opt.key)}
                          disabled={resolving === issue.id}
                          className={`flex flex-col items-center justify-center gap-1.5 p-3 rounded-xl border text-[10px] font-bold ${opt.color}`}
                        >
                          {resolving === issue.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <opt.icon className="w-4 h-4" />}
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
      </div>
    </div>
  );
}
