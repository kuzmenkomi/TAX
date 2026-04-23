import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../auth/AuthContext';
import { useToast } from '../context/ToastContext';
import { AuthLayout } from '../components/AuthLayout';

export function LoginPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const { loginWithPassword } = useAuth();
  const { addToast } = useToast();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (!email) {
        throw new Error(t('auth.error.invalidEmail'));
      }
      if (!password) {
        throw new Error(t('auth.error.invalidCredentials'));
      }

      await loginWithPassword(email, password);
      navigate('/app', { replace: true });
    } catch (err: any) {
      setError(err.message || t('auth.error.invalidCredentials'));
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

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 bg-brand-green-500 hover:bg-brand-green-400 text-brand-dark font-bold py-3.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-all shadow-xl shadow-brand-green-500/20 disabled:opacity-50 active:scale-[0.98]"
        >
          {loading ? (
            <div className="w-5 h-5 border-2 border-brand-dark/20 border-t-brand-dark rounded-full animate-spin" />
          ) : (
            <>
              {t('auth.submit')}
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      {/* Divider */}
      <div className="relative my-8">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t" style={{ borderColor: 'var(--border)' }}></div>
        </div>
        <div className="relative flex justify-center text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: 'var(--text3)' }}>
          <span className="px-4" style={{ background: 'var(--surface)' }}>or</span>
        </div>
      </div>

      {/* Social Login */}
      <div className="grid grid-cols-2 gap-3">
        <button 
          type="button"
          onClick={() => addToast?.('Google Login coming soon', 'info')}
          className="flex items-center justify-center gap-2 py-2.5 border rounded-xl text-xs font-medium transition-all active:scale-95 group"
          style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text2)' }}
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
          Google
        </button>
        <button 
          type="button"
          onClick={() => addToast?.('GitHub Login coming soon', 'info')}
          className="flex items-center justify-center gap-2 py-2.5 border rounded-xl text-xs font-medium transition-all active:scale-95"
          style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text2)' }}
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
          </svg>
          GitHub
        </button>
      </div>

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
