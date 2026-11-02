import React, { useState, useEffect } from 'react';
import { billing } from '../api/v1';
import { CheckCircle, Zap, Shield, Crown, ArrowLeft, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: '0',
    description: 'For Beginners',
    features: ['25 transactions', 'Up to 5 wallets', 'Tax Report Preview', 'Portfolio tracking'],
    buttonText: 'Current Plan',
    disabled: true
  },
  {
    id: 'starter',
    name: 'Starter',
    price: '19.99',
    description: 'Most Popular',
    features: ['150 transactions', 'Up to 15 wallets', 'PDF Tax Report', 'Email Support'],
    buttonText: 'Choose Starter',
    popular: true
  },
  {
    id: 'trader',
    name: 'Trader',
    price: '49.99',
    description: 'For Active Users',
    features: ['1000 transactions', 'Unlimited wallets', 'Basic DeFi & NFT', 'Priority Support'],
    buttonText: 'Choose Trader'
  },
  {
    id: 'expert',
    name: 'Expert',
    price: '99.99',
    description: 'For Pros',
    features: ['3000 transactions', 'Unlimited wallets', 'High-Volume CSV Support', 'Loss Harvesting'],
    buttonText: 'Choose Expert'
  }
];

export function BillingPage({ setActiveTab }: { setActiveTab?: (tab: string) => void }) {
  const navigate = useNavigate();
  const [subscription, setSubscription] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    loadSubscription();
  }, []);

  const loadSubscription = async () => {
    try {
      const status = await billing.getStatus();
      setSubscription(status);
    } catch (err) {
      console.error('Failed to load subscription', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planId: string) => {
    if (planId === 'free') return;

    setActionLoading(planId);
    try {
      const successUrl = `${window.location.origin}/billing?success=true`;
      const cancelUrl = `${window.location.origin}/billing?canceled=true`;

      const { url } = await billing.createCheckout(planId, successUrl, cancelUrl);
      window.location.href = url; // Redirect to Stripe
    } catch (err: any) {
      alert(`Error: ${err.message || 'Failed to start checkout'}`);
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="billing-plans-page min-h-screen flex items-center justify-center bg-[var(--bg)]">
        <Loader2 className="animate-spin text-brand-green-legacy-500" size={48} />
      </div>
    );
  }

  return (
    <div className="billing-plans-page min-h-screen bg-[var(--bg)] text-[var(--text)] p-6 md:p-12">
      <div className="max-w-6xl mx-auto">
        <button
          onClick={() => setActiveTab ? setActiveTab('dashboard') : navigate(-1)}
          className="inline-flex items-center gap-2 text-[var(--text2)] hover:text-brand-green-legacy-500 transition-colors mb-8"
        >
          <ArrowLeft size={18} />
          Back to Dashboard
        </button>

        <header className="mb-12">
          <h1 className="font-['Syne'] text-4xl font-extrabold mb-4">Crypto taxes without the stress</h1>
          <p className="text-[var(--text2)] text-lg">Everything you need to calculate and file your crypto taxes with confidence.</p>
        </header>

        {/* Current Plan Summary */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl p-8 mb-12 flex flex-col md:flex-row justify-between items-center gap-6">
          <div>
            <div className="text-[var(--text3)] text-xs font-black uppercase tracking-widest mb-2">Your Current Plan</div>
            <div className="flex items-center gap-3">
              <h2 className="text-3xl font-bold capitalize">{subscription?.plan || 'Free'}</h2>
              <span className="px-3 py-1 bg-brand-green-legacy-500/10 text-brand-green-legacy-500 text-xs font-bold rounded-full border border-brand-green-legacy-500/20">
                {subscription?.status === 'active' ? 'Active' : 'Expired'}
              </span>
            </div>
          </div>

          <div className="text-center md:text-right">
            <p className="text-[var(--text3)] text-sm mb-1">Next renewal / Expiry</p>
            <p className="font-bold">{subscription?.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : 'N/A'}</p>
          </div>
        </div>

        {/* Pricing Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {PLANS.map((plan) => {
            const isCurrent = subscription?.plan === plan.id;

            return (
              <div
                key={plan.id}
                className={`relative p-8 rounded-[2.5rem] border transition-all flex flex-col ${plan.popular
                  ? 'bg-gradient-to-br from-[var(--surface)] to-brand-green-legacy-500/5 border-brand-green-legacy-500/30 ring-1 ring-brand-green-legacy-500/20'
                  : 'bg-[var(--surface)] border-[var(--border)]'
                  }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand-green-legacy-500 text-brand-dark text-[9px] font-black uppercase px-4 py-1 rounded-full shadow-lg">
                    Popular
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                  <p className="text-sm text-[var(--text2)]">{plan.description}</p>
                </div>

                <div className="flex items-baseline gap-1 mb-8">
                  <span className="text-lg font-bold">$</span>
                  <span className="text-5xl font-black">{plan.price}</span>
                  <span className="text-[var(--text3)] text-xs ml-1">/ tax year</span>
                </div>

                <ul className="space-y-4 mb-10 flex-grow">
                  {plan.features.map((feat, i) => {
                    const isNegative = false; // No export is replaced by Portfolio tracking
                    return (
                      <li key={i} className={`flex items-start gap-3 text-sm ${isNegative ? 'text-[var(--text3)] line-through opacity-50' : 'text-[var(--text2)]'}`}>
                        {isNegative ? (
                          <span className="text-[#ff4d6a] shrink-0 font-black text-xs mt-0.5">✕</span>
                        ) : (
                          <CheckCircle size={16} className="text-brand-green-legacy-500 shrink-0 mt-0.5" />
                        )}
                        {feat}
                      </li>
                    );
                  })}
                </ul>

                <button
                  onClick={() => handleUpgrade(plan.id)}
                  disabled={isCurrent || plan.disabled || !!actionLoading}
                  className={`w-full py-4 rounded-xl font-bold text-sm transition-all flex items-center justify-center gap-2 ${isCurrent
                    ? 'bg-[var(--border)] text-[var(--text3)] cursor-default'
                    : plan.popular
                      ? 'bg-brand-green-legacy-500 hover:bg-brand-green-legacy-600 text-brand-dark shadow-xl shadow-brand-green-legacy-600/20'
                      : 'bg-[var(--bg2)] border border-[var(--border)] hover:bg-[var(--surface2)]'
                    }`}
                >
                  {actionLoading === plan.id && <Loader2 size={16} className="animate-spin" />}
                  {isCurrent ? 'Current Plan' : plan.buttonText}
                </button>
              </div>
            );
          })}
        </div>

        {/* Footer Info */}
        <div className="mt-16 text-center text-[var(--text3)] text-sm">
          <p>Payments are secured by Stripe. You can cancel your subscription at any time via the Stripe Customer Portal.</p>
        </div>
      </div>
    </div>
  );
}
