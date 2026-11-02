import { useRef, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  XCircle,
  Loader2,
  ChevronDown,
  RefreshCw,
  Plus
} from 'lucide-react';
import apiV1, {
  AnalyzeResult,
  MatchEntry,
  RunHistoryItem,
} from '../api/v1';
import { useAppContext } from '../context/AppContext';
import { useI18n } from '../i18n/I18nContext';
import { TaxProgressBar, EngineConfigPanel, TaxResultsSummary, HistoryBar } from './TaxCenterShell';
import { cn } from '../utils/cn';
import { UpgradeModal } from './UpgradeModal';

// ── Helpers ──────────────────────────────────────────────────────────────────
function formatQuote(n: number | undefined | null, currency: string): string {
  if (n == null || isNaN(Number(n))) return '—';
  const ccy = currency === 'BRL' ? 'BRL' : 'USD';
  const loc = currency === 'BRL' ? 'pt-BR' : 'en-US';
  return new Intl.NumberFormat(loc, { style: 'currency', currency: ccy }).format(Number(n));
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

// ── Match Row ────────────────────────────────────────────────────────────────
function MatchRow({ match, index }: { match: MatchEntry; index: number }) {
  const [open, setOpen] = useState(false);
  const asset = String(match.asset ?? match.symbol ?? '—').toUpperCase();
  const confidence = Number(match.confidence ?? 0);
  const explanation = String(match.explanation ?? 'No explanation available');

  return (
    <div className="rounded-[9px] overflow-hidden mb-[8px]" style={{ background: 'var(--card2)', border: '1px solid var(--border)' }}>
      <div 
        className="p-[12px] flex items-center justify-between cursor-pointer" 
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-[12px]">
          <span className="text-[11px] font-bold" style={{ color: 'var(--text3)' }}>#{index + 1}</span>
          <span className="text-[13px] font-bold" style={{ color: 'var(--text)' }}>{asset}</span>
          <span className={cn(
            "text-[9px] font-extrabold px-[6px] py-[2px] rounded-full",
            confidence >= 0.8 ? "bg-[rgba(16, 185, 129,0.1)] text-[var(--accent)]" : "bg-[rgba(245,158,11,0.1)] text-[#f59e0b]"
          )}>
            {Math.round(confidence * 100)}% MATCH
          </span>
        </div>
        <ChevronDown size={14} className={cn("transition-transform", open && "rotate-180")} style={{ color: 'var(--text3)' }} />
      </div>
      <AnimatePresence>
        {open && (
          <motion.div 
            initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}
            className="overflow-hidden" style={{ borderTop: '1px solid var(--border)' }}
          >
            <div className="p-[12px] text-[11px] leading-relaxed italic" style={{ color: 'var(--text2)' }}>
              {explanation}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────
export function TaxOptimizer() {
  const {
    analyzeResult, setAnalyzeResult,
    accountingMethod, setAccountingMethod,
    isLoading, setIsLoading,
    error, setError,
    uploadedFile, setUploadedFile,
    backendOnline,
  } = useAppContext();
  
  const multiRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [quoteCurrency, setQuoteCurrency] = useState<'BRL' | 'USD'>('BRL');
  const [usePtax, setUsePtax] = useState(false);
  const [importTab, setImportTab] = useState<'exchange' | 'csv' | 'wallet'>('csv');
  const [runHistory, setRunHistory] = useState<RunHistoryItem[]>([]);
  const [upgradeOpen, setUpgradeOpen] = useState(false);

  // ── Handlers ──
  async function handleMultiAnalyze() {
    if (!backendOnline) return;
    const fl = multiRef.current?.files;
    if (!fl?.length) { setError('Select one or more CSVs.'); return; }
    setIsLoading(true); setError(null); setAnalyzeResult(null);
    try {
      const result = await apiV1.analysis.uploadMulti(Array.from(fl), { 
        format: 'native', accounting_method: accountingMethod, country: 'br', 
        quote_currency: quoteCurrency, use_ptax: usePtax 
      });
      setAnalyzeResult(result);
    } catch (e) { setError(e instanceof Error ? e.message : 'Upload error'); }
    finally { setIsLoading(false); }
  }

  const handleDownload = async (format: any, ext: string) => {
    const id = analyzeResult?.analysis_run_id;
    if (!id) return;
    try {
      const blob = await apiV1.tax.exportReport(id as number, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `tax_report_${id}.${ext}`; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { setError(e instanceof Error ? e.message : 'Download failed'); }
  };

  async function handleLoadRunHistory() {
    try { 
      const data = await apiV1.analysis.listRuns();
      setRunHistory(data.runs || []); 
    } catch { /* silent */ }
  }

  function reset() {
    setUploadedFile(null); setAnalyzeResult(null); setError(null);
  }

  const pnl = analyzeResult ? parsePnl(analyzeResult.pnl) : null;
  const matches = analyzeResult?.matches ?? [];
  const estimatedTax = pnl ? Math.max(0, pnl.net * 0.15) : 0;
  const monthSalesMap = analyzeResult?.monthly_sales_brl ?? {};
  const latestMonth = Object.keys(monthSalesMap).sort().at(-1) ?? '';
  const latestSales = latestMonth ? Number(monthSalesMap[latestMonth] ?? 0) : 0;
  const threshold = Number(analyzeResult?.isencao_threshold_brl ?? 35000);
  const progressPct = threshold > 0 ? (latestSales / threshold) * 100 : 0;
  const displayQuote = (analyzeResult?.quote_currency as string) || quoteCurrency;
  const fnameLabel = analyzeResult?.filename ? (Array.isArray(analyzeResult.filename) ? analyzeResult.filename.join(', ') : analyzeResult.filename) : '';

  const step1 = !!(analyzeResult || uploadedFile);
  const step2 = !!(analyzeResult);
  const step3 = !!(analyzeResult && matches.length > 0);

  return (
    <div className="space-y-[16px] animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
           <h1 className="font-syne font-extrabold text-[24px] tracking-tight" style={{ color: 'var(--text)' }}>Tax Optimizer</h1>
           <p className="text-[12px]" style={{ color: 'var(--text3)' }}>Calculate crypto liabilities and export reports for Receita Federal.</p>
        </div>
        {analyzeResult && (
          <button onClick={reset} className="btn-secondary flex items-center gap-[8px]">
             <RefreshCw size={14} /> NEW ANALYSIS
          </button>
        )}
      </div>

      <TaxProgressBar step1={step1} step2={step2} step3={step3} />

      {!analyzeResult && !isLoading ? (
        <div className="grid grid-cols-[1fr_260px] gap-[14px]">
           <div className="space-y-[14px]">
              <div className="card">
                 <div className="card-hd">
                    <span className="card-title">IMPORT DATA SOURCE</span>
                 </div>
                 <div className="p-[24px]">
                    <div 
                      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                      onDragLeave={() => setDragOver(false)}
                      onDrop={(e) => {
                        e.preventDefault(); setDragOver(false);
                        const fl = e.dataTransfer.files;
                        if (fl && multiRef.current) {
                           multiRef.current.files = fl;
                           handleMultiAnalyze();
                        }
                      }}
                      className={cn(
                        "border-2 border-dashed rounded-[14px] p-[40px] text-center transition-all cursor-pointer group",
                        dragOver ? "border-[var(--accent)] bg-[rgba(16, 185, 129,0.05)]" : "hover:border-[rgba(16, 185, 129,0.3)]"
                      )}
                      style={!dragOver ? { borderColor: 'var(--border2)', background: 'var(--bg)' } : undefined}
                      onClick={() => multiRef.current?.click()}
                    >
                       <Upload size={32} className="mx-auto mb-[16px] group-hover:text-[var(--accent)] transition-colors" style={{ color: 'var(--text3)' }} />
                       <p className="text-[14px] font-bold mb-[4px]" style={{ color: 'var(--text)' }}>Drop your CSV files here</p>
                       <p className="text-[11px]" style={{ color: 'var(--text3)' }}>Supported: Binance, Coinbase, Mercado Bitcoin, Foxbit.</p>
                       <input ref={multiRef} type="file" multiple accept=".csv" className="hidden" onChange={handleMultiAnalyze} />
                    </div>
                    
                    {error && (
                      <div className="mt-[16px] space-y-2">
                        <div className="p-[10px] bg-[rgba(255,77,106,0.1)] border border-[rgba(255,77,106,0.2)] rounded-[8px] flex items-center gap-[8px]">
                           <XCircle size={14} className="text-[#ff4d6a]" />
                           <span className="text-[11px] font-bold text-[#ff4d6a]">{error}</span>
                        </div>
                        {(error.toLowerCase().includes('limit') || error.toLowerCase().includes('upgrade')) && (
                          <button 
                            onClick={() => setUpgradeOpen(true)}
                            className="w-full flex items-center justify-center gap-1.5 py-2.5 px-4 rounded-xl text-[11px] font-bold bg-[var(--accent)] text-black hover:opacity-90 transition-all cursor-pointer shadow-[0_0_15px_rgba(16, 185, 129,0.15)]"
                          >
                            Upgrade Plan to Process More Transactions
                          </button>
                        )}
                      </div>
                    )}
                 </div>
              </div>

              <div className="card">
                 <div className="card-hd">
                    <span className="card-title">ALTERNATIVE METHODS</span>
                 </div>
                 <div className="p-[16px] grid grid-cols-2 gap-[12px]">
                    <div className="p-[16px] rounded-[11px] opacity-50 cursor-not-allowed" style={{ background: 'var(--card2)', border: '1px solid var(--border)' }}>
                       <p className="text-[12px] font-bold mb-[4px]" style={{ color: 'var(--text)' }}>Exchange API</p>
                       <p className="text-[10px]" style={{ color: 'var(--text3)' }}>Connect via read-only API keys for live tracking.</p>
                    </div>
                    <div className="p-[16px] rounded-[11px] opacity-50 cursor-not-allowed" style={{ background: 'var(--card2)', border: '1px solid var(--border)' }}>
                       <p className="text-[12px] font-bold mb-[4px]" style={{ color: 'var(--text)' }}>On-chain Scan</p>
                       <p className="text-[10px]" style={{ color: 'var(--text3)' }}>Input wallet address for ETH, BSC, Polygon.</p>
                    </div>
                 </div>
              </div>
           </div>

           <EngineConfigPanel
             quoteCurrency={quoteCurrency} setQuoteCurrency={setQuoteCurrency}
             usePtax={usePtax} setUsePtax={setUsePtax}
             accountingMethod={accountingMethod} setAccountingMethod={setAccountingMethod}
           />
        </div>
      ) : isLoading ? (
        <div className="h-[400px] flex flex-col items-center justify-center text-center">
           <Loader2 size={40} className="text-[var(--accent)] animate-spin mb-[16px]" />
           <h2 className="font-syne font-extrabold text-[20px] mb-[4px]" style={{ color: 'var(--text)' }}>Processing Ledger</h2>
           <p className="text-[12px]" style={{ color: 'var(--text3)' }}>Applying {accountingMethod} logic to your transaction stream...</p>
        </div>
      ) : (
        <div className="space-y-[14px]">
           <TaxResultsSummary
             pnl={pnl} displayQuote={displayQuote} accountingMethod={accountingMethod}
             estimatedTax={estimatedTax} latestSales={latestSales} threshold={threshold}
             progressPct={progressPct} handleDownload={handleDownload} formatQuote={formatQuote}
             fnameLabel={fnameLabel}
           />
           
           {matches.length > 0 && (
             <div className="card">
                <div className="card-hd">
                   <span className="card-title">INTERNAL TRANSFER MATCHES</span>
                   <span className="tag tag-gray">{matches.length} FOUND</span>
                </div>
                <div className="p-[16px]">
                   {matches.slice(0, 10).map((m, i) => (
                     <MatchRow key={i} match={m} index={i} />
                   ))}
                </div>
             </div>
           )}
        </div>
      )}

      <HistoryBar runHistory={runHistory} onLoad={handleLoadRunHistory} formatQuote={formatQuote} />
      <UpgradeModal 
        isOpen={upgradeOpen} 
        onClose={() => setUpgradeOpen(false)} 
        currentPlan="free" 
      />
    </div>
  );
}
