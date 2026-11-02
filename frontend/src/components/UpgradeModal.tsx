import React, { useState } from 'react';
import { ShieldCheck, Zap, X, Check, Loader2 } from 'lucide-react';
import { billing } from '../api/v1';
import { useToast } from '../context/ToastContext';
import { cn } from '../utils/cn';

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPlan?: string;
}

export function UpgradeModal({ isOpen, onClose, currentPlan = 'free' }: UpgradeModalProps) {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const successUrl = window.location.origin + '/tax-center?payment=success';
      const cancelUrl = window.location.origin + '/tax-center?payment=cancelled';
      const res = await billing.createCheckout('starter', successUrl, cancelUrl);
      if (res.url) {
        window.location.href = res.url;
      } else {
        throw new Error('No checkout URL returned');
      }
    } catch (err: any) {
      addToast(err.message || 'Failed to start checkout. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-md transition-opacity" 
        onClick={onClose}
      />

      {/* Glassmorphic Container */}
      <div 
        className="relative max-w-lg w-full rounded-3xl overflow-hidden shadow-[0_0_50px_0_rgba(0,0,0,0.5)] border border-slate-800 transition-all transform scale-100"
        style={{
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(9, 15, 29, 0.95) 100%)',
          backdropFilter: 'blur(20px)',
        }}
      >
        {/* Glow Effects */}
        <div className="absolute top-0 left-1/4 w-40 h-40 bg-[var(--accent)]/10 rounded-full blur-[80px]" />
        <div className="absolute bottom-0 right-1/4 w-40 h-40 bg-blue-500/10 rounded-full blur-[80px]" />

        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white bg-slate-800/40 hover:bg-slate-800/80 rounded-full p-1.5 transition-all z-10"
        >
          <X size={16} />
        </button>

        <div className="p-8 relative">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-[var(--accent-dim)] border border-[var(--accent)]/30 text-[var(--accent)] mb-4 shadow-[0_0_15px_rgba(16, 185, 129,0.15)]">
              <Zap size={24} className="fill-[var(--accent)]" />
            </div>
            <h3 className="font-syne font-extrabold text-2xl text-white tracking-tight">Upgrade to Premium</h3>
            <p className="text-[13px] text-slate-400 mt-1.5">
              Unlock professional tax exports and compliance-ready reports.
            </p>
          </div>

          {/* Features Comparison */}
          <div className="space-y-3.5 mb-8">
            <div 
              className="flex items-start gap-3.5 p-3.5 rounded-2xl border border-slate-800/60"
              style={{ background: 'rgba(255, 255, 255, 0.02)' }}
            >
              <div className="w-5 h-5 rounded-full bg-[var(--accent-dim)] flex items-center justify-center text-[var(--accent)] flex-shrink-0 mt-0.5">
                <Check size={12} strokeWidth={3} />
              </div>
              <div>
                <p className="text-[13px] font-bold text-slate-200">Unlimited CSV & PDF Exports</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Official "Declairo" premium reports compliant with local tax authorities.</p>
              </div>
            </div>

            <div 
              className="flex items-start gap-3.5 p-3.5 rounded-2xl border border-slate-800/60"
              style={{ background: 'rgba(255, 255, 255, 0.02)' }}
            >
              <div className="w-5 h-5 rounded-full bg-[var(--accent-dim)] flex items-center justify-center text-[var(--accent)] flex-shrink-0 mt-0.5">
                <Check size={12} strokeWidth={3} />
              </div>
              <div>
                <p className="text-[13px] font-bold text-slate-200">Large Datasets Support</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Process thousands of transactions asynchronously in the background.</p>
              </div>
            </div>

            <div 
              className="flex items-start gap-3.5 p-3.5 rounded-2xl border border-slate-800/60"
              style={{ background: 'rgba(255, 255, 255, 0.02)' }}
            >
              <div className="w-5 h-5 rounded-full bg-[var(--accent-dim)] flex items-center justify-center text-[var(--accent)] flex-shrink-0 mt-0.5">
                <Check size={12} strokeWidth={3} />
              </div>
              <div>
                <p className="text-[13px] font-bold text-slate-200">FIFO, HIFO, and Weighted Average Methods</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Advanced matching rules dynamically tailored to your tax jurisdiction.</p>
              </div>
            </div>
          </div>

          {/* Pricing & Call to Action */}
          <div className="space-y-4">
            <div className="flex items-baseline justify-center gap-1.5">
              <span className="text-3xl font-extrabold text-white font-syne">$29</span>
              <span className="text-slate-400 text-sm">/ year</span>
              <span className="ml-2.5 text-[10px] font-black uppercase tracking-wider px-2 py-0.5 bg-[var(--accent)] text-black rounded-md">SAVE 50%</span>
            </div>
            
            <button
              onClick={handleUpgrade}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-[var(--accent)] disabled:bg-[var(--accent-dim)] text-black font-black py-4 rounded-2xl transition-all duration-300 hover:scale-[1.02] shadow-[0_0_24px_rgba(16, 185, 129,0.25)] hover:shadow-[0_0_35px_rgba(16, 185, 129,0.4)]"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  STARTING SECURE CHECKOUT...
                </>
              ) : (
                <>
                  <ShieldCheck size={18} />
                  UPGRADE NOW
                </>
              )}
            </button>
            
            <button
              onClick={onClose}
              disabled={loading}
              className="w-full text-center text-[12px] font-bold text-slate-400 hover:text-slate-200 transition-colors uppercase tracking-wider py-1"
            >
              Maybe Later
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
