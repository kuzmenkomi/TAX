import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAppContext } from '../context/AppContext';
import apiV1, { apiFetch } from '../api/v1';
import { formatCsvImportDateTime } from '../utils/importSources';

export interface AuditSource {
  id: string;
  kind: 'wallet' | 'exchange';
  name: string;
  address: string;
  transactionCount: number;
  lastSyncedAt: string | null;
  syncStatus: string | null;
}

export interface ReconciliationIssueRow {
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
  suggested_matches: unknown[];
  resolved: boolean;
  resolved_as: string | null;
}

export interface ReconciliationStats {
  total: number;
  resolved: number;
  unresolved: number;
  progress_pct: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
}

export type AuditPageState = 'empty' | 'ok' | 'errors';

function shortenAddress(addr: string): string {
  if (!addr || addr.length < 12) return addr || '—';
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`;
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return 'Never';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 48) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function useAuditData() {
  const { analyzeResult, backendOnline, dataVersion } = useAppContext();

  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState<AuditSource[]>([]);
  const [totalTransactions, setTotalTransactions] = useState(0);
  const [runId, setRunId] = useState<number | null>(null);
  const [issues, setIssues] = useState<ReconciliationIssueRow[]>([]);
  const [stats, setStats] = useState<ReconciliationStats | null>(null);
  const [scanning, setScanning] = useState(false);
  const [autoMatching, setAutoMatching] = useState(false);

  const hasConnections = sources.length > 0;
  const hasAuditData = hasConnections || totalTransactions > 0 || runId != null;

  const loadConnections = useCallback(async () => {
    if (!backendOnline) {
      setSources([]);
      setTotalTransactions(0);
      return;
    }
    try {
      const [exRes, wRes, txRes, runsRes] = await Promise.allSettled([
        apiV1.exchange.listMy(),
        apiV1.wallet.list(),
        apiV1.wallet.getTransactions(undefined, 10000),
        apiV1.analysis.listRuns(),
      ]);

      const next: AuditSource[] = [];
      let txSum = 0;

      if (exRes.status === 'fulfilled' && Array.isArray(exRes.value)) {
        exRes.value.forEach((ex: any) => {
          const count = Number(ex.transaction_count ?? 0);
          txSum += count;
          next.push({
            id: `ex_${ex.id}`,
            kind: 'exchange',
            name: String(ex.exchange_name || ex.exchange || ex.provider || 'Exchange'),
            address: 'API connected',
            transactionCount: count,
            lastSyncedAt: (ex.last_synced_at as string) || (ex.last_synced as string) || null,
            syncStatus: (ex.sync_status as string) || null,
          });
        });
      }

      if (wRes.status === 'fulfilled' && wRes.value) {
        const wallets = Array.isArray(wRes.value) ? wRes.value : (wRes.value as { wallets?: unknown[] }).wallets ?? [];
        wallets.forEach((w: Record<string, unknown>) => {
          const count = Number(w.transaction_count ?? w.transactions_count ?? 0);
          txSum += count;
          const addr = String(w.address || '');
          next.push({
            id: `w_${w.id}`,
            kind: 'wallet',
            name: String(w.label || w.name || w.chain || 'Wallet'),
            address: shortenAddress(addr),
            transactionCount: count,
            lastSyncedAt: (w.last_synced_at as string) || null,
            syncStatus: (w.sync_status as string) || null,
          });
        });
      }

      let txTotal = txSum;
      if (txRes.status === 'fulfilled' && Array.isArray(txRes.value)) {
        txTotal = txRes.value.length;
      }

      if (runsRes.status === 'fulfilled') {
        const runs = runsRes.value?.runs ?? [];
        runs.forEach((run: Record<string, unknown>) => {
          const format = String(run.format || '').trim().toLowerCase();
          if (format.startsWith('onchain:')) return;
          const runIdNum = Number(run.run_id ?? run.id ?? 0);
          if (!runIdNum) return;
          const count = Number(run.rows_processed ?? 0);
          const label = format
            ? format.charAt(0).toUpperCase() + format.slice(1)
            : 'CSV Import';
          const when = run.created_at ? formatCsvImportDateTime(String(run.created_at)) : '';
          next.push({
            id: `csv_${runIdNum}`,
            kind: 'exchange',
            name: when ? `${label} CSV · ${when}` : `${label} CSV`,
            address: `Import #${runIdNum}`,
            transactionCount: count,
            lastSyncedAt: (run.created_at as string) || null,
            syncStatus: 'completed',
          });
        });
      }

      setTotalTransactions(txTotal);
      setSources(next);
    } catch (err) {
      console.error('Failed to load audit connections', err);
      setSources([]);
      setTotalTransactions(0);
    }
  }, [backendOnline]);

  const resolveRunId = useCallback(async (): Promise<number | null> => {
    if (analyzeResult?.analysis_run_id) return analyzeResult.analysis_run_id;
    try {
      const runData = await apiV1.analysis.listRuns();
      const latest = Number(runData?.runs?.[0]?.run_id ?? 0);
      return latest || null;
    } catch {
      return null;
    }
  }, [analyzeResult?.analysis_run_id]);

  const loadIssues = useCallback(async (activeRunId: number) => {
    try {
      const res = await apiFetch(`/reconciliation/issues/${activeRunId}`);
      const data = await res.json();
      setIssues(data.issues || []);
      setStats(data.stats || null);
    } catch (err) {
      console.error('Failed to load reconciliation issues', err);
      setIssues([]);
      setStats(null);
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    await loadConnections();
    const id = await resolveRunId();
    setRunId(id);
    if (id) await loadIssues(id);
    else {
      setIssues([]);
      setStats(null);
    }
    setLoading(false);
  }, [loadConnections, resolveRunId, loadIssues]);

  useEffect(() => {
    refresh();
  }, [refresh, dataVersion]);

  const handleScan = useCallback(async () => {
    let id = runId;
    if (!id) {
      id = await resolveRunId();
      setRunId(id);
    }
    if (!id) return;
    setScanning(true);
    try {
      await apiFetch(`/reconciliation/scan/${id}`, { method: 'POST' });
      await loadIssues(id);
    } catch (err) {
      console.error('Scan failed', err);
    } finally {
      setScanning(false);
    }
  }, [runId, resolveRunId, loadIssues]);

  const handleAutoMatch = useCallback(async () => {
    if (!runId) return;
    setAutoMatching(true);
    try {
      await apiFetch(`/reconciliation/auto-match/${runId}`, { method: 'POST' });
      await loadIssues(runId);
    } catch (err) {
      console.error('Auto-match failed', err);
    } finally {
      setAutoMatching(false);
    }
  }, [runId, loadIssues]);

  const handleResolve = useCallback(
    async (issueId: number, resolution: string) => {
      try {
        await apiFetch('/reconciliation/resolve', {
          method: 'POST',
          body: JSON.stringify({ issue_id: issueId, resolution }),
        });
        if (runId) await loadIssues(runId);
      } catch (err) {
        console.error('Resolve failed', err);
      }
    },
    [runId, loadIssues],
  );

  const unresolvedIssues = useMemo(
    () => issues.filter((i) => !i.resolved),
    [issues],
  );

  const pageState: AuditPageState = useMemo(() => {
    const hasData = hasConnections || totalTransactions > 0 || runId != null;
    if (!hasData) return 'empty';
    if (!runId) return 'ok';
    if (stats && stats.unresolved > 0) return 'errors';
    if (unresolvedIssues.length > 0) return 'errors';
    return 'ok';
  }, [hasConnections, totalTransactions, runId, stats, unresolvedIssues.length]);

  const matchedCount = useMemo(() => {
    const openIssues = unresolvedIssues.length;
    if (totalTransactions > 0) {
      if (openIssues === 0) return totalTransactions;
      return Math.max(0, totalTransactions - openIssues);
    }
    if (stats && stats.total > 0) return stats.resolved ?? 0;
    return issues.filter((i) => i.resolved).length;
  }, [totalTransactions, unresolvedIssues.length, stats, issues]);

  const reviewCount = useMemo(() => {
    const transferTypes = ['POSSIBLE_INTERNAL_TRANSFER', 'UNKNOWN_SOURCE', 'ORPHAN_RECEIVE'];
    return unresolvedIssues.filter((i) => transferTypes.includes(i.issue_type)).length;
  }, [unresolvedIssues]);

  const errorCount = unresolvedIssues.filter(
    (i) => !['POSSIBLE_INTERNAL_TRANSFER', 'UNKNOWN_SOURCE', 'ORPHAN_RECEIVE'].includes(i.issue_type),
  ).length;

  const progressPct = useMemo(() => {
    if (totalTransactions > 0) {
      if (unresolvedIssues.length === 0) return 100;
      return Math.round((matchedCount / totalTransactions) * 100);
    }
    return stats?.progress_pct ?? (issues.length ? Math.round((matchedCount / Math.max(issues.length, 1)) * 100) : 0);
  }, [totalTransactions, unresolvedIssues.length, matchedCount, stats?.progress_pct, issues.length]);

  const lastSyncLabel = useMemo(() => {
    const times = sources.map((s) => s.lastSyncedAt).filter(Boolean) as string[];
    if (!times.length) return 'Not synced yet';
    const latest = times.sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0];
    return formatRelativeTime(latest);
  }, [sources]);

  const issuesByType = useMemo(() => {
    const groups: Record<string, ReconciliationIssueRow[]> = {};
    unresolvedIssues.forEach((issue) => {
      const key = issue.issue_type;
      if (!groups[key]) groups[key] = [];
      groups[key].push(issue);
    });
    return groups;
  }, [unresolvedIssues]);

  return {
    loading,
    pageState,
    hasConnections,
    hasAuditData,
    sources,
    totalTransactions,
    runId,
    issues,
    unresolvedIssues,
    stats,
    scanning,
    autoMatching,
    matchedCount,
    reviewCount,
    errorCount,
    progressPct,
    lastSyncLabel,
    issuesByType,
    refresh,
    handleScan,
    handleAutoMatch,
    handleResolve,
  };
}
