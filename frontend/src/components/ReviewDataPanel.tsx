import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Info,
  Layers,
  Sparkles,
  Database,
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { cn } from '../utils/cn';

interface ReviewDataPanelProps {
  isCalculating: boolean;
  onProceed: () => void;
}

const cardClass =
  'rounded-2xl border border-[var(--border)] overflow-hidden';
const cardStyle = { background: 'var(--card)' } as const;

export function ReviewDataPanel({ isCalculating, onProceed }: ReviewDataPanelProps) {
  const { analyzeResult } = useAppContext();

  if (isCalculating) {
    return (
      <div className={cn(cardClass, 'p-10 text-center space-y-6 animate-pulse')} style={cardStyle}>
        <div className="relative w-16 h-16 mx-auto">
          <div className="absolute inset-0 rounded-full border-4 border-[var(--accent)]/20 animate-ping" />
          <div className="absolute inset-0 rounded-full border-4 border-t-[var(--accent)] border-r-transparent border-b-transparent border-l-transparent animate-spin" />
        </div>
        <div className="space-y-2">
          <h4 className="font-syne font-bold text-lg text-[var(--text)]">Running Tax Engine Calculations</h4>
          <p className="text-[13px] text-[var(--text2)] max-w-[400px] mx-auto">
            Applying accounting rules, matching buy/sell lots, and computing realized capital gains...
          </p>
        </div>
      </div>
    );
  }

  if (!analyzeResult) {
    return (
      <div className={cn(cardClass, 'p-10 text-center space-y-6')} style={cardStyle}>
        <div
          className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto text-[var(--text3)]"
          style={{ background: 'var(--card2)', border: '1px solid var(--border)' }}
        >
          <Database size={24} />
        </div>
        <div className="space-y-1">
          <h4 className="font-syne font-bold text-lg text-[var(--text)]">No Calculation Results Available</h4>
          <p className="text-[13px] text-[var(--text2)] max-w-[400px] mx-auto">
            Please select your sources and configure tax settings, then click &quot;Start Calculation&quot; to see results here.
          </p>
        </div>
      </div>
    );
  }

  const pnl = analyzeResult.pnl || {};
  const realizedPnlByAsset = pnl.realized_pnl_by_asset || {};
  const lotMatches = analyzeResult.lot_matches || pnl.lot_matches || [];
  const issues = analyzeResult.issues || [];

  let totalGain = 0;
  let totalLoss = 0;
  let netPnl = 0;

  Object.entries(realizedPnlByAsset).forEach(([asset, value]) => {
    if (asset === 'GAS_EXPENSE') return;
    const numValue = Number(value) || 0;
    if (numValue > 0) totalGain += numValue;
    else totalLoss += numValue;
    netPnl += numValue;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          className={cn(cardClass, 'p-5 relative group hover:border-[var(--accent)]/30 transition-all duration-300')}
          style={cardStyle}
        >
          <div className="absolute top-0 right-0 w-24 h-24 bg-[var(--accent)]/5 rounded-full blur-xl pointer-events-none" />
          <div className="flex justify-between items-start mb-4">
            <span className="text-[11px] font-black tracking-widest text-[var(--text3)] uppercase">Total Realized Gains</span>
            <div className="w-8 h-8 rounded-lg bg-[var(--accent-dim)] flex items-center justify-center text-[var(--accent)]">
              <TrendingUp size={16} />
            </div>
          </div>
          <div className="space-y-1">
            <h4 className="text-2xl font-extrabold text-[var(--accent)] font-syne">
              ${totalGain.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h4>
            <p className="text-[11px] text-[var(--text2)]">Profitable match transactions</p>
          </div>
        </div>

        <div
          className={cn(cardClass, 'p-5 relative group hover:border-[var(--danger)]/30 transition-all duration-300')}
          style={cardStyle}
        >
          <div className="absolute top-0 right-0 w-24 h-24 bg-[var(--danger)]/5 rounded-full blur-xl pointer-events-none" />
          <div className="flex justify-between items-start mb-4">
            <span className="text-[11px] font-black tracking-widest text-[var(--text3)] uppercase">Total Realized Losses</span>
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--danger)]"
              style={{ background: 'rgba(255, 77, 106, 0.1)' }}
            >
              <TrendingDown size={16} />
            </div>
          </div>
          <div className="space-y-1">
            <h4 className="text-2xl font-extrabold text-[var(--danger)] font-syne">
              ${Math.abs(totalLoss).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h4>
            <p className="text-[11px] text-[var(--text2)]">Capital loss offset events</p>
          </div>
        </div>

        <div
          className={cn(cardClass, 'p-5 relative group hover:border-[var(--accent)]/30 transition-all duration-300')}
          style={cardStyle}
        >
          <div className="absolute top-0 right-0 w-24 h-24 bg-[var(--accent)]/5 rounded-full blur-xl pointer-events-none" />
          <div className="flex justify-between items-start mb-4">
            <span className="text-[11px] font-black tracking-widest text-[var(--text3)] uppercase">Net Capital P&L</span>
            <div className="w-8 h-8 rounded-lg bg-[var(--accent-dim)] flex items-center justify-center text-[var(--accent)]">
              <DollarSign size={16} />
            </div>
          </div>
          <div className="space-y-1">
            <h4
              className={cn(
                'text-2xl font-extrabold font-syne',
                netPnl >= 0 ? 'text-[var(--accent)]' : 'text-[var(--danger)]',
              )}
            >
              {netPnl >= 0 ? '+' : '-'}$
              {Math.abs(netPnl).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h4>
            <p className="text-[11px] text-[var(--text2)]">
              Calculated via {analyzeResult.accounting_method || 'FIFO'} method
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lot Matches Table */}
        <div className={cn(cardClass, 'lg:col-span-2 flex flex-col')} style={cardStyle}>
          <div
            className="p-5 pb-4 flex justify-between items-center"
            style={{ borderBottom: '1px solid var(--border)' }}
          >
            <div className="flex items-center gap-2">
              <Layers size={16} className="text-[var(--accent)]" />
              <h4 className="font-syne font-bold text-[15px] text-[var(--text)]">
                Calculated Lot Matches ({lotMatches.length})
              </h4>
            </div>
            <span
              className="text-[11px] font-bold text-[var(--text2)] px-2.5 py-1 rounded-lg"
              style={{ background: 'var(--card2)', border: '1px solid var(--border)' }}
            >
              FIFO Pairs
            </span>
          </div>

          <div className="flex-1">
            {lotMatches.length > 0 ? (
              <>
                <div className="space-y-3 md:hidden p-4">
                  {lotMatches.slice(0, 10).map((match: any, index: number) => {
                    const gainVal = Number(match.gain_loss) || 0;
                    const buyDate = match.buy_date || match.buy_timestamp || '';
                    const sellDate = match.sell_date || match.sell_timestamp || '';
                    return (
                      <div key={index} className="rounded-xl border border-[var(--border)] bg-[var(--card2)] p-4 text-[12px]">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="font-semibold text-[var(--text)]">{match.asset || match.symbol}</div>
                            <div className="mt-1 font-mono text-[var(--text2)]">
                              {(Number(match.amount) || 0).toLocaleString(undefined, { maximumFractionDigits: 6 })}
                            </div>
                          </div>
                          <div className={cn('font-bold font-mono', gainVal >= 0 ? 'text-[var(--accent)]' : 'text-[var(--danger)]')}>
                            {gainVal >= 0 ? '+' : '-'}${Math.abs(gainVal).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </div>
                        </div>
                        <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] text-[var(--text3)]">
                          <div>Buy: {buyDate.split('T')[0] || buyDate}</div>
                          <div className="text-right">Sell: {sellDate.split('T')[0] || sellDate}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="hidden md:block overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr
                        className="text-[10px] font-black tracking-widest text-[var(--text3)] uppercase"
                        style={{ background: 'var(--card2)', borderBottom: '1px solid var(--border)' }}
                      >
                        <th className="px-5 py-3">Asset</th>
                        <th className="px-4 py-3 text-right">Qty</th>
                        <th className="px-4 py-3">Buy Date</th>
                        <th className="px-4 py-3">Sell Date</th>
                        <th className="px-5 py-3 text-right">Gain / Loss</th>
                      </tr>
                    </thead>
                    <tbody className="text-[12px]" style={{ borderColor: 'var(--border)' }}>
                      {lotMatches.slice(0, 10).map((match: any, index: number) => {
                        const gainVal = Number(match.gain_loss) || 0;
                        const buyDate = match.buy_date || match.buy_timestamp || '';
                        const sellDate = match.sell_date || match.sell_timestamp || '';
                        return (
                          <tr
                            key={index}
                            className="hover:bg-[var(--card2)] transition-colors text-[var(--text2)]"
                            style={{ borderBottom: '1px solid var(--border)' }}
                          >
                            <td className="px-5 py-3 font-semibold text-[var(--text)]">{match.asset || match.symbol}</td>
                            <td className="px-4 py-3 text-right font-mono">
                              {(Number(match.amount) || 0).toLocaleString(undefined, { maximumFractionDigits: 6 })}
                            </td>
                            <td className="px-4 py-3 text-[var(--text3)]">{buyDate.split('T')[0] || buyDate}</td>
                            <td className="px-4 py-3 text-[var(--text3)]">{sellDate.split('T')[0] || sellDate}</td>
                            <td
                              className={cn(
                                'px-5 py-3 text-right font-bold font-mono',
                                gainVal >= 0 ? 'text-[var(--accent)]' : 'text-[var(--danger)]',
                              )}
                            >
                              {gainVal >= 0 ? '+' : '-'}$
                              {Math.abs(gainVal).toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <div className="py-10 text-center text-[var(--text2)]">No lot-match pairs found.</div>
            )}
          </div>

          {lotMatches.length > 10 && (
            <div
              className="p-4 text-center"
              style={{ borderTop: '1px solid var(--border)', background: 'var(--card2)' }}
            >
              <span className="text-[11px] text-[var(--text2)] font-semibold">
                Showing top 10 matches · Upgrade to view and download full official report containing all{' '}
                {lotMatches.length} lots.
              </span>
            </div>
          )}
        </div>

        {/* Data Issues & Summary */}
        <div className="space-y-4">
          <div className={cn(cardClass, 'p-5 space-y-4')} style={cardStyle}>
            <div
              className="flex items-center gap-2 pb-2"
              style={{ borderBottom: '1px solid var(--border)' }}
            >
              <AlertTriangle size={16} className="text-[var(--warning)]" />
              <h4 className="font-syne font-bold text-[15px] text-[var(--text)]">
                Data Consistency Issues ({issues.length})
              </h4>
            </div>

            <div className="space-y-2 max-h-[220px] overflow-y-auto">
              {issues.length > 0 ? (
                issues.map((issue: any, index: number) => (
                  <div
                    key={index}
                    className="p-3 rounded-xl flex items-start gap-2.5 text-[11px] leading-relaxed"
                    style={{ background: 'var(--card2)', border: '1px solid var(--border)' }}
                  >
                    <Info
                      size={14}
                      className={cn(
                        'flex-shrink-0 mt-0.5',
                        issue.severity === 'high' ? 'text-[var(--danger)]' : 'text-[var(--warning)]',
                      )}
                    />
                    <div>
                      <p className="font-bold text-[var(--text)]">
                        {issue.asset}: {issue.issue_type}
                      </p>
                      <p className="text-[var(--text2)] mt-0.5">{issue.description}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-6 text-center space-y-2">
                  <div className="w-8 h-8 rounded-full bg-[var(--accent-dim)] flex items-center justify-center mx-auto text-[var(--accent)]">
                    <CheckCircle2 size={16} />
                  </div>
                  <div>
                    <p className="text-[12px] font-bold text-[var(--text)]">Data looks flawless!</p>
                    <p className="text-[10px] text-[var(--text2)]">No calculation anomalies detected.</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div
            className={cn(cardClass, 'p-5 relative overflow-hidden')}
            style={{
              background: 'linear-gradient(135deg, var(--accent-dim) 0%, var(--card2) 100%)',
              borderColor: 'var(--border)',
            }}
          >
            <div className="space-y-3 relative">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[var(--accent-dim)] border border-[var(--accent)]/30 text-[var(--accent)] text-[9px] font-black tracking-wide uppercase">
                <Sparkles size={10} className="fill-[var(--accent)]" /> Ready for Export
              </div>
              <h5 className="font-syne font-bold text-[var(--text)] text-[14px]">Tax calculations are locked in.</h5>
              <p className="text-[11px] text-[var(--text2)] leading-relaxed">
                Generate and download official filings compliant with local regulatory standards.
              </p>
              <button
                onClick={onProceed}
                className="w-full flex items-center justify-center gap-2 bg-[var(--accent)] text-white font-black py-2.5 rounded-xl text-[12px] hover:scale-[1.02] transition-all shadow-[var(--accent-shadow-md)]"
              >
                PROCEED TO REPORTS <ArrowRight size={14} strokeWidth={3} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
