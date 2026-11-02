import React from 'react';
import { Calculator, ShieldCheck, FileText, RefreshCw, ChevronDown, XCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '../utils/cn';

// ── Progress Bar ────────────────────────────────────────────────────────────────
export function TaxProgressBar({ step1, step2, step3 }: { step1: boolean; step2: boolean; step3: boolean }) {
  const steps = [
    { label: 'Connect Source', done: step1, now: !step1 },
    { label: 'Configure Engine', done: step2, now: step1 && !step2 },
    { label: 'Review Data', done: step3, now: step2 && !step3 },
    { label: 'Export Report', done: false, now: step3 },
  ];

  return (
    <div className="rounded-[12px] p-[16px] px-[20px] mb-[16px] flex items-center" style={{ background: 'var(--card)', border: '1px solid var(--border)' }}>
      {steps.map((s, i) => (
        <React.Fragment key={i}>
          <div className={cn("flex flex-col items-center gap-[6px] flex-shrink-0 z-10", s.done ? "done" : s.now ? "now" : "idle")}>
            <div className={cn(
              "w-[32px] h-[32px] rounded-full flex items-center justify-center font-syne font-extrabold text-[12px] transition-all",
              s.done ? "bg-[var(--accent)] text-black shadow-[0_0_0_4px_rgba(16, 185, 129,0.12)]" :
              s.now ? "bg-[rgba(16, 185, 129,0.12)] border-2 border-[var(--accent)] text-[var(--accent)]" : ""
            )}
            style={!s.done && !s.now ? { background: 'var(--card2)', border: '1px solid var(--border2)', color: 'var(--text3)' } : undefined}
            >
              {s.done ? '✓' : i + 1}
            </div>
            <span className={cn("text-[10px] font-semibold whitespace-nowrap",
              s.done ? "text-[var(--accent)]" : "")}
              style={!s.done ? { color: s.now ? 'var(--text)' : 'var(--text3)' } : undefined}
            >
              {s.label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div className="flex-1 h-[2px] mt-[-19px] z-0">
              <div className={cn("h-full transition-all duration-500", s.done ? "bg-[var(--accent)]" : "")}
                style={!s.done ? { background: 'var(--border2)' } : undefined}
              />
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

// ── Engine Config Panel ─────────────────────────────────────────────────────────
export function EngineConfigPanel({ quoteCurrency, setQuoteCurrency, usePtax, setUsePtax, accountingMethod, setAccountingMethod }: any) {
  const METHODS = [
    { id: 'FIFO', name: 'First In First Out' },
    { id: 'LIFO', name: 'Last In First Out' },
    { id: 'HIFO', name: 'Highest In First Out' },
    { id: 'AVCO', name: 'Average Cost' }
  ];

  return (
    <div className="flex flex-col gap-[14px]">
      <div className="card">
        <div className="card-hd">
          <span className="card-title">BASE CURRENCY</span>
        </div>
        <div className="p-[16px] space-y-[12px]">
          <div className="form-field">
            <select value={quoteCurrency} onChange={e => setQuoteCurrency(e.target.value)} className="form-select">
              <option value="BRL">BRL — Binance Rate</option>
              <option value="BRL_PTAX">BRL — Official PTAX Rate</option>
              <option value="USD">USD — Universal Rate</option>
            </select>
          </div>
          <div className="flex items-center justify-between mt-[8px]">
            <div>
              <p className="text-[12px] font-semibold" style={{ color: 'var(--text)' }}>Use Official PTAX Rate</p>
              <p className="text-[10px]" style={{ color: 'var(--text3)' }}>Recommended by Receita Federal</p>
            </div>
            <div onClick={() => setUsePtax(!usePtax)} className={cn("toggle", usePtax && "on")}>
              <div className="toggle-knob" />
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-hd">
          <span className="card-title">ACCOUNTING LOGIC</span>
        </div>
        <div className="p-[16px] space-y-[5px]">
          {METHODS.map(m => (
            <div key={m.id} onClick={() => setAccountingMethod(m.id)} className={cn("logic-btn", accountingMethod === m.id && "sel")}>
              <div className="flex flex-col text-left">
                <span>{m.id}</span>
                <span className="logic-desc opacity-50">{m.name}</span>
              </div>
              {accountingMethod === m.id && <div className="w-[6px] h-[6px] rounded-full bg-[var(--accent)]" />}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Results Summary ─────────────────────────────────────────────────────────────
export function TaxResultsSummary({ pnl, displayQuote, accountingMethod, estimatedTax, latestSales, threshold, progressPct, handleDownload, formatQuote, fnameLabel }: any) {
  return (
    <div className="grid grid-cols-[1fr_260px] gap-[14px] animate-fade-in">
      <div className="space-y-[14px]">
        <div className="grid grid-cols-4 gap-[12px]">
          {[
            { label: 'TOTAL REALIZED P&L', val: formatQuote(pnl.net, displayQuote), color: pnl.net >= 0 ? 'var(--accent)' : '#ff4d6a' },
            { label: 'PORTFOLIO GAIN', val: formatQuote(pnl.totalGain, displayQuote), color: 'var(--accent)' },
            { label: 'REALIZED LOSS', val: formatQuote(pnl.totalLoss, displayQuote), color: '#ff4d6a' },
            { label: 'EST. LIABILITY', val: formatQuote(estimatedTax, displayQuote), color: '#f59e0b' },
          ].map((kpi, i) => (
            <div key={i} className="kpi">
              <p className="kpi-label">{kpi.label}</p>
              <p className="kpi-value" style={{ color: kpi.color }}>{kpi.val}</p>
              <div className="kpi-change neutral"><span>{accountingMethod} Basis</span></div>
            </div>
          ))}
        </div>

        <div className="card">
          <div className="card-hd"><span className="card-title">TAX REPORTS & EXPORTS</span></div>
          <div className="p-[16px] reports-grid">
            {[
              { label: 'Comprehensive CSV', format: 'br', ext: 'csv', icon: '📊', desc: 'Full audit history for Receita Federal' },
              { label: 'Tax Audit PDF', format: 'audit', ext: 'pdf', icon: '📄', desc: 'Signed summary with methodology' },
              { label: 'DeCripto JSON', format: 'decripto', ext: 'json', icon: '💎', desc: 'Secure portable tax record' },
              { label: 'GCAP Format', format: 'gcap', ext: 'csv', icon: '🇧🇷', desc: 'Optimized for GCAP software' },
            ].map((report, i) => (
              <div key={i} onClick={() => handleDownload(report.format, report.ext)} className="report-card">
                <div className="report-icon">{report.icon}</div>
                <p className="report-name">{report.label}</p>
                <p className="report-desc">{report.desc}</p>
                <div className="report-footer">
                  <span className="report-format uppercase">{report.ext}</span>
                  <span className="report-dl">DOWNLOAD</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-[14px]">
        <div className="card">
          <div className="card-hd"><span className="card-title">COMPLIANCE (BR)</span></div>
          <div className="p-[16px] space-y-[12px]">
            <div>
              <p className="text-[12px] font-semibold" style={{ color: 'var(--text)' }}>Monthly Exemption</p>
              <p className="text-[10px]" style={{ color: 'var(--text3)' }}>Limit: R$ 35,000.00</p>
            </div>
            <div className="h-[8px] w-full rounded-full overflow-hidden" style={{ background: 'var(--card2)', border: '1px solid var(--border)' }}>
              <div className={cn("h-full transition-all duration-1000", progressPct > 100 ? "bg-[#ff4d6a]" : "bg-[var(--accent)]")} style={{ width: `${Math.min(progressPct, 100)}%` }} />
            </div>
            <div className="flex justify-between text-[9px] font-bold" style={{ color: 'var(--text3)' }}>
              <span>{Math.round(progressPct)}% USED</span>
              <span>R$ 35k</span>
            </div>
            <div className={cn("tag w-full justify-center py-[4px]", progressPct < 100 ? "tag-green" : "tag-red")}>
              {progressPct < 100 ? 'SAFE MODE' : 'TAXABLE MODE'}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="p-[16px] space-y-[10px]">
            <div className="flex items-center gap-[8px]">
              <ShieldCheck className="text-[var(--accent)] w-[16px] h-[16px]" />
              <span className="text-[11px] font-bold" style={{ color: 'var(--text)' }}>Data Verified</span>
            </div>
            <p className="text-[10px] leading-relaxed" style={{ color: 'var(--text3)' }}>
              Your transactions are matched using institutional grade FIFO/LIFO logic.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── History Bar ───────────────────────────────────────────────────────────────
export function HistoryBar({ runHistory, onLoad, formatQuote }: any) {
  const [open, setOpen] = React.useState(false);
  return (
    <div className="card mt-[16px]">
      <div onClick={() => { setOpen(!open); if(!open) onLoad(); }} className="card-hd cursor-pointer" style={{ transition: 'background 0.2s' }}
        onMouseEnter={e => (e.currentTarget.style.background = 'var(--card2)')} onMouseLeave={e => (e.currentTarget.style.background = '')}>
        <span className="card-title flex items-center gap-[8px]">
          <RefreshCw size={14} className={cn(open && "animate-spin")} /> CALCULATION HISTORY
        </span>
        <ChevronDown size={14} className={cn("transition-transform", open && "rotate-180")} />
      </div>
      {open && (
        <div className="p-[16px] space-y-[8px] animate-fade-in">
          {runHistory.length === 0 ? (
            <p className="text-center py-[20px] text-[11px] italic" style={{ color: 'var(--text3)' }}>No history found</p>
          ) : (
            runHistory.map((r: any) => (
              <div key={r.run_id} className="flex items-center justify-between p-[10px] rounded-[8px]" style={{ background: 'var(--card2)', border: '1px solid var(--border)' }}>
                <div>
                  <p className="text-[12px] font-bold" style={{ color: 'var(--text)' }}>{formatQuote(r.realized_pnl, r.quote_currency)}</p>
                  <p className="text-[9px]" style={{ color: 'var(--text3)' }}>{new Date(r.created_at).toLocaleDateString()}</p>
                </div>
                <span className="tag tag-gray uppercase">{r.accounting_method}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
