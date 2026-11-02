import React, { useState, useEffect } from 'react';
import { ReconciliationAuditView } from './audit/ReconciliationAuditView';
import { ResolutionAuditView } from './audit/ResolutionAuditView';
import { useAuditData } from '../hooks/useAuditData';
import { AlertCircle, ArrowLeftRight, Loader2, RefreshCw } from 'lucide-react';
import { cn } from '../utils/cn';

export function AuditHub({
  setActiveTab,
  initialSubTab,
}: {
  setActiveTab: (tab: string, subTab?: string) => void;
  initialSubTab?: 'reconciliation' | 'issues';
}) {
  const [activeSubTab, setActiveSubTab] = useState<'reconciliation' | 'issues'>(initialSubTab || 'reconciliation');
  const audit = useAuditData();

  useEffect(() => {
    if (initialSubTab) setActiveSubTab(initialSubTab);
  }, [initialSubTab]);

  const issueBadge = audit.unresolvedIssues.length;
  const showRescan = audit.hasAuditData && audit.runId;

  return (
    <div className="audit-hub animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div>
          <h1 className="font-syne font-extrabold text-[24px] tracking-tight text-[var(--text)]">Audit &amp; Issues</h1>
          <p className="text-[12px] text-[var(--text3)]">
            Monitor sync status, identify missing cost basis, and resolve discrepancies
            {audit.pageState === 'ok' && audit.hasAuditData && audit.totalTransactions > 0 && (
              <span className="ml-1">· {audit.totalTransactions.toLocaleString()} transactions reconciled</span>
            )}
            {audit.pageState === 'errors' && (
              <span className="ml-1 text-[var(--danger)]">
                · {issueBadge} issue{issueBadge !== 1 ? 's' : ''} require attention
              </span>
            )}
          </p>
        </div>
        {showRescan && (
          <button
            type="button"
            className="audit-btn audit-btn-primary audit-btn-sm"
            disabled={audit.scanning}
            onClick={audit.handleScan}
          >
            {audit.scanning ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            Re-scan All
          </button>
        )}
      </div>

      <div className="audit-tabs">
        <button
          type="button"
          className={cn('audit-tab', activeSubTab === 'reconciliation' && 'active')}
          onClick={() => setActiveSubTab('reconciliation')}
        >
          <ArrowLeftRight size={15} />
          Reconciliation
        </button>
        <button
          type="button"
          className={cn('audit-tab', activeSubTab === 'issues' && 'active')}
          onClick={() => setActiveSubTab('issues')}
        >
          <AlertCircle size={15} />
          Resolution Center
          <span className={cn('audit-tab-badge', issueBadge > 0 && 'red')}>{issueBadge}</span>
        </button>
      </div>

      <div className="audit-tab-content animate-in fade-in slide-in-from-bottom-4 duration-500">
        {activeSubTab === 'reconciliation' ? (
          <ReconciliationAuditView
            audit={audit}
            setActiveTab={setActiveTab}
            onGoToIssues={() => setActiveSubTab('issues')}
          />
        ) : (
          <ResolutionAuditView
            audit={audit}
            setActiveTab={setActiveTab}
            onGoToReconciliation={() => setActiveSubTab('reconciliation')}
          />
        )}
      </div>
    </div>
  );
}
