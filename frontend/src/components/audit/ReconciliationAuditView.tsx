import { Check, Loader2, Plus, RefreshCw, Sparkles } from 'lucide-react';
import type { useAuditData } from '../../hooks/useAuditData';
import { AuditEmptyState } from './AuditEmptyState';
import { ReconciliationIssuesPanel } from './ReconciliationIssuesPanel';
import { COST_BASIS_TYPES, TRANSFER_TYPES, formatIssueSummary, issueActionLabel } from './auditUtils';
import type { ReconciliationIssueRow } from '../../hooks/useAuditData';

type AuditData = ReturnType<typeof useAuditData>;

type Props = {
  audit: AuditData;
  setActiveTab?: (tab: string, subTab?: string) => void;
  onGoToIssues: () => void;
};

function sourceEmoji(kind: 'wallet' | 'exchange', name: string): string {
  if (kind === 'exchange') return '🟡';
  const n = name.toLowerCase();
  if (n.includes('btc') || n.includes('bitcoin')) return '₿';
  if (n.includes('eth')) return 'Ξ';
  if (n.includes('sol')) return '◎';
  return '🔗';
}

export function ReconciliationAuditView({ audit, setActiveTab, onGoToIssues }: Props) {
  const {
    loading,
    pageState,
    sources,
    totalTransactions,
    runId,
    unresolvedIssues,
    stats,
    scanning,
    autoMatching,
    matchedCount,
    reviewCount,
    errorCount,
    progressPct,
    lastSyncLabel,
    handleScan,
    handleAutoMatch,
  } = audit;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  if (pageState === 'empty') {
    return (
      <AuditEmptyState
        onConnectWallet={() => setActiveTab?.('integrations', 'WALLETS')}
        onAddExchange={() => setActiveTab?.('integrations', 'EXCHANGES')}
      />
    );
  }

  if (!runId) {
    return (
      <div className="audit-panel audit-tab-panel-shell">
        <div className="audit-rc-empty">
          <div className="audit-rce-icon">
            <Sparkles size={24} />
          </div>
          <h3 className="audit-rce-title">Ready to reconcile</h3>
          <p className="audit-rce-desc">
            {totalTransactions > 0
              ? `You have ${totalTransactions.toLocaleString()} transaction${totalTransactions !== 1 ? 's' : ''} imported. Run a tax calculation in Tax Center to scan for missing cost basis and unmatched transfers.`
              : `You have ${sources.length} connected source${sources.length !== 1 ? 's' : ''}. Run a tax calculation in Tax Center to scan transactions for missing cost basis and unmatched transfers.`}
          </p>
          <button type="button" className="audit-btn audit-btn-primary" style={{ marginTop: 8 }} onClick={() => setActiveTab?.('tax')}>
            Go to Tax Center →
          </button>
        </div>
      </div>
    );
  }

  if (pageState === 'ok') {
    const total = stats?.total ?? totalTransactions;
    const matched = matchedCount;
    return (
      <div className="animate-fade-in">
        <div className="audit-ok-banner">
          <div className="audit-ok-check">
            <Check size={28} strokeWidth={3} />
          </div>
          <div>
            <div className="audit-ok-title">All transactions reconciled</div>
            <div className="audit-ok-desc">
              Every transaction across {sources.length} source{sources.length !== 1 ? 's' : ''} is matched and classified.
              You&apos;re ready to generate your tax report.
            </div>
          </div>
          <div className="audit-ok-meta">
            <strong>{progressPct}%</strong>
            reconciled
          </div>
        </div>

        <div className="audit-stats-4">
          <div className="audit-stat-card">
            <div className="audit-stat-num">{matched.toLocaleString()}</div>
            <div className="audit-stat-lbl">Matched</div>
            <div className="audit-stat-sub">All transactions classified</div>
          </div>
          <div className="audit-stat-card">
            <div className="audit-stat-num">0</div>
            <div className="audit-stat-lbl">Errors</div>
            <div className="audit-stat-sub">No issues found</div>
          </div>
          <div className="audit-stat-card">
            <div className="audit-stat-num muted">{sources.length}</div>
            <div className="audit-stat-lbl">Sources</div>
            <div className="audit-stat-sub">
              {sources.filter((s) => s.kind === 'wallet').length} wallets ·{' '}
              {sources.filter((s) => s.kind === 'exchange').length} exchanges
            </div>
          </div>
          <div className="audit-stat-card">
            <div className="audit-stat-num muted">{lastSyncLabel}</div>
            <div className="audit-stat-lbl">Last Sync</div>
            <div className="audit-stat-sub">{total.toLocaleString()} transactions</div>
          </div>
        </div>

        <div className="audit-ok-main">
          <div className="audit-panel">
            <div className="audit-panel-hd">
              <div className="audit-ph-icon">🔗</div>
              <div style={{ flex: 1 }}>
                <div className="audit-ph-title">Connected Sources</div>
                <div className="audit-ph-sub">All sources synced and matched</div>
              </div>
              <button type="button" className="audit-btn audit-btn-ghost audit-btn-sm" onClick={() => setActiveTab?.('integrations')}>
                <Plus size={12} /> Add
              </button>
            </div>
            {sources.map((s) => (
              <div key={s.id} className="audit-source-row">
                <div className="audit-source-icon">{sourceEmoji(s.kind, s.name)}</div>
                <div>
                  <div className="audit-source-name">{s.name}</div>
                  <div className="audit-source-addr">{s.address}</div>
                </div>
                <div>
                  <div className="audit-source-status">
                    <span className="audit-ws-dot" />
                    Synced
                  </div>
                  <div className="audit-source-count">{s.transactionCount.toLocaleString()} transactions</div>
                </div>
              </div>
            ))}
          </div>

          <div className="audit-panel">
            <div className="audit-panel-hd">
              <div className="audit-ph-icon">📋</div>
              <div>
                <div className="audit-ph-title">Sync History</div>
                <div className="audit-ph-sub">Recent reconciliation events</div>
              </div>
            </div>
            <div style={{ padding: '16px 20px' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>Reconciliation complete</div>
              <div style={{ fontSize: 11, color: 'var(--text3)' }}>
                {matched.toLocaleString()} items resolved · {lastSyncLabel}
              </div>
              <button
                type="button"
                className="audit-btn audit-btn-primary audit-btn-sm"
                style={{ marginTop: 16, width: '100%' }}
                onClick={() => setActiveTab?.('tax')}
              >
                Generate Tax Report →
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const costBasisIssues = unresolvedIssues.filter(
    (i) => COST_BASIS_TYPES.has(i.issue_type) || (i.severity === 'error' && !TRANSFER_TYPES.has(i.issue_type)),
  );
  const transferIssues = unresolvedIssues.filter((i) => TRANSFER_TYPES.has(i.issue_type));

  const totalTx = totalTransactions || stats?.total || unresolvedIssues.length + matchedCount;
  const matchedNum = matchedCount;
  const reviewNum = reviewCount || transferIssues.length;
  const errNum = errorCount;
  const matchedPct = totalTx > 0 ? (matchedNum / totalTx) * 100 : progressPct;
  const reviewPct = totalTx > 0 ? (reviewNum / totalTx) * 100 : 0;
  const errPct = totalTx > 0 ? (errNum / totalTx) * 100 : 0;

  return (
    <div className="animate-fade-in">
      <div className="audit-err-alert">
        <span style={{ fontSize: 24 }}>⚠️</span>
        <div style={{ flex: 1 }}>
          <div className="audit-err-title">{errNum} issue{errNum !== 1 ? 's' : ''} require your attention</div>
          <div className="audit-err-desc">
            Missing cost basis and unmatched transfers prevent accurate tax calculation. Fix these before generating your
            report.
          </div>
        </div>
        <button
          type="button"
          className="audit-btn audit-btn-danger audit-btn-sm"
          disabled={autoMatching}
          onClick={handleAutoMatch}
        >
          {autoMatching ? <Loader2 size={14} className="animate-spin" /> : 'Auto-Fix All'}
        </button>
      </div>

      <div className="audit-stats-4">
        <div className="audit-stat-card">
          <div className="audit-stat-num">{matchedNum.toLocaleString()}</div>
          <div className="audit-stat-lbl">Matched</div>
          <div className="audit-stat-sub">{matchedPct.toFixed(1)}% of total</div>
        </div>
        <div className="audit-stat-card warn">
          <div className="audit-stat-num warn">{reviewNum}</div>
          <div className="audit-stat-lbl">Needs Review</div>
          <div className="audit-stat-sub">Unmatched transfers</div>
        </div>
        <div className="audit-stat-card danger">
          <div className="audit-stat-num danger">{errNum}</div>
          <div className="audit-stat-lbl">Errors</div>
          <div className="audit-stat-sub">Missing cost basis</div>
        </div>
        <div className="audit-stat-card">
          <div className="audit-stat-num muted">{totalTx}</div>
          <div className="audit-stat-lbl">Total TX</div>
          <div className="audit-stat-sub">Across {sources.length} sources</div>
        </div>
      </div>

      <div className="audit-issue-grid">
        <IssueGroupCard
          title="Missing Cost Basis"
          severity="hi"
          countLabel={`${costBasisIssues.length} critical`}
          countClass="audit-count-red"
          description="These transactions are missing purchase price. Capital gains cannot be calculated without this data."
          issues={costBasisIssues}
          onFix={onGoToIssues}
        />
        <IssueGroupCard
          title="Unmatched Transfers"
          severity="md"
          countLabel={`${transferIssues.length} warning${transferIssues.length !== 1 ? 's' : ''}`}
          countClass="audit-count-ylw"
          description="Outgoing transfers with no matching incoming transaction. May be taxable events or missing wallet connections."
          issues={transferIssues}
          onFix={onGoToIssues}
        />
      </div>

      <div className="audit-panel audit-recon-overview">
        <div className="audit-panel-hd" style={{ justifyContent: 'space-between' }}>
          <div>
            <div className="audit-ph-title">Reconciliation Overview</div>
            <div className="audit-ph-sub">
              Last synced: {lastSyncLabel} · {totalTx.toLocaleString()} total transactions
            </div>
          </div>
          <button type="button" className="audit-btn audit-btn-ghost audit-btn-sm" disabled={scanning} onClick={handleScan}>
            {scanning ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />} Re-sync
          </button>
        </div>
        <div className="audit-recon-prog">
          <div className="audit-rp-cell">
            <div className="audit-rp-num" style={{ color: 'var(--accent)' }}>
              {matchedNum.toLocaleString()}
            </div>
            <div className="audit-rp-lbl">Matched</div>
          </div>
          <div className="audit-rp-cell">
            <div className="audit-rp-num" style={{ color: 'var(--warning)' }}>
              {reviewNum}
            </div>
            <div className="audit-rp-lbl">Needs Review</div>
          </div>
          <div className="audit-rp-cell">
            <div className="audit-rp-num" style={{ color: 'var(--danger)' }}>
              {errNum}
            </div>
            <div className="audit-rp-lbl">Errors</div>
          </div>
          <div className="audit-rp-cell">
            <div className="audit-rp-num" style={{ color: 'var(--text)' }}>
              {totalTx}
            </div>
            <div className="audit-rp-lbl">Total</div>
          </div>
        </div>
        <div className="audit-recon-bar-wrap">
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text3)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase' }}>
            <span>Transaction Breakdown</span>
            <span>{totalTx} total</span>
          </div>
          <div className="audit-rb-track">
            <div className="audit-rb-seg audit-rb-grn" style={{ width: `${Math.max(matchedPct, 0)}%` }} />
            <div className="audit-rb-seg audit-rb-ylw" style={{ width: `${Math.max(reviewPct, 0)}%` }} />
            <div className="audit-rb-seg audit-rb-red" style={{ width: `${Math.max(errPct, 0)}%` }} />
          </div>
        </div>
      </div>

      <ReconciliationIssuesPanel issues={audit.issues} onResolve={audit.handleResolve} />
    </div>
  );
}

function IssueGroupCard({
  title,
  severity,
  countLabel,
  countClass,
  description,
  issues,
  onFix,
}: {
  title: string;
  severity: 'hi' | 'md';
  countLabel: string;
  countClass: string;
  description: string;
  issues: ReconciliationIssueRow[];
  onFix: () => void;
}) {
  return (
    <div className="audit-issue-card">
      <div className="audit-issue-card-hd">
        <span className={`audit-sev audit-sev-${severity}`} />
        <span className="audit-issue-card-title">{title}</span>
        <span className={`audit-issue-count ${countClass}`}>{countLabel}</span>
      </div>
      <div className="audit-issue-card-body">
        <div className="audit-issue-card-desc">{description}</div>
        {issues.length === 0 ? (
          <p style={{ fontSize: 12, color: 'var(--text3)' }}>No items in this category.</p>
        ) : (
          issues.slice(0, 6).map((issue) => (
            <div key={issue.id} className="audit-issue-item">
              <span style={{ fontSize: 15, flexShrink: 0 }}>{issue.asset?.slice(0, 1) || '•'}</span>
              <div className="audit-ii-txt">
                <b>{issue.asset || '—'}</b> {formatIssueSummary(issue)}
              </div>
              <button type="button" className="audit-ii-fix" onClick={onFix}>
                {issueActionLabel(issue.issue_type)}
              </button>
            </div>
          ))
        )}
        {issues.length > 6 && (
          <button type="button" className="audit-ii-fix" style={{ marginTop: 8 }} onClick={onFix}>
            View all {issues.length} →
          </button>
        )}
      </div>
    </div>
  );
}
