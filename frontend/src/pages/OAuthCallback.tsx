import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { apiFetch } from '../api/client';
import { useAuth } from '../auth/AuthContext';

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    const finalizeOAuth = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const provider = sessionStorage.getItem('oauth_provider');
      const savedState = sessionStorage.getItem('oauth_state');

      if (!code || !state || !provider || state !== savedState) {
        setStatus('error');
        setError('Invalid OAuth session or missing parameters');
        return;
      }

      try {
        const response = await apiFetch(`/oauth/${provider}/finalize?code=${code}&state=${state}`, {
          method: 'POST',
          token,
        });

        if (response.ok) {
          setStatus('success');
          // Clear session storage
          sessionStorage.removeItem('oauth_provider');
          sessionStorage.removeItem('oauth_state');
          
          // Redirect back to exchanges after a short delay
          setTimeout(() => {
            navigate('/dashboard?tab=exchanges'); // Adjust as per your routing
          }, 2000);
        } else {
          const data = await response.json();
          setStatus('error');
          setError(data.detail || 'Failed to finalize connection');
        }
      } catch (err) {
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
      }
    };

    if (token) {
      finalizeOAuth();
    }
  }, [searchParams, token, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-brand-dark p-6">
      <div className="max-w-md w-full border rounded-[2rem] p-10 text-center space-y-6 animate-in fade-in zoom-in duration-500" 
           style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
        
        {status === 'loading' && (
          <>
            <div className="w-16 h-16 bg-brand-green-500/10 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <Loader2 className="w-8 h-8 text-brand-green-500 animate-spin" />
            </div>
            <h2 className="text-2xl font-syne font-bold" style={{ color: 'var(--text)' }}>Finalizing Connection</h2>
            <p className="text-sm opacity-70" style={{ color: 'var(--text3)' }}>
              Verifying your authorization with the exchange...
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-[#6af0c8]/10 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="w-8 h-8 text-[#6af0c8]" />
            </div>
            <h2 className="text-2xl font-syne font-bold" style={{ color: 'var(--text)' }}>Successfully Connected!</h2>
            <p className="text-sm opacity-70" style={{ color: 'var(--text3)' }}>
              Your account has been linked. Redirecting you back to the dashboard...
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-danger/10 rounded-3xl flex items-center justify-center mx-auto mb-6">
              <AlertCircle className="w-8 h-8 text-danger" />
            </div>
            <h2 className="text-2xl font-syne font-bold" style={{ color: 'var(--text)' }}>Connection Failed</h2>
            <p className="text-sm text-danger opacity-90">{error}</p>
            <button 
              onClick={() => navigate('/dashboard?tab=exchanges')}
              className="mt-6 px-6 py-3 bg-brand-green-500 text-brand-dark rounded-xl font-bold text-sm"
            >
              Back to Exchanges
            </button>
          </>
        )}
      </div>
    </div>
  );
}
