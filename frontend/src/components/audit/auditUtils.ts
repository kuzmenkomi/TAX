import type { ReconciliationIssueRow } from '../../hooks/useAuditData';

export function issueTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    MISSING_COST_BASIS: 'Missing Cost Basis',
    UNKNOWN_SOURCE: 'Unknown Source',
    ORPHAN_RECEIVE: 'Orphan Receive',
    POSSIBLE_INTERNAL_TRANSFER: 'Unmatched Transfer',
    POSSIBLE_AIRDROP: 'Possible Airdrop',
    DUPLICATE_SUSPECT: 'Duplicate Suspect',
  };
  return labels[type] || type.replace(/_/g, ' ');
}

export function issueActionLabel(type: string): string {
  if (type === 'MISSING_COST_BASIS') return 'Fix →';
  if (type === 'POSSIBLE_INTERNAL_TRANSFER') return 'Match';
  return 'Classify →';
}

export function formatIssueSummary(issue: ReconciliationIssueRow): string {
  const asset = issue.asset || 'Asset';
  const amt = issue.amount != null ? issue.amount.toFixed(issue.amount < 1 ? 6 : 4) : '—';
  const date = issue.timestamp ? issue.timestamp.split('T')[0] : '';
  if (issue.issue_type === 'MISSING_COST_BASIS') {
    return `${amt} ${asset} · missing purchase price${date ? ` · ${date}` : ''}`;
  }
  if (issue.issue_type === 'POSSIBLE_INTERNAL_TRANSFER') {
    return `${amt} ${asset} → transfer${date ? ` · ${date}` : ''}`;
  }
  return `${amt} ${asset}${issue.description ? ` · ${issue.description}` : ''}`;
}

export const COST_BASIS_TYPES = new Set(['MISSING_COST_BASIS', 'POSSIBLE_AIRDROP', 'DUPLICATE_SUSPECT']);
export const TRANSFER_TYPES = new Set(['POSSIBLE_INTERNAL_TRANSFER', 'UNKNOWN_SOURCE', 'ORPHAN_RECEIVE']);
