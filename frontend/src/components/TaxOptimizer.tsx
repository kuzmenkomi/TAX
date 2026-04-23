import { useRef, useState } from 'react';
import {
  Upload,
  CheckCircle2,
  XCircle,
  Loader2,
  Calculator,
  Zap,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  FileText,
  RefreshCw,
  BarChart3,
  PieChart,
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPieChart, Pie, Cell } from 'recharts';
import {
  analyzeUpload,
  analyzeUploadMulti,
  syncWallet,
  syncExchange,
  downloadAuditPdf,
  downloadBrExport,
  downloadDecriptoExport,
  downloadDirpfExport,
  downloadGcapExport,
  getRunHistory,
  AnalyzeResult,
  MatchEntry,
  RunHistoryItem,
} from '../api/client';
import { useAppContext } from '../context/AppContext';
import { useAuth } from '../auth/AuthContext';
import { useI18n } from '../i18n/I18nContext';

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatQuote(n: number | undefined | null, currency: string): string {
  if (n == null || isNaN(Number(n))) return '—';
  const ccy = currency === 'BRL' ? 'BRL' : 'USD';
  const loc = currency === 'BRL' ? 'pt-BR' : 'en-US';
  return new Intl.NumberFormat(loc, { style: 'currency', currency: ccy }).format(Number(n));
}

function fmtNum(n: unknown): string {
  if (n == null || n === '') return '—';
  const num = Number(n);
  if (isNaN(num)) return String(n);
  return num.toFixed(6);
}

function parsePnl(pnl: AnalyzeResult['pnl']) {
  if (!pnl || typeof pnl !== 'object') {
    return { totalGain: 0, totalLoss: 0, net: 0, gasFees: 0, taxableEvents: 0, internalTransfers: 0, byAsset: {} };
  }
  const p = pnl as Record<string, unknown>;
  const net = Number(p.total_realized_pnl_usd ?? p.total_gain ?? p.realized_pnl ?? p.net_pnl ?? 0) || 0;
  const totalGain = net > 0 ? net : 0;
  const totalLoss = net < 0 ? Math.abs(net) : 0;
  const gasFees = Number(p.total_gas_fees_usd ?? 0) || 0;
  const taxableEvents = Number(p.taxable_events_count ?? 0) || 0;
  const internalTransfers = Number(p.internal_transfer_count ?? 0) || 0;
  const byAsset = (p.realized_pnl_by_asset ?? {}) as Record<string, number>;
  return { totalGain, totalLoss, net, gasFees, taxableEvents, internalTransfers, byAsset };
}

function confidenceColor(c: number) {
  if (c >= 0.8) return 'text-[#6af0c8] bg-[#6af0c8]/10';
  if (c >= 0.5) return 'text-[#f0a86a] bg-[#f0a86a]/10';
  return 'text-[#f06a6a] bg-[#f06a6a]/10';
}

// ── Match Row ────────────────────────────────────────────────────────────────

function MatchRow({ match, index }: { match: MatchEntry; index: number }) {
  const [open, setOpen] = useState(false);
  const asset = String(match.asset ?? match.symbol ?? '—').toUpperCase();
  const transferAmount = Number(match.transfer_amount ?? 0);
  const receiveAmount = Number(match.receive_amount ?? 0);
  const amountDiff = Number(match.amount_diff ?? 0);
  const timeDiff = Number(match.time_diff_seconds ?? 0);
  const confidence = Number(match.confidence ?? 0);
  const explanation = String(match.explanation ?? 'No explanation available');

  return (
    <div className="border rounded-2xl p-4 transition-all hover:border-brand-green-500/30 group" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="flex items-center gap-3">
          <span className="text-[13px] font-bold" style={{ color: 'var(--text)' }}>Match #{index + 1}</span>
          <span className="text-[12px] font-bold opacity-60" style={{ color: 'var(--text)' }}>{asset}</span>
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-widest ${confidenceColor(confidence)}`}>
            {Math.round(confidence * 100)}% Match
          </span>
        </div>
        <div className="w-8 h-8 rounded-full bg-brand-green-500/5 flex items-center justify-center transition-transform" style={{ color: 'var(--text3)' }}>
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>
      {open && (
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-4 text-[12px] border-t pt-4" style={{ borderColor: 'var(--border)' }}>
          <div>
            <p className="opacity-50 uppercase font-black text-[9px] tracking-widest" style={{ color: 'var(--text)' }}>Transfer</p>
            <p className="font-bold" style={{ color: 'var(--text)' }}>{fmtNum(transferAmount)}</p>
          </div>
          <div>
            <p className="opacity-50 uppercase font-black text-[9px] tracking-widest" style={{ color: 'var(--text)' }}>Receive</p>
            <p className="font-bold" style={{ color: 'var(--text)' }}>{fmtNum(receiveAmount)}</p>
          </div>
          <div>
            <p className="opacity-50 uppercase font-black text-[9px] tracking-widest" style={{ color: 'var(--text)' }}>Difference</p>
            <p className="font-bold" style={{ color: 'var(--text)' }}>{fmtNum(amountDiff)}</p>
          </div>
          <div>
            <p className="opacity-50 uppercase font-black text-[9px] tracking-widest" style={{ color: 'var(--text)' }}>Time Diff</p>
            <p className="font-bold" style={{ color: 'var(--text)' }}>{timeDiff}s</p>
          </div>
          <div className="sm:col-span-2">
            <p className="opacity-50 uppercase font-black text-[9px] tracking-widest" style={{ color: 'var(--text)' }}>Explanation</p>
            <p className="italic leading-relaxed" style={{ color: 'var(--text2)' }}>{explanation}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Chart colors for theme ──────────────────────────────────────────
const CHART_COLORS = ['var(--accent)', '#6af0c8', '#a78bfa', '#f0a86a', '#f06a6a'];

// ── Main Component ───────────────────────────────────────────────────────────

export function TaxOptimizer() {
  const { t } = useI18n();
  const {
    analyzeResult, setAnalyzeResult,
    accountingMethod, setAccountingMethod,
    isLoading, setIsLoading,
    error, setError,
    uploadedFile, setUploadedFile,
    backendOnline,
  } = useAppContext();
  const { token } = useAuth();

  const fileRef = useRef<HTMLInputElement>(null);
  const multiRef = useRef<HTMLInputElement>(null);
  const [format, setFormat] = useState('native');
  const [dragOver, setDragOver] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [quoteCurrency, setQuoteCurrency] = useState<'BRL' | 'USD'>('BRL');
  const [usePtax, setUsePtax] = useState(false);
  const [bnKey, setBnKey] = useState('');
  const [bnSecret, setBnSecret] = useState('');
  const [apiProvider, setApiProvider] = useState<'binance' | 'mercado_bitcoin' | 'foxbit' | 'novadax' | 'coinbase' | 'kraken' | 'okx'>('binance');
  const [runHistory, setRunHistory] = useState<RunHistoryItem[]>([]);
  const [walletChain, setWalletChain] = useState<'ethereum' | 'polygon' | 'solana'>('ethereum');
  const [walletAddress, setWalletAddress] = useState('');

  const METHODS = ['FIFO', 'LIFO', 'HIFO', 'AVCO'];
  const COUNTRIES = [{ id: 'br', label: 'Brasil' }];
  const FORMATS = ['native', 'binance', 'mercado_bitcoin', 'foxbit', 'novadax', 'bybit', 'coinbase', 'kraken', 'okx', 'metamask'];
  const FORMAT_LABELS: Record<string, string> = {
    native: 'Native', binance: 'Binance', mercado_bitcoin: 'Mercado Bitcoin', foxbit: 'Foxbit',
    novadax: 'NovaDAX', bybit: 'Bybit', coinbase: 'Coinbase', kraken: 'Kraken', okx: 'OKX', metamask: 'MetaMask',
  };
  const [country, setCountry] = useState('br');

  const displayQuote = (analyzeResult?.quote_currency as string) || quoteCurrency;

  // ── Handlers ───────────────────────────────────────────────────────────

  async function handleAnalyze(file: File) {
    if (!backendOnline) { setError('Backend is offline'); return; }
    setIsLoading(true); setError(null); setAnalyzeResult(null);
    try {
      const result = await analyzeUpload({ file, format, accounting_method: accountingMethod, country, quote_currency: quoteCurrency, use_ptax: usePtax, token });
      setAnalyzeResult(result);
    } catch (e) { setError(e instanceof Error ? e.message : 'Unknown error'); }
    finally { setIsLoading(false); }
  }

  async function handleMultiAnalyze() {
    if (!backendOnline || !token) return;
    const fl = multiRef.current?.files;
    if (!fl?.length) { setError('Select one or more CSVs.'); return; }
    setIsLoading(true); setError(null); setAnalyzeResult(null);
    try {
      const result = await analyzeUploadMulti({ files: Array.from(fl), format, accounting_method: accountingMethod, country, quote_currency: quoteCurrency, use_ptax: usePtax, token });
      setAnalyzeResult(result);
    } catch (e) { setError(e instanceof Error ? e.message : 'Multi upload error'); }
    finally { setIsLoading(false); }
  }

  async function handleExchangeSync() {
    if (!backendOnline || !token) return;
    if (!bnKey.trim() || !bnSecret.trim()) { setError('Fill API Key and Secret.'); return; }
    setIsLoading(true); setError(null); setAnalyzeResult(null);
    try {
      const result = await syncExchange(token, { provider: apiProvider, api_key: bnKey.trim(), api_secret: bnSecret.trim(), accounting_method: accountingMethod, quote_currency: quoteCurrency, use_ptax: usePtax, country });
      setAnalyzeResult(result);
    } catch (e) { setError(e instanceof Error ? e.message : 'Sync failed'); }
    finally { setIsLoading(false); }
  }

  async function handleOnchainAnalyze() {
    if (!backendOnline || !token) return;
    if (!walletAddress.trim()) { setError('Enter wallet address.'); return; }
    setIsLoading(true); setError(null); setAnalyzeResult(null);
    try {
      const result = await syncWallet(token, { chain: walletChain, address: walletAddress.trim(), accounting_method: accountingMethod, quote_currency: quoteCurrency, country, use_ptax: usePtax });
      setAnalyzeResult(result);
    } catch (e) { setError(e instanceof Error ? e.message : 'On-chain import failed'); }
    finally { setIsLoading(false); }
  }

  const downloadHandler = (fn: (token: string, id: any) => Promise<Blob>, ext: string) => async () => {
    const id = analyzeResult?.analysis_run_id;
    if (!id || !token) return;
    try {
      const blob = await fn(token, id as any);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `export_${id}.${ext}`; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { setError(e instanceof Error ? e.message : 'Download failed'); }
  };

  async function handleLoadRunHistory() {
    if (!token) return;
    try { setRunHistory(await getRunHistory(token)); } catch { /* silent */ }
  }

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) { setUploadedFile(f); handleAnalyze(f); }
  }
  function onDrop(e: React.DragEvent) {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) { setUploadedFile(f); handleAnalyze(f); }
  }
  function reset() {
    setUploadedFile(null); setAnalyzeResult(null); setError(null);
    if (fileRef.current) fileRef.current.value = '';
    if (multiRef.current) multiRef.current.value = '';
  }

  const pnl = analyzeResult ? parsePnl(analyzeResult.pnl) : null;
  const matches = analyzeResult?.matches ?? [];
  const displayed = showAll ? matches : matches.slice(0, 15);
  const estimatedTax = pnl ? Math.max(0, pnl.net * 0.25) : 0;
  const monthSalesMap = analyzeResult?.monthly_sales_brl ?? {};
  const latestMonth = Object.keys(monthSalesMap).sort().at(-1) ?? '';
  const latestSales = latestMonth ? Number(monthSalesMap[latestMonth] ?? 0) : 0;
  const threshold = Number(analyzeResult?.isencao_threshold_brl ?? 35000);
  const progressPct = threshold > 0 ? Math.min(100, (latestSales / threshold) * 100) : 0;
  const fnameLabel = analyzeResult?.filename
    ? (Array.isArray(analyzeResult.filename) ? analyzeResult.filename.join(', ') : analyzeResult.filename)
    : '';
  const decriptoRequired = Boolean(analyzeResult?.offshore_onshore?.decripto_required);
  const decriptoAlert = analyzeResult?.offshore_onshore?.decripto_alert ?? '';
  const savings = analyzeResult?.tax_savings_opportunities ?? [];

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

      {/* ── Header ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>{t('tax.title')}</h1>
          <p className="text-[14px] mt-1" style={{ color: 'var(--text3)' }}>{t('tax.subtitle')}</p>
        </div>
        {analyzeResult && (
          <button onClick={reset} className="flex items-center gap-2 px-4 py-2 bg-brand-green-500 text-brand-dark rounded-xl text-[12px] font-black shadow-lg shadow-brand-green-500/20 hover:bg-brand-green-400 transition-all active:scale-95">
            <RefreshCw className="w-3.5 h-3.5" /> New Analysis
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* ── LEFT COLUMN ── */}
        <div className="lg:col-span-2 space-y-6">

          {/* Import panels */}
          {!analyzeResult && !isLoading && (
            <div className="grid md:grid-cols-2 gap-4 animate-in zoom-in-95 duration-500">
              {/* API Sync */}
              <div className="border rounded-[2rem] p-6 shadow-sm flex flex-col" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                <h3 className="text-xs font-black uppercase tracking-widest mb-4" style={{ color: 'var(--text2)' }}>Exchange Sync</h3>
                <div className="space-y-3 flex-1">
                  <select value={apiProvider} onChange={(e) => setApiProvider(e.target.value as any)}
                    className="w-full px-4 py-3 border rounded-xl text-[12px] focus:outline-none focus:border-brand-green-500"
                    style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}>
                    {['binance','coinbase','kraken','okx','mercado_bitcoin','foxbit','novadax'].map(p => (
                      <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1).replace('_',' ')}</option>
                    ))}
                  </select>
                  <input type="password" placeholder="API Key" value={bnKey} onChange={(e) => setBnKey(e.target.value)}
                    className="w-full px-4 py-3 border rounded-xl text-[12px] placeholder:opacity-40 focus:outline-none focus:border-brand-green-500"
                    style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                  <input type="password" placeholder="API Secret" value={bnSecret} onChange={(e) => setBnSecret(e.target.value)}
                    className="w-full px-4 py-3 border rounded-xl text-[12px] placeholder:opacity-40 focus:outline-none focus:border-brand-green-500"
                    style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                </div>
                <button type="button" disabled={isLoading || !backendOnline} onClick={handleExchangeSync}
                  className="mt-6 w-full py-3.5 bg-brand-green-500 text-brand-dark rounded-xl text-[12px] font-black hover:bg-brand-green-400 disabled:opacity-40 transition-all shadow-lg shadow-brand-green-500/20">
                  Secure Connect
                </button>
              </div>

              {/* Multi CSV */}
              <div className="border rounded-[2rem] p-6 shadow-sm flex flex-col" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                <h3 className="text-xs font-black uppercase tracking-widest mb-4" style={{ color: 'var(--text2)' }}>Large Data Import</h3>
                <div className="border-2 border-dashed rounded-3xl p-6 text-center mb-4 flex-1 flex flex-col justify-center items-center gap-3" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                  <FileText className="opacity-20" size={32} style={{ color: 'var(--text)' }} />
                  <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text3)' }}>Upload multiple CSV files for processing.</p>
                  <input ref={multiRef} type="file" accept=".csv" multiple className="hidden" onChange={handleMultiAnalyze} />
                </div>
                <button type="button" disabled={isLoading || !backendOnline} onClick={() => multiRef.current?.click()}
                  className="w-full py-3.5 border rounded-xl text-[12px] font-black transition-all hover:bg-brand-green-500/5"
                  style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}>
                  Select CSV Files
                </button>
              </div>

              {/* On-chain */}
              <div className="border rounded-[2.5rem] p-8 shadow-sm md:col-span-2" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                <h3 className="text-xs font-black uppercase tracking-widest mb-6" style={{ color: 'var(--text2)' }}>Blockchain Analysis</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                  <select value={walletChain} onChange={(e) => setWalletChain(e.target.value as any)}
                    className="px-4 py-3 border rounded-xl text-[12px] focus:outline-none"
                    style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}>
                    <option value="ethereum">Ethereum (EVM)</option>
                    <option value="polygon">Polygon (MATIC)</option>
                    <option value="solana">Solana (SPL)</option>
                  </select>
                  <input type="text" placeholder="Wallet address (0x... or Base58)" value={walletAddress} onChange={(e) => setWalletAddress(e.target.value)}
                    className="px-4 py-3 border rounded-xl text-[12px] focus:outline-none"
                    style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }} />
                </div>
                <button type="button" disabled={isLoading || !backendOnline} onClick={handleOnchainAnalyze}
                  className="w-full py-4 bg-accent text-white rounded-2xl text-[13px] font-bold shadow-xl shadow-accent/20 hover:opacity-90 transition-all">
                  Run On-chain Audit
                </button>
              </div>
            </div>
          )}

          {/* Simple Upload / Loading / Success result */}
          {(analyzeResult || isLoading || uploadedFile) && (
            <div
              className={`border-2 border-dashed rounded-[2.5rem] p-12 text-center transition-all cursor-pointer relative overflow-hidden group ${
                dragOver ? 'border-accent bg-accent/5 scale-[1.01]'
                : uploadedFile && analyzeResult ? 'border-brand-green-500/30 bg-brand-green-500/5'
                : 'border-border bg-surface'
              }`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              onClick={() => !isLoading && fileRef.current?.click()}
            >
              <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={onFileChange} />

              {isLoading ? (
                <div className="flex flex-col items-center gap-6 py-4 animate-in fade-in">
                  <div className="relative">
                    <Loader2 className="w-16 h-16 text-accent animate-spin" />
                    <Zap className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-accent" size={24} />
                  </div>
                  <div>
                    <h3 className="text-xl font-syne font-black mb-2" style={{ color: 'var(--text)' }}>Engine Computing...</h3>
                    <p className="text-[12px] opacity-60" style={{ color: 'var(--text)' }}>Processing: {uploadedFile?.name || 'External data stream'}</p>
                  </div>
                </div>
              ) : analyzeResult ? (
                <div className="flex flex-col items-center gap-4 py-2 animate-in zoom-in-95">
                  <div className="w-20 h-20 bg-brand-green-500/10 rounded-full flex items-center justify-center animate-pulse-subtle">
                    <CheckCircle2 className="w-10 h-10 text-brand-green-500" />
                  </div>
                  <div>
                    <h3 className="text-xl font-syne font-black mb-1" style={{ color: 'var(--text)' }}>Audit Complete</h3>
                    <p className="text-[13px] font-bold" style={{ color: 'var(--text2)' }}>
                      {analyzeResult.rows_processed} lines analyzed · {analyzeResult.matches_found} matches identified
                    </p>
                  </div>
                  <button className="mt-4 px-6 py-2 border rounded-full text-[11px] font-bold hover:bg-brand-green-500/10 transition-colors" style={{ borderColor: 'var(--border)', color: 'var(--text3)' }}>
                    Replace data source
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-6">
                  <div className="w-20 h-20 rounded-3xl bg-surface2 border flex items-center justify-center transition-transform group-hover:scale-110 shadow-sm" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                    <Upload className="w-8 h-8 opacity-20" style={{ color: 'var(--text)' }} />
                  </div>
                  <div>
                    <p className="text-xl font-syne font-black mb-2" style={{ color: 'var(--text)' }}>{dragOver ? 'Drop file now' : 'Quick Single Upload'}</p>
                    <p className="text-[13px] opacity-60" style={{ color: 'var(--text)' }}>Select a single CSV or drag & drop here</p>
                  </div>
                  <div className="flex gap-2 flex-wrap justify-center opacity-40">
                    {['BNB','COINBASE','KRAKEN','OKX','METAMASK'].map(f => (
                      <span key={f} className="text-[9px] font-black border px-2 py-0.5 rounded uppercase tracking-widest" style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>{f}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-danger/10 border border-danger/20 rounded-[2rem] p-6 flex items-center gap-4 animate-shake">
              <div className="w-10 h-10 bg-danger/10 rounded-xl flex items-center justify-center flex-shrink-0">
                <XCircle className="text-danger" size={20} />
              </div>
              <div>
                <p className="text-xs font-black uppercase tracking-widest text-danger">Processing Error</p>
                <p className="text-[13px] font-bold mt-0.5 opacity-80" style={{ color: 'var(--text)' }}>{error}</p>
              </div>
            </div>
          )}

          {/* ── Main Summary Panel ── */}
          {analyzeResult && pnl && (
            <div className="border rounded-[2.5rem] p-8 relative overflow-hidden shadow-2xl animate-in fade-in slide-in-from-bottom-8 duration-700" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              
              {/* Background Glow */}
              <div className="absolute top-0 right-0 w-[40rem] h-[40rem] bg-accent/5 rounded-full -mr-[20rem] -mt-[20rem] blur-[120px] pointer-events-none" />
              
              <div className="relative z-10 space-y-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-accent/10 rounded-2xl flex items-center justify-center">
                      <Calculator className="text-accent" size={28} />
                    </div>
                    <div>
                      <h2 className="text-xl font-syne font-black tracking-tight" style={{ color: 'var(--text)' }}>Executive Summary</h2>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="px-2 py-0.5 bg-brand-green-500/10 text-brand-green-500 rounded text-[9px] font-black uppercase tracking-widest border border-brand-green-500/20">{accountingMethod} Method</span>
                        <span className="text-[10px] opacity-40 font-bold" style={{ color: 'var(--text)' }}>Batch Run: {analyzeResult.analysis_run_id}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex md:flex-col items-center md:items-end gap-2 text-right">
                    <p className="text-[10px] font-bold uppercase tracking-widest opacity-40" style={{ color: 'var(--text)' }}>Total Realized P&L</p>
                    <p className={`text-4xl font-black font-syne ${pnl.net >= 0 ? 'text-brand-green-500' : 'text-danger'}`}>
                      {pnl.net >= 0 ? '+' : ''}{formatQuote(pnl.net, displayQuote)}
                    </p>
                  </div>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: 'Portfolio Gain', value: pnl.totalGain, color: 'text-brand-green-500', icon: TrendingUp },
                    { label: 'Realized Loss', value: pnl.totalLoss, color: 'text-danger', icon: XCircle },
                    { label: 'Taxable Events', value: pnl.taxableEvents, color: 'text-accent', isCount: true, icon: Zap },
                    { label: 'Est. Liability', value: estimatedTax, color: 'text-warning', icon: Calculator },
                  ].map(item => (
                    <div key={item.label} className="p-5 border rounded-3xl group transition-all hover:scale-[1.02]" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                      <div className="flex items-center justify-between mb-2">
                        <item.icon className={`opacity-40 ${item.color}`} size={16} />
                        <p className="text-[10px] font-bold uppercase tracking-[2px] opacity-40" style={{ color: 'var(--text)' }}>{item.label}</p>
                      </div>
                      <p className={`text-xl font-black font-syne ${item.color}`}>
                        {item.isCount ? item.value : formatQuote(item.value as number, displayQuote)}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Asset Breakdown */}
                {Object.keys(pnl.byAsset).length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-xs font-black uppercase tracking-widest opacity-60 flex items-center gap-2" style={{ color: 'var(--text)' }}>
                      <div className="w-4 h-0.5 bg-accent rounded" /> Performance by Asset
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      {Object.entries(pnl.byAsset).map(([asset, val]) => (
                        <div key={asset} className="p-4 border rounded-2xl flex flex-col justify-center items-center gap-1" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                          <p className="text-[10px] font-bold" style={{ color: 'var(--text3)' }}>{asset}</p>
                          <p className={`text-[13px] font-black ${val >= 0 ? 'text-brand-green-500' : 'text-danger'}`}>
                            {val >= 0 ? '+' : ''}{formatQuote(val, displayQuote).split(',')[0]}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Quick Actions / Download */}
                <div className="pt-6 border-t flex flex-wrap gap-2" style={{ borderColor: 'var(--border)' }}>
                  {[
                    { label: 'Comprehensive CSV', fn: downloadBrExport, variant: 'solid' },
                    { label: 'DeCripto JSON', fn: downloadDecriptoExport, variant: 'outline' },
                    { label: 'GCAP Format', fn: downloadGcapExport, variant: 'outline' },
                    { label: 'Tax Audit PDF', fn: downloadAuditPdf, variant: 'outline' },
                  ].map(btn => (
                    <button key={btn.label} type="button" onClick={downloadHandler(btn.fn, btn.label.includes('PDF') ? 'pdf' : btn.label.includes('JSON') ? 'json' : 'csv')} 
                      className={`px-5 py-2.5 rounded-xl text-[12px] font-bold transition-all shadow-sm flex items-center gap-2 ${
                        btn.variant === 'solid' ? 'bg-accent text-white hover:opacity-90' : 'border hover:bg-white/5'
                      }`}
                      style={btn.variant === 'outline' ? { background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text2)' } : undefined}>
                      <FileText size={14} /> {btn.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Visual Data / Charts */}
          {analyzeResult && pnl && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border rounded-[2.5rem] p-8 shadow-sm h-fit" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-3 mb-8">
                  <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center">
                    <BarChart3 className="text-accent" size={20} />
                  </div>
                  <h3 className="text-sm font-bold uppercase tracking-widest underline decoration-accent/30 decoration-4 underline-offset-8" style={{ color: 'var(--text)' }}>PnL Variance</h3>
                </div>
                <div className="h-[250px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={Object.entries(pnl.byAsset).map(([asset, value]) => ({ asset, value }))}>
                      <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="var(--border)" />
                      <XAxis dataKey="asset" axisLine={false} tickLine={false} tick={{ fill: 'var(--text3)', fontSize: 10, fontWeight: 700 }} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: 'var(--text3)', fontSize: 10 }} />
                      <Tooltip 
                        cursor={{ fill: 'var(--bg2)' }}
                        contentStyle={{ 
                          backgroundColor: 'var(--surface)', 
                          borderRadius: '1.5rem', 
                          border: '1px solid var(--border)', 
                          boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)',
                          padding: '1rem'
                        }}
                        itemStyle={{ color: 'var(--text)', fontWeight: 800, fontSize: '13px' }}
                        labelStyle={{ color: 'var(--text3)', fontWeight: 700, marginBottom: '0.25rem' }}
                        formatter={(value: any) => [formatQuote(Number(value), displayQuote), 'PnL']} 
                      />
                      <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                        {Object.entries(pnl.byAsset).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={Number(entry[1]) >= 0 ? '#6af0c8' : '#f06a6a'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="border rounded-[2.5rem] p-8 shadow-sm h-fit" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-3 mb-8">
                  <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center">
                    <PieChart className="text-accent" size={20} />
                  </div>
                  <h3 className="text-sm font-bold uppercase tracking-widest underline decoration-accent/30 decoration-4 underline-offset-8" style={{ color: 'var(--text)' }}>Event Distribution</h3>
                </div>
                <div className="h-[250px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPieChart>
                      <Pie
                        data={[
                          { name: 'Taxable', value: pnl.taxableEvents },
                          { name: 'Transfers', value: pnl.internalTransfers },
                        ]}
                        cx="50%" cy="50%" 
                        innerRadius={60} outerRadius={90} paddingAngle={8}
                        dataKey="value" stroke="none"
                      >
                        <Cell fill="var(--accent)" />
                        <Cell fill="#6af0c8" />
                      </Pie>
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'var(--surface)', 
                          borderRadius: '1.5rem', 
                          border: '1px solid var(--border)',
                          padding: '1rem'
                        }}
                        itemStyle={{ color: 'var(--text)', fontWeight: 800 }}
                      />
                    </RechartsPieChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center gap-6 mt-4">
                    <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-accent" /> <span className="text-[10px] font-bold" style={{ color: 'var(--text3)' }}>Taxable</span></div>
                    <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#6af0c8]" /> <span className="text-[10px] font-bold" style={{ color: 'var(--text3)' }}>Internal</span></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Brazilian Specific Tax Indicators */}
          {analyzeResult && (
            <div className="border rounded-[2.5rem] p-8 space-y-6" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-3">
                <ShieldCheck className="text-brand-green-500" size={24} />
                <h3 className="text-lg font-syne font-black tracking-tight" style={{ color: 'var(--text)' }}>Regulatory Compliance (BR)</h3>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-bold" style={{ color: 'var(--text)' }}>Monthly Exemption Status (R$ 35,000)</p>
                  <span className={`text-xs font-black uppercase tracking-widest ${latestSales <= threshold ? 'text-brand-green-500' : 'text-danger'}`}>
                    {latestSales <= threshold ? 'Safe Mode' : 'Taxable Mode'}
                  </span>
                </div>
                
                <div className="relative h-4 rounded-full overflow-hidden p-1 shadow-inner" style={{ background: 'var(--bg2)' }}>
                  <motion.div 
                    className={`h-full rounded-full shadow-lg ${latestSales <= threshold ? 'bg-brand-green-500 shadow-brand-green-500/20' : 'bg-danger shadow-danger/20'}`} 
                    initial={{ width: 0 }}
                    animate={{ width: `${progressPct}%` }}
                    transition={{ duration: 1.2, ease: 'circOut' }}
                  />
                  {/* Threshold marker */}
                  <div className="absolute top-0 right-0 h-full w-[2px] bg-danger/30" />
                </div>
                
                <div className="flex justify-between text-[10px] font-bold" style={{ color: 'var(--text3)' }}>
                  <span>{formatQuote(latestSales, 'BRL')} utilized</span>
                  <span>{formatQuote(threshold, 'BRL')} monthly limit</span>
                </div>

                {decriptoRequired && (
                  <div className="mt-6 p-4 rounded-2xl bg-danger/10 border border-danger/20 flex items-start gap-4 animate-in slide-in-from-left">
                    <XCircle className="text-danger flex-shrink-0 mt-0.5" size={18} />
                    <div>
                      <p className="text-[12px] font-black uppercase tracking-widest text-danger">DeCripto Warning</p>
                      <p className="text-[13px] font-bold mt-1 leading-relaxed" style={{ color: 'var(--text)' }}>
                        {decriptoAlert || 'Transaction volume exceeds DeCripto simplified reporting limits.'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Optimization Savings */}
          {savings.length > 0 && (
            <div className="border rounded-[2.5rem] p-8 shadow-sm space-y-4" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-3">
                <Zap className="text-warning" size={24} />
                <h3 className="text-lg font-syne font-black tracking-tight" style={{ color: 'var(--text)' }}>Optimization Opportunities</h3>
              </div>
              <div className="grid grid-cols-1 gap-3">
                {savings.map((s, idx) => (
                  <div key={`${s.asset}-${idx}`} className="p-5 rounded-2xl border flex items-center justify-between group transition-all" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                    <p className="text-[13px] font-bold leading-relaxed pr-8" style={{ color: 'var(--text2)' }}>{s.message_pt}</p>
                    <div className="h-8 w-8 rounded-full bg-warning/10 flex items-center justify-center text-warning">
                      <TrendingUp size={16} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Match Pairs */}
          {matches.length > 0 && (
            <div className="border rounded-[2.5rem] overflow-hidden shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <div className="px-8 py-6 border-b flex items-center justify-between" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                <div>
                  <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Transaction Match Pairings</h3>
                  <p className="text-[11px] mt-1 opacity-50 font-bold" style={{ color: 'var(--text)' }}>High-fidelity audit log of acquisition vs disposal</p>
                </div>
                <div className="px-4 py-2 bg-accent/10 text-accent rounded-full text-[11px] font-black border border-accent/20">
                  {analyzeResult?.matches_found} PAIRS
                </div>
              </div>
              <div className="p-6 space-y-3">
                {displayed.map((m, i) => <MatchRow key={i} match={m} index={i} />)}
              </div>
              {matches.length > 15 && (
                <button onClick={() => setShowAll(!showAll)} className="w-full py-5 border-t text-xs font-black uppercase tracking-[3px] opacity-40 hover:opacity-100 hover:bg-brand-green-500/5 transition-all" style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>
                  {showAll ? 'View Less' : `View All ${matches.length} matches`}
                </button>
              )}
            </div>
          )}
        </div>

        {/* ── RIGHT COLUMN — Settings ── */}
        <div className="space-y-6">

          {/* Calculation Engine Settings */}
          <div className="border rounded-[2.5rem] p-8 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <h3 className="text-sm font-black uppercase tracking-widest mb-8 underline decoration-brand-green-500/30 decoration-4 underline-offset-8" style={{ color: 'var(--text)' }}>Engine Config</h3>
            
            <div className="space-y-8">
              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-widest opacity-40 ml-1" style={{ color: 'var(--text)' }}>Base Currency</label>
                <select value={quoteCurrency} onChange={(e) => setQuoteCurrency(e.target.value as 'BRL' | 'USD')}
                  className="w-full px-4 py-3.5 border rounded-2xl text-[12px] font-bold focus:outline-none focus:border-brand-green-500"
                  style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}>
                  <option value="BRL">BRL (Binance Rate)</option>
                  <option value="USD">USD (Universal)</option>
                </select>
                <label className="flex items-center gap-3 px-2 py-1 cursor-pointer group">
                  <div className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" checked={usePtax} onChange={(e) => setUsePtax(e.target.checked)} className="sr-only peer" />
                    <div className="w-11 h-6 bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-green-500"></div>
                  </div>
                  <span className="text-[11px] font-bold opacity-60 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--text)' }}>Use Official PTAX Rate</span>
                </label>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black uppercase tracking-widest opacity-40 ml-1" style={{ color: 'var(--text)' }}>Accounting Logic</label>
                <div className="grid grid-cols-1 gap-2">
                  {METHODS.map(m => (
                    <button key={m} onClick={() => setAccountingMethod(m)}
                      className={`w-full text-left px-5 py-4 rounded-2xl text-[11px] font-black border transition-all uppercase tracking-widest ${
                        accountingMethod === m
                          ? 'border-brand-green-500 bg-brand-green-500/10 text-brand-green-500 shadow-lg shadow-brand-green-500/10'
                          : 'opacity-40 hover:opacity-100'
                      }`}
                      style={accountingMethod !== m ? { background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' } : undefined}>
                      {m}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Run History Sidebar */}
          <div className="border rounded-[2.5rem] p-8 shadow-sm flex flex-col" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-sm font-black uppercase tracking-widest underline decoration-accent/30 decoration-4 underline-offset-8" style={{ color: 'var(--text)' }}>History</h3>
              <button onClick={handleLoadRunHistory} className="p-2 rounded-lg bg-surface2 border hover:bg-white/5 transition-all" style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text3)' }}>
                <RefreshCw size={14} />
              </button>
            </div>
            
            {runHistory.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center py-12 opacity-20">
                <FileText size={40} className="mb-4" style={{ color: 'var(--text)' }} />
                <p className="text-[11px] font-bold">No previous reports</p>
              </div>
            ) : (
              <div className="space-y-3">
                {runHistory.slice(0, 5).map((r) => (
                  <div key={r.run_id} className="rounded-2xl border p-4 transition-all hover:bg-brand-green-500/5 cursor-pointer" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[9px] font-black opacity-40 uppercase" style={{ color: 'var(--text)' }}>{new Date(r.created_at).toLocaleDateString()}</span>
                      <span className="text-[9px] font-black text-brand-green-500 px-1.5 py-0.5 bg-brand-green-500/10 rounded uppercase">{r.accounting_method}</span>
                    </div>
                    <p className="text-[13px] font-black" style={{ color: 'var(--text)' }}>
                      {formatQuote(r.realized_pnl, r.quote_currency || 'BRL')}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Engine Status Block */}
          <div className={`rounded-[2.5rem] border p-8 shadow-inner transition-all duration-700 ${backendOnline ? 'bg-brand-green-500/5 border-brand-green-500/20 shadow-brand-green-500/5' : 'bg-danger/5 border-danger/20'}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-3 h-3 rounded-full ${backendOnline ? 'bg-brand-green-500 shadow-[0_0_12px_var(--accent)]' : 'bg-danger'}`} />
              <p className="text-[11px] font-black uppercase tracking-[2px]" style={{ color: backendOnline ? 'var(--text)' : 'var(--danger)' }}>
                {backendOnline ? 'System Live' : 'System Down'}
              </p>
            </div>
            <p className="text-[12px] font-bold leading-relaxed opacity-60" style={{ color: 'var(--text)' }}>
              {backendOnline 
                ? 'Hypercharged engine is active. All calculations are real-time and cryptographically verified.' 
                : 'Connection to calculation node lost. Please restart the uvicorn service.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
