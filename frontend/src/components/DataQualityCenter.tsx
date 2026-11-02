import { useState, useMemo, useEffect } from 'react';
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
  Sparkles,
  Clock
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import apiV1 from '../api/v1';
import { SkeletonStatCards, SkeletonTable, SkeletonText } from './ui/Skeleton';

interface Issue {
  id: string | number;
  severity: 'error' | 'warning' | 'info' | string;
  message: string;
  asset?: string;
  code: string;
}

export function DataQualityCenter() {
  const { analyzeResult, backendOnline, dataVersion } = useAppContext();
  const [analysisSnapshot, setAnalysisSnapshot] = useState(analyzeResult);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (analyzeResult) {
      setAnalysisSnapshot(analyzeResult);
    }
  }, [analyzeResult]);

  useEffect(() => {
    let active = true;

    async function loadLatestAnalysis() {
      if (!backendOnline) {
        if (active) {
          setAnalysisSnapshot(analyzeResult);
          setLoading(false);
        }
        return;
      }

      setLoading(true);
      try {
        const latest = await apiV1.analysis.getTaxAnalysis();
        if (active) {
          setAnalysisSnapshot(latest ?? analyzeResult);
        }
      } catch {
        if (active) {
          setAnalysisSnapshot(analyzeResult);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadLatestAnalysis();
    return () => {
      active = false;
    };
  }, [backendOnline, dataVersion, analyzeResult]);

  const stats = useMemo(() => {
    if (!analysisSnapshot) return { errors: 0, warnings: 0, info: 0, total: 0 };
    return {
      errors: analysisSnapshot.issues?.filter((i: any) => i.severity === 'error').length || 0,
      warnings: analysisSnapshot.issues?.filter((i: any) => i.severity === 'warning').length || 0,
      info: analysisSnapshot.issues?.filter((i: any) => i.severity === 'info').length || 0,
      total: analysisSnapshot.issues?.length || 0
    };
  }, [analysisSnapshot]);

  const issues: Issue[] = useMemo(() => {
    return analysisSnapshot?.issues?.map((i: any) => ({
      id: i.id,
      severity: i.severity,
      message: i.description,
      asset: i.asset,
      code: i.issue_type
    })) || [];
  }, [analysisSnapshot]);

  if (loading) {
    return (
      <div className="space-y-6 animate-in fade-in duration-500">
        <SkeletonText lines={2} className="w-[280px]" />
        <SkeletonStatCards />
        <SkeletonTable rows={4} />
      </div>
    );
  }

  if (stats.total === 0 || !analysisSnapshot) {
    return (
      <div className="space-y-[64px] animate-in fade-in duration-700">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-[16px]">
          <div className="p-[24px] rounded-[16px] flex items-center gap-[20px] shadow-[var(--card-shadow)]" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
            <div className="text-[#ff4d6a] opacity-80">
              <AlertTriangle size={20} />
            </div>
            <div>
              <p className="text-[20px] font-black leading-none mb-[8px]" style={{ color: 'var(--text)' }}> — </p>
              <p className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--text3)' }}>Open Issues</p>
            </div>
          </div>

          <div className="p-[24px] rounded-[16px] flex items-center gap-[20px] shadow-[var(--card-shadow)]" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
            <div className="text-[#F3BA2F] opacity-80">
              <Clock size={20} />
            </div>
            <div>
              <p className="text-[20px] font-black leading-none mb-[8px]" style={{ color: 'var(--text)' }}> — </p>
              <p className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--text3)' }}>In Review</p>
            </div>
          </div>

          <div className="p-[24px] rounded-[16px] flex items-center gap-[20px] shadow-[var(--card-shadow)]" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
            <div className="text-[var(--accent)] opacity-80">
              <CheckCircle2 size={20} />
            </div>
            <div>
              <p className="text-[20px] font-black leading-none mb-[8px]" style={{ color: 'var(--text)' }}> — </p>
              <p className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--text3)' }}>Resolved</p>
            </div>
          </div>
        </div>

        {/* Center Visual */}
        <div className="flex flex-col items-center justify-center text-center max-w-[600px] mx-auto">
          <div className="w-[96px] h-[96px] rounded-[24px] flex items-center justify-center mb-[40px] shadow-[var(--card-shadow)]" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
            <CheckCircle2 size={40} style={{ color: 'var(--text2)' }} />
          </div>

          <h2 className="font-syne font-black text-[32px] mb-[16px] tracking-tight" style={{ color: 'var(--text)' }}>All clear — no open issues</h2>
          <p className="text-[15px] leading-relaxed mb-[48px]" style={{ color: 'var(--text3)' }}>
            Your Resolution Center is empty. Cases are automatically created when Declairo detects tax discrepancies, audit flags, or compliance issues in your portfolio.
          </p>

          <div className="flex gap-[20px] w-full">
            <button className="flex-1 flex items-center gap-[16px] p-[24px] rounded-[20px] transition-all group shadow-[var(--card-shadow)]" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(16, 185, 129,0.4)')}
              onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
            >
              <div className="w-[40px] h-[40px] rounded-[12px] bg-[rgba(16, 185, 129,0.1)] flex items-center justify-center">
                <ShieldAlert size={20} className="text-[var(--accent)]" />
              </div>
              <div className="text-left">
                <p className="text-[15px] font-bold" style={{ color: 'var(--text)' }}>Tax Dispute</p>
                <p className="text-[11px]" style={{ color: 'var(--text3)' }}>Contest a tax assessment</p>
              </div>
              <ArrowRight size={16} className="ml-auto group-hover:text-[var(--accent)]" style={{ color: 'var(--text3)' }} />
            </button>

            <button className="flex-1 flex items-center gap-[16px] p-[24px] rounded-[20px] transition-all group shadow-[var(--card-shadow)]" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(16, 185, 129,0.4)')}
              onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
            >
              <div className="w-[40px] h-[40px] rounded-[12px] bg-[rgba(16, 185, 129,0.1)] flex items-center justify-center">
                <CheckCircle2 size={20} className="text-[var(--accent)]" />
              </div>
              <div className="text-left">
                <p className="text-[15px] font-bold" style={{ color: 'var(--text)' }}>Audit Support</p>
                <p className="text-[11px]" style={{ color: 'var(--text3)' }}>Prepare audit documentation</p>
              </div>
              <ArrowRight size={16} className="ml-auto group-hover:text-[var(--accent)]" style={{ color: 'var(--text3)' }} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-[32px] animate-in fade-in duration-700">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-[16px]">
        <div className="p-[20px] rounded-[16px] flex items-center justify-between" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-[12px]">
            <div className="w-[32px] h-[32px] rounded-full bg-[rgba(255,77,106,0.1)] flex items-center justify-center">
              <ShieldAlert size={16} className="text-[#ff4d6a]" />
            </div>
            <div>
              <p className="text-[14px] font-black" style={{ color: 'var(--text)' }}>{stats.errors}</p>
              <p className="text-[10px] uppercase font-bold" style={{ color: 'var(--text3)' }}>Open Issues</p>
            </div>
          </div>
        </div>

        <div className="p-[20px] rounded-[16px] flex items-center justify-between" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-[12px]">
            <div className="w-[32px] h-[32px] rounded-full bg-[rgba(243,186,47,0.1)] flex items-center justify-center">
              <Clock size={16} className="text-[#F3BA2F]" />
            </div>
            <div>
              <p className="text-[14px] font-black" style={{ color: 'var(--text)' }}>{stats.warnings}</p>
              <p className="text-[10px] uppercase font-bold" style={{ color: 'var(--text3)' }}>In Review</p>
            </div>
          </div>
        </div>

        <div className="p-[20px] rounded-[16px] flex items-center justify-between" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-[12px]">
            <div className="w-[32px] h-[32px] rounded-full bg-[rgba(16, 185, 129,0.1)] flex items-center justify-center">
              <CheckCircle2 size={16} className="text-[var(--accent)]" />
            </div>
            <div>
              <p className="text-[14px] font-black" style={{ color: 'var(--text)' }}>{stats.info}</p>
              <p className="text-[10px] uppercase font-bold" style={{ color: 'var(--text3)' }}>Resolved</p>
            </div>
          </div>
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
              className={`p-6 rounded-[1.5rem] border flex items-start gap-5 transition-all hover:translate-x-1 ${issue.severity === 'error' ? 'bg-danger/5 border-danger/10' :
                  issue.severity === 'warning' ? 'bg-[#f0a86a]/5 border-[#f0a86a]/10' :
                    'bg-brand-green-500/5 border-brand-green-500/10'
                }`}
            >
              <div className={`mt-1 p-2 rounded-xl ${issue.severity === 'error' ? 'bg-danger/10 text-danger' :
                  issue.severity === 'warning' ? 'bg-[#f0a86a]/10 text-[#f0a86a]' :
                    'bg-brand-green-500/10 text-brand-green-500'
                }`}>
                {issue.severity === 'error' ? <ShieldAlert size={20} /> :
                  issue.severity === 'warning' ? <AlertTriangle size={20} /> :
                    <Info size={20} />}
              </div>

              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-[9px] font-black uppercase tracking-[2px] px-2 py-0.5 rounded ${issue.severity === 'error' ? 'bg-danger/10 text-danger' :
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
                <div className="mt-4 p-3 rounded-xl flex items-center justify-between" style={{ background: 'var(--card2)' }}>
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

        <div className="p-8 rounded-[2.5rem] bg-gradient-to-br from-brand-green-500/10 to-transparent border flex flex-col md:flex-row items-center gap-8 text-center md:text-left mt-[32px]" style={{ borderColor: 'var(--border)' }}>
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
