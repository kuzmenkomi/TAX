import { useState, useEffect } from 'react';
import {
  Printer,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { useAuth } from '../auth/AuthContext';

export function AuditMode() {
  const { analyzeResult, currentJurisdiction } = useAppContext();
  const { user } = useAuth();
  const [printing, setPrinting] = useState(false);
  const [stampUrl, setStampUrl] = useState<string | null>(null);

  useEffect(() => {
    setStampUrl(`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=DECLAIRO_VERIFY_${analyzeResult?.analysis_run_id || 'DEMO'}`);
  }, [analyzeResult]);

  const handlePrint = () => {
    setPrinting(true);
    setTimeout(() => { window.print(); setPrinting(false); }, 100);
  };

  const pnlData: any = analyzeResult?.pnl || {};
  const totalGain = Number(pnlData.total_realized_pnl_usd || 0);
  const costBasis = Number(pnlData.cost_basis || 0);
  const matchedCount = analyzeResult?.matches_found || 0;
  const totalRows = analyzeResult?.rows_processed || 0;

  if (!analyzeResult) {
    return (
      <div className="text-center py-24">
        <div className="w-20 h-20 mx-auto mb-5 rounded-3xl border flex items-center justify-center shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
          <ShieldCheck className="w-10 h-10" style={{ color: 'var(--text3)' }} />
        </div>
        <h2 className="text-2xl font-syne font-bold mb-2" style={{ color: 'var(--text)' }}>Audit Mode</h2>
        <p className="max-w-xs mx-auto text-[14px]" style={{ color: 'var(--text3)' }}>Run an analysis first to generate a verifiable, audit-ready fiscal report.</p>
      </div>
    );
  }

  return (
    <div className={`max-w-[850px] mx-auto ${printing ? 'bg-white p-0' : 'animate-in fade-in slide-in-from-bottom-4 duration-500'}`}>
      {/* Controls (Hidden when printing) */}
      {!printing && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 pb-6 border-b print:hidden gap-4" style={{ borderColor: 'var(--border)' }}>
          <div>
            <h1 className="text-2xl font-syne font-black tracking-tight flex items-center gap-3" style={{ color: 'var(--text)' }}>
              <ShieldCheck className="w-6 h-6 text-brand-green-500" />
              Audit Mode
            </h1>
            <p className="text-[13px] mt-1" style={{ color: 'var(--text3)' }}>Generate a data-dense, verifiable format for tax authorities.</p>
          </div>
          <button onClick={handlePrint}
            className="flex items-center gap-2 px-6 py-3 bg-brand-green-500 text-brand-dark rounded-xl text-[12px] font-black shadow-lg shadow-brand-green-500/20 hover:bg-brand-green-400 transition-all active:scale-95">
            <Printer className="w-4 h-4" /> EXPORT PDF REPORT
          </button>
        </div>
      )}

      {/* Audit Report Container — White background is forced for printability */}
      <div className="bg-white border rounded-[2rem] p-8 md:p-12 print:border-none print:shadow-none print:p-0 shadow-2xl relative overflow-hidden text-slate-900" style={{ borderColor: 'rgba(0,0,0,0.1)' }}>
        
        {/* Decorative background for the screen view only */}
        {!printing && (
           <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-brand-green-500 via-accent to-[#a78bfa] blur-[1px]" />
        )}

        {/* Watermark */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[120px] font-black text-slate-200 opacity-20 pointer-events-none rotate-[-30deg] select-none z-0">
          CERTIFIED
        </div>

        <div className="relative z-10">
          {/* Document Header */}
          <header className="flex justify-between items-start border-b-2 border-slate-900 pb-8 mb-10">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-slate-900 rounded-lg flex items-center justify-center">
                  <ShieldCheck className="text-white" size={18} />
                </div>
                <h2 className="text-2xl font-black tracking-tighter text-slate-900 uppercase">Declairo Audit Proof</h2>
              </div>
              <div className="text-[11px] text-slate-500 font-mono tracking-tight space-y-1">
                <p>BLOCK_ID: {analyzeResult.analysis_run_id || 'T-2024-X44'}</p>
                <p>ISSUED_AT: {new Date().toUTCString().toUpperCase()}</p>
                <p>METHOD: {analyzeResult.accounting_method || 'FIFO'} / {currentJurisdiction}</p>
              </div>
            </div>
            {stampUrl && (
              <div className="text-right">
                <img src={stampUrl} alt="Verification QR" className="w-24 h-24 ml-auto border border-slate-200 p-1 rounded-xl shadow-inner bg-white" />
                <p className="text-[8px] text-slate-400 mt-2 font-black uppercase tracking-widest">Digital Auth Stamp</p>
              </div>
            )}
          </header>

          {/* User Profile */}
          <section className="mb-10 grid grid-cols-1 sm:grid-cols-2 gap-10">
            <div>
              <h3 className="font-black text-slate-400 uppercase tracking-[3px] text-[10px] mb-4">Taxpayer Profile</h3>
              <div className="space-y-2 border-l-4 border-slate-900 pl-4 py-1">
                <p className="text-sm"><span className="font-black text-slate-900 w-24 inline-block uppercase text-[11px]">Primary Alias:</span> {user?.email ? user.email.split('@')[0] : 'N/A'}</p>
                <p className="text-sm"><span className="font-black text-slate-900 w-24 inline-block uppercase text-[11px]">Registry ID:</span> <span className="font-mono text-xs">{user?.email || 'UNIDENTIFIED'}</span></p>
                <p className="text-sm"><span className="font-black text-slate-900 w-24 inline-block uppercase text-[11px]">Region:</span> {currentJurisdiction}</p>
              </div>
            </div>
            <div>
              <h3 className="font-black text-slate-400 uppercase tracking-[3px] text-[10px] mb-4">Verification Specs</h3>
              <div className="space-y-2 border-l-4 border-slate-900 pl-4 py-1">
                <p className="text-sm"><span className="font-black text-slate-900 w-28 inline-block uppercase text-[11px]">Process Count:</span> <span className="font-mono">{totalRows.toLocaleString()}</span></p>
                <p className="text-sm"><span className="font-black text-slate-900 w-28 inline-block uppercase text-[11px]">Match Integrity:</span> <span className="font-mono">{matchedCount.toLocaleString()} Verified</span></p>
                <p className="text-sm"><span className="font-black text-slate-900 w-28 inline-block uppercase text-[11px]">Currency Unit:</span> {analyzeResult.quote_currency || 'BRL'}</p>
              </div>
            </div>
          </section>

          {/* Financial Summary */}
          <section className="mb-12">
            <h3 className="font-black text-slate-900 uppercase text-xs tracking-[3px] border-b-2 border-slate-100 pb-3 mb-6">Financial Ledger Summary</h3>
            <div className="bg-slate-50 border border-slate-200 rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <tbody className="divide-y divide-slate-200">
                  <tr>
                    <td className="px-6 py-4 text-slate-600 font-bold uppercase text-[11px]">Aggregate Cost Basis</td>
                    <td className="px-6 py-4 text-right font-mono font-black text-slate-900 text-lg">${costBasis.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 text-slate-600 font-bold uppercase text-[11px]">Realized Flux (PnL)</td>
                    <td className={`px-6 py-4 text-right font-mono font-black text-xl ${totalGain >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                      {totalGain >= 0 ? '+' : ''}${totalGain.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                  {analyzeResult.income_events && Object.keys(analyzeResult.income_events).length > 0 && (
                    <tr>
                      <td className="px-6 py-4 text-slate-600 font-bold uppercase text-[11px]">Reportable Global Income</td>
                      <td className="px-6 py-4 text-right font-mono font-black text-slate-900">
                        ${(analyzeResult.income_events.total || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {/* Legal Section */}
          <section className="mb-12 p-6 bg-slate-50 border-l-8 border-slate-900 rounded-r-2xl">
            <div className="flex gap-4">
              <AlertTriangle className="w-6 h-6 text-slate-900 flex-shrink-0" />
              <div className="text-[11px] text-slate-600 leading-relaxed space-y-3">
                <p><strong className="text-slate-900 uppercase">Certification Note:</strong> This document serves as a computational proof of digital asset transactions. Calculations are performed according to local jurisdictional rules selected by the user.</p>
                <p>Hash tracking is used where available to link cross-exchange transfers. Users are advised to verify this report with a qualified local legal representative before final submission.</p>
              </div>
            </div>
          </section>

          {/* Footer */}
          <footer className="mt-16 pt-6 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center gap-4 text-[9px] text-slate-400 font-black uppercase tracking-widest text-center sm:text-left">
            <p>© {new Date().getFullYear()} DECLAIRO SECURE AUDIT PROTOCOL</p>
            <p>DOC_ID: {analyzeResult.analysis_run_id || 'DEMO'}-{Date.now().toString().slice(-4)}</p>
          </footer>
        </div>
      </div>
      
      {/* Help Note (Hidden when printing) */}
      {!printing && (
        <div className="mt-8 p-5 rounded-2xl border text-center" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
          <p className="text-[12px] font-bold" style={{ color: 'var(--text2)' }}>
            💡 Need to add manual attachments? Use the "Export PDF" button above and choose "Save as PDF" to include this report in your local filings.
          </p>
        </div>
      )}
    </div>
  );
}
