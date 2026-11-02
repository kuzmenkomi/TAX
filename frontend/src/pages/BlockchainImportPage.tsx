import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { BlockchainWalletImport } from '../components/BlockchainWalletImport';
import { apiFetch } from '../api/v1';

export function BlockchainImportPage() {
  const [walletCount, setWalletCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/br/connections')
      .then(r => r.ok ? r.json() : { wallets: [] })
      .then(d => setWalletCount((d.wallets || []).length))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '80px 0' }}>
        <Loader2 size={28} className="animate-spin" style={{ color: 'var(--accent)' }} />
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
        height: 'calc(100vh - 130px)',
        animation: 'fadeIn .3s ease',
      }}
    >
      {/* Page header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
        <div>
          <h1 style={{ fontFamily: 'Syne, sans-serif', fontWeight: 800, fontSize: 20, letterSpacing: -0.5, color: 'var(--text)', margin: 0 }}>
            Wallets
          </h1>
          <p style={{ fontSize: 12, color: 'var(--text3)', marginTop: 4 }}>
            Connect wallets from 10+ blockchains for automatic transaction tracking
          </p>
        </div>
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '6px 14px', fontSize: 12, color: 'var(--text3)', display: 'flex', alignItems: 'center', gap: 6 }}>
          Connected:{' '}
          <strong style={{ color: 'var(--text)', fontSize: 14, fontFamily: 'Syne, sans-serif' }}>{walletCount}</strong>{' '}
          wallets
        </div>
      </div>

      {/* Two-column layout (rendered inside the component) */}
      <BlockchainWalletImport
        onSuccess={() => setWalletCount(c => c + 1)}
        onError={() => {}}
      />
    </div>
  );
}
