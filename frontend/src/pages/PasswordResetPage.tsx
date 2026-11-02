import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, AlertCircle, CheckCircle, Loader2, Mail, Lock, ShieldCheck } from 'lucide-react';
import apiV1 from '../api/v1';
import { useI18n } from '../i18n/I18nContext';
import { useToast } from '../context/ToastContext';
import { AuthLayout } from '../components/AuthLayout';

export function PasswordResetPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { t } = useI18n();
  const { addToast } = useToast();
  
  const resetToken = searchParams.get('token');
  const [step, setStep] = useState<'request' | 'reset'>(resetToken ? 'reset' : 'request');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }

    setLoading(true);
    try {
      await apiV1.auth.requestPasswordReset(email);
      setSuccess(true);
      addToast('Check your email for reset instructions', 'success', 5000);
      
      setTimeout(() => {
        navigate('/login', { replace: true });
      }, 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to request password reset';
      setError(msg);
      addToast(msg, 'error', 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!password || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!resetToken) {
      setError('Invalid reset token');
      return;
    }

    setLoading(true);
    try {
      await apiV1.auth.resetPassword(resetToken, password);
      setSuccess(true);
      addToast('Password reset successful! Please login.', 'success', 5000);
      
      setTimeout(() => {
        navigate('/login', { replace: true });
      }, 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to reset password';
      setError(msg);
      addToast(msg, 'error', 5000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout 
      title={step === 'request' ? 'Reset Password' : 'New Password'} 
      subtitle={step === 'request' ? 'Enter your email to receive a link' : 'Create a secure new password'}
    >
      {!success ? (
        <form onSubmit={step === 'request' ? handleRequestReset : handleReset} className="space-y-6">
          {error && (
            <div className="p-4 bg-danger/10 border border-danger/20 rounded-xl flex items-center gap-3 animate-shake">
              <div className="w-1.5 h-1.5 rounded-full bg-danger animate-pulse" />
              <p className="text-danger text-xs font-bold leading-tight">{error}</p>
            </div>
          )}

          {step === 'request' ? (
            <div className="space-y-2">
              <label className="block text-[11px] font-bold uppercase tracking-[1.2px] ml-1" style={{ color: 'var(--text3)' }}>
                Email Address
              </label>
              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors" style={{ color: 'var(--text3)' }} />
                <input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 border rounded-xl text-sm transition-all focus:outline-none focus:border-brand-green-500/50 focus:ring-4 focus:ring-brand-green-500/5"
                  style={{
                    background: 'var(--bg2)',
                    borderColor: 'var(--border)',
                    color: 'var(--text)',
                  }}
                  disabled={loading}
                  autoComplete="email"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              <div className="space-y-2">
                <label className="block text-[11px] font-bold uppercase tracking-[1.2px] ml-1" style={{ color: 'var(--text3)' }}>
                  New Password
                </label>
                <div className="relative group">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors" style={{ color: 'var(--text3)' }} />
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 border rounded-xl text-sm transition-all focus:outline-none focus:border-brand-green-500/50 focus:ring-4 focus:ring-brand-green-500/5"
                    style={{
                      background: 'var(--bg2)',
                      borderColor: 'var(--border)',
                      color: 'var(--text)',
                    }}
                    disabled={loading}
                    autoComplete="new-password"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="block text-[11px] font-bold uppercase tracking-[1.2px] ml-1" style={{ color: 'var(--text3)' }}>
                  Confirm Password
                </label>
                <div className="relative group">
                  <ShieldCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors" style={{ color: 'var(--text3)' }} />
                  <input
                    type="password"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 border rounded-xl text-sm transition-all focus:outline-none focus:border-brand-green-500/50 focus:ring-4 focus:ring-brand-green-500/5"
                    style={{
                      background: 'var(--bg2)',
                      borderColor: 'var(--border)',
                      color: 'var(--text)',
                    }}
                    disabled={loading}
                    autoComplete="new-password"
                  />
                </div>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-green-500 hover:bg-brand-green-400 text-brand-dark font-bold py-3.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-xl shadow-brand-green-500/20 disabled:opacity-50 active:scale-95"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-brand-dark/20 border-t-brand-dark rounded-full animate-spin" />
            ) : (
              <>
                {step === 'request' ? 'Send Reset Link' : 'Reset Password'}
                <ArrowLeft className="w-4 h-4 rotate-180" />
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => navigate('/login')}
            className="w-full flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-widest transition-colors hover:opacity-80"
            style={{ color: 'var(--text3)' }}
          >
            <ArrowLeft size={14} />
            Back to Login
          </button>
        </form>
      ) : (
        <div className="text-center py-6 space-y-6">
          <div className="w-20 h-20 bg-brand-green-500/10 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle className="w-10 h-10 text-brand-green-500 shadow-[0_0_20px_var(--accent)]" />
          </div>
          <div>
            <h3 className="text-xl font-bold mb-2 tracking-tight" style={{ color: 'var(--text)' }}>Success!</h3>
            <p className="text-sm leading-relaxed" style={{ color: 'var(--text2)' }}>
              Instructions have been sent if an account exists. Redirecting...
            </p>
          </div>
        </div>
      )}
    </AuthLayout>
  );
}
