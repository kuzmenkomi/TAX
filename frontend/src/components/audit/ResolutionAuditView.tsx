import { useMemo, useState } from 'react';
import { Check, Loader2, Plug, Plus } from 'lucide-react';
import type { useAuditData } from '../../hooks/useAuditData';
import type { ReconciliationIssueRow } from '../../hooks/useAuditData';
import { issueTypeLabel } from './auditUtils';

type AuditData = ReturnType<typeof useAuditData>;

type Props = {
  audit: AuditData;
  setActiveTab?: (tab: string, subTab?: string) => void;
  onGoToReconciliation: () => void;
};

type FilterKey = 'all' | 'high' | 'medium';

function priorityFor(issue: ReconciliationIssueRow): 'high' | 'medium' | 'low' {
  if (issue.severity === 'error') return 'high';
  if (issue.severity === 'warning') return 'medium';
  return 'low';
}

function actionLabel(issue: ReconciliationIssueRow): string {
  if (issue.issue_type === 'MISSING_COST_BASIS') return 'Enter price →';
  if (issue.issue_type === 'POSSIBLE_INTERNAL_TRANSFER') return 'Match tx →';
  if (issue.issue_type === 'UNKNOWN_SOURCE') return 'Link exchange →';
  return 'Classify →';
}

function subLabel(issue: ReconciliationIssueRow): string {
  if (issue.issue_type === 'MISSING_COST_BASIS') return 'No purchase price found';
  if (issue.issue_type === 'POSSIBLE_INTERNAL_TRANSFER') return 'No matching incoming tx';
  if (issue.issue_type === 'UNKNOWN_SOURCE') return 'Exchange not connected';
  return issue.description || issueTypeLabel(issue.issue_type);
}

export function ResolutionAuditView({ audit, setActiveTab, onGoToReconciliation }: Props) {
  const { loading, pageState, unresolvedIssues, totalTransactions } = audit;
  const [filter, setFilter] = useState<FilterKey>('all');

  const filtered = useMemo(() => {
    if (filter === 'high') return unresolvedIssues.filter((i) => priorityFor(i) === 'high');
    if (filter === 'medium') return unresolvedIssues.filter((i) => priorityFor(i) === 'medium');
    return unresolvedIssues;
  }, [unresolvedIssues, filter]);

  const highCount = unresolvedIssues.filter((i) => priorityFor(i) === 'high').length;
  const medCount = unresolvedIssues.filter((i) => priorityFor(i) === 'medium').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  if (pageState === 'empty') {
    return (
      <div className="audit-panel audit-tab-panel-shell">
        <div className="audit-rc-empty">
          <div className="audit-rce-icon">
            <Plug size={22} />
          </div>
          <div className="audit-rce-title">Connect a data source first</div>
          <div className="audit-rce-desc">
            Once you connect wallets or exchanges, any issues found during reconciliation will appear here for review.
          </div>
          <button
            type="button"
            className="audit-btn audit-btn-primary"
            style={{ marginTop: 8 }}
            onClick={() => setActiveTab?.('integrations', 'WALLETS')}
          >
            <Plus size={14} /> Connect Wallet
          </button>
        </div>
      </div>
    );
  }

  if (!audit.runId) {
    return (
      <div className="audit-panel audit-tab-panel-shell">
        <div className="audit-rc-empty">
          <div className="audit-rce-icon">
            <Plug size={22} style={{ opacity: 0.6 }} />
          </div>
          <div className="audit-rce-title">Run reconciliation first</div>
          <div className="audit-rce-desc">
            {totalTransactions > 0
              ? `You have ${totalTransactions.toLocaleString()} transactions imported. Run a tax calculation in Tax Center to scan for issues.`
              : 'Run a tax calculation in Tax Center to detect issues that need your review.'}
          </div>
          <button
            type="button"
            className="audit-btn audit-btn-primary"
            style={{ marginTop: 8 }}
            onClick={() => setActiveTab?.('tax')}
          >
            Go to Tax Center →
          </button>
        </div>
      </div>
    );
  }

  if (pageState === 'ok' || unresolvedIssues.length === 0) {
    const txLabel = totalTransactions > 0 ? totalTransactions.toLocaleString() : 'your';
    return (
      <div className="audit-panel audit-tab-panel-shell">
        <div className="audit-rc-empty">
          <div className="audit-rce-icon">
            <Check size={24} />
          </div>
          <div className="audit-rce-title">No issues to resolve</div>
          <div className="audit-rce-desc">
            All {txLabel} transactions are classified and matched. Your books are clean and ready for tax report
            generation.
          </div>
          <button type="button" className="audit-btn audit-btn-primary" style={{ marginTop: 8 }} onClick={() => setActiveTab?.('tax')}>
            → Generate Tax Report
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="audit-panel">
      <div className="audit-panel-hd audit-panel-hd-filters-only">
        <div className="audit-rc-filters">
          {(
            [
              { key: 'all' as const, label: `All (${unresolvedIssues.length})` },
              { key: 'high' as const, label: `High (${highCount})` },
              { key: 'medium' as const, label: `Medium (${medCount})` },
            ] as const
          ).map((f) => (
            <button
              key={f.key}
              type="button"
              className={`audit-rc-filter ${filter === f.key ? 'active' : ''}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table className="audit-rc-table">
          <thead>
            <tr>
              <th>Issue</th>
              <th>Asset</th>
              <th>Amount</th>
              <th>Date</th>
              <th>Type</th>
              <th>Priority</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((issue) => {
              const pri = priorityFor(issue);
              const date = issue.timestamp ? issue.timestamp.split('T')[0] : '—';
              return (
                <tr key={issue.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text)' }}>{issueTypeLabel(issue.issue_type)}</div>
                    <div style={{ fontSize: 11, color: 'var(--text3)' }}>{subLabel(issue)}</div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text)' }}>{issue.asset || '—'}</div>
                    {issue.tx_hash && (
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 11, color: 'var(--text3)' }}>
                        {issue.tx_hash.slice(0, 10)}…
                      </div>
                    )}
                  </td>
                  <td>
                    <div style={{ fontFamily: "'DM Mono', monospace", fontWeight: 600, color: 'var(--text)' }}>
                      {issue.amount != null ? issue.amount.toFixed(issue.amount < 1 ? 5 : 4) : '—'}
                    </div>
                  </td>
                  <td style={{ fontSize: 12 }}>{date}</td>
                  <td style={{ fontSize: 12 }}>{issueTypeLabel(issue.issue_type)}</td>
                  <td>
                    <span className={`audit-pri ${pri === 'high' ? 'audit-p-hi' : 'audit-p-md'}`}>
                      ● {pri === 'high' ? 'High' : 'Medium'}
                    </span>
                  </td>
                  <td>
                    <button type="button" className="audit-act-link" onClick={onGoToReconciliation}>
                      {actionLabel(issue)}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {filtered.length === 0 && (
        <div className="audit-rc-empty">
          <p className="audit-rce-desc">No issues match this filter.</p>
        </div>
      )}
    </div>
  );
}
