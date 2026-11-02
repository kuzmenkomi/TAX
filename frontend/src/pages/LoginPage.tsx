import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';
import { useAuth, TwoFactorRequiredError } from '../auth/AuthContext';
import { useToast } from '../context/ToastContext';
import { AuthLayout } from '../components/AuthLayout';

export function LoginPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const { loginWithPassword, completeTwoFactorLogin } = useAuth();
  const { addToast } = useToast();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [twoFactorToken, setTwoFactorToken] = useState<string | null>(null);
  const [twoFactorCode, setTwoFactorCode] = useState('');

  const goToDashboard = () => {
    localStorage.setItem('activeTab', 'dashboard');
    navigate('/dashboard', { replace: true });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (twoFactorToken) {
        if (!twoFactorCode.trim()) {
          throw new Error(t('auth.error.invalidCredentials'));
        }
        await completeTwoFactorLogin(twoFactorToken, twoFactorCode.trim());
        goToDashboard();
        return;
      }

      if (!email) {
        throw new Error(t('auth.error.invalidEmail'));
      }
      if (!password) {
        throw new Error(t('auth.error.invalidCredentials'));
      }

      await loginWithPassword(email, password);
      goToDashboard();
    } catch (err: unknown) {
      if (err instanceof TwoFactorRequiredError) {
        setTwoFactorToken(err.twoFactorToken);
        setError('');
        addToast('Enter the code from your authenticator app.', 'info');
      } else {
        setError(err instanceof Error ? err.message : t('auth.error.invalidCredentials'));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title={t('auth.login')}
      subtitle={t('auth.welcomeBack')}
    >
      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-danger/10 border border-danger/20 rounded-xl flex items-center gap-3 animate-shake">
          <div className="w-1.5 h-1.5 rounded-full bg-danger animate-pulse" />
          <p className="text-danger text-xs font-bold leading-tight">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {twoFactorToken ? (
          <div className="space-y-2">
            <label className="block text-[11px] font-bold uppercase tracking-[1.2px] ml-1" style={{ color: 'var(--text3)' }}>
              Authenticator code
            </label>
            <input
              value={twoFactorCode}
              onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, '').slice(0, 8))}
              placeholder="6-digit code"
              className="w-full px-4 py-3 border rounded-xl text-sm transition-all focus:outline-none focus:border-brand-green-500/50"
              style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
              disabled={loading}
              autoComplete="one-time-code"
              autoFocus
            />
            <button
              type="button"
              onClick={() => {
                setTwoFactorToken(null);
                setTwoFactorCode('');
              }}
              className="text-[11px] font-bold text-[var(--text3)] hover:text-[var(--text)]"
            >
              ← Back to email login
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              <label className="block text-[11px] font-bold uppercase tracking-[1.2px] ml-1" style={{ color: 'var(--text3)' }}>
                {t('auth.email')}
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

            <div className="space-y-2">
              <div className="flex items-center justify-between ml-1 text-[10px] font-bold uppercase tracking-[0.15em]" style={{ color: 'var(--text3)' }}>
                <label>{t('auth.password')}</label>
                <Link to="/password-reset" className="text-brand-green-500 hover:text-brand-green-400 normal-case tracking-normal">
                  {t('auth.forgotPassword')}
                </Link>
              </div>
              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors" style={{ color: 'var(--text3)' }} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-11 py-3 border rounded-xl text-sm transition-all focus:outline-none focus:border-brand-green-500/50 focus:ring-4 focus:ring-brand-green-500/5"
                  style={{
                    background: 'var(--bg2)',
                    borderColor: 'var(--border)',
                    color: 'var(--text)',
                  }}
                  disabled={loading}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 transition-colors hover:text-brand-green-500"
                  style={{ color: 'var(--text3)' }}
                  disabled={loading}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 bg-brand-green-500 hover:bg-brand-green-400 text-brand-dark font-bold py-3.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-xl shadow-brand-green-500/20 disabled:opacity-50 active:scale-[0.98]"
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-brand-dark/20 border-t-brand-dark rounded-full animate-spin" />
          ) : (
            <>
              {twoFactorToken ? 'Verify' : t('auth.submit')}
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      {!twoFactorToken && (
        <>
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t" style={{ borderColor: 'var(--border)' }}></div>
            </div>
            <div className="relative flex justify-center text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: 'var(--text3)' }}>
              <span className="px-4" style={{ background: 'var(--surface)' }}>or</span>
            </div>
          </div>

          {/* Social Login */}
          <div className="flex flex-col gap-3">
            <button
              type="button"
              onClick={() => {
                const baseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
                window.location.href = `${baseUrl}/api/v1/auth/google/login`;
              }}
              className="flex items-center justify-center gap-3 py-3 border rounded-xl text-sm font-bold transition-all active:scale-[0.98] group hover:border-brand-green-500/30"
              style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
              Continue with Google
            </button>

            <button
              type="button"
              onClick={() => {
                const baseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
                window.location.href = `${baseUrl}/api/v1/auth/github/login`;
              }}
              className="flex items-center justify-center gap-3 py-3 border rounded-xl text-sm font-bold transition-all active:scale-[0.98] group hover:border-brand-green-500/30"
              style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
              Continue with GitHub
            </button>
          </div>
        </>
      )}

      <div className="mt-8 text-center pt-2">
        <p className="text-[11px] font-bold uppercase tracking-wider" style={{ color: 'var(--text3)' }}>
          {t('auth.noAccount')}{' '}
          <Link to="/register" className="text-brand-green-500 hover:text-brand-green-400 transition-colors">
            {t('auth.register')}
          </Link>
        </p>
      </div>
    </AuthLayout>
  );
}
