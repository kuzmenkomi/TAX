import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  History, 
  ArrowRight, 
  Calendar, 
  Tag, 
  ExternalLink,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  Clock
} from 'lucide-react';
import { apiFetch } from '../api/v1';

interface LotMatch {
  id: number;
  asset: string;
  amount: number;
  buy_price: number;
  sell_price: number;
  cost_basis: number;
  proceeds: number;
  gain_loss: number;
  buy_timestamp: string;
  sell_timestamp: string;
  buy_tx_external_id: string;
  sell_tx_external_id: string;
  holding_period_days: number;
}

interface AuditTrailModalProps {
  isOpen: boolean;
  onClose: () => void;
  txId?: number | string;
  asset?: string;
  amount?: number;
}

export function AuditTrailModal({ isOpen, onClose, txId, asset, amount }: AuditTrailModalProps) {
  const [matches, setMatches] = useState<LotMatch[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && txId) {
      loadMatches();
    }
  }, [isOpen, txId]);

  async function loadMatches() {
    setLoading(true);
    try {
      const res = await apiFetch(`/accounting/matches/transaction/${txId}`, { useAuth: true });
      const data = await res.json();
      setMatches(data.matches || []);
    } catch (err) {
      console.error('Failed to load audit trail', err);
    } finally {
      setLoading(false);
    }
  }

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="w-full max-w-4xl max-h-[85vh] overflow-hidden border rounded-[2.5rem] shadow-2xl flex flex-col"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
        >
          {/* Header */}
          <div className="p-8 border-b flex items-center justify-between" style={{ borderColor: 'var(--border)' }}>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-brand-green-500/10 flex items-center justify-center">
                <ShieldCheck className="text-brand-green-500" size={24} />
              </div>
              <div>
                <h2 className="text-2xl font-syne font-bold" style={{ color: 'var(--text)' }}>Audit Trail</h2>
                <p className="text-[13px]" style={{ color: 'var(--text3)' }}>
                  Detailed cost-basis matching for {amount} {asset}
                </p>
              </div>
            </div>
            <button 
              onClick={onClose}
              className="w-10 h-10 rounded-full flex items-center justify-center transition-colors hover:bg-brand-green-500/10"
              style={{ color: 'var(--text2)' }}
            >
              <X size={20} />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-8">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 gap-4">
                <div className="w-12 h-12 border-4 border-brand-green-500/20 border-t-brand-green-500 rounded-full animate-spin" />
                <p className="text-sm font-bold" style={{ color: 'var(--text3)' }}>Calculating cost basis matches...</p>
              </div>
            ) : matches.length === 0 ? (
              <div className="text-center py-20">
                <History className="w-16 h-16 mx-auto mb-4 opacity-20" />
                <p style={{ color: 'var(--text3)' }}>No lot matches found for this transaction.</p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                  <div className="p-6 rounded-[2rem] border bg-brand-green-500/5" style={{ borderColor: 'var(--border)' }}>
                    <p className="text-[10px] font-bold uppercase tracking-wider mb-1" style={{ color: 'var(--text3)' }}>Total Proceeds</p>
                    <p className="text-2xl font-black" style={{ color: 'var(--text)' }}>
                      ${matches.reduce((acc, m) => acc + m.proceeds, 0).toFixed(2)}
                    </p>
                  </div>
                  <div className="p-6 rounded-[2rem] border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                    <p className="text-[10px] font-bold uppercase tracking-wider mb-1" style={{ color: 'var(--text3)' }}>Total Cost Basis</p>
                    <p className="text-2xl font-black" style={{ color: 'var(--text)' }}>
                      ${matches.reduce((acc, m) => acc + m.cost_basis, 0).toFixed(2)}
                    </p>
                  </div>
                  <div className={`p-6 rounded-[2rem] border ${matches.reduce((acc, m) => acc + m.gain_loss, 0) >= 0 ? 'bg-brand-green-500/10' : 'bg-danger/10'}`} style={{ borderColor: 'var(--border)' }}>
                    <p className="text-[10px] font-bold uppercase tracking-wider mb-1" style={{ color: 'var(--text3)' }}>Realized P&L</p>
                    <p className={`text-2xl font-black ${matches.reduce((acc, m) => acc + m.gain_loss, 0) >= 0 ? 'text-brand-green-500' : 'text-danger'}`}>
                      {matches.reduce((acc, m) => acc + m.gain_loss, 0) >= 0 ? '+' : ''}${matches.reduce((acc, m) => acc + m.gain_loss, 0).toFixed(2)}
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Matching Breakdown</h3>
                  {matches.map((match, i) => (
                    <div 
                      key={match.id}
                      className="p-6 rounded-[1.5rem] border transition-all hover:border-brand-green-500/30"
                      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                        <div className="flex items-center gap-6">
                          {/* Buy Side */}
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 text-[10px] font-bold uppercase text-brand-green-500">
                              <Calendar size={12} />
                              Acquired
                            </div>
                            <p className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                              {new Date(match.buy_timestamp).toLocaleDateString()}
                            </p>
                            <p className="text-[11px] font-mono opacity-50" style={{ color: 'var(--text3)' }}>
                              Price: ${match.buy_price.toFixed(2)}
                            </p>
                          </div>

                          <ArrowRight className="text-brand-green-500 opacity-30" />

                          {/* Sell Side */}
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 text-[10px] font-bold uppercase text-[#a78bfa]">
                              <Tag size={12} />
                              Liquidated
                            </div>
                            <p className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                              {new Date(match.sell_timestamp).toLocaleDateString()}
                            </p>
                            <p className="text-[11px] font-mono opacity-50" style={{ color: 'var(--text3)' }}>
                              Price: ${match.sell_price.toFixed(2)}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-8 border-l pl-8" style={{ borderColor: 'var(--border)' }}>
                          <div className="text-right">
                            <p className="text-[10px] font-bold uppercase tracking-wider mb-1" style={{ color: 'var(--text3)' }}>Amount Used</p>
                            <p className="text-sm font-black" style={{ color: 'var(--text)' }}>{match.amount.toFixed(6)} {asset}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-[10px] font-bold uppercase tracking-wider mb-1" style={{ color: 'var(--text3)' }}>Gain / Loss</p>
                            <div className="flex items-center justify-end gap-1">
                              {match.gain_loss >= 0 ? <TrendingUp size={14} className="text-brand-green-500" /> : <TrendingDown size={14} className="text-danger" />}
                              <p className={`text-sm font-black ${match.gain_loss >= 0 ? 'text-brand-green-500' : 'text-danger'}`}>
                                {match.gain_loss >= 0 ? '+' : ''}${match.gain_loss.toFixed(2)}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Footer Info */}
                      <div className="mt-6 pt-4 border-t flex items-center justify-between" style={{ borderColor: 'var(--border)' }}>
                        <div className="flex items-center gap-4 text-[10px]" style={{ color: 'var(--text3)' }}>
                          <span className="flex items-center gap-1">
                            <Clock size={10} />
                            Holding Period: <strong>{Math.floor((new Date(match.sell_timestamp).getTime() - new Date(match.buy_timestamp).getTime()) / (1000 * 60 * 60 * 24))} days</strong>
                          </span>
                        </div>
                        <div className="flex gap-3">
                          <button className="text-[10px] font-bold flex items-center gap-1 hover:text-brand-green-500 transition-colors" style={{ color: 'var(--text3)' }}>
                            <ExternalLink size={10} />
                            Buy TX
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="p-8 bg-brand-green-500/5 border-t text-center" style={{ borderColor: 'var(--border)' }}>
            <p className="text-[11px] leading-relaxed max-w-lg mx-auto" style={{ color: 'var(--text3)' }}>
              This audit trail matches incoming assets with outgoing transactions using <strong>FIFO (First-In, First-Out)</strong>. 
              Each row represents a specific fraction of a purchased lot being liquidated.
            </p>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
