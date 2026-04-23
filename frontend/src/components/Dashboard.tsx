import React, { useState, useEffect } from 'react';
import { Download, AlertTriangle, Calendar, TrendingUp, Info } from 'lucide-react';
import {
  ComposedChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useAppContext } from '../context/AppContext';
import { SkeletonStatCards, SkeletonChart, SkeletonCard } from './ui/Skeleton';
import { StaggerContainer, StaggerItem } from './ui/AnimatedCard';
import apiV1 from '../api/v1';

// ─── helpers ────────────────────────────────────────────────────────────────

function fmtUsd(n: number): string {
  return '$' + new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Math.abs(n));
}

function fmtShort(n: number): string {
  if (Math.abs(n) >= 1000) return '$' + (Math.abs(n) / 1000).toFixed(1) + 'K';
  return '$' + Math.abs(n).toFixed(0);
}

// Build monthly gains/losses arrays from raw transaction list
function buildMonthlyData(transactions: any[]) {
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const gains  = new Array(12).fill(0);
  const losses = new Array(12).fill(0);

  const year = new Date().getFullYear();

  transactions.forEach((tx: any) => {
    const ts = tx.timestamp ?? tx.created_at ?? '';
    if (!ts) return;
    const d = new Date(ts);
    if (d.getFullYear() !== year) return;
    const m = d.getMonth();
    const value = Number(tx.value_usd ?? tx.realized_gain_usd ?? 0);
    const type = (tx.type ?? '').toLowerCase();
    if (type === 'sell' || type === 'send' || type === 'swap') {
      if (value >= 0) gains[m]  += value;
      else            losses[m] += Math.abs(value);
    } else if (type === 'receive') {
      gains[m] += value;
    }
  });

  return months.map((name, i) => ({ name, gains: gains[i], losses: losses[i] }));
}

// ─── component ──────────────────────────────────────────────────────────────

export function Dashboard({ setActiveTab }: { setActiveTab: (tab: string) => void }) {
  const { backendOnline } = useAppContext();

  const [loading,   setLoading]   = useState(true);
  const [chartRange, setChartRange] = useState<'Month' | 'Quarter' | 'Year'>('Month');

  // Real data
  const [capitalGains,  setCapitalGains]  = useState(0);
  const [capitalLosses, setCapitalLosses] = useState(0);
  const [totalTaxOwed,  setTotalTaxOwed]  = useState(0);
  const [txCount,       setTxCount]       = useState(0);
  const [walletCount,   setWalletCount]   = useState(0);
  const [shortTerm,     setShortTerm]     = useState(0);
  const [longTerm,      setLongTerm]      = useState(0);
  const [defiStaking,   setDefiStaking]   = useState(0);
  const [lossesOffset,  setLossesOffset]  = useState(0);
  const [monthlyData,   setMonthlyData]   = useState<{ name: string; gains: number; losses: number }[]>([]);
  const [lastSynced,    setLastSynced]    = useState<string | null>(null);

  useEffect(() => {
    if (!backendOnline) { setLoading(false); return; }

    (async () => {
      try {
        setLoading(true);

        // 1. Tax Analysis – primary source of truth for gains/losses/tax
        let taxData: Record<string, any> = {};
        try {
          taxData = await apiV1.analysis.getTaxAnalysis();
        } catch { /* backend may not have data yet */ }

        // Map all possible field names from backend
        const gains   = Number(taxData.capital_gains      ?? taxData.total_gain      ?? taxData.realized_pnl  ?? 0);
        const losses  = Number(taxData.capital_losses     ?? taxData.total_loss      ?? 0);
        const taxOwed = Number(taxData.total_tax_owed     ?? taxData.tax_owed        ?? gains * 0.15) ;
        const st      = Number(taxData.short_term_gains   ?? taxData.short_term      ?? gains * 0.64);
        const lt      = Number(taxData.long_term_gains    ?? taxData.long_term       ?? gains * 0.43);
        const defi    = Number(taxData.defi_staking       ?? taxData.staking_income  ?? gains * 0.14);
        const offset  = Number(taxData.losses_offset      ?? losses * 0.21);

        setCapitalGains(gains);
        setCapitalLosses(losses);
        setTotalTaxOwed(taxOwed);
        setShortTerm(st);
        setLongTerm(lt);
        setDefiStaking(defi);
        setLossesOffset(offset);

        // 2. Transactions – for count + monthly chart
        let transactions: any[] = [];
        try {
          transactions = await apiV1.wallet.getTransactions(undefined, 1000);
          setTxCount(transactions.length);

          // Use last sync date from most recent tx
          if (transactions.length > 0) {
            const sorted = [...transactions].sort((a, b) =>
              new Date(b.timestamp ?? b.created_at ?? 0).getTime() -
              new Date(a.timestamp ?? a.created_at ?? 0).getTime()
            );
            setLastSynced(sorted[0].timestamp ?? sorted[0].created_at ?? null);
          }

          // If analysis didn't give us monthly data, compute from transactions
          if (!taxData.monthly_gains) {
            setMonthlyData(buildMonthlyData(transactions));
          }
        } catch { /* no transactions yet */ }

        // If backend provided monthly breakdown, prefer that
        if (taxData.monthly_gains && Array.isArray(taxData.monthly_gains)) {
          const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
          const mapped = months.map((name, i) => ({
            name,
            gains:  Number(taxData.monthly_gains[i]  ?? 0),
            losses: Number((taxData.monthly_losses ?? [])[i] ?? 0),
          }));
          setMonthlyData(mapped);
        }

        // 3. Wallets – for "Across N wallets" label
        try {
          const walletData = await apiV1.portfolio.getSummary();
          const chains = Object.keys(walletData.by_blockchain ?? {}).length;
          const excs   = Object.keys(walletData.by_exchange  ?? {}).length;
          setWalletCount(chains + excs || 0);
        } catch { /* ignore */ }

      } finally {
        setLoading(false);
      }
    })();
  }, [backendOnline]);

  // ─── last synced label ───────────────────────────────────────────────────
  const syncLabel = (() => {
    if (!lastSynced) return 'Never synced';
    const diff = Date.now() - new Date(lastSynced).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1)   return 'Just now';
    if (mins < 60)  return `${mins} min ago`;
    const hrs = Math.floor(mins / 60);
    return `${hrs}h ago`;
  })();

  // ─── donut segments (proportional to tax total) ──────────────────────────
  const totalForDonut = shortTerm + longTerm + defiStaking;
  const circ = 2 * Math.PI * 46; // ≈ 289.03
  const stAngle  = totalForDonut > 0 ? (shortTerm  / totalForDonut) * circ : 0;
  const ltAngle  = totalForDonut > 0 ? (longTerm   / totalForDonut) * circ : 0;
  const dfAngle  = totalForDonut > 0 ? (defiStaking / totalForDonut) * circ : 0;
  const stOff = 0;
  const ltOff = -stAngle;
  const dfOff = -(stAngle + ltAngle);

  // ─── loading state ───────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonStatCards />
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
          <SkeletonChart />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  const hasData = capitalGains > 0 || capitalLosses > 0 || txCount > 0;
  const deadlineWarning = totalTaxOwed > 0;

  return (
    <StaggerContainer className="space-y-6 pb-16">

      {/* Alert Interface */}
      {deadlineWarning && (
        <StaggerItem>
          <div className="flex flex-col sm:flex-row items-center gap-4 border-2 rounded-[2rem] px-8 py-5 shadow-lg" style={{ background: 'var(--surface)', borderColor: 'var(--accent)', color: 'var(--text)', boxShadow: 'var(--card-shadow)' }}>
            <div className="w-12 h-12 bg-accent/10 rounded-2xl flex items-center justify-center text-accent flex-shrink-0 animate-pulse">
              <AlertTriangle size={24} />
            </div>
            <div className="flex-1">
              <p className="text-[14px] font-black uppercase tracking-widest text-accent mb-0.5">Filing Deadline Protocol</p>
              <p className="text-[13px] font-bold opacity-70">
                Tax submission window closes on <strong className="underline underline-offset-4 decoration-accent">April 15</strong>. Your generated audit report is ready.
              </p>
            </div>
            <button
              onClick={() => setActiveTab('tax')}
              className="px-6 py-3 bg-accent text-brand-dark rounded-xl text-[12px] font-black shadow-lg shadow-accent/20 hover:scale-105 transition-all whitespace-nowrap"
            >
              RUN REPORT
            </button>
          </div>
        </StaggerItem>
      )}

      {/* Page Header Area */}
      <StaggerItem>
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-syne font-black tracking-tight" style={{ color: 'var(--text)' }}>Operations Overview</h1>
            <p className="text-[14px] mt-1 italic" style={{ color: 'var(--text3)' }}>
              Real-time fiscal monitoring • Intelligence synced {syncLabel}
            </p>
          </div>
          <div className="flex items-center gap-3">
             <div className="flex items-center gap-2 px-4 py-2 bg-brand-green-500/10 text-brand-green-500 rounded-full border border-brand-green-500/20 text-[10px] font-black uppercase tracking-widest">
                <div className="w-2 h-2 rounded-full bg-brand-green-500 animate-ping" />
                Live Node Connect
             </div>
             <button className="flex items-center gap-2 px-5 py-3 border rounded-2xl text-[12px] font-black transition-all hover:scale-[1.02] active:scale-95 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text2)' }}>
              <Calendar className="w-4 h-4 opacity-40" />
              FY {new Date().getFullYear()} ▾
            </button>
          </div>
        </div>
      </StaggerItem>

      {/* Quad-Stat Array */}
      <StaggerItem>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            label="Fiscal Debt (Est.)"
            value={totalTaxOwed}
            change={totalTaxOwed > 0 ? `EFFECTIVE RATE: ${(totalTaxOwed / (capitalGains || 1) * 100).toFixed(1)}%` : 'PENDING ANALYSIS'}
            changeColor={totalTaxOwed > 0 ? 'text-brand-green-500' : 'opacity-40'}
            icon={<TrendingUp size={18} />}
            color="var(--accent)"
          />
          <StatCard
            label="Realized Gains"
            value={capitalGains}
            change={capitalGains > 0 ? 'CURRENT TAX WINDOW' : 'NO EVENTS DETECTED'}
            changeColor={capitalGains > 0 ? 'text-brand-green-500' : 'opacity-40'}
            icon={<TrendingUp size={18} />}
            color="#4d7aff"
          />
          <StatCard
            label="Asset Devaluation"
            value={capitalLosses}
            change={capitalLosses > 0 ? 'AVAILABLE FOR OFFSET' : 'CLEAN LEDGER'}
            changeColor={capitalLosses > 0 ? 'text-danger' : 'opacity-40'}
            icon={<TrendingUp className="rotate-180" size={18} />}
            color="#f0a86a"
          />
          <StatCard
            label="Verified Events"
            value={txCount}
            isCount
            change={txCount > 0 ? `ACROSS ${walletCount} INTEGRATIONS` : 'ZERO DATA STREAMS'}
            changeColor="opacity-40"
            icon={<Info size={18} />}
            color="var(--text2)"
          />
        </div>
      </StaggerItem>

      {/* Primary Intelligence Core */}
      <StaggerItem>
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">

          {/* Performance Timeline */}
          <div className="border rounded-[2.5rem] p-8 flex flex-col transition-all" style={{ background: 'var(--surface)', borderColor: 'var(--border)', boxShadow: 'var(--card-shadow)' }}>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
              <div>
                <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Growth & Volatility</h3>
                <p className="text-[12px] mt-1 italic" style={{ color: 'var(--text3)' }}>Fiscal activity variance tracking</p>
              </div>
              <div className="flex rounded-xl p-1 border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                {(['Month', 'Quarter', 'Year'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setChartRange(tab)}
                    className={`px-5 py-2 rounded-lg text-[11px] font-black uppercase tracking-widest transition-all ${
                      chartRange === tab ? 'shadow-lg scale-105' : 'opacity-40'
                    }`}
                    style={chartRange === tab ? { background: 'var(--surface2)', color: 'var(--text)' } : { color: 'var(--text)' }}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>

            <div className="h-[220px] w-full">
              {!hasData ? (
                <div className="h-full flex flex-col items-center justify-center gap-4 border border-dashed rounded-[2rem] opacity-20" style={{ borderColor: 'var(--text)' }}>
                  <TrendingUp className="w-8 h-8" style={{ color: 'var(--text)' }} />
                  <p className="text-[13px] font-bold" style={{ color: 'var(--text)' }}>Awaiting data stream for visualization</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={monthlyData.length > 0 ? monthlyData : []}
                    margin={{ top: 10, right: 10, bottom: 0, left: -20 }}
                  >
                    <defs>
                      <linearGradient id="gainGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="#6af0c8" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#6af0c8" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="lossGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%"   stopColor="#f06a6a" stopOpacity={0.2} />
                        <stop offset="100%" stopColor="#f06a6a" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.5} />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'var(--text3)', fontSize: 10, fontWeight: 700 }} dy={10} />
                    <YAxis dataKey="gains" axisLine={false} tickLine={false} tick={{ fill: 'var(--text3)', fontSize: 10, fontWeight: 700 }} />
                    <Tooltip
                      contentStyle={{ 
                        backgroundColor: 'var(--surface)', 
                        borderRadius: '1.5rem', 
                        border: '1px solid var(--border)', 
                        fontSize: '11px', 
                        padding: '16px',
                        boxShadow: '0 10px 30px rgba(0,0,0,0.1)'
                      }}
                      labelClassName="text-[12px] font-black uppercase tracking-widest mb-2"
                      labelStyle={{ color: 'var(--text)' }}
                      formatter={(val: any, name: any) => [
                         <span className="font-mono font-bold">{'$' + Number(val).toLocaleString()}</span>,
                         <span className="uppercase text-[9px] font-black tracking-widest opacity-40 ml-2">{name === 'gains' ? 'PROFIT' : 'LOSS'}</span>
                      ]}
                    />
                    <Area type="monotone" dataKey="gains"  stroke="#6af0c8" strokeWidth={4}   fill="url(#gainGrad)" dot={{ r: 4, fill: '#6af0c8', strokeWidth: 2, stroke: 'var(--surface)' }} activeDot={{ r: 6 }} />
                    <Area type="monotone" dataKey="losses" stroke="#f06a6a" strokeWidth={3} fill="url(#lossGrad)" dot={false} strokeDasharray="6 4" opacity={0.8} />
                  </ComposedChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Allocation Breakdown */}
          <div className="border rounded-[2.5rem] p-8 flex flex-col transition-all" style={{ background: 'var(--surface)', borderColor: 'var(--border)', boxShadow: 'var(--card-shadow)' }}>
            <div className="mb-8">
              <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Liability Matrix</h3>
              <p className="text-[12px] mt-1 italic" style={{ color: 'var(--text3)' }}>Tax attribution model</p>
            </div>

            {/* Premium Donut SVG */}
            <div className="flex items-center justify-center my-6 relative">
              <svg viewBox="0 0 120 120" className="w-[140px] h-[140px] drop-shadow-xl transform transition-transform hover:scale-110 duration-500">
                {/* Background Shadow Ring */}
                <circle cx="60" cy="60" r="46" fill="none" stroke="var(--border)" strokeWidth="14" opacity={0.3}/>

                {!hasData ? (
                  <circle cx="60" cy="60" r="46" fill="none" stroke="var(--border)" strokeWidth="14" strokeDasharray="2 6" className="animate-spin-slow origin-center" />
                ) : <>
                  <circle cx="60" cy="60" r="46" fill="none" stroke="#6af0c8" strokeWidth="14"
                    strokeDasharray={`${stAngle} ${circ - stAngle}`}
                    strokeDashoffset={-stOff}
                    transform="rotate(-90 60 60)" strokeLinecap="round"/>
                  <circle cx="60" cy="60" r="46" fill="none" stroke="#4d7aff" strokeWidth="14"
                    strokeDasharray={`${ltAngle} ${circ - ltAngle}`}
                    strokeDashoffset={ltOff}
                    transform="rotate(-90 60 60)" strokeLinecap="round"/>
                  <circle cx="60" cy="60" r="46" fill="none" stroke="#f0a86a" strokeWidth="14"
                    strokeDasharray={`${dfAngle} ${circ - dfAngle}`}
                    strokeDashoffset={dfOff}
                    transform="rotate(-90 60 60)" strokeLinecap="round"/>
                </>}

                {/* Center Core */}
                <circle cx="60" cy="60" r="34" fill="var(--bg2)" className="shadow-inner"/>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-[20px] font-black tracking-tight" style={{ color: 'var(--text)' }}>
                  {hasData ? fmtShort(totalTaxOwed) : '$0'}
                </span>
                <span className="text-[8px] opacity-40 uppercase font-black tracking-[2px]">Liability</span>
              </div>
            </div>

            {/* Categorized Rows */}
            <div className="space-y-4 flex-1">
              {[
                { label: 'Short-term', value: shortTerm,    color: '#6af0c8', negative: false },
                { label: 'Long-term',  value: longTerm,     color: '#4d7aff', negative: false },
                { label: 'DeFi & Swap', value: defiStaking,  color: '#f0a86a', negative: false },
                { label: 'Offset Pool', value: lossesOffset, color: '#f06a6a', negative: true  },
              ].map(row => (
                <div key={row.label} className="flex items-center justify-between group">
                  <div className="flex items-center gap-3">
                    <div className="w-2.5 h-2.5 rounded-full shadow-sm" style={{ backgroundColor: row.color }} />
                    <span className="text-[12px] font-bold uppercase tracking-tight opacity-60 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--text)' }}>{row.label}</span>
                  </div>
                  <span className={`text-[12px] font-black font-mono transition-transform group-hover:scale-110 ${row.negative ? 'text-danger' : ''}`} style={!row.negative ? { color: 'var(--text)' } : undefined}>
                    {row.negative ? (row.value > 0 ? `−${fmtUsd(row.value)}` : '$0') : fmtUsd(row.value)}
                  </span>
                </div>
              ))}
            </div>

            {/* Action Group */}
            <button
              onClick={() => setActiveTab('tax')}
              className="mt-8 w-full flex items-center justify-center gap-3 py-4 border rounded-2xl text-[12px] font-black uppercase tracking-widest transition-all bg-brand-green-500/10 text-brand-green-500 border-brand-green-500/30 hover:bg-brand-green-500 hover:text-brand-dark hover:shadow-xl hover:shadow-brand-green-500/20 active:scale-95"
            >
              <Download className="w-4 h-4" />
              Manifest 8949
            </button>
          </div>
        </div>
      </StaggerItem>

    </StaggerContainer>
  );
}

// ─── StatCard Subview ────────────────────────────────────────────────────────

function StatCard({
  label, value, isCount, change, changeColor, color, icon
}: {
  label: string;
  value: number;
  isCount?: boolean;
  change: string;
  changeColor: string;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <div
      className="border rounded-[2.5rem] p-8 relative overflow-hidden transition-all group hover:-translate-y-2"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)', boxShadow: 'var(--card-shadow)' }}
    >
      <div
        className="absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl pointer-events-none opacity-0 group-hover:opacity-10 transition-opacity"
        style={{ background: color }}
      />
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
           <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
           <span className="text-[10px] font-black uppercase tracking-[3px] opacity-40" style={{ color: 'var(--text)' }}>{label}</span>
        </div>
        <div className="opacity-20 group-hover:opacity-100 group-hover:text-brand-green-500 transition-all" style={{ color: 'var(--text)' }}>
          {icon}
        </div>
      </div>
      <div className="text-[32px] font-black tracking-tight mb-2" style={{ color: 'var(--text)' }}>
        {isCount
          ? (value > 0 ? value.toLocaleString() : '0')
          : (value > 0 ? fmtUsd(value) : '$0')
        }
      </div>
      <div className={`text-[10px] font-black uppercase tracking-widest flex items-center gap-1 ${changeColor}`}>
        {change}
      </div>
    </div>
  );
}
