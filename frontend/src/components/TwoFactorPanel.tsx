import { useCallback, useEffect, useState } from 'react';
import { Shield, Loader2 } from 'lucide-react';
import apiV1 from '../api/v1';

export function TwoFactorPanel() {
  const [loading, setLoading] = useState(true);
  const [enabled, setEnabled] = useState(false);
  const [pending, setPending] = useState(false);
  const [otpauthUri, setOtpauthUri] = useState<string | null>(null);
  const [setupCode, setSetupCode] = useState('');
  const [disablePassword, setDisablePassword] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const s = await apiV1.twoFactor.status();
      setEnabled(s.enabled);
      setPending(s.pending_setup);
    } catch {
      setEnabled(false);
      setPending(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const beginSetup = async () => {
    setErr(null);
    setMsg(null);
    try {
      const r = await apiV1.twoFactor.setupBegin();
      setOtpauthUri(r.otpauth_uri);
      setPending(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not start 2FA setup');
    }
  };

  const confirmSetup = async () => {
    setErr(null);
    setMsg(null);
    try {
      await apiV1.twoFactor.setupConfirm(setupCode.trim());
      setOtpauthUri(null);
      setSetupCode('');
      setMsg('Two-factor authentication is now enabled.');
      await refresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Invalid code');
    }
  };

  const cancelSetup = async () => {
    setErr(null);
    try {
      await apiV1.twoFactor.setupCancel();
      setOtpauthUri(null);
      setSetupCode('');
      await refresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Cancel failed');
    }
  };

  const disable = async () => {
    setErr(null);
    setMsg(null);
    try {
      await apiV1.twoFactor.disable(disablePassword, disableCode.trim());
      setDisablePassword('');
      setDisableCode('');
      setMsg('2FA has been disabled.');
      await refresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Could not disable 2FA');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-5 py-4 text-sm" style={{ color: 'var(--text2)' }}>
        <Loader2 className="w-4 h-4 animate-spin" />
        Loading security settings…
      </div>
    );
  }

  return (
    <div className="px-5 py-4 space-y-3 border-b" style={{ borderColor: 'var(--border)' }}>
      <div className="flex items-start gap-3">
        <Shield className="w-5 h-5 shrink-0 mt-0.5" style={{ color: 'var(--accent)' }} />
        <div className="flex-1 space-y-1">
          <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Two-factor authentication (TOTP)
          </p>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--text3)' }}>
            Use an authenticator app (Google Authenticator, 1Password, etc.). Required after email/password or social sign-in once enabled.
          </p>
          {enabled ? (
            <p className="text-xs font-bold text-[var(--accent)]">Enabled</p>
          ) : pending ? (
            <p className="text-xs font-bold" style={{ color: 'var(--warning)' }}>Setup in progress</p>
          ) : (
            <p className="text-xs" style={{ color: 'var(--text2)' }}>Off</p>
          )}
        </div>
      </div>

      {msg && <p className="text-xs font-bold text-[var(--accent)]">{msg}</p>}
      {err && <p className="text-xs font-bold text-[var(--red)]">{err}</p>}

      {!enabled && !otpauthUri && (
        <button
          type="button"
          onClick={beginSetup}
          className="text-xs font-bold px-3 py-2 rounded-lg bg-[var(--accent-dim)] text-[var(--accent)]"
        >
          Set up authenticator
        </button>
      )}

      {otpauthUri && (
        <div className="space-y-2 rounded-xl border p-3" style={{ borderColor: 'var(--border)', background: 'var(--bg2)' }}>
          <p className="text-[11px] font-bold uppercase tracking-wide" style={{ color: 'var(--text2)' }}>
            Scan QR in your app
          </p>
          <div className="flex justify-center bg-white p-2 rounded-lg">
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(otpauthUri)}`}
              alt="2FA QR"
              width={160}
              height={160}
              className="rounded"
            />
          </div>
          <p className="text-[10px] break-all font-mono opacity-80" style={{ color: 'var(--text2)' }}>
            {otpauthUri}
          </p>
          <input
            value={setupCode}
            onChange={(e) => setSetupCode(e.target.value.replace(/\D/g, '').slice(0, 8))}
            placeholder="6-digit code"
            className="w-full px-3 py-2 rounded-lg border text-sm outline-none"
            style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
          />
          <div className="flex gap-2">
            <button type="button" onClick={confirmSetup} className="text-xs font-bold px-3 py-2 rounded-lg bg-[var(--accent)] text-black">
              Confirm & enable
            </button>
            <button type="button" onClick={cancelSetup} className="text-xs font-bold px-3 py-2 rounded-lg border" style={{ borderColor: 'var(--border)', color: 'var(--text2)' }}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {enabled && (
        <div className="space-y-2">
          <p className="text-[11px] font-bold" style={{ color: 'var(--text2)' }}>
            Disable 2FA
          </p>
          <input
            type="password"
            value={disablePassword}
            onChange={(e) => setDisablePassword(e.target.value)}
            placeholder="Account password"
            className="w-full px-3 py-2 rounded-lg border text-sm outline-none"
            style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
          />
          <input
            value={disableCode}
            onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, '').slice(0, 8))}
            placeholder="Current 6-digit code"
            className="w-full px-3 py-2 rounded-lg border text-sm outline-none"
            style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
          />
          <button type="button" onClick={disable} className="text-xs font-bold px-3 py-2 rounded-lg border border-[var(--red)] text-[var(--red)]">
            Turn off 2FA
          </button>
        </div>
      )}
    </div>
  );
}
