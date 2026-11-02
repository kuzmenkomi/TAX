import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  Loader2, 
  Lock, 
  Sparkles,
  ArrowRight,
  ShieldCheck,
  FileSpreadsheet
} from 'lucide-react';
import apiV1 from '../api/v1';
import { useAppContext } from '../context/AppContext';
import { useToast } from '../context/ToastContext';
import { UpgradeModal } from './UpgradeModal';
import { cn } from '../utils/cn';

export function GenerateReportsPanel() {
  const { addToast } = useToast();
  const { analyzeResult } = useAppContext();
  
  const [planCheck, setPlanCheck] = useState<{ can_export: boolean; plan: string; upgrade_required: boolean } | null>(null);
  const [upgradeOpen, setUpgradeOpen] = useState(false);
  const [generatingFormat, setGeneratingFormat] = useState<'csv' | 'pdf' | null>(null);
  const [taskProgress, setTaskProgress] = useState<{ progress: number; message: string } | null>(null);

  // Live plan checking on mount
  useEffect(() => {
    let active = true;
    const checkUserPlan = async () => {
      try {
        const res = await apiV1.exports.planCheck();
        if (active) {
          setPlanCheck(res);
        }
      } catch (err) {
        console.error("Plan check failed", err);
      }
    };
    checkUserPlan();
    return () => { active = false; };
  }, []);

  const triggerBlobDownload = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const handleDownload = async (format: 'csv' | 'pdf') => {
    if (planCheck?.plan === 'free') {
      setUpgradeOpen(true);
      return;
    }

    setGeneratingFormat(format);
    setTaskProgress({ progress: 10, message: "Initiating report generation..." });
    
    try {
      const runId = analyzeResult?.analysis_run_id;
      if (!runId) throw new Error("No calculation run ID found. Please recalculate.");
      
      // Step 1: Request generation
      const res = await apiV1.exports.generate(format, runId);
      
      if (res.status === 'completed') {
        setTaskProgress({ progress: 100, message: "Download started." });
        const blob = await apiV1.exports.download(res.task_id);
        triggerBlobDownload(blob, `declairo_tax_report_${runId}.${format}`);
        addToast(`${format.toUpperCase()} Report downloaded successfully!`, 'success');
      } else {
        // Step 2: Poll status
        const taskId = res.task_id;
        let finished = false;
        let attempts = 0;
        
        while (!finished && attempts < 100) { // ~5 minutes max
          await new Promise(resolve => setTimeout(resolve, 3000));
          attempts++;
          
          const statusRes = await apiV1.exports.checkStatus(taskId);
          
          if (statusRes.status === 'completed') {
            finished = true;
            setTaskProgress({ progress: 100, message: "Download started." });
            const blob = await apiV1.exports.download(taskId);
            triggerBlobDownload(blob, `declairo_tax_report_${runId}.${format}`);
            addToast(`${format.toUpperCase()} Report downloaded successfully!`, 'success');
          } else if (statusRes.status === 'failed') {
            throw new Error(statusRes.error || "Async report generation failed");
          } else {
            setTaskProgress({ 
              progress: statusRes.progress, 
              message: statusRes.message || "Generating report in background..." 
            });
          }
        }
        
        if (!finished) {
          throw new Error("Report generation timed out. Please check again in a few minutes.");
        }
      }
    } catch (err: any) {
      addToast(err.message || `Failed to download ${format.toUpperCase()}`, 'error');
    } finally {
      setGeneratingFormat(null);
      setTaskProgress(null);
    }
  };

  const isFreePlan = planCheck?.plan === 'free';

  return (
    <div className="space-y-6 animate-fade-in relative">
      <div className="flex flex-col md:flex-row gap-6">
        
        {/* CSV Export Card */}
        <div 
          className="flex-1 rounded-2xl border border-[var(--border)] p-6 flex flex-col justify-between relative overflow-hidden group hover:border-[var(--accent)]/20 transition-all duration-300"
          style={{ background: 'var(--card)' }}
        >
          <div className="space-y-4">
            <div className="flex justify-between items-start">
              <div className="w-10 h-10 rounded-xl bg-[var(--accent-dim)] flex items-center justify-center text-[var(--accent)]">
                <FileSpreadsheet size={20} />
              </div>
              {isFreePlan && (
                <span
                  className="text-[10px] font-black tracking-wider uppercase px-2 py-0.5 rounded text-[var(--text2)] flex items-center gap-1"
                  style={{ background: 'var(--card2)', border: '1px solid var(--border)' }}
                >
                  <Lock size={10} /> Paid Tiers
                </span>
              )}
            </div>
            <div className="space-y-1.5">
              <h4 className="font-syne font-bold text-lg text-[var(--text)]">CSV Data Export</h4>
              <p className="text-[12px] text-[var(--text2)] leading-relaxed">
                Download raw calculated transaction logs (Buy/Sell, quantity, price, fee, realized P&L). Standard RFC 4180 format for easy importing into Excel, Google Sheets, or other ledger software.
              </p>
            </div>
          </div>

          <div className="pt-8">
            <button
              onClick={() => handleDownload('csv')}
              disabled={generatingFormat !== null}
              className={cn(
                'w-full flex items-center justify-center gap-2 font-black py-3 px-4 rounded-xl text-[12px] transition-all hover:scale-[1.01]',
                isFreePlan ? 'text-[var(--text3)] cursor-not-allowed' : 'text-[var(--text)] hover:opacity-90',
              )}
              style={{
                background: 'var(--card2)',
                border: `1px solid ${isFreePlan ? 'var(--border)' : 'var(--border2)'}`,
              }}
            >
              {generatingFormat === 'csv' ? (
                <>
                  <Loader2 size={16} className="animate-spin text-[var(--accent)]" />
                  <span>{taskProgress?.progress}% · {taskProgress?.message}</span>
                </>
              ) : (
                <>
                  <Download size={14} />
                  <span>DOWNLOAD CSV DATA</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* PDF Official Tax Report Card */}
        <div 
          className="flex-1 rounded-2xl border border-[var(--border)] p-6 flex flex-col justify-between relative overflow-hidden group hover:border-[var(--accent)]/20 transition-all duration-300"
          style={{ background: 'var(--card)' }}
        >
          {/* Top glow */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-[var(--accent)]/5 rounded-full blur-2xl pointer-events-none" />

          <div className="space-y-4 relative">
            <div className="flex justify-between items-start">
              <div className="w-10 h-10 rounded-xl bg-[var(--accent-dim)] flex items-center justify-center text-[var(--accent)]">
                <FileText size={20} />
              </div>
              {isFreePlan ? (
                <span className="text-[10px] font-black tracking-wider uppercase px-2 py-0.5 rounded bg-[var(--accent)] text-white flex items-center gap-1">
                  <Lock size={10} /> UPGRADE
                </span>
              ) : (
                <span className="text-[10px] font-black tracking-wider uppercase px-2 py-0.5 rounded bg-[var(--accent-dim)] text-[var(--accent)] border border-[var(--accent)]/30">
                  Premium Active
                </span>
              )}
            </div>
            <div className="space-y-1.5">
              <h4 className="font-syne font-bold text-lg text-[var(--text)]">PDF Official Tax Report</h4>
              <p className="text-[12px] text-[var(--text2)] leading-relaxed">
                Generate a beautifully styled, branded Declairo tax report with cover page, jurisdiction filing profiles, summary cards, and multi-page FIFO match logs compliant with audit procedures.
              </p>
            </div>
          </div>

          <div className="pt-8 relative">
            <button
              onClick={() => handleDownload('pdf')}
              disabled={generatingFormat !== null}
              className="w-full flex items-center justify-center gap-2 bg-[var(--accent)] disabled:bg-[var(--accent-dim)] disabled:text-[var(--text3)] text-white font-black py-3 px-4 rounded-xl text-[12px] transition-all hover:scale-[1.01] shadow-[var(--accent-shadow-md)]"
            >
              {generatingFormat === 'pdf' ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>{taskProgress?.progress}% · {taskProgress?.message}</span>
                </>
              ) : (
                <>
                  <Download size={14} />
                  <span>DOWNLOAD PDF COMPLIANCE REPORT</span>
                </>
              )}
            </button>
          </div>
        </div>

      </div>

      {/* Free Plan Glassmorphic Gated Overlay */}
      {isFreePlan && (
        <div
          className="rounded-2xl border border-[var(--border)] p-8 flex flex-col md:flex-row items-center justify-between gap-6 relative overflow-hidden mt-6"
          style={{
            background: 'linear-gradient(135deg, var(--accent-dim) 0%, var(--card2) 100%)',
          }}
        >
          {/* Subtle Accent Glow */}
          <div className="absolute -top-10 -left-10 w-40 h-40 bg-[var(--accent)]/5 rounded-full blur-3xl pointer-events-none" />
          
          <div className="space-y-2 text-center md:text-left relative">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[var(--accent-dim)] border border-[var(--accent)]/20 text-[var(--accent)] text-[9px] font-black tracking-wide uppercase">
              <Sparkles size={10} className="fill-[var(--accent)]" /> Gated Plan Feature
            </div>
            <h5 className="font-syne font-bold text-[var(--text)] text-[15px]">You&apos;re on the Free tier plan.</h5>
            <p className="text-[12px] text-[var(--text2)] max-w-[500px] leading-relaxed">
              Export is locked for the Free plan. Upgrade to the **Starter** or **Pro** plan to unlock immediate CSV and PDF downloads.
            </p>
          </div>

          <button
            onClick={() => setUpgradeOpen(true)}
            className="flex items-center justify-center gap-2 bg-[var(--accent)] text-white font-black py-3.5 px-8 rounded-xl text-[12px] hover:scale-[1.03] transition-all shadow-[var(--accent-shadow-md)] flex-shrink-0"
          >
            <ShieldCheck size={16} />
            UPGRADE NOW <ArrowRight size={14} strokeWidth={3} />
          </button>
        </div>
      )}

      {/* Upgrade Modal */}
      <UpgradeModal 
        isOpen={upgradeOpen} 
        onClose={() => setUpgradeOpen(false)} 
        currentPlan="free" 
      />
    </div>
  );
}
