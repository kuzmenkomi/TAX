import { useState, useEffect } from 'react';
import { useToast } from '../context/ToastContext';
import {
  Calculator,
  FileText,
  ChevronRight,
  Zap,
  Plus,
  Globe,
  ShieldCheck,
  Download,
  Search,
  CheckCircle2,
  Clock,
  ArrowRight,
  Settings,
  Link as LinkIcon,
  Database,
  RefreshCw,
  Lock,
  AlertTriangle,
  TrendingUp,
  Sparkles,
  ChevronDown
} from 'lucide-react';
import { cn } from '../utils/cn';
import apiV1, { tax, billing } from '../api/v1';
import { useAppContext } from '../context/AppContext';
import { buildCsvImportSources } from '../utils/importSources';
import { getTaxJurisdictionConfig } from '../utils/taxJurisdictionConfig';
import { SkeletonCard, SkeletonText } from './ui/Skeleton';
import { useAuth } from '../auth/AuthContext';
import { ReviewDataPanel } from './ReviewDataPanel';
import { GenerateReportsPanel } from './GenerateReportsPanel';

// ── Plan configuration ──
const PLAN_META: Record<string, { name: string; emoji: string; limit: number; wallets: number; color: string }> = {
  free: { name: 'Free Plan', emoji: '🆓', limit: 25, wallets: 5, color: 'text-[var(--text2)]' },
  starter: { name: 'Starter Plan', emoji: '⭐', limit: 150, wallets: 15, color: 'text-[var(--accent)]' },
  trader: { name: 'Trader Plan', emoji: '📈', limit: 1000, wallets: 999, color: 'text-[#5b8dee]' },
  expert: { name: 'Expert Plan', emoji: '🏆', limit: 3000, wallets: 999, color: 'text-[#9f7aea]' },
};
const DEMO_PLANS = ['free', 'starter', 'trader', 'expert'] as const;

const COUNTRIES: Record<string, { flag: string; name: string; auth: string; rate: string; ptax: boolean }> = {
  us: { flag: '🇺🇸', name: 'United States', auth: 'IRS', rate: 'Market', ptax: false },
  mx: { flag: '🇲🇽', name: 'Mexico', auth: 'SAT', rate: 'MXN Market', ptax: false },
  br: { flag: '🇧🇷', name: 'Brazil', auth: 'Receita Federal', rate: 'PTAX Official', ptax: true },
  ar: { flag: '🇦🇷', name: 'Argentina', auth: 'ARCA', rate: 'ARS Market', ptax: false },
  co: { flag: '🇨🇴', name: 'Colombia', auth: 'DIAN', rate: 'COP Market', ptax: false },
  pe: { flag: '🇵🇪', name: 'Peru', auth: 'SUNAT', rate: 'PEN Market', ptax: false },
  cl: { flag: '🇨🇱', name: 'Chile', auth: 'SII', rate: 'CLP Market', ptax: false },
  gt: { flag: '🇬🇹', name: 'Guatemala', auth: 'SAT', rate: 'GTQ Market', ptax: false },
  ec: { flag: '🇪🇨', name: 'Ecuador', auth: 'SRI', rate: 'USD Market', ptax: false },
  uy: { flag: '🇺🇾', name: 'Uruguay', auth: 'DGI', rate: 'UYU Market', ptax: false },
  cr: { flag: '🇨🇷', name: 'Costa Rica', auth: 'Hacienda', rate: 'CRC Market', ptax: false },
  hn: { flag: '🇭🇳', name: 'Honduras', auth: 'SAR', rate: 'HNL Market', ptax: false },
  bo: { flag: '🇧🇴', name: 'Bolivia', auth: 'SIN', rate: 'BOB Market', ptax: false },
};
const CP_POPULAR = ['us', 'br', 'mx', 'ar', 'co'];
const CP_SOUTH_AMERICA = ['cl', 'pe', 'ec', 'uy', 'bo'];
const CP_CENTRAL_AMERICA = ['gt', 'cr', 'hn'];

type TaxStep = 'connect' | 'configure' | 'review' | 'export';
type TaxSource = {
  id: string;
  provider: string;
  name: string;
  transactionCount: number;
};

export function TaxHub({ setActiveTab: setGlobalTab }: { setActiveTab?: (tab: string, subTab?: any) => void }) {
  const { addToast } = useToast();
  const { refreshUser } = useAuth();
  const [activeStep, setActiveStep] = useState<TaxStep>('connect');
  const [activeTab, setActiveTab] = useState<'sources' | 'configure' | 'review' | 'reports'>('sources');
  const [integrations, setIntegrations] = useState<TaxSource[]>([]);
  const [selectedIntegrationIds, setSelectedIntegrationIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const {
    backendOnline,
    dataVersion,
    accountingMethod,
    setAccountingMethod,
    analyzeResult,
    setAnalyzeResult,
    currentJurisdiction,
    setCurrentJurisdiction,
  } = useAppContext();
  const [jurisdictionName, setJurisdictionName] = useState<string>('');
  const [regionalToggles, setRegionalToggles] = useState<Record<string, boolean>>({});
  const [geoReady, setGeoReady] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);
  const [hasConfirmedSources, setHasConfirmedSources] = useState(false);
  const [countryPanelOpen, setCountryPanelOpen] = useState(false);
  const [cpSearch, setCpSearch] = useState('');
  const [lockedTooltipMethod, setLockedTooltipMethod] = useState<string | null>(null);
  const [advancedFeaturesOpen, setAdvancedFeaturesOpen] = useState(false);
  // Plan state
  const [demoPlan, setDemoPlan] = useState<string>('starter');
  const [realPlan, setRealPlan] = useState<string | null>(null);

  const jurisdictionConfig = getTaxJurisdictionConfig(currentJurisdiction);
  const methods = jurisdictionConfig.methods;
  const countryCode = currentJurisdiction.toLowerCase();
  const countryInfo = COUNTRIES[countryCode];

  // Resolved plan: use real plan from backend if loaded, otherwise demo selection
  const activePlanKey = (realPlan && PLAN_META[realPlan]) ? realPlan : demoPlan;
  const activePlan = PLAN_META[activePlanKey];
  const selectedIntegrations = integrations.filter((item) => selectedIntegrationIds.includes(item.id));
  const totalTxns = selectedIntegrations.reduce((sum, item) => sum + (item.transactionCount ?? 0), 0);
  const willProcess = Math.min(totalTxns, activePlan.limit);
  const txBarPct = activePlan.limit > 0 ? Math.min(100, Math.round((willProcess / activePlan.limit) * 100)) : 0;
  const isOverLimit = totalTxns > activePlan.limit;

  const renderCountryRow = (code: string) => {
    const c = COUNTRIES[code];
    if (!c) return null;
    const isSelected = countryCode === code;
    return (
      <div
        key={code}
        onClick={async () => {
          try {
            const saved = await tax.setJurisdiction(code.toUpperCase());
            setCurrentJurisdiction(saved.jurisdiction_code);
            try {
              await refreshUser();
            } catch (err) {
              console.error('Failed to refresh user auth state:', err);
            }
            setCountryPanelOpen(false);
            setCpSearch('');
            addToast(`Tax rules updated for ${c.name}`, 'success');
          } catch (err) {
            addToast(err instanceof Error ? err.message : 'Failed to update jurisdiction', 'error');
          }
        }}
        className={cn(
          'flex items-center gap-2.5 px-2 py-2 rounded-lg cursor-pointer transition-colors',
          isSelected ? 'bg-[var(--accent-dim)]' : 'hover:bg-[var(--card)]'
        )}
      >
        <span className="text-[18px] leading-none">{c.flag}</span>
        <span className={cn('text-[13px] font-semibold flex-1', isSelected ? 'text-[var(--accent)]' : 'text-[var(--text)]')}>{c.name}</span>
        <span className="text-[11px] text-[var(--text3)]">{c.auth}</span>
        <div className={cn('w-4 h-4 rounded-full border flex-shrink-0 flex items-center justify-center', isSelected ? 'bg-[var(--accent)] border-[var(--accent)]' : 'border-[var(--border2)]')}>
          {isSelected && <CheckCircle2 size={9} strokeWidth={3} className="text-black" />}
        </div>
      </div>
    );
  };

  const handleStartCalculation = async () => {
    if (!backendOnline) {
      addToast('Backend is offline. Please try again later.', 'error');
      return;
    }
    if (selectedIntegrations.length === 0) {
      addToast('Select at least one connection before calculation.', 'warning');
      return;
    }

    setIsCalculating(true);
    setActiveStep('review');
    setActiveTab('review');

    try {
      const result = await apiV1.analysis.analyzeSources({
        source_ids: selectedIntegrationIds,
        accounting_method: accountingMethod,
        country: currentJurisdiction.toLowerCase(),
        use_ptax: regionalToggles.ptax ?? false,
        auto_classify: regionalToggles.auto_classify ?? false,
      });

      setAnalyzeResult(result);
      addToast('Tax calculation completed successfully!', 'success');
    } catch (err: any) {
      addToast(err.message || 'Calculation failed. Please check your source data.', 'error');
      setActiveStep('configure');
      setActiveTab('configure');
    } finally {
      setIsCalculating(false);
    }
  };

  const steps: { id: TaxStep; label: string; num: number }[] = [
    { id: 'connect', label: 'Select Sources', num: 1 },
    { id: 'configure', label: 'Tax Settings', num: 2 },
    { id: 'review', label: 'Review Data', num: 3 },
    { id: 'export', label: 'Generate Reports', num: 4 },
  ];
  const activeStepIndex = Math.max(0, steps.findIndex((step) => step.id === activeStep));
  const activeStepMeta = steps[activeStepIndex];
  const mobileProgressPct = ((activeStepIndex + 1) / steps.length) * 100;

  const refreshIntegrations = async () => {
    if (!backendOnline) {
      setIntegrations([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [exData, wData, runsData, billingData] = await Promise.allSettled([
        apiV1.exchange.listMy(),
        apiV1.wallet.list(),
        apiV1.analysis.listRuns(),
        billing.getStatus(),
      ]);

      const combined: TaxSource[] = [];

      if (exData.status === 'fulfilled' && exData.value) {
        combined.push(...exData.value.map((e: any) => ({
          id: `ex_${e.id}`,
          provider: e.exchange || e.provider || 'exchange',
          name: e.exchange_name || 'API Connection',
          transactionCount: e.transaction_count ?? 0
        })));
      }

      if (wData.status === 'fulfilled' && wData.value) {
        const wallets = Array.isArray(wData.value) ? wData.value : (wData.value?.wallets ?? []);
        combined.push(...wallets.map((w: any) => ({
          id: `w_${w.id}`,
          provider: w.chain || 'wallet',
          name: w.address,
          transactionCount: w.transaction_count ?? w.transactions_count ?? 0
        })));
      }

      if (runsData.status === 'fulfilled') {
        const csvSources = buildCsvImportSources(runsData.value?.runs ?? []);
        combined.push(...csvSources.map((source) => ({
          id: source.id,
          provider: source.provider || 'csv',
          name: source.name,
          transactionCount: source.transaction_count ?? 0
        })));
      }

      if (billingData.status === 'fulfilled' && (billingData.value as any)?.plan) {
        let p = String((billingData.value as any).plan).toLowerCase();
        if (p === 'pro') p = 'starter';
        if (p === 'business') p = 'trader';
        if (PLAN_META[p]) {
          setRealPlan(p);
          setDemoPlan(p);
        }
      }

      setIntegrations(combined);
      setSelectedIntegrationIds((prev) => {
        const availableIds = new Set(combined.map((item) => item.id));
        const preserved = prev.filter((id) => availableIds.has(id));
        return preserved.length > 0 || prev.length > 0
          ? preserved
          : combined.map((item) => item.id);
      });
      if (combined.length === 0) {
        setHasConfirmedSources(false);
        setActiveStep('connect');
        setActiveTab('sources');
      }
    } catch (err) {
      console.error("Failed to fetch integrations", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshIntegrations();
  }, [backendOnline, dataVersion]);

  useEffect(() => {
    if (selectedIntegrations.length === 0) {
      setHasConfirmedSources(false);
    }
  }, [selectedIntegrations.length]);

  useEffect(() => {
    if (!backendOnline) return;
    let cancelled = false;
    (async () => {
      try {
        const detected = await tax.autoDetectJurisdiction();
        if (cancelled) return;
        setCurrentJurisdiction(detected.jurisdiction_code);
        setJurisdictionName(detected.jurisdiction_name);
        const cfg = getTaxJurisdictionConfig(detected.jurisdiction_code);
        const defaults: Record<string, boolean> = {};
        cfg.regionalToggles.forEach((t) => {
          defaults[t.id] = t.defaultOn;
        });
        setRegionalToggles(defaults);
        setGeoReady(true);
      } catch (err) {
        console.error('Geo jurisdiction detection failed', err);
        const cfg = getTaxJurisdictionConfig(currentJurisdiction);
        setJurisdictionName(cfg.name);
        const defaults: Record<string, boolean> = {};
        cfg.regionalToggles.forEach((t) => {
          defaults[t.id] = t.defaultOn;
        });
        setRegionalToggles(defaults);
        setGeoReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [backendOnline]);

  useEffect(() => {
    const cfg = getTaxJurisdictionConfig(currentJurisdiction);
    setJurisdictionName(cfg.name);
    setRegionalToggles((prev) => {
      const next = { ...prev };
      cfg.regionalToggles.forEach((t) => {
        if (next[t.id] === undefined) next[t.id] = t.defaultOn;
      });
      return next;
    });

    // Auto-select the required or recommended method for the selected jurisdiction
    if (currentJurisdiction.toLowerCase() === 'br') {
      setAccountingMethod('WEIGHTED_AVERAGE');
    } else {
      setAccountingMethod('FIFO');
    }
  }, [currentJurisdiction]);

  if (loading && integrations.length === 0) {
    return (
      <div className="space-y-6 animate-fade-in w-full">
        <div className="flex items-center justify-between gap-4">
          <SkeletonText lines={2} className="w-[280px]" />
          <div className="w-[280px] h-[46px] rounded-xl animate-pulse" style={{ background: 'var(--card2)' }} />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, idx) => (
            <SkeletonCard key={idx} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <SkeletonText lines={3} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: 4 }).map((_, idx) => (
                <SkeletonCard key={idx} />
              ))}
            </div>
          </div>
          <SkeletonCard />
        </div>
      </div>
    );
  }

  // ── Step progress bar (redesign style) ──────────────────────────────────────
  const renderProgress = () => {
    const activeIdx = steps.findIndex(s => s.id === activeStep);
    const calculationComplete = !!analyzeResult;
    return (
      <div className="flex items-center gap-0 px-1 mb-6">
        {steps.map((step, idx) => {
          const isDone = idx < activeIdx;
          const isActive = idx === activeIdx;
          const isConfigureLocked = step.id === 'configure' && !hasConfirmedSources;
          const isLocked =
            isConfigureLocked ||
            ((step.id === 'review' || step.id === 'export') && !calculationComplete && !isCalculating);

          return (
            <div key={step.id} className="flex items-center">
              <div
                onClick={() => {
                  if (isLocked) {
                    addToast(
                      isConfigureLocked
                        ? 'Tax Settings will unlock after you click CONFIRM & PROCEED.'
                        : 'Please run Start Calculation first',
                      "warning"
                    );
                    return;
                  }
                  if (step.id === 'connect') { 
                    setActiveStep('connect'); 
                    setActiveTab('sources'); 
                  } else if (step.id === 'configure') { 
                    setActiveStep('configure'); 
                    setActiveTab('configure'); 
                  } else if (step.id === 'review') {
                    setActiveStep('review');
                    setActiveTab('review');
                  } else if (step.id === 'export') { 
                    setActiveStep('export'); 
                    setActiveTab('reports'); 
                  }
                }}
                className={cn(
                  'flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer transition-all duration-150 select-none',
                  isActive
                    ? 'bg-[var(--accent-dim)] text-[var(--accent)]'
                    : isDone
                    ? 'text-[var(--text3)] hover:text-[var(--text2)]'
                    : 'text-[var(--text3)] hover:text-[var(--text2)]',
                  isLocked && 'opacity-50 cursor-not-allowed'
                )}
              >
                <div className={cn(
                  'w-[22px] h-[22px] rounded-full border-2 flex items-center justify-center flex-shrink-0 text-[10px] font-bold',
                  isActive
                    ? 'bg-[var(--accent)] border-[var(--accent)] text-black'
                    : isDone
                    ? 'bg-[var(--card2)] border-[var(--accent)]/40 text-[var(--accent)]'
                    : 'border-[var(--border2)] text-[var(--text3)]'
                  )}
                  style={!isActive && !isDone ? { background: 'var(--card2)' } : undefined}
                >
                  {isLocked ? <Lock size={10} /> : (isDone ? '✓' : step.num)}
                </div>
                <span className={cn('text-[12px] font-semibold whitespace-nowrap', isLocked && 'text-[var(--text3)]')}>{step.label}</span>
              </div>
              {idx < steps.length - 1 && (
                <div
                  className="w-12 h-px flex-shrink-0 mx-0"
                  style={{
                    background: isDone
                      ? 'var(--accent-dim)'
                      : 'var(--border)',
                    borderTop: isDone ? '1px dashed var(--accent-soft)' : undefined,
                  }}
                />
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const toggleIntegrationSelection = (sourceId: string) => {
    setSelectedIntegrationIds((prev) =>
      prev.includes(sourceId)
        ? prev.filter((id) => id !== sourceId)
        : [...prev, sourceId]
    );
  };

  return (
    <div className="tax-center-page space-y-0 animate-fade-in w-full pb-24 md:pb-0">
      {/* ── Header ── */}
      <div className="flex items-center justify-between gap-4 mb-5">
        <div>
          <h1 className="font-syne font-extrabold text-[28px] tracking-tight text-[var(--text)] mb-0.5">Tax Center</h1>
          <p className="text-[13px] text-[var(--text2)]">Configure your tax calculation settings</p>
        </div>
      </div>

      <div className="mb-5 md:hidden">
        <div className="text-[13px] font-bold text-[var(--text)]">
          Step {activeStepMeta.num} of {steps.length}: {activeStepMeta.label}
        </div>
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-[var(--card2)]">
          <div className="h-full rounded-full bg-[var(--accent)] transition-all" style={{ width: `${mobileProgressPct}%` }} />
        </div>
      </div>

      {/* ── Step Progress Bar ── */}
      <div className="hidden md:block">{renderProgress()}</div>

      {/* ── Panels ── */}
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">

        {/* ── Step 1: Active Sources ── */}
        {activeTab === 'sources' && (
          <div
            className="rounded-[16px] overflow-hidden"
            style={{ background: 'var(--card)', border: '1px solid var(--border)' }}
          >
            {/* Card Header */}
            <div className="flex items-center gap-3 p-5 pb-4 border-b border-[var(--border)]">
              <div
                className="w-9 h-9 rounded-[9px] flex items-center justify-center flex-shrink-0"
                style={{ background: 'var(--accent-dim)', border: '1px solid var(--accent-soft)' }}
              >
                <Database size={16} className="text-[var(--accent)]" />
              </div>
              <div className="flex-1">
                <h3 className="font-syne font-bold text-[16px] text-[var(--text)] leading-tight">Select Calculation Sources</h3>
                <p className="text-[12px] text-[var(--text2)] mt-0.5">We've synced your connections from the main hub</p>
              </div>
              <button
                onClick={refreshIntegrations}
                className="flex items-center gap-1.5 text-[11px] font-bold text-[var(--text2)] hover:text-[var(--accent)] transition-colors"
              >
                <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> Sync Now
              </button>
            </div>

            <div className="p-6">
              {integrations.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <p className="text-[10px] font-black uppercase tracking-widest text-[var(--text3)]">
                      Selected Connections ({selectedIntegrations.length}/{integrations.length})
                    </p>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setSelectedIntegrationIds(integrations.map((item) => item.id))}
                        className="text-[11px] font-bold px-3 py-1.5 rounded-lg transition-all"
                        style={{ background: 'var(--card2)', color: 'var(--text2)', border: '1px solid var(--border)' }}
                      >
                        Select All
                      </button>
                      <button
                        type="button"
                        onClick={() => setSelectedIntegrationIds([])}
                        className="text-[11px] font-bold px-3 py-1.5 rounded-lg transition-all"
                        style={{ background: 'var(--card2)', color: 'var(--text2)', border: '1px solid var(--border)' }}
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                  <p className="text-[12px] text-[var(--text2)]">
                    Choose which connections should be included in this tax calculation.
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {integrations.map((intg) => (
                      <button
                        type="button"
                        key={intg.id}
                        className="flex items-center justify-between p-3.5 rounded-[10px] cursor-pointer group transition-all text-left w-full"
                        style={{
                          background: selectedIntegrationIds.includes(intg.id) ? 'var(--accent-dim)' : 'var(--card2)',
                          border: selectedIntegrationIds.includes(intg.id) ? '1px solid var(--accent-soft)' : '1px solid var(--border)'
                        }}
                        onClick={() => toggleIntegrationSelection(intg.id)}
                        onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--accent-soft)')}
                        onMouseLeave={e => (e.currentTarget.style.borderColor = selectedIntegrationIds.includes(intg.id) ? 'var(--accent-soft)' : 'var(--border)')}
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className="w-9 h-9 rounded-[8px] flex items-center justify-center font-bold text-[var(--text)] text-[13px]"
                            style={{ background: 'var(--card3)' }}
                          >
                            {intg.provider?.[0]?.toUpperCase() || 'E'}
                          </div>
                          <div>
                            <p className="text-[13px] font-bold text-[var(--text)] capitalize">{intg.provider}</p>
                            <p className="text-[10px] text-[var(--text3)] truncate max-w-[140px]">{intg.name} · {intg.transactionCount ?? 0} txns</p>
                          </div>
                        </div>
                        {selectedIntegrationIds.includes(intg.id) ? (
                          <div className="w-5 h-5 rounded-full bg-[var(--accent)] flex items-center justify-center text-black flex-shrink-0">
                            <CheckCircle2 size={11} strokeWidth={3} />
                          </div>
                        ) : (
                          <div
                            className="px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide flex-shrink-0"
                            style={{ background: 'var(--card3)', color: 'var(--text3)', border: '1px solid var(--border)' }}
                          >
                            Excluded
                          </div>
                        )}
                      </button>
                    ))}
                    <button
                      onClick={() => setGlobalTab?.('integrations')}
                      className="flex flex-col items-center justify-center p-3.5 rounded-[10px] border border-dashed border-[var(--border2)] hover:border-[var(--accent)] hover:bg-[var(--accent-dim)] transition-all group gap-1.5"
                    >
                      <Plus size={18} className="text-[var(--text3)] group-hover:text-[var(--accent)]" />
                      <span className="text-[10px] font-bold text-[var(--text3)] group-hover:text-[var(--accent)] uppercase tracking-wider">Add Connection</span>
                    </button>
                  </div>

                  <div className="hidden md:flex pt-6 justify-center">
                    <button
                      onClick={() => {
                        if (selectedIntegrations.length === 0) {
                          addToast('Select at least one connection to continue.', 'warning');
                          return;
                        }
                        setHasConfirmedSources(true);
                        setActiveStep('configure');
                        setActiveTab('configure');
                      }}
                      disabled={selectedIntegrations.length === 0}
                      className="flex items-center gap-3 text-black font-black px-10 py-3 rounded-xl shadow-lg transition-all hover:scale-105"
                      style={{
                        background: 'var(--accent)',
                        boxShadow: 'var(--accent-shadow-md)',
                        opacity: selectedIntegrations.length === 0 ? 0.55 : 1,
                        cursor: selectedIntegrations.length === 0 ? 'not-allowed' : 'pointer',
                      }}
                    >
                      CONFIRM & PROCEED <ArrowRight size={16} strokeWidth={3} />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="py-10 text-center space-y-5">
                  <div
                    className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto text-[var(--text3)]"
                    style={{ background: 'var(--card2)' }}
                  >
                    <LinkIcon size={32} />
                  </div>
                  <div className="space-y-1.5">
                    <h4 className="font-syne font-bold text-lg text-[var(--text)]">No connections found</h4>
                    <p className="text-[13px] text-[var(--text2)] max-w-[400px] mx-auto">
                      You need to connect at least one exchange or wallet to calculate your taxes.
                    </p>
                  </div>
                  <button
                    onClick={() => setGlobalTab?.('integrations')}
                    className="bg-[var(--accent)] text-white font-black px-8 py-3 rounded-xl transition-all hover:brightness-95 shadow-[0_2px_6px_rgba(16,185,129,0.3)]"
                  >
                    GO TO CONNECTIONS
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Step 2: Configuration (redesign layout) ── */}
        {activeTab === 'configure' && (
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
            {/* ── Left: Main Config Card ── */}
            <div
              className="order-2 rounded-[16px] overflow-hidden flex flex-col lg:order-1"
              style={{ background: 'var(--card)', border: '1px solid var(--border)' }}
            >
              {/* Card Header */}
              <div className="flex items-center gap-3 p-5 pb-4 border-b border-[var(--border)]">
                <div
                  className="w-9 h-9 rounded-[9px] flex items-center justify-center flex-shrink-0"
                  style={{ background: 'var(--accent-dim)', border: '1px solid var(--accent-soft)' }}
                >
                  <Settings size={16} className="text-[var(--accent)]" />
                </div>
                <div>
                  <h3 className="font-syne font-bold text-[16px] text-[var(--text)] leading-tight">Tax Engine Configuration</h3>
                  <p className="text-[12px] text-[var(--text2)] mt-0.5">Define how we should process your transactions</p>
                </div>
              </div>

              {/* Calculation Method */}
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.1em] text-[var(--text3)] px-[22px] pt-4 pb-2.5">Calculation Method</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 px-[22px] pb-5">
                  {methods.map((m) => {
                    const isBrazil = countryCode === 'br';
                    const isLocked = isBrazil && m.id !== 'WEIGHTED_AVERAGE';
                    const isSelected = accountingMethod === m.id;
                    const cleanLabel = m.label.replace(' (Recommended)', '');

                    let fullName = '';
                    let description = '';
                    if (m.id === 'FIFO') { fullName = 'First In, First Out'; description = 'Oldest assets sold first · Most common globally'; }
                    else if (m.id === 'LIFO') { fullName = 'Last In, First Out'; description = 'Newest assets sold first'; }
                    else if (m.id === 'HIFO') { fullName = 'Highest In, First Out'; description = 'Minimizes taxable gains'; }
                    else if (m.id === 'WEIGHTED_AVERAGE') { fullName = 'Weighted Average Cost'; description = 'Average cost across all purchases'; }
                    else { fullName = m.label; }

                    const showRecommendedBadge = !isBrazil && m.id === 'FIFO';
                    const showRequiredBadge = isBrazil && m.id === 'WEIGHTED_AVERAGE';

                    return (
                      <div
                        key={m.id}
                        onClick={() => {
                          if (isLocked) {
                            setLockedTooltipMethod(m.id);
                            setTimeout(() => {
                              setLockedTooltipMethod(prev => prev === m.id ? null : prev);
                            }, 3000);
                            return;
                          }
                          setAccountingMethod(m.id);
                        }}
                        className={cn(
                          'rounded-[10px] p-3 cursor-pointer transition-all relative',
                          isLocked
                            ? 'opacity-45 cursor-not-allowed'
                            : isSelected
                            ? ''
                            : ''
                        )}
                        style={{
                          border: isSelected
                            ? '1.5px solid var(--accent)'
                            : '1.5px solid var(--border2)',
                          background: isSelected
                            ? 'var(--accent-dim)'
                            : 'var(--card2)',
                        }}
                        onMouseEnter={e => {
                          if (!isSelected && !isLocked)
                            (e.currentTarget as HTMLElement).style.borderColor = 'var(--border-hover)';
                        }}
                        onMouseLeave={e => {
                          if (!isSelected)
                            (e.currentTarget as HTMLElement).style.borderColor = 'var(--border2)';
                        }}
                      >
                        {/* Top row: radio + name + badge */}
                        <div className="flex items-center mb-1">
                          {isLocked ? (
                            <div className="w-4 h-4 flex-shrink-0 flex items-center justify-center text-[var(--text3)] mr-2">
                              <Lock size={11} />
                            </div>
                          ) : (
                            <div
                              className="w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center mr-2 transition-all"
                              style={{
                                borderColor: isSelected ? 'var(--accent)' : 'var(--border2)',
                                background: isSelected ? 'var(--accent)' : 'transparent',
                              }}
                            >
                              {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-black" />}
                            </div>
                          )}
                          <span
                            className="font-mono text-[13px] font-medium"
                            style={{ color: isSelected ? 'var(--accent)' : 'var(--text)', fontFamily: "'DM Mono', monospace" }}
                          >
                            {cleanLabel}
                          </span>
                          {showRecommendedBadge && (
                            <span className="ml-auto text-[9px] font-black uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-[var(--accent)] text-white">
                              Recommended
                            </span>
                          )}
                          {showRequiredBadge && (
                            <span className="ml-auto text-[9px] font-black uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-[rgba(240,165,0,0.15)] text-[#f0a500]">
                              Required BR
                            </span>
                          )}
                        </div>
                        {fullName && <div className="text-[11px] font-medium text-[var(--text2)] pl-6">{fullName}</div>}
                        {description && <div className="text-[11px] text-[var(--text3)] mt-0.5 pl-6">{description}</div>}

                        {lockedTooltipMethod === m.id && (
                          <div className="absolute z-20 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-black/90 text-white text-[11px] font-bold rounded-lg shadow-xl border border-white/10 whitespace-nowrap animate-in fade-in slide-in-from-bottom-1 duration-200">
                            Receita Federal standard method. Locked for Brazil
                            <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[5px] border-[5px] border-transparent border-t-black/90" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Divider */}
              <div className="mx-[22px]" style={{ height: '1px', background: 'var(--border)' }} />

              {/* Bottom Row: Jurisdiction + Settings */}
              <div className="grid grid-cols-2" style={{ borderTop: '1px solid var(--border)' }}>
                {/* Jurisdiction column */}
                <div className="p-[18px] pr-4" style={{ borderRight: '1px solid var(--border)' }}>
                  <p className="text-[10px] font-black uppercase tracking-[0.1em] text-[var(--text3)] mb-2">Jurisdiction</p>

                  {geoReady && (
                    <div
                      className="inline-flex items-center gap-1.5 text-[9px] font-black uppercase tracking-wide px-2 py-1 rounded-full mb-2"
                      style={{ color: 'var(--accent)', background: 'var(--accent-dim)', border: '1px solid var(--accent-soft)' }}
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
                      Auto-detected
                    </div>
                  )}

                  <div
                    className="flex items-center gap-3 p-2.5 rounded-[10px] relative"
                    style={{ background: 'var(--accent-dim)', border: '1.5px solid var(--border-sel)', boxShadow: 'var(--accent-shadow-sm)' }}
                  >
                    <div
                      className="w-7 h-7 rounded-[6px] flex items-center justify-center text-[16px] flex-shrink-0"
                      style={{ background: 'var(--card3)' }}
                    >
                      {countryInfo?.flag ?? '🌍'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[14px] font-semibold text-[var(--text)] truncate leading-tight">{countryInfo?.name ?? jurisdictionName}</p>
                      <p className="text-[11px] text-[var(--text3)]">{countryInfo?.auth}</p>
                    </div>
                    <button
                      onClick={() => setCountryPanelOpen(!countryPanelOpen)}
                      className="flex-shrink-0 text-[12px] font-medium px-2.5 py-1 rounded-[7px] transition-all"
                      style={{ background: 'var(--card3)', border: '1px solid var(--border)', color: 'var(--text2)' }}
                      onMouseEnter={e => {
                        (e.currentTarget as HTMLElement).style.borderColor = 'var(--accent)';
                        (e.currentTarget as HTMLElement).style.color = 'var(--accent)';
                      }}
                      onMouseLeave={e => {
                        (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)';
                        (e.currentTarget as HTMLElement).style.color = 'var(--text2)';
                      }}
                    >
                      Change
                    </button>
                  </div>

                  {/* Country picker dropdown */}
                  {countryPanelOpen && (
                    <div
                      className="mt-2 rounded-xl overflow-hidden"
                      style={{ background: 'var(--card2)', border: '1px solid var(--border2)' }}
                    >
                      <div className="relative p-2.5 pb-1.5">
                        <Search size={13} className="absolute left-5 top-1/2 -translate-y-1/2 text-[var(--text3)] pointer-events-none" />
                        <input
                          autoFocus
                          value={cpSearch}
                          onChange={e => setCpSearch(e.target.value)}
                          placeholder="Search country…"
                          className="w-full rounded-lg pl-8 pr-3 py-2 text-[13px] text-[var(--text)] placeholder:text-[var(--text3)] outline-none transition-colors"
                          style={{ background: 'var(--bg)', border: '1px solid var(--border2)' }}
                          onFocus={e => (e.currentTarget.style.borderColor = 'var(--accent)')}
                          onBlur={e => (e.currentTarget.style.borderColor = 'var(--border2)')}
                        />
                      </div>
                      <div className="max-h-[200px] overflow-y-auto px-2.5 pb-2.5">
                        {!cpSearch && <p className="text-[10px] font-black uppercase tracking-widest text-[var(--text3)] px-2 py-1.5">Popular</p>}
                        {CP_POPULAR.filter(c => !cpSearch || COUNTRIES[c]?.name.toLowerCase().includes(cpSearch.toLowerCase())).map(renderCountryRow)}
                        {!cpSearch && <p className="text-[10px] font-black uppercase tracking-widest text-[var(--text3)] px-2 py-1.5">South America</p>}
                        {CP_SOUTH_AMERICA.filter(c => !cpSearch || COUNTRIES[c]?.name.toLowerCase().includes(cpSearch.toLowerCase())).map(renderCountryRow)}
                        {!cpSearch && <p className="text-[10px] font-black uppercase tracking-widest text-[var(--text3)] px-2 py-1.5">Central America</p>}
                        {CP_CENTRAL_AMERICA.filter(c => !cpSearch || COUNTRIES[c]?.name.toLowerCase().includes(cpSearch.toLowerCase())).map(renderCountryRow)}
                      </div>
                    </div>
                  )}
                </div>

                {/* Additional Settings column */}
                <div className="p-[18px] pl-4">
                  <p className="text-[10px] font-black uppercase tracking-[0.1em] text-[var(--text3)] mb-2">Additional Settings</p>

                  {geoReady && (
                    <div className="space-y-0">
                      {/* Official Exchange Rates */}
                      <div className="flex items-center gap-3 py-2.5 border-b border-[var(--border)]">
                        <div
                          className="w-[30px] h-[30px] rounded-[8px] flex items-center justify-center text-[14px] flex-shrink-0"
                          style={{ background: 'var(--card2)' }}
                        >
                          🌐
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-[13px] font-medium text-[var(--text)] leading-tight">Official Exchange Rates</p>
                          <p className="text-[11px] text-[var(--text3)] mt-0.5">Use central bank rates for fiat conversion</p>
                        </div>
                        <div
                          onClick={() => setRegionalToggles(prev => ({ ...prev, official_rates: !(prev.official_rates ?? true) }))}
                          className={cn('w-9 h-5 rounded-full relative transition-all duration-300 flex-shrink-0 cursor-pointer')}
                          style={{ background: (regionalToggles.official_rates ?? true) ? 'var(--accent)' : 'var(--card3)', border: (regionalToggles.official_rates ?? true) ? 'none' : '1px solid var(--border2)' }}
                        >
                          <div
                            className={cn('absolute top-[3px] w-3.5 h-3.5 rounded-full transition-all duration-200 shadow-sm')}
                            style={{
                              left: (regionalToggles.official_rates ?? true) ? 'calc(100% - 17px)' : '2px',
                              background: (regionalToggles.official_rates ?? true) ? '#000' : '#fff',
                            }}
                          />
                        </div>
                      </div>

                      {/* Regional toggles */}
                      {jurisdictionConfig.regionalToggles
                        .filter(t => t.id !== 'ptax' && t.id !== 'auto_classify')
                        .map((toggle) => {
                          const on = regionalToggles[toggle.id] ?? toggle.defaultOn;
                          return (
                            <div
                              key={toggle.id}
                              onClick={() => setRegionalToggles(prev => ({ ...prev, [toggle.id]: !on }))}
                              className="flex items-center gap-3 py-2.5 border-b border-[var(--border)] cursor-pointer"
                            >
                              <div
                                className="w-[30px] h-[30px] rounded-[8px] flex items-center justify-center text-[14px] flex-shrink-0"
                                style={{ background: 'var(--card2)' }}
                              >
                                🔄
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="text-[13px] font-medium text-[var(--text)] leading-tight">{toggle.label}</p>
                                <p className="text-[11px] text-[var(--text3)] mt-0.5">{toggle.description}</p>
                              </div>
                              <div
                                className="w-9 h-5 rounded-full relative transition-all duration-300 flex-shrink-0"
                                style={{ background: on ? 'var(--accent)' : 'var(--card3)', border: on ? 'none' : '1px solid var(--border2)' }}
                              >
                                <div
                                  className="absolute top-[3px] w-3.5 h-3.5 rounded-full transition-all duration-200 shadow-sm"
                                  style={{
                                    left: on ? 'calc(100% - 17px)' : '2px',
                                    background: on ? '#000' : '#fff',
                                  }}
                                />
                              </div>
                            </div>
                          );
                        })}

                      {/* Advanced Features Collapsible */}
                      <div
                        onClick={() => setAdvancedFeaturesOpen(!advancedFeaturesOpen)}
                        className="flex items-center gap-3 py-2.5 cursor-pointer opacity-70 hover:opacity-90 transition-opacity"
                      >
                        <div
                          className="w-[30px] h-[30px] rounded-[8px] flex items-center justify-center text-[14px] flex-shrink-0"
                          style={{ background: 'var(--card2)' }}
                        >
                          ✦
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-[13px] font-medium text-[var(--text)] leading-tight">
                            Advanced Features{' '}
                            <span
                              className="text-[9px] font-black uppercase tracking-wide px-1.5 py-0.5 rounded ml-1"
                              style={{ background: 'var(--card3)', border: '1px solid var(--border)', color: 'var(--text3)' }}
                            >
                              Pro
                            </span>
                          </p>
                          <p className="text-[11px] text-[var(--text3)] mt-0.5">Match transfers, auto-classify, harvesting</p>
                        </div>
                        <ChevronDown size={14} className={cn("text-[var(--text3)] transition-transform", advancedFeaturesOpen && "rotate-180")} />
                      </div>

                      {/* Advanced features expanded */}
                      {advancedFeaturesOpen && (
                        <div className="space-y-2 pt-2 pb-1 border-t border-[var(--border)]">
                          {/* Match Internal Transfers */}
                          <div
                            className="p-3 rounded-[10px] flex items-center justify-between relative overflow-hidden cursor-pointer"
                            style={{ background: 'var(--bg)', border: '1px solid var(--border)' }}
                          >
                            <div className="flex items-center gap-3 flex-1">
                              <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(91,141,238,0.1)', color: '#5b8dee' }}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                              </div>
                              <div>
                                <p className="text-[12px] font-bold text-[var(--text)]">Match Internal Transfers</p>
                                <p className="text-[11px] text-[var(--text3)]">Exclude wallet-to-wallet from taxable events</p>
                              </div>
                            </div>
                            <div
                              onClick={e => { e.stopPropagation(); if (activePlanKey !== 'free') setRegionalToggles(prev => ({ ...prev, transfer_match: !(prev.transfer_match ?? true) })); }}
                              className="w-9 h-5 rounded-full relative transition-all duration-300 flex-shrink-0"
                              style={{ background: (regionalToggles.transfer_match ?? true) ? 'var(--accent)' : 'var(--card3)', border: (regionalToggles.transfer_match ?? true) ? 'none' : '1px solid var(--border2)' }}
                            >
                              <div className="absolute top-[3px] w-3.5 h-3.5 rounded-full transition-all duration-200 shadow-sm" style={{ left: (regionalToggles.transfer_match ?? true) ? 'calc(100% - 17px)' : '2px', background: (regionalToggles.transfer_match ?? true) ? '#000' : '#fff' }} />
                            </div>
                            {activePlanKey === 'free' && (
                              <div
                                className="absolute inset-0 z-10 bg-[var(--card)]/85 flex items-center justify-center cursor-pointer transition-all hover:bg-[var(--card)]/75"
                                onClick={() => setGlobalTab?.('billing')}
                              >
                                <span className="text-[11px] font-semibold text-[var(--text3)] flex items-center gap-1.5">
                                  <Lock size={12} className="text-[var(--text3)]" />
                                  Starter+ required — Upgrade
                                </span>
                              </div>
                            )}
                          </div>

                          {/* Auto-classify */}
                          <div
                            className="p-3 rounded-[10px] flex items-center justify-between relative overflow-hidden cursor-pointer"
                            style={{ background: 'var(--bg)', border: '1px solid var(--border)' }}
                          >
                            <div className="flex items-center gap-3 flex-1">
                              <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(240,165,0,0.1)', color: '#f0a500' }}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                              </div>
                              <div>
                                <p className="text-[12px] font-bold text-[var(--text)]">Auto-classify Rewards & Airdrops</p>
                                <p className="text-[11px] text-[var(--text3)]">Detect staking income, airdrops, mining</p>
                              </div>
                            </div>
                            <div
                              onClick={e => { e.stopPropagation(); if (activePlanKey === 'trader' || activePlanKey === 'expert') setRegionalToggles(prev => ({ ...prev, auto_classify: !(prev.auto_classify ?? false) })); }}
                              className="w-9 h-5 rounded-full relative transition-all duration-300 flex-shrink-0"
                              style={{ background: (regionalToggles.auto_classify ?? false) ? 'var(--accent)' : 'var(--card3)', border: (regionalToggles.auto_classify ?? false) ? 'none' : '1px solid var(--border2)' }}
                            >
                              <div className="absolute top-[3px] w-3.5 h-3.5 rounded-full transition-all duration-200 shadow-sm" style={{ left: (regionalToggles.auto_classify ?? false) ? 'calc(100% - 17px)' : '2px', background: (regionalToggles.auto_classify ?? false) ? '#000' : '#fff' }} />
                            </div>
                            {activePlanKey !== 'trader' && activePlanKey !== 'expert' && (
                              <div
                                className="absolute inset-0 z-10 bg-[var(--card)]/85 flex items-center justify-center cursor-pointer transition-all hover:bg-[var(--card)]/75"
                                onClick={() => setGlobalTab?.('billing')}
                              >
                                <span className="text-[11px] font-semibold text-[var(--text3)] flex items-center gap-1.5">
                                  <Lock size={12} className="text-[var(--text3)]" />
                                  Trader+ required — Upgrade
                                </span>
                              </div>
                            )}
                          </div>

                          {/* Tax Loss Harvesting */}
                          <div
                            className="p-3 rounded-[10px] flex items-center justify-between relative overflow-hidden cursor-pointer"
                            style={{ background: 'var(--bg)', border: '1px solid var(--border)' }}
                          >
                            <div className="flex items-center gap-3 flex-1">
                              <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(159,122,234,0.1)', color: '#9f7aea' }}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
                              </div>
                              <div>
                                <p className="text-[12px] font-bold text-[var(--text)]">Tax Loss Harvesting Suggestions</p>
                                <p className="text-[11px] text-[var(--text3)]">Identify unrealized losses to offset gains</p>
                              </div>
                            </div>
                            <div
                              onClick={e => { e.stopPropagation(); if (activePlanKey === 'expert') setRegionalToggles(prev => ({ ...prev, loss_harvesting: !(prev.loss_harvesting ?? false) })); }}
                              className="w-9 h-5 rounded-full relative transition-all duration-300 flex-shrink-0"
                              style={{ background: (regionalToggles.loss_harvesting ?? false) ? 'var(--accent)' : 'var(--card3)', border: (regionalToggles.loss_harvesting ?? false) ? 'none' : '1px solid var(--border2)' }}
                            >
                              <div className="absolute top-[3px] w-3.5 h-3.5 rounded-full transition-all duration-200 shadow-sm" style={{ left: (regionalToggles.loss_harvesting ?? false) ? 'calc(100% - 17px)' : '2px', background: (regionalToggles.loss_harvesting ?? false) ? '#000' : '#fff' }} />
                            </div>
                            {activePlanKey !== 'expert' && (
                              <div
                                className="absolute inset-0 z-10 bg-[var(--card)]/85 flex items-center justify-center cursor-pointer transition-all hover:bg-[var(--card)]/75"
                                onClick={() => setGlobalTab?.('billing')}
                              >
                                <span className="text-[11px] font-semibold text-[var(--text3)] flex items-center gap-1.5">
                                  <Lock size={12} className="text-[var(--text3)]" />
                                  Expert only — Upgrade
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* CTA bar */}
              <div
                className="hidden md:flex items-center justify-between px-[22px] py-[18px] mt-auto"
                style={{ borderTop: '1px solid var(--border)' }}
              >
                <div className="text-[12px] text-[var(--text3)]">
                  Ready to process{' '}
                  <strong style={{ color: 'var(--text)' }}>
                    {isOverLimit
                      ? `${willProcess.toLocaleString()} of ${totalTxns.toLocaleString()}`
                      : totalTxns.toLocaleString()}
                  </strong>{' '}transactions
                  {countryInfo && <> · <strong style={{ color: 'var(--text)' }}>{countryInfo.name}</strong></>}
                </div>
                <button
                  onClick={handleStartCalculation}
                  disabled={isCalculating}
                  className={cn(
                    'flex items-center justify-center gap-2 font-syne font-black text-[13px] text-white h-[38px] px-6 rounded-[9px] transition-all',
                    isCalculating && 'opacity-70 cursor-wait'
                  )}
                  style={{ background: 'var(--accent)', boxShadow: 'var(--accent-shadow-md)' }}
                  onMouseEnter={e => !isCalculating && ((e.currentTarget as HTMLElement).style.boxShadow = 'var(--accent-shadow-lg)')}
                  onMouseLeave={e => !isCalculating && ((e.currentTarget as HTMLElement).style.boxShadow = 'var(--accent-shadow-md)')}
                >
                  {isCalculating ? (
                    <>
                      <RefreshCw size={14} className="animate-spin flex-shrink-0" />
                      <span className="leading-none mt-[1px]">CALCULATING...</span>
                    </>
                  ) : (
                    <>
                      <ArrowRight size={14} className="flex-shrink-0" />
                      <span className="leading-none mt-[1px]">Start Calculation</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* ── Right Column ── */}
            <div className="order-1 flex flex-col gap-4 lg:order-2">
              {/* Calculation Summary */}
              <div
                className="rounded-[16px] overflow-hidden"
                style={{ background: 'var(--card)', border: '1px solid var(--border)' }}
              >
                <div
                  className="px-[18px] py-3.5"
                  style={{ borderBottom: '1px solid var(--border)' }}
                >
                  <span className="font-syne font-black text-[10px] tracking-[0.08em] uppercase text-[var(--text3)]">Calculation Summary</span>
                </div>
                {[
                  { label: 'Jurisdiction', value: `${countryInfo?.flag ?? ''} ${countryInfo?.name ?? jurisdictionName}`.trim() },
                  { label: 'Authority', value: countryInfo?.auth ?? '—' },
                  { label: 'Fiscal Year', value: '2024' },
                  { label: 'Method', value: accountingMethod },
                  { label: 'Transactions', value: String(totalTxns) },
                  { label: 'Exchange Rates', value: countryInfo?.rate ?? 'Market' },
                  { label: 'Auto-classify', value: (regionalToggles.auto_classify ?? false) ? 'On' : 'Off' },
                  { label: 'Transfer Match', value: (regionalToggles.transfer_match !== false) ? 'On' : 'Off' },
                ].map(({ label, value }) => (
                  <div
                    key={label}
                    className="flex justify-between items-center px-[18px] py-[9px]"
                    style={{ borderBottom: '1px solid var(--border)' }}
                  >
                    <span className="text-[13px] text-[var(--text3)]">{label}</span>
                    <span
                      className="text-[12px] font-semibold"
                      style={{
                        fontFamily: "'DM Mono', monospace",
                        color: 'var(--text)',
                      }}
                    >
                      {value}
                    </span>
                  </div>
                ))}
              </div>

              {/* Plan Card */}
              {(() => {
                const planFeatures: Record<string, { on: boolean; label: string; req?: string }[]> = {
                  free: [
                    { on: true, label: '25 transactions' },
                    { on: true, label: 'Up to 5 wallets' },
                    { on: true, label: 'Tax Report Preview' },
                    { on: false, label: 'PDF Tax Report', req: 'Starter' },
                    { on: false, label: 'Transfer Match', req: 'Starter' },
                    { on: false, label: 'HIFO / Weighted Avg', req: 'Trader' },
                    { on: false, label: 'DeFi & NFT Support', req: 'Trader' },
                    { on: false, label: 'Loss Harvesting', req: 'Expert' },
                  ],
                  starter: [
                    { on: true, label: '150 transactions' },
                    { on: true, label: 'Up to 15 wallets' },
                    { on: true, label: 'PDF Tax Report' },
                    { on: true, label: 'Transfer Match' },
                    { on: false, label: 'HIFO / Weighted Avg', req: 'Trader' },
                    { on: false, label: 'DeFi & NFT Support', req: 'Trader' },
                    { on: false, label: 'Loss Harvesting', req: 'Expert' },
                  ],
                  trader: [
                    { on: true, label: '1,000 transactions' },
                    { on: true, label: 'Unlimited wallets' },
                    { on: true, label: 'HIFO & Weighted Avg' },
                    { on: true, label: 'DeFi & NFT Support' },
                    { on: true, label: 'Auto-classify Rewards' },
                    { on: false, label: 'Loss Harvesting', req: 'Expert' },
                    { on: false, label: 'High-Volume CSV', req: 'Expert' },
                  ],
                  expert: [
                    { on: true, label: '3,000 transactions' },
                    { on: true, label: 'Unlimited wallets' },
                    { on: true, label: 'All calc methods' },
                    { on: true, label: 'DeFi & NFT Support' },
                    { on: true, label: 'Loss Harvesting ✦' },
                    { on: true, label: 'High-Volume CSV' },
                    { on: true, label: 'Early Access features' },
                  ],
                };
                const badgeColors: Record<string, string> = {
                  free: 'var(--text3)',
                  starter: 'var(--accent)',
                  trader: '#5b8dee',
                  expert: '#9f7aea',
                };
                const features = planFeatures[activePlanKey] ?? [];
                return (
                  <div
                    className="rounded-[16px] overflow-hidden"
                    style={{ background: 'var(--card)', border: '1px solid var(--border)' }}
                  >
                    {/* Plan header */}
                    <div
                      className="flex items-center justify-between px-[18px] py-3.5"
                      style={{ borderBottom: '1px solid var(--border)' }}
                    >
                      <span className="font-syne font-bold text-[14px] text-[var(--text)]">{activePlan.name}</span>
                      <span
                        className="text-[10px] font-black uppercase tracking-[0.08em] px-2.5 py-1 rounded-full"
                        style={{
                          background: 'var(--card2)',
                          border: '1px solid var(--border)',
                          color: badgeColors[activePlanKey],
                        }}
                      >
                        {activePlanKey.toUpperCase()}
                      </span>
                    </div>

                    {/* Features list */}
                    <div className="px-[18px] py-3 border-b border-[var(--border)] space-y-1.5">
                      {features.filter(f => f.on).map((f) => (
                        <div key={f.label} className="flex items-center gap-2 text-[13px] text-[var(--text2)]">
                          <span className="text-[12px]" style={{ color: 'var(--accent)' }}>✓</span>
                          {f.label}
                        </div>
                      ))}
                    </div>

                    {/* Usage section */}
                    <div className="px-[18px] py-3">
                      <div className="flex justify-between text-[11px] mb-2">
                        <span className="font-black uppercase tracking-[0.05em] text-[var(--text3)]">Transactions Used</span>
                        <span style={{ fontFamily: "'DM Mono', monospace", color: 'var(--text2)' }}>{willProcess.toLocaleString()} / {activePlan.limit.toLocaleString()}</span>
                      </div>
                      <div className="w-full h-1 rounded-full overflow-hidden mb-2" style={{ background: 'var(--card3)' }}>
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${txBarPct}%`,
                            background: isOverLimit || txBarPct >= 70 ? '#f59e0b' : 'var(--accent)',
                          }}
                        />
                      </div>
                      {isOverLimit && (
                        <div
                          className="flex items-start gap-1.5 text-[11px] px-2.5 py-1.5 rounded-[7px] mb-3"
                          style={{ color: '#f59e0b', background: 'rgba(245,158,11,0.1)', lineHeight: '1.4' }}
                        >
                          <AlertTriangle size={12} className="flex-shrink-0 mt-[1px]" />
                          <span>
                            Only <strong className="mx-0.5">{willProcess.toLocaleString()}</strong> of <strong className="mx-0.5">{totalTxns.toLocaleString()}</strong> transactions will be processed.
                          </span>
                        </div>
                      )}
                    </div>

                    {activePlanKey !== 'expert' && (
                      <button
                        onClick={() => setGlobalTab?.('billing')}
                        className="w-full py-3 text-white text-[12px] font-black text-center transition-all hover:opacity-90"
                        style={{ background: 'var(--accent)' }}
                      >
                        Upgrade for more features →
                      </button>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* ── Step 3: Review Data ── */}
        {activeTab === 'review' && (
          <ReviewDataPanel 
            isCalculating={isCalculating} 
            onProceed={() => { 
              setActiveStep('export'); 
              setActiveTab('reports'); 
            }} 
          />
        )}

        {/* ── Step 4: Reports ── */}
        {activeTab === 'reports' && (
          <GenerateReportsPanel />
        )}
      </div>

      {activeTab === 'sources' && integrations.length > 0 && (
        <div className="fixed inset-x-0 bottom-0 z-[120] border-t border-[var(--border)] bg-[color:rgba(8,15,25,0.94)] px-4 py-3 backdrop-blur-xl md:hidden">
          <button
            onClick={() => {
              if (selectedIntegrations.length === 0) {
                addToast('Select at least one connection to continue.', 'warning');
                return;
              }
              setHasConfirmedSources(true);
              setActiveStep('configure');
              setActiveTab('configure');
            }}
            disabled={selectedIntegrations.length === 0}
            className="flex min-h-[48px] w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-6 text-sm font-black text-black disabled:opacity-50"
          >
            Confirm & Proceed <ArrowRight size={16} strokeWidth={3} />
          </button>
        </div>
      )}

      {activeTab === 'configure' && (
        <div className="fixed inset-x-0 bottom-0 z-[120] border-t border-[var(--border)] bg-[color:rgba(8,15,25,0.94)] px-4 py-3 backdrop-blur-xl md:hidden">
          <button
            onClick={handleStartCalculation}
            disabled={isCalculating}
            className="flex min-h-[48px] w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-6 text-sm font-black text-black disabled:opacity-60"
          >
            {isCalculating ? <RefreshCw size={16} className="animate-spin" /> : <ArrowRight size={16} strokeWidth={3} />}
            {isCalculating ? 'Calculating...' : 'Start Calculation'}
          </button>
        </div>
      )}
    </div>
  );
}
