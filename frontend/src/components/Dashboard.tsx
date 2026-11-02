import { useState, useEffect, useMemo, useRef, type ReactNode } from 'react';
import {
  Download,
  Wallet,
  ArrowRight,
  Zap,
  TrendingUp,
  Shield,
  BarChart3,
  Briefcase,
  AlertCircle,
  AlertTriangle,
  ChevronRight,
  ChevronDown,
  Calendar,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useAuth } from '../auth/AuthContext';
import { useAppContext } from '../context/AppContext';
import apiV1 from '../api/v1';
import { SkeletonStatCards, SkeletonChart, SkeletonCard } from './ui/Skeleton';
import { maskValue } from '../utils/privacy';

// ─── formatting ─────────────────────────────────────────────────────────────

function fmtUsd(n: number): string {
  const sign = n < 0 ? '−' : '';
  return (
    sign +
    '$' +
    new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Math.abs(n))
  );
}

function fmtUsdSigned(n: number): string {
  const s = n > 0 ? '+' : '';
  return s + fmtUsd(n);
}

function fmtShort(n: number): string {
  const a = Math.abs(n);
  if (a >= 1_000_000) return '$' + (a / 1_000_000).toFixed(1) + 'M';
  if (a >= 1000) return '$' + (a / 1000).toFixed(1) + 'K';
  return '$' + a.toFixed(0);
}

function displayNameFromEmail(email: string | undefined): string {
  if (!email) return 'there';
  const local = email.split('@')[0] || 'there';
  const cleaned = local.replace(/[._]+/g, ' ').trim();
  return cleaned ? cleaned.charAt(0).toUpperCase() + cleaned.slice(1) : 'there';
}

function greetingPrefix(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}

const DASHBOARD_TAX_YEAR_STORAGE = 'declairo_dashboard_tax_year';

function txTimestampYear(tx: any): number | null {
  const ts = tx?.timestamp ?? tx?.created_at ?? '';
  if (!ts) return null;
  const y = new Date(ts).getFullYear();
  return Number.isFinite(y) && y > 2000 && y <= new Date().getFullYear() + 1 ? y : null;
}

/** Compute the earliest year from transactions and csv runs. */
function computeEarliestDataYear(transactions: any[], csvRuns: any[], pnlMonthlyKeys: string[]): number {
  const thisYear = new Date().getFullYear();
  let minY = thisYear;
  let found = false;

  for (const tx of transactions) {
    const y = txTimestampYear(tx);
    if (y != null) { found = true; minY = Math.min(minY, y); }
  }
  // Use pnl monthly keys (format YYYY-MM) for a more accurate lower bound
  for (const ym of pnlMonthlyKeys) {
    const y = parseInt(ym.slice(0, 4), 10);
    if (Number.isFinite(y) && y > 2000) { found = true; minY = Math.min(minY, y); }
  }
  if (!found) return thisYear;
  return minY;
}

/** Compute the latest year that actually has data (pnl monthly keys or transaction timestamps). */
function computeLatestDataYear(transactions: any[], pnlMonthlyKeys: string[]): number {
  const thisYear = new Date().getFullYear();
  let maxY = 0;

  for (const ym of pnlMonthlyKeys) {
    const y = parseInt(ym.slice(0, 4), 10);
    if (Number.isFinite(y) && y > 2000 && y <= thisYear) maxY = Math.max(maxY, y);
  }
  for (const tx of transactions) {
    const y = txTimestampYear(tx);
    if (y != null && y <= thisYear) maxY = Math.max(maxY, y);
  }
  return maxY > 0 ? maxY : thisYear;
}

function buildMonthlyData(
  transactions: any[],
  year: number,
  mode: 'gains' | 'portfolio' | 'trades',
): { name: string; v: number }[] {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const bucket = new Array(12).fill(0);

  if (mode === 'trades') {
    transactions.forEach((tx: any) => {
      const ts = tx.timestamp ?? tx.created_at ?? '';
      if (!ts) return;
      const d = new Date(ts);
      if (d.getFullYear() !== year) return;
      bucket[d.getMonth()] += 1;
    });
    return months.map((name, i) => ({ name, v: bucket[i] }));
  }

  if (mode === 'portfolio') {
    transactions.forEach((tx: any) => {
      const ts = tx.timestamp ?? tx.created_at ?? '';
      if (!ts) return;
      const d = new Date(ts);
      if (d.getFullYear() !== year) return;
      const m = d.getMonth();
      bucket[m] += Math.abs(Number(tx.value_usd ?? tx.amount_usd ?? 0) || 0);
    });
    return months.map((name, i) => ({ name, v: Math.round(bucket[i]) }));
  }

  // gains — approximate monthly realized from sells / outflows
  transactions.forEach((tx: any) => {
    const ts = tx.timestamp ?? tx.created_at ?? '';
    if (!ts) return;
    const d = new Date(ts);
    if (d.getFullYear() !== year) return;
    const m = d.getMonth();
    // Prefer realized_gain_usd (net gain after cost basis) over gross value_usd
    const value = tx.realized_gain_usd != null ? Number(tx.realized_gain_usd) : Number(tx.value_usd ?? 0);
    const type = String(tx.type ?? tx.tx_type ?? '').toLowerCase();
    if (type === 'sell' || type === 'send' || type === 'swap' || type === 'out' || type === 'withdraw') {
      bucket[m] += value;
    }
  });
  return months.map((name, i) => ({ name, v: Math.round(bucket[i]) }));
}

type PositionRow = {
  asset: string;
  quantity: number;
  current_value_usd: number;
  unrealized_pnl_pct: number;
  unrealized_pnl_usd: number;
};

const ASSET_DOT: Record<string, string> = {
  BTC: 'rgba(247,147,26,.12)',
  ETH: 'rgba(98,126,234,.12)',
  SOL: 'rgba(153,69,255,.12)',
  ADA: 'rgba(0,51,173,.10)',
  USDT: 'rgba(38,161,123,.12)',
  USDC: 'rgba(39,117,202,.12)',
};

const ASSET_FG: Record<string, string> = {
  BTC: '#f7931a',
  ETH: '#627eea',
  SOL: '#9945ff',
  ADA: '#3366dd',
  USDT: '#26a17b',
  USDC: '#2775ca',
};

function issueBadgeClass(sev: string): string {
  const s = sev.toLowerCase();
  if (s === 'high' || s === 'critical' || s === 'error') return 'bg-[rgba(240,82,82,0.12)] text-[var(--danger)]';
  if (s === 'low' || s === 'info' || s === 'ok') return 'bg-[var(--accent-dim)] text-[var(--accent)]';
  return 'bg-[rgba(245,158,11,0.12)] text-[var(--warning)]';
}

function issueBadgeLabel(sev: string): string {
  const s = sev.toLowerCase();
  if (s === 'high' || s === 'critical' || s === 'error') return 'HIGH';
  if (s === 'low' || s === 'info' || s === 'ok') return 'OK';
  return 'MED';
}

export function Dashboard({ setActiveTab }: { setActiveTab: (tab: string, subTab?: string) => void }) {
  const { user } = useAuth();
  const { backendOnline, dataVersion, isPrivacyMode, togglePrivacyMode } = useAppContext();
  const [loading, setLoading] = useState(true);
  const [chartTab, setChartTab] = useState<'gains' | 'portfolio' | 'trades'>('gains');

  const [selectedTaxYear, setSelectedTaxYearState] = useState<number>(() => {
    const thisYear = new Date().getFullYear();
    try {
      const raw = localStorage.getItem(DASHBOARD_TAX_YEAR_STORAGE);
      if (raw == null) return thisYear;
      const y = parseInt(raw, 10);
      if (Number.isFinite(y) && y >= 1900 && y <= thisYear + 1) return y;
    } catch {
      /* ignore */
    }
    return thisYear;
  });

  const setSelectedTaxYear = (y: number) => {
    setSelectedTaxYearState(y);
    try {
      localStorage.setItem(DASHBOARD_TAX_YEAR_STORAGE, String(y));
    } catch {
      /* ignore */
    }
  };

  const firstName = displayNameFromEmail(user?.email);

  const [yearDropdownOpen, setYearDropdownOpen] = useState(false);
  const yearDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (yearDropdownRef.current && !yearDropdownRef.current.contains(event.target as Node)) {
        setYearDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.addEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const [livePortfolio, setLivePortfolio] = useState({
    portfolioValue: 0,
    unrealizedPnl: 0,
    unrealizedPct: 0,
    positions: [] as PositionRow[],
  });

  const [data, setData] = useState({
    capitalGains: 0,
    capitalLosses: 0,
    totalTaxOwed: 0,
    txCount: 0,
    walletCount: 0,
    exchangeCount: 0,
    csvRunCount: 0,
    shortTerm: 0,
    longTerm: 0,
    monthlyDataFromTax: null as { gains: number[]; losses: number[] } | null,
    monthlyData: [] as { name: string; gains: number; losses: number }[],
    issues: [] as any[],
    transactions: [] as any[],
    pnlRaw: {} as Record<string, unknown>,
    earliestDataYear: null as number | null,
    latestDataYear: null as number | null,
  });

  useEffect(() => {
    if (!backendOnline) {
      return;
    }

    setLoading(true);

    (async () => {
      try {
        const [taxRes, txRes, exchangeRes, walletRes, runsRes] = await Promise.allSettled([
          apiV1.analysis.getTaxAnalysis({ tax_year: selectedTaxYear }),
          apiV1.wallet.getTransactions(undefined, 10000),
          apiV1.exchange.listMy(),
          apiV1.wallet.list(),
          apiV1.analysis.listRuns(),
        ]);

        const taxData =
          taxRes.status === 'fulfilled' && taxRes.value && typeof taxRes.value === 'object'
            ? (taxRes.value as Record<string, any>)
            : {};
        const transactions =
          txRes.status === 'fulfilled' && Array.isArray(txRes.value) ? txRes.value : [];
        const exchangeConnections =
          exchangeRes.status === 'fulfilled' && Array.isArray(exchangeRes.value) ? exchangeRes.value : [];
        const walletConnectionsRaw =
          walletRes.status === 'fulfilled' && walletRes.value ? walletRes.value : [];
        const walletConnections = Array.isArray(walletConnectionsRaw)
          ? walletConnectionsRaw
          : Array.isArray(walletConnectionsRaw?.wallets)
            ? walletConnectionsRaw.wallets
            : [];
        const csvRunsRaw = runsRes.status === 'fulfilled' && runsRes.value ? runsRes.value : {};
        const csvRuns = Array.isArray(csvRunsRaw)
          ? csvRunsRaw
          : Array.isArray(csvRunsRaw?.runs)
            ? csvRunsRaw.runs
            : [];

        const pnl = (taxData.pnl && typeof taxData.pnl === 'object' ? taxData.pnl : {}) as Record<string, any>;
        const gains = Number(taxData.capital_gains ?? pnl.total_realized_pnl_usd ?? taxData.total_gain ?? 0);
        const losses = Number(
          taxData.capital_losses ?? pnl.total_realized_loss_usd ?? taxData.total_loss ?? 0,
        );
        const taxOwed = Number(
          taxData.total_tax_owed ?? taxData.tax_owed ?? pnl.total_tax_owed_usd ?? 0,
        );

        let shortTerm = Number(
          taxData.short_term_gains ?? pnl.short_term_gains ?? pnl.short_term_realized_usd ?? 0,
        );
        let longTerm = Number(
          taxData.long_term_gains ?? pnl.long_term_gains ?? pnl.long_term_realized_usd ?? 0,
        );
        const netPositive = Math.max(0, gains);
        if (shortTerm === 0 && longTerm === 0 && netPositive > 0) {
          shortTerm = netPositive;
        }

        let monthlyFromTax: { gains: number[]; losses: number[] } | null = null;
        let monthly: { name: string; gains: number; losses: number }[] = [];
        if (taxData.monthly_gains && Array.isArray(taxData.monthly_gains)) {
          const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
          const mg = taxData.monthly_gains as number[];
          const mls = (taxData.monthly_losses ?? []) as number[];
          monthlyFromTax = {
            gains: months.map((_, i) => Number(mg[i] ?? 0)),
            losses: months.map((_, i) => Number(mls[i] ?? 0)),
          };
          monthly = months.map((name, i) => ({
            name,
            gains: Number(mg[i] ?? 0),
            losses: Number(mls[i] ?? 0),
          }));
        } else {
          monthly = [];
        }

        const exCount = exchangeConnections.length;
        const connectedWalletCount = walletConnections.length;

        let issues: any[] = [];
        const latestRunId = csvRuns[0]?.run_id ?? csvRuns[0]?.id;
        if (typeof latestRunId === 'number') {
          try {
            const issRes = await apiV1.reconciliation.listIssues(latestRunId, false);
            const raw = (issRes as any)?.issues;
            issues = Array.isArray(raw) ? raw.filter((x: any) => !x.resolved).slice(0, 5) : [];
          } catch {
            issues = [];
          }
        }

        // Collect all YYYY-MM keys from pnl monthly dicts to find the real year range
        const pnlMonthlyKeys = [
          ...Object.keys((pnl.monthly_gains as Record<string,unknown>) || {}),
          ...Object.keys((pnl.monthly_losses as Record<string,unknown>) || {}),
        ];
        const earliestDataYear = computeEarliestDataYear(transactions, csvRuns, pnlMonthlyKeys);
        const latestDataYear = computeLatestDataYear(transactions, pnlMonthlyKeys);

        setData({
          capitalGains: gains,
          capitalLosses: losses,
          totalTaxOwed: taxOwed,
          txCount: transactions.length,
          walletCount: connectedWalletCount,
          exchangeCount: exCount,
          csvRunCount: csvRuns.length,
          shortTerm,
          longTerm,
          monthlyDataFromTax: monthlyFromTax,
          monthlyData: monthly,
          issues,
          transactions,
          pnlRaw: pnl,
          earliestDataYear,
          latestDataYear,
        });
      } catch (err) {
        console.error('Dashboard fetch error:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, [backendOnline, dataVersion, selectedTaxYear]);

  const applyPortfolioPayload = (portfolioPayload: Record<string, any>) => {
    const positionsRaw = Array.isArray(portfolioPayload.positions) ? portfolioPayload.positions : [];
    const positions: PositionRow[] = positionsRaw
      .map((p: any) => ({
        asset: String(p.asset ?? p.symbol ?? '').toUpperCase() || '—',
        quantity: Number(p.quantity ?? 0),
        current_value_usd: Number(p.current_value_usd ?? p.value_usd ?? 0),
        unrealized_pnl_pct: Number(p.unrealized_pnl_pct ?? 0),
        unrealized_pnl_usd: Number(p.unrealized_pnl_usd ?? 0),
      }))
      .sort((a, b) => b.current_value_usd - a.current_value_usd);

    setLivePortfolio({
      portfolioValue: Number(
        portfolioPayload.total_current_value_usd ?? portfolioPayload.total_value_usd ?? 0,
      ),
      unrealizedPnl: Number(
        portfolioPayload.total_unrealized_pnl_usd ?? portfolioPayload.unrealized_pnl?.amount_usd ?? 0,
      ),
      unrealizedPct: Number(
        portfolioPayload.total_unrealized_pnl_pct ?? portfolioPayload.unrealized_pnl?.percentage ?? 0,
      ),
      positions,
    });
  };

  const portfolioPollLive = useMemo(() => {
    const thisYear = new Date().getFullYear();
    return selectedTaxYear >= thisYear || selectedTaxYear === (data.latestDataYear ?? thisYear);
  }, [selectedTaxYear, data.latestDataYear]);

  // Portfolio snapshot for the selected tax year; live price polling only for the current/latest year.
  useEffect(() => {
    if (!backendOnline) return;

    let cancelled = false;

    const refreshPortfolio = async () => {
      try {
        const portfolioPayload = (await apiV1.portfolio.getSummary({
          tax_year: selectedTaxYear,
        })) as Record<string, any>;
        if (!cancelled) applyPortfolioPayload(portfolioPayload);
      } catch {
        // ignore transient polling errors
      }
    };

    refreshPortfolio();
    if (!portfolioPollLive) {
      return () => {
        cancelled = true;
      };
    }

    const intervalId = window.setInterval(refreshPortfolio, 1000);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [backendOnline, dataVersion, selectedTaxYear, portfolioPollLive]);

  const yearOptions = useMemo(() => {
    const thisYear = new Date().getFullYear();
    const minY = data.earliestDataYear ?? thisYear;
    const maxY = data.latestDataYear ?? thisYear;
    const lo = Math.min(minY, maxY);
    const hi = Math.max(minY, maxY);
    const out: number[] = [];
    for (let y = hi; y >= lo; y--) out.push(y);
    return out;
  }, [data.earliestDataYear, data.latestDataYear]);

  // Clamp selectedTaxYear to the available range whenever data loads
  useEffect(() => {
    if (loading || yearOptions.length === 0) return;
    const hi = yearOptions[0];
    const lo = yearOptions[yearOptions.length - 1];
    if (selectedTaxYear > hi || selectedTaxYear < lo) {
      setSelectedTaxYear(Math.min(hi, Math.max(lo, selectedTaxYear)));
    }
  }, [loading, yearOptions, selectedTaxYear]);

  // Auto-select the latest year with actual data when no saved preference
  useEffect(() => {
    if (loading || data.latestDataYear == null) return;
    const hasSavedYear = localStorage.getItem(DASHBOARD_TAX_YEAR_STORAGE) !== null;
    if (!hasSavedYear && selectedTaxYear !== data.latestDataYear) {
      setSelectedTaxYear(data.latestDataYear);
    }
  }, [loading, data.latestDataYear]);

  const yearlyMetrics = useMemo(() => {
    const months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
    let gains = 0;
    let losses = 0;
    let taxOwed = 0;
    let shortTerm = 0;
    let longTerm = 0;
    
    const monthlyGainsList: number[] = [];
    const monthlyLossesList: number[] = [];
    const monthlyList: { name: string; gains: number; losses: number; tax: number }[] = [];
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    const pnl = data.pnlRaw || {};
    const mg = (pnl.monthly_gains || {}) as Record<string, number>;
    const ml = (pnl.monthly_losses || {}) as Record<string, number>;
    const mt = (pnl.monthly_tax_owed || {}) as Record<string, number>;
    const mst = (pnl.monthly_short_term || {}) as Record<string, number>;
    const mlt = (pnl.monthly_long_term || {}) as Record<string, number>;
    
    for (let i = 0; i < 12; i++) {
      const ym = `${selectedTaxYear}-${months[i]}`;
      const g = Number(mg[ym] ?? 0);
      const l = Number(ml[ym] ?? 0);
      const t = Number(mt[ym] ?? 0);
      const st = Number(mst[ym] ?? 0);
      const lt = Number(mlt[ym] ?? 0);
      
      gains += g;
      losses += l;
      taxOwed += t;
      shortTerm += st;
      longTerm += lt;
      
      monthlyGainsList.push(g);
      monthlyLossesList.push(l);
      monthlyList.push({
        name: monthNames[i],
        gains: g,
        losses: l,
        tax: t,
      });
    }
    
    // Fallback: if no monthly breakdown for selected year, compute from transactions
    const hasMonthlyData = monthlyList.some((r) => r.gains !== 0 || r.losses !== 0 || r.tax !== 0);
    if (!hasMonthlyData) {
      // For latest year, use all-time totals as fallback
      if (selectedTaxYear === data.latestDataYear) {
        gains = data.capitalGains;
        losses = data.capitalLosses;
        taxOwed = data.totalTaxOwed;
        shortTerm = data.shortTerm;
        longTerm = data.longTerm;
      } else {
        // For historical years, compute from transactions in that year
        let txGains = 0;
        let txLosses = 0;
        data.transactions.forEach((tx: any) => {
          const y = txTimestampYear(tx);
          if (y !== selectedTaxYear) return;
          // Prefer realized_gain_usd (net gain after cost basis) over gross value_usd
          const val = tx.realized_gain_usd != null ? Number(tx.realized_gain_usd) : Number(tx.value_usd ?? 0);
          const type = String(tx.type ?? tx.tx_type ?? '').toLowerCase();
          if (type === 'sell' || type === 'send' || type === 'swap' || type === 'out' || type === 'withdraw') {
            if (val > 0) txGains += val;
            else txLosses += Math.abs(val);
          }
        });
        gains = txGains - txLosses;
        losses = txLosses;
        taxOwed = Math.max(0, gains) * 0.15;
      }
    }

    // Fallback for short/long term: only for latest year to avoid mixing all-time data with historical years
    const hasStLtData = shortTerm !== 0 || longTerm !== 0;
    if (!hasStLtData && gains !== 0 && selectedTaxYear === data.latestDataYear) {
      shortTerm = data.shortTerm;
      longTerm = data.longTerm;
    }

    const netRealized = hasMonthlyData ? gains - losses : gains;
    const apiTax = Number(pnl.total_tax_owed_usd);
    const resolvedTax =
      Number.isFinite(apiTax) && (apiTax > 0 || netRealized <= 0)
        ? apiTax
        : Math.max(0, netRealized) * 0.15;

    return {
      capitalGains: netRealized,
      capitalLosses: losses,
      totalTaxOwed: resolvedTax,
      shortTermGains: shortTerm,
      longTermGains: longTerm,
      monthlyDataFromTax: { gains: monthlyGainsList, losses: monthlyLossesList },
      monthlyData: monthlyList,
    };
  }, [selectedTaxYear, data.pnlRaw, data.capitalGains, data.capitalLosses, data.totalTaxOwed, data.shortTerm, data.longTerm, data.latestDataYear]);

  // (duplicate effect removed — handled above)

  const chartHasTaxMonthly = useMemo(
    () => yearlyMetrics.monthlyData.some((row) => row.gains !== 0 || row.losses !== 0 || (row.tax ?? 0) !== 0),
    [yearlyMetrics.monthlyData],
  );

  const chartData = useMemo(() => {
    if (chartTab === 'gains' && chartHasTaxMonthly) {
      return yearlyMetrics.monthlyData.map((row) => ({
        name: row.name,
        gains: row.gains,
        losses: row.losses,
        net: row.gains - row.losses,
        tax: row.tax ?? 0,
        v: row.gains - row.losses,
      }));
    }

    return buildMonthlyData(data.transactions, selectedTaxYear, chartTab);
  }, [chartTab, chartHasTaxMonthly, yearlyMetrics.monthlyData, data.transactions, selectedTaxYear]);

  const topAssets = useMemo(() => livePortfolio.positions.slice(0, 5), [livePortfolio.positions]);
  const maxAssetVal = useMemo(() => Math.max(...topAssets.map((a) => a.current_value_usd), 1), [topAssets]);

  const transactionsInSelectedYear = useMemo(() => {
    return data.transactions.filter((tx) => txTimestampYear(tx) === selectedTaxYear);
  }, [data.transactions, selectedTaxYear]);

  const walletsAndExchangesInYear = useMemo(() => {
    const walletIds = new Set<string>();
    const exchangeIds = new Set<string>();
    
    transactionsInSelectedYear.forEach((tx: any) => {
      // Primary: Use IDs if available
      if (tx.wallet_id) {
        walletIds.add(String(tx.wallet_id));
      }
      if (tx.connection_id) {
        exchangeIds.add(String(tx.connection_id));
      }
      
      // Fallback: Use import_format if IDs not available
      if (!tx.connection_id && tx.import_format) {
        const fmt = String(tx.import_format).toLowerCase();
        if (fmt && fmt !== 'csv' && fmt !== 'native') {
          exchangeIds.add(fmt);
        }
      }
      
      // Fallback: Count blockchain addresses as wallets
      if (!tx.wallet_id && tx.source_method === 'wallet') {
        if (tx.from_address) walletIds.add(String(tx.from_address));
        if (tx.to_address) walletIds.add(String(tx.to_address));
      }
    });
    
    return {
      walletCount: walletIds.size,
      exchangeCount: exchangeIds.size,
    };
  }, [transactionsInSelectedYear, selectedTaxYear]);

  const recentActivity = useMemo(() => {
    const rows = [...transactionsInSelectedYear].sort(
      (a, b) =>
        new Date(b.timestamp || b.created_at || 0).getTime() -
        new Date(a.timestamp || a.created_at || 0).getTime(),
    );
    return rows.slice(0, 5);
  }, [transactionsInSelectedYear]);

  const donut = useMemo(() => {
    let lossMag = Math.max(0, yearlyMetrics.capitalLosses, yearlyMetrics.capitalGains < 0 ? Math.abs(yearlyMetrics.capitalGains) : 0);
    let st = Math.max(0, yearlyMetrics.shortTermGains);
    let lt = Math.max(0, yearlyMetrics.longTermGains);
    const estTax = Math.max(0, yearlyMetrics.totalTaxOwed);
    
    // Ultimate fallback: if we have gains but NO st/lt split, use all gains as short-term
    if (st === 0 && lt === 0 && yearlyMetrics.capitalGains > 0) {
      st = yearlyMetrics.capitalGains;
    }
    
    const totalArc = st + lt + lossMag + estTax;
    const r = 64;
    const circ = 2 * Math.PI * r;
    const hasStLtSplit =
      yearlyMetrics.longTermGains > 0 ||
      yearlyMetrics.shortTermGains > 0 ||
      Number(data.pnlRaw.short_term_gains ?? 0) > 0 ||
      Number(data.pnlRaw.long_term_gains ?? 0) > 0;
    type Seg = { color: string; len: number; label: string; val: number };
    const segments: Seg[] = [];
    if (st > 0) {
      const len = totalArc > 0 ? (st / totalArc) * circ : 0;
      segments.push({
        color: 'var(--accent)',
        len,
        label: hasStLtSplit ? 'Short-term' : 'Realized',
        val: st,
      });
    }
    if (lt > 0) {
      const len = totalArc > 0 ? (lt / totalArc) * circ : 0;
      segments.push({ color: 'var(--blue)', len, label: 'Long-term', val: lt });
    }
    if (lossMag > 0) {
      const len = totalArc > 0 ? (lossMag / totalArc) * circ : 0;
      segments.push({ color: 'var(--danger)', len, label: 'Losses', val: -lossMag });
    }
    if (estTax > 0) {
      const len = totalArc > 0 ? (estTax / totalArc) * circ : 0;
      segments.push({ color: 'rgba(240,82,82,0.55)', len, label: 'Est. tax', val: estTax });
    }

    const arcs = segments.map((s, i) => {
      const dasharray = `${s.len} ${circ}`;
      let dashOffset = 0;
      for (let j = 0; j < i; j++) dashOffset += segments[j].len;
      return { ...s, dasharray, dashOffset: -dashOffset };
    });

    const centerTotal = estTax > 0 ? estTax : yearlyMetrics.capitalGains;
    const centerLabel = estTax > 0 ? 'est. tax' : 'realized';
    return {
      arcs,
      circ,
      r,
      centerTotal,
      centerLabel,
      lossMag,
      segments,
      totalArc,
    };
  }, [yearlyMetrics.capitalGains, yearlyMetrics.capitalLosses, yearlyMetrics.shortTermGains, yearlyMetrics.longTermGains, yearlyMetrics.totalTaxOwed, data.pnlRaw]);

  const connectedSourceCount = data.walletCount + data.exchangeCount;
  const hasImportedData =
    data.txCount > 0 ||
    data.csvRunCount > 0 ||
    data.capitalGains !== 0 ||
    data.capitalLosses !== 0 ||
    livePortfolio.portfolioValue > 0;
  const hasData = connectedSourceCount > 0 || hasImportedData;

  const reportSubtitle =
    data.txCount > 0
      ? `${transactionsInSelectedYear.length.toLocaleString()} transactions in ${selectedTaxYear} · ${fmtUsd(yearlyMetrics.totalTaxOwed)} est. tax (latest analysis) · ${data.csvRunCount > 0 ? 'Analysis on file' : 'Sync your data for reports'}`
      : 'Connect data to process transactions and generate your report.';

  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonStatCards />
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-4">
          <SkeletonChart />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="flex flex-col items-center justify-center py-[40px] text-center animate-in fade-in zoom-in duration-500">
        <div
          className="flex items-center gap-[6px] px-[12px] py-[6px] rounded-full border text-[10px] font-bold uppercase tracking-[1px] mb-[24px]"
          style={{ background: 'var(--accent-dim)', borderColor: 'var(--border)', color: 'var(--accent)' }}
        >
          <div className="w-[6px] h-[6px] rounded-full bg-[var(--accent)] animate-pulse" />
          Welcome to Declairo
        </div>
        <h1 className="font-syne font-bold text-[36px] leading-tight mb-[16px] max-w-[600px]" style={{ color: 'var(--text)' }}>
          Your crypto tax dashboard <br />
          <span className="text-[var(--accent)]">is ready — add your data</span>
        </h1>
        <p className="text-[14px] leading-relaxed mb-[32px] max-w-[540px]" style={{ color: 'var(--text2)' }}>
          Connect wallets or exchanges and Declairo will calculate your taxes and generate reports.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-[16px] w-full max-w-[900px]">
          <div
            className="rounded-[14px] border p-[24px] text-left group cursor-pointer transition-all"
            style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
            onClick={() => setActiveTab('integrations', 'WALLETS')}
          >
            <Wallet className="text-[var(--accent)] mb-4" size={28} />
            <h3 className="text-[15px] font-bold" style={{ color: 'var(--text)' }}>
              Connect wallets
            </h3>
            <button className="text-[12px] font-bold text-[var(--accent)] mt-4 flex items-center gap-2">
              Add Wallet <ArrowRight size={14} />
            </button>
          </div>
          <div
            className="rounded-[14px] border p-[24px] text-left group cursor-pointer transition-all"
            style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
            onClick={() => setActiveTab('integrations', 'EXCHANGES')}
          >
            <Zap className="text-[var(--accent)] mb-4" size={28} />
            <h3 className="text-[15px] font-bold" style={{ color: 'var(--text)' }}>
              Link exchanges
            </h3>
            <button className="text-[12px] font-bold text-[var(--accent)] mt-4 flex items-center gap-2">
              Connect API <ArrowRight size={14} />
            </button>
          </div>
          <div
            className="rounded-[14px] border p-[24px] text-left group cursor-pointer transition-all"
            style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
            onClick={() => setActiveTab('integrations', 'EXCHANGES')}
          >
            <Download className="text-[var(--accent)] mb-4" size={28} />
            <h3 className="text-[15px] font-bold" style={{ color: 'var(--text)' }}>
              Upload history
            </h3>
            <button className="text-[12px] font-bold text-[var(--accent)] mt-4 flex items-center gap-2">
              Upload CSV <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  const issueCount = data.issues.length;
  const chartTitle =
    chartTab === 'gains'
      ? `Monthly P&L — ${selectedTaxYear}`
      : chartTab === 'portfolio'
        ? `Monthly volume (USD) — ${selectedTaxYear}`
        : `Trades per month — ${selectedTaxYear}`;

  return (
    <div className="max-w-[1280px] mx-auto pb-16 space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-syne text-[22px] font-bold tracking-tight" style={{ color: 'var(--text)' }}>
              {greetingPrefix()}, {firstName}
            </h1>
          </div>
          <p className="text-[13px] mt-1" style={{ color: 'var(--text2)' }}>
            Here&apos;s your crypto tax summary for FY {selectedTaxYear}
          </p>
        </div>
        <div className="flex flex-col items-stretch sm:items-end gap-2 shrink-0">
          <label className="sr-only" htmlFor="dashboard-tax-year">
            Tax year
          </label>
          <div className="relative group/year" ref={yearDropdownRef}>
            <div
              className="inline-flex items-center gap-2 rounded-lg border px-2.5 py-1.5 cursor-pointer transition-colors hover:border-[var(--border)]"
              style={{ background: 'var(--bg2)', borderColor: 'var(--border2)' }}
              onClick={() => setYearDropdownOpen(!yearDropdownOpen)}
            >
              <Calendar className="w-3.5 h-3.5 shrink-0" style={{ color: 'var(--text2)' }} />
              <span className="min-w-[60px] text-[12px] font-bold" style={{ color: 'var(--text)' }}>
                FY {selectedTaxYear}
              </span>
              <ChevronDown className={`w-3.5 h-3.5 shrink-0 transition-transform ${yearDropdownOpen ? 'rotate-180' : ''}`} style={{ color: 'var(--text2)' }} />
            </div>

            {yearDropdownOpen && (
              <div
                className="absolute top-full right-0 mt-2 min-w-[140px] rounded-[10px] border overflow-hidden z-[100] shadow-[var(--card-shadow)] py-1 animate-in fade-in zoom-in-95 duration-200"
                style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
              >
                {yearOptions.map((y) => (
                  <div
                    key={y}
                    onClick={() => {
                      setSelectedTaxYear(y);
                      setYearDropdownOpen(false);
                    }}
                    className="px-3 py-2 mx-1 rounded-md text-[12px] font-bold cursor-pointer transition-colors flex items-center hover:bg-[var(--card2)]"
                    style={{
                      color: selectedTaxYear === y ? 'var(--accent)' : 'var(--text2)',
                      background: selectedTaxYear === y ? 'var(--accent-dim)' : 'transparent',
                    }}
                  >
                    FY {y}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div
            className="inline-flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-[12px] font-bold"
            style={{ background: 'var(--surface)', borderColor: 'var(--border2)', color: 'var(--text2)' }}
          >
            <span>
              Jan 1 – Dec 31, <span style={{ color: 'var(--accent)' }}>{selectedTaxYear}</span>
            </span>
          </div>
        </div>
      </div>

      {/* Report CTA */}
      <button
        type="button"
        onClick={() => setActiveTab('tax')}
        className="w-full rounded-[14px] p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 text-left border-0 cursor-pointer transition-opacity hover:opacity-[0.96]"
        style={{
          background: 'linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 75%, #000) 100%)',
        }}
      >
        <div>
          <h3 className="font-syne text-[16px] font-bold text-black">Your tax report</h3>
          <p className="text-[12px] text-black/75 mt-1 max-w-xl">{reportSubtitle}</p>
        </div>
        <span
          className="inline-flex items-center justify-center rounded-[9px] px-[18px] py-2.5 text-[13px] font-bold text-black shrink-0"
          style={{ background: 'rgba(255,255,255,0.22)', border: '1.5px solid rgba(255,255,255,0.35)' }}
        >
          Generate report →
        </span>
      </button>

      {/* KPI */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3.5">
        <KpiCard
          accentClass="after:bg-[var(--accent)]"
          label="Realized P&L"
          value={maskValue(fmtUsd(yearlyMetrics.capitalGains), isPrivacyMode)}
          valueClass={yearlyMetrics.capitalGains >= 0 ? 'text-[var(--accent)]' : 'text-[var(--danger)]'}
          icon={<TrendingUp className="w-[15px] h-[15px]" />}
          iconWrapClass="bg-[var(--accent-dim)] text-[var(--accent)]"
          sub={
            <span className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] font-bold px-1.5 py-0.5 rounded-md bg-[var(--accent-dim)] text-[var(--accent)]">
                Net
              </span>
              <span>from your latest analysis</span>
            </span>
          }
        />
        <KpiCard
          accentClass="after:bg-[var(--danger)]"
          label="Est. tax liability"
          value={maskValue(fmtUsd(yearlyMetrics.totalTaxOwed), isPrivacyMode)}
          valueClass="text-[var(--text)]"
          icon={<Shield className="w-[15px] h-[15px]" />}
          iconWrapClass="bg-[rgba(240,82,82,0.1)] text-[var(--danger)]"
          sub={
            <span>
              {yearlyMetrics.totalTaxOwed <= 0 ? (
                <span className="text-[11px] font-bold text-[var(--text2)]">— No estimate / zero due</span>
              ) : (
                'Based on latest run'
              )}
            </span>
          }
        />
        <KpiCard
          accentClass="after:bg-[var(--warning)]"
          label="Unrealized P&L"
          value={maskValue(
            livePortfolio.unrealizedPnl >= 0
              ? fmtUsdSigned(livePortfolio.unrealizedPnl)
              : fmtUsd(livePortfolio.unrealizedPnl)
          , isPrivacyMode)}
          valueClass="text-[var(--warning)]"
          icon={<BarChart3 className="w-[15px] h-[15px]" />}
          iconWrapClass="bg-[rgba(245,158,11,0.12)] text-[var(--warning)]"
          sub={
            <span>
              {livePortfolio.unrealizedPct !== 0 ? (
                <>
                  <span
                    className={`text-[11px] font-bold ${livePortfolio.unrealizedPct >= 0 ? 'text-[var(--accent)]' : 'text-[var(--danger)]'}`}
                  >
                    {livePortfolio.unrealizedPct >= 0 ? '↑' : '↓'} {Math.abs(livePortfolio.unrealizedPct).toFixed(2)}%
                  </span>{' '}
                  on open positions
                </>
              ) : (
                `open positions · ${selectedTaxYear}`
              )}
            </span>
          }
        />
        <KpiCard
          accentClass="after:bg-[var(--blue)]"
          label="Portfolio value"
          value={maskValue(fmtUsd(livePortfolio.portfolioValue), isPrivacyMode)}
          valueClass="text-[var(--blue)]"
          icon={<Briefcase className="w-[15px] h-[15px]" />}
          iconWrapClass="bg-[rgba(0,119,255,0.1)] text-[var(--blue)]"
          sub={
            <span>
              <span className="text-[11px] font-bold text-[var(--text2)]">
                as of {selectedTaxYear}
                {portfolioPollLive ? ' · live prices' : ' · year-end prices'}
              </span>
              {' · '}
              {walletsAndExchangesInYear.exchangeCount} exchange{walletsAndExchangesInYear.exchangeCount === 1 ? '' : 's'}
              , {walletsAndExchangesInYear.walletCount} wallet{walletsAndExchangesInYear.walletCount === 1 ? '' : 's'}
            </span>
          }
        />
      </div>

      {/* Mid */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-3.5">
        <div
          className="rounded-[14px] border p-6 shadow-[var(--card-shadow)]"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
        >
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-5">
            <div>
              <div className="text-[13px] font-bold uppercase tracking-wider" style={{ color: 'var(--text2)' }}>
                Gains & losses
              </div>
              <div className="font-syne text-[15px] font-bold mt-0.5" style={{ color: 'var(--text)' }}>
                {chartTitle}
              </div>
            </div>
            <div className="flex gap-0.5 p-0.5 rounded-lg" style={{ background: 'var(--bg2)' }}>
              {(['gains', 'portfolio', 'trades'] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setChartTab(t)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-bold transition-colors ${
                    chartTab === t
                      ? 'bg-[var(--accent-dim)] text-[var(--accent)]'
                      : 'text-[var(--text3)] hover:text-[var(--text2)]'
                  }`}
                >
                  {t === 'gains' ? 'Gains' : t === 'portfolio' ? 'Volume' : 'Trades'}
                </button>
              ))}
            </div>
          </div>
          <div className="w-full overflow-x-auto no-scrollbar">
            <div className="h-[180px] min-w-[560px] md:min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              {chartTab === 'trades' ? (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.6} />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'var(--text3)', fontSize: 10 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text3)', fontSize: 10 }} width={32} />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--surface)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                  />
                  <Bar dataKey="v" fill="var(--accent)" radius={[4, 4, 0, 0]} />
                </BarChart>
              ) : chartTab === 'gains' && chartHasTaxMonthly ? (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.6} />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'var(--text3)', fontSize: 10 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text3)', fontSize: 10 }} width={44} />
                  <ReferenceLine y={0} stroke="var(--border2)" strokeWidth={1} />
                  <Tooltip
                    content={({ active, payload, label }) => {
                      if (!active || !payload?.length) return null;
                      const row = payload[0].payload as {
                        gains: number;
                        losses: number;
                        net: number;
                        tax: number;
                      };
                      return (
                        <div
                          className="rounded-lg border px-3 py-2 text-[11px] shadow-md"
                          style={{
                            background: 'var(--surface)',
                            borderColor: 'var(--border)',
                          }}
                        >
                          <div className="font-bold mb-1" style={{ color: 'var(--text)' }}>
                            {label} {selectedTaxYear}
                          </div>
                          <div className="text-[var(--accent)]">Gains: {fmtUsd(row.gains)}</div>
                          <div className="text-[var(--danger)]">Losses: {fmtUsd(row.losses)}</div>
                          <div className="font-semibold mt-1" style={{ color: 'var(--text)' }}>
                            Net: {row.net >= 0 ? fmtUsdSigned(row.net) : fmtUsd(row.net)}
                          </div>
                          {row.tax > 0 ? (
                            <div className="font-semibold mt-1 text-[var(--danger)]">
                              Est. tax: {fmtUsd(row.tax)}
                            </div>
                          ) : null}
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="net" name="Net P&L" radius={[3, 3, 0, 0]}>
                    {chartData.map((row) => (
                      <Cell
                        key={row.name}
                        fill={row.v >= 0 ? 'var(--accent)' : 'var(--danger)'}
                      />
                    ))}
                  </Bar>
                  <Bar dataKey="tax" name="Est. tax" fill="rgba(240,82,82,0.65)" radius={[3, 3, 0, 0]} />
                </BarChart>
              ) : (
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="dashPlGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" opacity={0.6} />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'var(--text3)', fontSize: 10 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text3)', fontSize: 10 }} width={44} />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--surface)',
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      fontSize: '11px',
                    }}
                  />
                  <Area type="monotone" dataKey="v" stroke="var(--accent)" strokeWidth={2} fill="url(#dashPlGrad)" dot={{ r: 3, fill: 'var(--accent)' }} />
                </AreaChart>
              )}
            </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Donut */}
        <div
          className="rounded-[14px] border p-6 shadow-[var(--card-shadow)] flex flex-col"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
        >
          <div className="text-[13px] font-bold uppercase tracking-wider" style={{ color: 'var(--text2)' }}>
            Tax breakdown
          </div>
          <div className="font-syne text-[15px] font-bold mt-0.5 mb-2" style={{ color: 'var(--text)' }}>
            {yearlyMetrics.totalTaxOwed > 0 ? 'Gains & estimated tax' : 'Gains by type'}
          </div>

          <div className="relative flex items-center justify-center my-4 min-h-[160px]">
            <svg width="160" height="160" viewBox="0 0 160 160" className="shrink-0">
              <circle cx="80" cy="80" r={donut.r} fill="none" stroke="var(--border)" strokeWidth="16" opacity={0.5} />
              {donut.totalArc > 0
                ? donut.arcs.map((a) => (
                    <circle
                      key={a.label + a.color}
                      cx="80"
                      cy="80"
                      r={donut.r}
                      fill="none"
                      stroke={a.color}
                      strokeWidth="16"
                      strokeDasharray={a.dasharray}
                      strokeDashoffset={a.dashOffset}
                      strokeLinecap="round"
                      transform="rotate(-90 80 80)"
                    />
                  ))
                : null}
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="font-syne text-[22px] font-bold" style={{ color: 'var(--text)' }}>
                {maskValue(fmtUsd(donut.centerTotal), isPrivacyMode)}
              </span>
              <span className="text-[11px]" style={{ color: 'var(--text2)' }}>
                {donut.centerLabel}
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-2 mt-auto">
            {donut.segments.length === 0 ? (
              <div className="text-center text-[12px] py-4" style={{ color: 'var(--text3)' }}>
                Run an analysis to see gain types.
              </div>
            ) : (
              donut.segments.map((s) => {
                const pct = donut.totalArc > 0 ? (Math.abs(s.val) / donut.totalArc) * 100 : 0;
                return (
                  <div
                    key={s.label}
                    className="flex items-center gap-2 px-2.5 py-2 rounded-lg"
                    style={{ background: 'var(--bg2)' }}
                  >
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: s.color }} />
                    <span className="flex-1 text-[12px] font-medium" style={{ color: 'var(--text)' }}>
                      {s.label}
                    </span>
                    <span className="text-[12px] font-bold font-mono tabular-nums" style={{ color: s.color }}>
                      {maskValue(s.val < 0 ? fmtUsd(s.val) : fmtUsd(s.val), isPrivacyMode)}
                    </span>
                    <span className="text-[11px] tabular-nums" style={{ color: 'var(--text2)' }}>
                      {pct.toFixed(1)}%
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Bottom */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5">
        {/* Holdings */}
        <div
          className="rounded-[14px] border p-5 shadow-[var(--card-shadow)]"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
        >
          <div className="mb-3">
            <div className="text-[13px] font-bold uppercase tracking-wider" style={{ color: 'var(--text2)' }}>
              Holdings
            </div>
            <div className="font-syne text-[15px] font-bold" style={{ color: 'var(--text)' }}>
              Top assets
            </div>
          </div>
          {topAssets.length === 0 ? (
            <div className="text-[12px] text-center py-8" style={{ color: 'var(--text3)' }}>
              No open positions yet. Import trades to compute holdings.
            </div>
          ) : (
            <>
              {topAssets.map((a) => {
                const bg = ASSET_DOT[a.asset] ?? 'var(--accent-dim)';
                const fg = ASSET_FG[a.asset] ?? 'var(--accent)';
                const barPct = Math.max(8, Math.round((a.current_value_usd / maxAssetVal) * 100));
                const pctChange = a.unrealized_pnl_pct;
                return (
                  <div
                    key={a.asset}
                    className="flex flex-col items-start gap-2.5 py-2.5 border-b last:border-0 sm:flex-row sm:items-center"
                    style={{ borderColor: 'var(--border)' }}
                  >
                    <div
                      className="w-8 h-9 rounded-[9px] flex items-center justify-center text-[11px] font-extrabold shrink-0"
                      style={{ background: bg, color: fg }}
                    >
                      {a.asset.slice(0, 3)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-[13px] font-bold truncate" style={{ color: 'var(--text)' }}>
                        {a.asset}
                      </div>
                      <div className="text-[11px] truncate" style={{ color: 'var(--text2)' }}>
                        {a.quantity.toLocaleString(undefined, { maximumFractionDigits: 6 })} {a.asset}
                      </div>
                      <div className="mt-1 h-[3px] rounded overflow-hidden" style={{ background: 'var(--border)' }}>
                        <div className="h-full rounded" style={{ width: `${barPct}%`, background: fg }} />
                      </div>
                    </div>
                    <div className="w-full text-left sm:w-auto sm:text-right shrink-0">
                      <div className="text-[13px] font-bold font-mono tabular-nums" style={{ color: 'var(--text)' }}>
                        {maskValue(fmtUsd(a.current_value_usd), isPrivacyMode)}
                      </div>
                      <div
                        className={`text-[11px] font-semibold ${pctChange >= 0 ? 'text-[var(--accent)]' : 'text-[var(--danger)]'}`}
                      >
                        {pctChange >= 0 ? '+' : ''}
                        {pctChange.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                );
              })}
              <button
                type="button"
                onClick={() => setActiveTab('integrations')}
                className="w-full flex min-h-[48px] items-center justify-center gap-1 pt-3 mt-1 text-[12px] font-semibold text-[var(--accent)] hover:underline"
              >
                View integrations <ChevronRight className="w-3 h-3" />
              </button>
            </>
          )}
        </div>

        {/* Issues */}
        <div
          className="rounded-[14px] border p-5 shadow-[var(--card-shadow)]"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
        >
          <div className="flex items-start justify-between gap-2 mb-3">
            <div>
              <div className="text-[13px] font-bold uppercase tracking-wider" style={{ color: 'var(--text2)' }}>
                Audit
              </div>
              <div className="font-syne text-[15px] font-bold" style={{ color: 'var(--text)' }}>
                Open issues
              </div>
            </div>
            {issueCount > 0 ? (
              <span
                className="text-[11px] font-bold px-2 py-1 rounded-full shrink-0"
                style={{ background: 'rgba(240,82,82,0.12)', color: 'var(--danger)' }}
              >
                {issueCount} issue{issueCount === 1 ? '' : 's'}
              </span>
            ) : (
              <span
                className="text-[11px] font-bold px-2 py-1 rounded-full shrink-0"
                style={{ background: 'var(--accent-dim)', color: 'var(--accent)' }}
              >
                Clear
              </span>
            )}
          </div>
          {data.issues.length === 0 ? (
            <div className="text-[12px] py-6 text-center" style={{ color: 'var(--text3)' }}>
              No open reconciliation issues on your latest run.
            </div>
          ) : (
            data.issues.map((iss) => (
              <div
                key={iss.id}
                className="flex items-center gap-2.5 py-2.5 border-b last:border-0"
                style={{ borderColor: 'var(--border)' }}
              >
                <div
                  className={`w-[30px] h-[30px] rounded-lg flex items-center justify-center shrink-0 ${issueBadgeClass(iss.severity)}`}
                >
                  {String(iss.severity).toLowerCase() === 'high' ||
                  String(iss.severity).toLowerCase() === 'critical' ? (
                    <AlertCircle className="w-3.5 h-3.5" />
                  ) : (
                    <AlertTriangle className="w-3.5 h-3.5" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] font-semibold truncate" style={{ color: 'var(--text)' }}>
                    {String(iss.issue_type ?? 'Issue').replace(/_/g, ' ')}
                  </div>
                  <div className="text-[11px] truncate mt-0.5" style={{ color: 'var(--text2)' }}>
                    {iss.asset ? `${iss.asset}` : '—'}
                    {iss.amount != null ? ` · ${iss.amount}` : ''}
                  </div>
                </div>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 ${issueBadgeClass(iss.severity)}`}>
                  {issueBadgeLabel(iss.severity)}
                </span>
              </div>
            ))
          )}
          <button
            type="button"
            onClick={() => setActiveTab('health', 'reconciliation')}
            className="w-full flex items-center justify-between mt-3 pt-3 border-t text-[12px] cursor-pointer group"
            style={{ borderColor: 'var(--border)', color: 'var(--text2)' }}
          >
            <span className="text-[var(--accent)] font-semibold group-hover:underline">Go to Resolution Center</span>
            <ChevronRight className="w-[13px] h-[13px] text-[var(--accent)]" />
          </button>
        </div>

        {/* Activity */}
        <div
          className="rounded-[14px] border p-5 shadow-[var(--card-shadow)] md:col-span-2 xl:col-span-1"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
        >
          <div className="mb-3">
            <div className="text-[13px] font-bold uppercase tracking-wider" style={{ color: 'var(--text2)' }}>
              Activity
            </div>
            <div className="font-syne text-[15px] font-bold" style={{ color: 'var(--text)' }}>
              Recent trades · FY {selectedTaxYear}
            </div>
          </div>
          {recentActivity.length === 0 ? (
            <div className="text-[12px] py-6 text-center" style={{ color: 'var(--text3)' }}>
              No transactions in FY {selectedTaxYear}.
            </div>
          ) : (
            <>
              {recentActivity.map((tx) => {
                const t = String(tx.type ?? '').toUpperCase() || 'TX';
                const tok = String(tx.token ?? tx.asset ?? '').toUpperCase() || '—';
                const src = String(tx.blockchain ?? tx.source ?? tx.source_method ?? '').toUpperCase() || '—';
                const val = Number(tx.value_usd ?? 0);
                const dt = tx.timestamp ?? tx.created_at ?? '';
                const dStr = dt ? new Date(dt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '';
                const pos = val >= 0;
                return (
                  <div
                    key={tx.id ?? `${tx.hash}-${dt}`}
                    className="flex flex-col items-start gap-2.5 py-2 border-b last:border-0 sm:flex-row sm:items-center"
                    style={{ borderColor: 'var(--border)' }}
                  >
                    <div
                      className="w-[30px] h-[30px] rounded-lg flex items-center justify-center text-[10px] font-extrabold shrink-0"
                      style={{ background: 'var(--accent-dim)', color: 'var(--accent)' }}
                    >
                      {tok.slice(0, 1)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-[12px] font-semibold truncate" style={{ color: 'var(--text)' }}>
                        {t} {tok} · {src}
                      </div>
                      <div className="text-[11px] truncate mt-0.5" style={{ color: 'var(--text2)' }}>
                        {tx.amount != null ? `${tx.amount} ${tok}` : tok}
                        {tx.source_method ? ` · ${tx.source_method}` : ''}
                      </div>
                    </div>
                    <div className="w-full text-left sm:w-auto sm:text-right shrink-0">
                      <div
                        className={`text-[12px] font-bold font-mono tabular-nums ${pos ? 'text-[var(--accent)]' : 'text-[var(--danger)]'}`}
                      >
                        {pos ? '+' : ''}
                        {maskValue(fmtUsd(val), isPrivacyMode)}
                      </div>
                      <div className="text-[10px] mt-0.5" style={{ color: 'var(--text3)' }}>
                        {dStr}
                      </div>
                    </div>
                  </div>
                );
              })}
              <button
                type="button"
                onClick={() => setActiveTab('transactions')}
                className="w-full flex min-h-[48px] items-center justify-center gap-1 pt-3 mt-1 text-[12px] font-semibold text-[var(--accent)] hover:underline"
              >
                View all transactions <ChevronRight className="w-3 h-3" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function KpiCard({
  label,
  value,
  valueClass,
  icon,
  iconWrapClass,
  sub,
  accentClass,
}: {
  label: string;
  value: string;
  valueClass: string;
  icon: ReactNode;
  iconWrapClass: string;
  sub: ReactNode;
  accentClass: string;
}) {
  return (
    <div
      className={`relative rounded-[14px] border p-5 pb-5 overflow-hidden shadow-[var(--card-shadow)] transition-all hover:-translate-y-px hover:shadow-lg after:content-[''] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[3px] after:rounded-b-[14px] ${accentClass}`}
      style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
    >
      <div className="flex items-center justify-between mb-3.5">
        <span className="text-[11px] font-bold uppercase tracking-wide" style={{ color: 'var(--text2)' }}>
          {label}
        </span>
        <div className={`w-[30px] h-[30px] rounded-lg flex items-center justify-center ${iconWrapClass}`}>{icon}</div>
      </div>
      <div className={`font-syne text-[28px] font-bold leading-none tracking-tight ${valueClass}`}>{value}</div>
      <div className="text-[11px] mt-1.5 flex items-center gap-1.5 flex-wrap" style={{ color: 'var(--text2)' }}>
        {sub}
      </div>
    </div>
  );
}
