/**
 * OAuth callback: social login (Google/GitHub), optional 2FA step, or exchange OAuth finalize.
 *
 * Social success (no 2FA): backend sets cookies and may include tokens in the query string.
 * With 2FA: backend redirects with `requires_two_factor=true` and `two_factor_token` (JWT);
 * no session cookies until POST /auth/login/2fa succeeds.
 */
import { FormEvent, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle2, AlertCircle, Shield } from 'lucide-react';
import { auth } from '../api/v1';
import { useAuth } from '../auth/AuthContext';

const OAUTH_TFA_STORAGE = 'declairo_oauth_tfa_token';

function persistMeToStorage(me: { id: string | number; email: string; created_at?: string }) {
  try {
    localStorage.setItem(
      'tax_auth_user_v1',
      JSON.stringify({
        id: String(me.id),
        email: me.email,
        created_at: (me as { created_at?: string }).created_at ?? '',
      }),
    );
  } catch {
    /* ignore */
  }
}

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { completeTwoFactorLogin } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'two_factor'>('loading');
  const [errorMsg, setErrorMsg] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [twoFactorBusy, setTwoFactorBusy] = useState(false);

  const goToDashboard = () => {
    localStorage.setItem('activeTab', 'dashboard');
    navigate('/dashboard', { replace: true });
  };

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      const errorParam = searchParams.get('error');
      if (errorParam) {
        setStatus('error');
        setErrorMsg(
          errorParam === 'google_oauth_failed'
            ? 'Google sign-in failed. Please try again.'
            : errorParam === 'github_oauth_failed'
              ? 'GitHub sign-in failed. Please try again.'
              : 'Authentication failed. Please try again.',
        );
        setTimeout(() => navigate('/login', { replace: true }), 3000);
        return;
      }

      if (searchParams.get('access_token')) {
        try {
          sessionStorage.removeItem(OAUTH_TFA_STORAGE);
        } catch {
          /* ignore */
        }
      }

      const code = searchParams.get('code');
      const provider = sessionStorage.getItem('oauth_provider');
      if (code && provider) {
        const state = searchParams.get('state') ?? '';
        try {
          const baseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
          const resp = await fetch(
            `${baseUrl}/api/v1/oauth/${provider}/finalize?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
            { method: 'POST', credentials: 'include' },
          );
          if (resp.ok) {
            sessionStorage.removeItem('oauth_provider');
            sessionStorage.removeItem('oauth_state');
            if (!cancelled) {
              setStatus('success');
              setTimeout(() => navigate('/dashboard?tab=exchanges', { replace: true }), 1800);
            }
          } else {
            const data = await resp.json().catch(() => ({}));
            throw new Error((data as { detail?: string }).detail || 'Failed to connect exchange');
          }
        } catch (err) {
          if (!cancelled) {
            setStatus('error');
            setErrorMsg(err instanceof Error ? err.message : 'Exchange connection failed');
          }
        }
        return;
      }

      const requires2fa = searchParams.get('requires_two_factor');
      const tfaFromUrl = searchParams.get('two_factor_token');
      if (requires2fa === 'true' && tfaFromUrl) {
        try {
          sessionStorage.setItem(OAUTH_TFA_STORAGE, tfaFromUrl);
          window.history.replaceState({}, '', '/oauth/callback');
        } catch {
          /* ignore */
        }
        if (!cancelled) setStatus('two_factor');
        return;
      }

      try {
        if (sessionStorage.getItem(OAUTH_TFA_STORAGE)) {
          if (!cancelled) setStatus('two_factor');
          return;
        }
      } catch {
        /* ignore */
      }

      try {
        const me = await auth.me();
        if (!me?.email) throw new Error('Session not established');

        persistMeToStorage(me);

        if (!cancelled) {
          setStatus('success');
          setTimeout(goToDashboard, 1000);
        }
      } catch (err) {
        if (!cancelled) {
          setStatus('error');
          setErrorMsg('Could not verify session. Please log in again.');
          setTimeout(() => navigate('/login', { replace: true }), 3000);
        }
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [searchParams, navigate]);

  async function onSubmitTwoFactor(e: FormEvent) {
    e.preventDefault();
    let token: string | null = null;
    try {
      token = sessionStorage.getItem(OAUTH_TFA_STORAGE);
    } catch {
      token = null;
    }
    if (!token || !twoFactorCode.trim()) {
      setErrorMsg('Enter the 6-digit code from your authenticator app.');
      return;
    }
    setTwoFactorBusy(true);
    setErrorMsg('');
    try {
      await completeTwoFactorLogin(token, twoFactorCode.trim());
      try {
        sessionStorage.removeItem(OAUTH_TFA_STORAGE);
      } catch {
        /* ignore */
      }
      const me = await auth.me().catch(() => null);
      if (me) persistMeToStorage(me);
      setStatus('success');
      setTimeout(goToDashboard, 900);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setTwoFactorBusy(false);
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-6"
      style={{ background: 'var(--bg)' }}
    >
      <div
        className="max-w-md w-full border rounded-[2rem] p-10 text-center space-y-6"
        style={{ background: 'var(--card)', borderColor: 'var(--border)', boxShadow: 'var(--card-shadow)' }}
      >
        {status === 'loading' && (
          <>
            <div className="w-16 h-16 bg-brand-green-500/10 rounded-3xl flex items-center justify-center mx-auto">
              <Loader2 className="w-8 h-8 text-brand-green-500 animate-spin" />
            </div>
            <h2 className="text-2xl font-syne font-bold" style={{ color: 'var(--text)' }}>
              Signing you in…
            </h2>
            <p className="text-sm" style={{ color: 'var(--text3)' }}>
              Verifying your account, please wait.
            </p>
          </>
        )}

        {status === 'two_factor' && (
          <>
            <div className="w-16 h-16 bg-brand-green-500/10 rounded-3xl flex items-center justify-center mx-auto">
              <Shield className="w-8 h-8 text-brand-green-500" />
            </div>
            <h2 className="text-2xl font-syne font-bold" style={{ color: 'var(--text)' }}>
              Two-factor authentication
            </h2>
            <p className="text-sm" style={{ color: 'var(--text3)' }}>
              Enter the code from your authenticator app to finish signing in.
            </p>
            <form onSubmit={onSubmitTwoFactor} className="space-y-4 text-left">
              <input
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                placeholder="000000"
                value={twoFactorCode}
                onChange={(ev) => setTwoFactorCode(ev.target.value.replace(/\s/g, ''))}
                className="w-full py-3 px-4 border rounded-xl text-center text-lg font-mono tracking-[0.3em] focus:outline-none focus:ring-2 focus:ring-brand-green-500/30"
                style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                disabled={twoFactorBusy}
              />
              {errorMsg ? <p className="text-sm text-red-500 text-center">{errorMsg}</p> : null}
              <button
                type="submit"
                disabled={twoFactorBusy}
                className="w-full py-3.5 rounded-xl bg-brand-green-500 text-brand-dark font-bold text-sm hover:bg-brand-green-400 disabled:opacity-50 transition-all"
              >
                {twoFactorBusy ? 'Verifying…' : 'Verify and continue'}
              </button>
              <button
                type="button"
                onClick={() => {
                  try {
                    sessionStorage.removeItem(OAUTH_TFA_STORAGE);
                  } catch {
                    /* ignore */
                  }
                  navigate('/login', { replace: true });
                }}
                className="w-full py-2 text-[11px] font-bold uppercase tracking-wider"
                style={{ color: 'var(--text3)' }}
              >
                Cancel
              </button>
            </form>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-brand-green-500/10 rounded-3xl flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8 text-brand-green-500" />
            </div>
            <h2 className="text-2xl font-syne font-bold" style={{ color: 'var(--text)' }}>
              Welcome!
            </h2>
            <p className="text-sm" style={{ color: 'var(--text3)' }}>
              Redirecting to your dashboard…
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-danger/10 rounded-3xl flex items-center justify-center mx-auto">
              <AlertCircle className="w-8 h-8 text-danger" />
            </div>
            <h2 className="text-2xl font-syne font-bold" style={{ color: 'var(--text)' }}>
              Sign-in Failed
            </h2>
            <p className="text-sm text-danger">{errorMsg}</p>
            <button
              onClick={() => navigate('/login', { replace: true })}
              className="mt-4 px-6 py-3 bg-brand-green-500 text-brand-dark rounded-xl font-bold text-sm transition-all hover:bg-brand-green-400"
            >
              Back to Login
            </button>
          </>
        )}
      </div>
    </div>
  );
}
