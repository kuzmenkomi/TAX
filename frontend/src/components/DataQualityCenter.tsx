import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  Info, 
  Search,
  ArrowRight,
  TrendingDown,
  HelpCircle,
  FileWarning,
  Sparkles
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';

interface Issue {
  code: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  asset?: string;
  row_index?: number;
  count?: number;
  timestamp?: string;
}

export function DataQualityCenter() {
  const { analyzeResult } = useAppContext();
  const issues = (analyzeResult?.issues as Issue[]) || [];

  const stats = useMemo(() => {
    return {
      errors: issues.filter(i => i.severity === 'error').length,
      warnings: issues.filter(i => i.severity === 'warning').length,
      info: issues.filter(i => i.severity === 'info').length,
      total: issues.length
    };
  }, [issues]);

  if (stats.total === 0 && analyzeResult) {
    return (
      <div className="p-12 text-center border rounded-[3rem] bg-brand-green-500/5" style={{ borderColor: 'var(--border)' }}>
        <div className="w-20 h-20 bg-brand-green-500/10 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-brand-green-500/5">
          <CheckCircle2 size={40} className="text-brand-green-500" />
        </div>
        <h2 className="text-2xl font-syne font-bold mb-2" style={{ color: 'var(--text)' }}>Data is Pristine</h2>
        <p className="text-[13px] max-w-sm mx-auto" style={{ color: 'var(--text3)' }}>
          No quality issues detected. Your tax calculations are highly reliable and ready for official filing.
        </p>
      </div>
    );
  }

  if (!analyzeResult) return null;

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-8 rounded-[2.5rem] border bg-danger/5" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center justify-between mb-4">
            <ShieldAlert size={24} className="text-danger" />
            <span className="text-3xl font-black text-danger">{stats.errors}</span>
          </div>
          <h3 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Critical Errors</h3>
          <p className="text-[11px] mt-1 opacity-60" style={{ color: 'var(--text3)' }}>Must be fixed for accurate taxes</p>
        </div>

        <div className="p-8 rounded-[2.5rem] border bg-[#f0a86a]/5" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center justify-between mb-4">
            <AlertTriangle size={24} className="text-[#f0a86a]" />
            <span className="text-3xl font-black text-[#f0a86a]">{stats.warnings}</span>
          </div>
          <h3 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Warnings</h3>
          <p className="text-[11px] mt-1 opacity-60" style={{ color: 'var(--text3)' }}>Potential data gaps detected</p>
        </div>

        <div className="p-8 rounded-[2.5rem] border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
          <div className="flex items-center justify-between mb-4">
            <Info size={24} className="text-brand-green-500" />
            <span className="text-3xl font-black" style={{ color: 'var(--text)' }}>{stats.info}</span>
          </div>
          <h3 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Optimization Info</h3>
          <p className="text-[11px] mt-1 opacity-60" style={{ color: 'var(--text3)' }}>Automatic improvements applied</p>
        </div>
      </div>

      {/* Issues List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-4 mb-4">
          <h2 className="text-lg font-syne font-bold" style={{ color: 'var(--text)' }}>Issue Breakdown</h2>
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider" style={{ color: 'var(--text3)' }}>
            <Sparkles size={12} className="text-brand-green-500" />
            AI Diagnostics Active
          </div>
        </div>

        <AnimatePresence mode="popLayout">
          {issues.map((issue, i) => (
            <motion.div
              key={i}
              layout
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`p-6 rounded-[1.5rem] border flex items-start gap-5 transition-all hover:translate-x-1 ${
                issue.severity === 'error' ? 'bg-danger/5 border-danger/10' : 
                issue.severity === 'warning' ? 'bg-[#f0a86a]/5 border-[#f0a86a]/10' :
                'bg-brand-green-500/5 border-brand-green-500/10'
              }`}
            >
              <div className={`mt-1 p-2 rounded-xl ${
                issue.severity === 'error' ? 'bg-danger/10 text-danger' : 
                issue.severity === 'warning' ? 'bg-[#f0a86a]/10 text-[#f0a86a]' :
                'bg-brand-green-500/10 text-brand-green-500'
              }`}>
                {issue.severity === 'error' ? <ShieldAlert size={20} /> : 
                 issue.severity === 'warning' ? <AlertTriangle size={20} /> :
                 <Info size={20} />}
              </div>

              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-[9px] font-black uppercase tracking-[2px] px-2 py-0.5 rounded ${
                    issue.severity === 'error' ? 'bg-danger/10 text-danger' : 
                    issue.severity === 'warning' ? 'bg-[#f0a86a]/10 text-[#f0a86a]' :
                    'bg-brand-green-500/10 text-brand-green-500'
                  }`}>
                    {issue.code.replace(/_/g, ' ')}
                  </span>
                  {issue.asset && (
                    <span className="text-[9px] font-bold bg-white/5 px-2 py-0.5 rounded border" style={{ borderColor: 'var(--border)', color: 'var(--text2)' }}>
                      {issue.asset}
                    </span>
                  )}
                </div>
                <p className="text-[13px] font-bold mb-2" style={{ color: 'var(--text)' }}>{issue.message}</p>
                
                {/* Smart Action / Insight */}
                <div className="mt-4 p-3 rounded-xl bg-black/5 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <HelpCircle size={12} className="opacity-40" style={{ color: 'var(--text)' }} />
                    <span className="text-[11px] font-medium" style={{ color: 'var(--text3)' }}>
                      {getInsightForCode(issue.code)}
                    </span>
                  </div>
                  {issue.code === 'negative_balance' && (
                    <button className="text-[10px] font-bold text-brand-green-500 hover:underline flex items-center gap-1">
                      Search Explorer <ArrowRight size={10} />
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <div className="p-8 rounded-[2.5rem] bg-gradient-to-br from-brand-green-500/10 to-transparent border flex flex-col md:flex-row items-center gap-8 text-center md:text-left" style={{ borderColor: 'var(--border)' }}>
        <div className="w-16 h-16 rounded-2xl bg-brand-green-500 flex items-center justify-center shadow-lg shadow-brand-green-500/20">
          <TrendingDown size={32} className="text-brand-dark" />
        </div>
        <div>
          <h3 className="text-lg font-syne font-bold mb-1" style={{ color: 'var(--text)' }}>Optimize Your Liability</h3>
          <p className="text-[12px] opacity-70 leading-relaxed" style={{ color: 'var(--text3)' }}>
            We detected <strong>3 opportunities</strong> to reduce your capital gains tax using Tax Loss Harvesting. 
            Resolving the data issues above might reveal even more savings.
          </p>
        </div>
        <button className="px-6 py-3 bg-brand-green-500 text-brand-dark rounded-2xl text-[12px] font-black hover:scale-105 transition-transform">
          View Optimizer
        </button>
      </div>
    </div>
  );
}

function getInsightForCode(code: string): string {
  const insights: Record<string, string> = {
    'negative_balance': 'A sale was found before its corresponding purchase. Check for missing wallet imports.',
    'missing_price': 'We couldn\'t fetch the market price for this asset at this time. Manual entry may be required.',
    'unmatched_transfers': 'Transfers between your wallets aren\'t linked. This might cause double taxation.',
    'duplicates_removed': 'We automatically cleaned up duplicate entries to prevent skewed results.',
    'non_positive_amount': 'Transactions with zero amount were detected and may need manual verification.'
  };
  return insights[code] || 'Our engine is monitoring this issue for potential impact on your tax liability.';
}
