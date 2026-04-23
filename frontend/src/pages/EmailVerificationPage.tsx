import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { verifyEmail } from '../api/client';
import { useI18n } from '../i18n/I18nContext';

export function EmailVerificationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { t } = useI18n();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setStatus('error');
      setMessage('No verification token provided');
      return;
    }

    const verify = async () => {
      try {
        const result = await verifyEmail(token);
        setStatus('success');
        setMessage(result.message || 'Email verified successfully!');
        
        // Redirect to login after 3 seconds
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
      } catch (error) {
        setStatus('error');
        setMessage(error instanceof Error ? error.message : 'Verification failed');
      }
    };

    verify();
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      <div className="w-full max-w-md animate-fade-in">
        <div 
          className="border rounded-[2.5rem] p-10 text-center shadow-2xl"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
        >
          {status === 'loading' && (
            <>
              <Loader2 className="w-16 h-16 mx-auto text-brand-green-500 animate-spin mb-6" />
              <h1 className="text-2xl font-bold mb-3 tracking-tight" style={{ color: 'var(--text)' }}>
                {t?.('email_verification.verifying') || 'Verifying Email'}
              </h1>
              <p style={{ color: 'var(--text2)' }}>
                Please wait while we verify your email address...
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <div className="w-20 h-20 bg-brand-green-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-10 h-10 text-brand-green-500 shadow-[0_0_20px_var(--accent)]" />
              </div>
              <h1 className="text-2xl font-bold mb-3 tracking-tight" style={{ color: 'var(--text)' }}>
                {t?.('email_verification.success') || 'Email Verified!'}
              </h1>
              <p className="mb-6" style={{ color: 'var(--text2)' }}>{message}</p>
              <div className="flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-widest text-brand-green-500">
                <div className="w-1 h-1 rounded-full bg-brand-green-500 animate-ping"></div>
                Redirecting to login...
              </div>
            </>
          )}

          {status === 'error' && (
            <>
              <div className="w-20 h-20 bg-danger/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <AlertTriangle className="w-10 h-10 text-danger" />
              </div>
              <h1 className="text-2xl font-bold mb-3 tracking-tight" style={{ color: 'var(--text)' }}>
                {t?.('email_verification.error') || 'Verification Failed'}
              </h1>
              <p className="mb-8" style={{ color: 'var(--text2)' }}>{message}</p>
              <button
                onClick={() => navigate('/login', { replace: true })}
                className="w-full bg-brand-green-500 hover:bg-brand-green-400 text-brand-dark font-bold py-3.5 px-4 rounded-xl transition-all shadow-xl shadow-brand-green-500/20 active:scale-95"
              >
                Back to Login
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
