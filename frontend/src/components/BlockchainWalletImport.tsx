import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { apiFetch } from '../api/v1';
import { triggerWeb3Load } from './LazyWeb3Provider';

const WalletConnectButton = React.lazy(() => import('./WalletConnectButton'));

interface ImportedWallet {
  wallet_id: number;
  chain: string;
  address: string;
  label?: string;
  transactions_count: number;
}

// ── SVG Chain Icons ──────────────────────────────────────────────────────────

const ETH_ICON = (
  <svg viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26 }}>
    <circle cx="16" cy="16" r="16" fill="#627EEA" opacity=".15"/>
    <path d="M16 5.5l-8 10.3 8-4.4 8 4.4L16 5.5z" fill="#627EEA"/>
    <path d="M8 15.8l8 4.8 8-4.8-8 4.4L8 15.8z" fill="#627EEA" opacity=".6"/>
    <path d="M16 22.2l-8-4.8L16 26.5l8-9.1-8 4.8z" fill="#627EEA"/>
  </svg>
);
const MATIC_ICON = (
  <svg viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26 }}>
    <circle cx="16" cy="16" r="16" fill="#8247E5" opacity=".15"/>
    <path d="M20.5 11.5l-6 3.5v7l6-3.5v-7z" fill="#8247E5"/>
    <path d="M14.5 15l-5 2.9v5.8l5-2.9V15z" fill="#8247E5" opacity=".7"/>
    <path d="M20.5 11.5L17 9.5l-7.5 4.3 5 2.9 6-4.7z" fill="#8247E5" opacity=".5"/>
  </svg>
);
const BNB_ICON = (
  <svg viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26 }}>
    <circle cx="16" cy="16" r="16" fill="#F3BA2F" opacity=".15"/>
    <path d="M16 8l2.3 2.3-5.6 5.6-2.3-2.3L16 8z" fill="#F3BA2F"/>
    <path d="M19.7 11.7L22 14l-2.3 2.3-2.3-2.3 2.3-2.3z" fill="#F3BA2F"/>
    <path d="M10.3 11.7l2.3 2.3L10.3 16.3 8 14l2.3-2.3z" fill="#F3BA2F"/>
    <path d="M16 19.4l2.3 2.3L16 24l-2.3-2.3 2.3-2.3z" fill="#F3BA2F"/>
    <path d="M16 13.7l2.3 2.3-2.3 2.3-2.3-2.3 2.3-2.3z" fill="#F3BA2F"/>
  </svg>
);
const BTC_ICON = (
  <svg viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26 }}>
    <circle cx="16" cy="16" r="16" fill="#F7931A" opacity=".15"/>
    <path d="M21.2 14.2c.3-1.8-1.1-2.8-3-3.4l.6-2.5-1.5-.4-.6 2.4-1.2-.3.6-2.4-1.5-.4-.6 2.5-2.4-.6-.4 1.6 1.1.3c.6.2.7.5.7.8l-1.7 7c-.1.3-.4.7-.9.5l-1.1-.3-.7 1.8 2.3.6-.6 2.5 1.5.4.6-2.5 1.2.3-.6 2.4 1.5.4.6-2.5c2.6.5 4.5.3 5.3-2.1.6-1.9 0-3 0-3 1.1-.5 1.7-1.4 1.35-2.9zm-2.5 3.5c-.4 1.8-3.3 1-4.3.7l.8-3.2c1 .2 3.9.8 3.5 2.5zm.4-3.5c-.4 1.7-2.8.9-3.6.6l.7-2.9c.8.2 3.3.6 2.9 2.3z" fill="#F7931A"/>
  </svg>
);
const SOL_ICON = (
  <svg viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26 }}>
    <circle cx="16" cy="16" r="16" fill="#9945FF" opacity=".15"/>
    <path d="M9 20.5h11.5l2.5-2.5H11.5L9 20.5z" fill="url(#sw1)"/>
    <path d="M9 13.5h11.5L23 11H11.5L9 13.5z" fill="url(#sw2)"/>
    <path d="M11.5 17H23l-2.5-2.5H9L11.5 17z" fill="url(#sw3)"/>
    <defs>
      <linearGradient id="sw1" x1="9" y1="19" x2="23" y2="19" gradientUnits="userSpaceOnUse"><stop stopColor="#9945FF"/><stop offset="1" stopColor="#14F195"/></linearGradient>
      <linearGradient id="sw2" x1="9" y1="12" x2="23" y2="12" gradientUnits="userSpaceOnUse"><stop stopColor="#9945FF"/><stop offset="1" stopColor="#14F195"/></linearGradient>
      <linearGradient id="sw3" x1="9" y1="15" x2="23" y2="15" gradientUnits="userSpaceOnUse"><stop stopColor="#9945FF"/><stop offset="1" stopColor="#14F195"/></linearGradient>
    </defs>
  </svg>
);
const AVAX_ICON = (
  <svg viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26 }}>
    <circle cx="16" cy="16" r="16" fill="#E84142" opacity=".15"/>
    <path d="M11 22h3.6L16 19.4 17.4 22H21l-5-9.5L11 22z" fill="#E84142"/>
    <path d="M8 22h2l1.5-2.8L9.5 17 8 22z" fill="#E84142" opacity=".5"/>
    <path d="M24 22h-2l-1.5-2.8L22.5 17 24 22z" fill="#E84142" opacity=".5"/>
  </svg>
);
const ARB_ICON = (
  <svg viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26 }}>
    <circle cx="16" cy="16" r="16" fill="#2D374B" opacity=".8"/>
    <path d="M16 6L8 20h16L16 6z" fill="#28A0F0" opacity=".3"/>
    <path d="M11 20l5-9 5 9H11z" fill="#28A0F0"/>
    <path d="M13 20l3-5 3 5H13z" fill="#1a2535"/>
  </svg>
);
const OP_ICON = (
  <svg viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26 }}>
    <circle cx="16" cy="16" r="16" fill="#FF0420" opacity=".15"/>
    <circle cx="16" cy="16" r="7" stroke="#FF0420" strokeWidth="2.5" fill="none"/>
    <circle cx="16" cy="16" r="3" fill="#FF0420"/>
  </svg>
);
const BASE_ICON = (
  <svg viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26 }}>
    <circle cx="16" cy="16" r="16" fill="#0052FF" opacity=".15"/>
    <circle cx="16" cy="16" r="7.5" fill="#0052FF"/>
    <circle cx="16" cy="16" r="3" fill="#080c10"/>
  </svg>
);
const TRON_ICON = (
  <svg viewBox="0 0 32 32" fill="none" style={{ width: 26, height: 26 }}>
    <circle cx="16" cy="16" r="16" fill="#EF0027" opacity=".15"/>
    <path d="M7 12l9 13 9-13H7z" fill="#EF0027" opacity=".3"/>
    <path d="M10 12l6 9 6-9H10z" fill="#EF0027"/>
    <path d="M13 12l3 5 3-5H13z" fill="#080c10" opacity=".6"/>
  </svg>
);

const CHAINS = [
  { id: 'ethereum',  name: 'Ethereum',  icon: ETH_ICON },
  { id: 'polygon',   name: 'Polygon',   icon: MATIC_ICON },
  { id: 'bsc',       name: 'BNB Chain', icon: BNB_ICON },
  { id: 'bitcoin',   name: 'Bitcoin',   icon: BTC_ICON },
  { id: 'solana',    name: 'Solana',    icon: SOL_ICON },
  { id: 'avalanche', name: 'Avalanche', icon: AVAX_ICON },
  { id: 'arbitrum',  name: 'Arbitrum',  icon: ARB_ICON },
  { id: 'optimism',  name: 'Optimism',  icon: OP_ICON },
  { id: 'base',      name: 'Base',      icon: BASE_ICON },
  { id: 'tron',      name: 'Tron',      icon: TRON_ICON },
];

const FAQ_ITEMS = [
  { q: '🔄 How often are wallets synced?', a: 'Transactions fetched once on import. Auto daily sync coming soon.' },
  { q: '🔒 Is my wallet safe?', a: 'We only use public blockchain data. Keys and seed phrases are never requested.' },
  { q: '🪙 Which tokens are supported?', a: 'All ERC-20, BEP-20 and native coins are tracked automatically.' },
  { q: '⚙️ What about DeFi and swaps?', a: 'Uniswap, Aave, Curve and other protocols are identified automatically.' },
];

// ── Styles ────────────────────────────────────────────────────────────────────

const S = {
  card: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 16 } as React.CSSProperties,
  label: { fontSize: 10, fontWeight: 700, letterSpacing: '1.5px', color: 'var(--text3)', textTransform: 'uppercase' as const },
  input: { background: 'var(--bg2)', border: '1px solid var(--border2)', borderRadius: 9, padding: '10px 13px', color: 'var(--text)', fontSize: 13, fontFamily: 'inherit', outline: 'none', width: '100%', boxSizing: 'border-box' as const, transition: '.2s' } as React.CSSProperties,
  btn: { width: '100%', padding: 12, background: 'var(--accent)', color: '#000', fontWeight: 700, fontSize: 14, border: 'none', borderRadius: 10, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, transition: '.2s' } as React.CSSProperties,
};

// ── Main Export ───────────────────────────────────────────────────────────────

export function BlockchainWalletImport({ onSuccess, onError }: { onSuccess?: (r: any) => void; onError?: (e: string) => void }) {
  const [chain, setChain] = useState('ethereum');
  const [address, setAddress] = useState('');
  const [label, setLabel] = useState('');
  const [loading, setLoading] = useState(false);
  const [wallets, setWallets] = useState<ImportedWallet[]>([]);
  const [walletsLoading, setWalletsLoading] = useState(true);
  const [error, setError] = useState('');
  const [web3Active, setWeb3Active] = useState(false);
  const [faqOpen, setFaqOpen] = useState(false);

  useEffect(() => {
    apiFetch('/br/connections').then(r => r.ok ? r.json() : { wallets: [] })
      .then(d => setWallets(d.wallets || []))
      .catch(() => {})
      .finally(() => setWalletsLoading(false));
  }, []);

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!address.trim()) { setError('Please enter a wallet address'); return; }
    setLoading(true); setError('');
    try {
      const res = await apiFetch('/br/wallet/import-blockchain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chain, address: address.trim(), label: label.trim() || null }),
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Import failed'); }
      const data = await res.json();
      setWallets(prev => [...prev, { wallet_id: Date.now(), chain, address: address.trim(), label: label.trim(), transactions_count: data.transactions_count ?? 0 }]);
      setAddress(''); setLabel('');
      if (onSuccess) onSuccess(data);
    } catch (err: any) {
      const msg = err.message || 'Failed to import wallet';
      setError(msg);
      if (onError) onError(msg);
    } finally { setLoading(false); }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 16, flex: 1, minHeight: 0 }}>

      {/* ── LEFT: Import Form ── */}
      <div style={{ ...S.card, padding: 20, display: 'flex', flexDirection: 'column', gap: 14, overflowY: 'auto' }}>

        {/* WalletConnect */}
        <div>
          <div
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, padding: 14, background: 'rgba(16, 185, 129,.06)', border: '1.5px dashed rgba(16, 185, 129,.3)', borderRadius: 12, cursor: 'pointer', fontWeight: 700, fontSize: 14, color: 'var(--accent)', transition: '.2s' }}
            onClick={() => { setWeb3Active(true); triggerWeb3Load(); }}
          >
            <span style={{ fontSize: 18 }}>🔗</span>
            {web3Active
              ? <React.Suspense fallback={<Loader2 className="animate-spin" size={18} />}><WalletConnectButton /></React.Suspense>
              : 'Connect with WalletConnect / MetaMask'}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text3)', textAlign: 'center', marginTop: 6 }}>
            Automatically imports your address — read-only, no signing required
          </div>
        </div>

        {/* Divider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          <span style={{ fontSize: 11, color: 'var(--text3)', fontWeight: 600, letterSpacing: 1 }}>OR ENTER MANUALLY</span>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        </div>

        {/* Chain selector */}
        <div>
          <div style={{ ...S.label, marginBottom: 8 }}>Select Blockchain</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 7 }}>
            {CHAINS.map(c => (
              <button key={c.id} type="button" onClick={() => setChain(c.id)}
                style={{ background: chain === c.id ? 'rgba(16, 185, 129,.06)' : 'var(--bg2)', border: `1px solid ${chain === c.id ? 'var(--accent)' : 'var(--border)'}`, borderRadius: 10, padding: '10px 6px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, cursor: 'pointer', transition: '.15s' }}>
                {c.icon}
                <span style={{ fontSize: 9, fontWeight: 600, color: chain === c.id ? 'var(--accent)' : 'var(--text3)', textAlign: 'center', lineHeight: 1.2 }}>{c.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Address + Label */}
        <form onSubmit={handleImport} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', gap: 10 }}>
            <div style={{ flex: 2, display: 'flex', flexDirection: 'column', gap: 5 }}>
              <label style={S.label}>Wallet Address</label>
              <input type="text" value={address} onChange={e => setAddress(e.target.value)}
                placeholder={chain === 'bitcoin' ? '1A1z7ag...' : chain === 'solana' ? 'So1111...' : '0x742d35Cc…'}
                style={S.input} disabled={loading} />
            </div>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 5 }}>
              <label style={S.label}>Label (optional)</label>
              <input type="text" value={label} onChange={e => setLabel(e.target.value)}
                placeholder="e.g. My Ledger" style={S.input} disabled={loading} />
            </div>
          </div>

          {error && (
            <div style={{ background: 'rgba(255,77,106,.1)', border: '1px solid rgba(255,77,106,.2)', borderRadius: 9, padding: '9px 12px', fontSize: 12, color: 'var(--danger)', fontWeight: 600 }}>
              ✗ {error}
            </div>
          )}

          <button type="submit" disabled={loading || !address.trim()} style={{ ...S.btn, opacity: loading || !address.trim() ? 0.5 : 1 }}>
            {loading ? <Loader2 size={16} className="animate-spin" /> : '+'}
            {loading ? 'Processing...' : 'Add Wallet'}
          </button>
        </form>

        {/* Security note */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(16, 185, 129,.04)', border: '1px solid rgba(16, 185, 129,.1)', borderRadius: 9, padding: '9px 12px', fontSize: 11, color: 'var(--text3)', lineHeight: 1.4 }}>
          <span style={{ fontSize: 14, flexShrink: 0 }}>🔒</span>
          Read-only access to your public transaction history. Private keys and seed phrases are never accessed or stored.
        </div>
      </div>

      {/* ── RIGHT: Connected Wallets + FAQ ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, overflow: 'hidden' }}>

        {/* Connected wallets card */}
        <div style={{ ...S.card, padding: 16, flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexShrink: 0 }}>
            <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 13, color: 'var(--text)' }}>Connected Wallets</span>
            <span style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 20, padding: '2px 10px', fontSize: 11, color: 'var(--text3)' }}>
              {wallets.length} total
            </span>
          </div>

          {walletsLoading ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Loader2 size={20} className="animate-spin" style={{ color: 'var(--accent)' }} />
            </div>
          ) : wallets.length === 0 ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', gap: 8 }}>
              <span style={{ fontSize: 28, opacity: .4 }}>⬡</span>
              <span style={{ fontSize: 13, color: 'var(--text3)' }}>No wallets yet</span>
              <span style={{ fontSize: 11, color: 'var(--text3)', opacity: .6 }}>Add your first wallet using the form →</span>
            </div>
          ) : (
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
              {wallets.map(w => (
                <div key={`${w.chain}-${w.wallet_id}`} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 10, padding: '10px 12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: 1 }}>{w.chain}</span>
                    <span style={{ fontSize: 10, color: 'var(--text3)' }}>{w.transactions_count} txns</span>
                  </div>
                  {w.label && <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>{w.label}</div>}
                  <div style={{ fontSize: 10, fontFamily: 'monospace', color: 'var(--text3)', wordBreak: 'break-all' }}>
                    {w.address.length > 32 ? `${w.address.slice(0, 16)}…${w.address.slice(-8)}` : w.address}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* FAQ card */}
        <div style={{ ...S.card, overflow: 'hidden', flexShrink: 0 }}>
          <div
            style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', borderBottom: faqOpen ? '1px solid var(--border)' : 'none' }}
            onClick={() => setFaqOpen(o => !o)}
          >
            <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 12, color: 'var(--text)', letterSpacing: .5 }}>FREQUENTLY ASKED QUESTIONS</span>
            <span style={{ color: 'var(--text3)', fontSize: 13, transition: '.2s', transform: faqOpen ? 'rotate(180deg)' : 'none', display: 'inline-block' }}>▾</span>
          </div>
          {faqOpen && (
            <div>
              {FAQ_ITEMS.map((item, i) => (
                <div key={i} style={{ padding: '11px 16px', borderBottom: i < FAQ_ITEMS.length - 1 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text3)', marginBottom: 3 }}>{item.q}</div>
                  <div style={{ fontSize: 11, color: 'var(--text3)', opacity: .7, lineHeight: 1.5 }}>{item.a}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
