import { Plug, Plus } from 'lucide-react';

type Props = {
  onConnectWallet: () => void;
  onAddExchange: () => void;
};

export function AuditEmptyState({ onConnectWallet, onAddExchange }: Props) {
  return (
    <div className="audit-empty">
      <div className="audit-empty-hero audit-tab-panel-shell">
        <div className="audit-empty-hero-top">
          <div className="audit-empty-icon-ring">
            <Plug size={32} style={{ color: 'var(--text3)' }} />
          </div>
          <h2 className="audit-empty-title">No data sources connected</h2>
          <p className="audit-empty-desc">
            Connect your wallets and exchanges to start reconciling your transactions and generate accurate tax reports.
          </p>
          <div className="audit-empty-actions">
            <button type="button" className="audit-btn audit-btn-primary" onClick={onConnectWallet}>
              <Plus size={14} strokeWidth={2.5} /> Connect Wallet
            </button>
            <button type="button" className="audit-btn audit-btn-ghost" onClick={onAddExchange}>
              <Plus size={14} strokeWidth={2.5} /> Add Exchange
            </button>
          </div>
        </div>
        <div className="audit-empty-steps">
          <div className="audit-step-cell">
            <div className="audit-step-num">1</div>
            <div>
              <div className="audit-step-title">Connect sources</div>
              <div className="audit-step-desc">Add wallets, exchanges or import CSV files with your transaction history</div>
            </div>
          </div>
          <div className="audit-step-cell">
            <div className="audit-step-num">2</div>
            <div>
              <div className="audit-step-title">Auto-reconcile</div>
              <div className="audit-step-desc">We&apos;ll match transfers, classify transactions and identify missing cost basis</div>
            </div>
          </div>
          <div className="audit-step-cell">
            <div className="audit-step-num">3</div>
            <div>
              <div className="audit-step-title">Review &amp; export</div>
              <div className="audit-step-desc">Fix any remaining issues and generate your IRS-ready tax report</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
