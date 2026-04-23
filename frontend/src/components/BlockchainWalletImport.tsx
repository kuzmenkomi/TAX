import React, { useState } from 'react';
import { AlertCircle, Loader2, CheckCircle2, Wallet, Plus } from 'lucide-react';
import { apiFetch } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { triggerWeb3Load } from './LazyWeb3Provider';

const WalletConnectButton = React.lazy(() => import('./WalletConnectButton'));

interface BlockchainWalletImportProps {
  onSuccess?: (result: any) => void;
  onError?: (error: string) => void;
}

export function BlockchainWalletImport({ onSuccess, onError }: BlockchainWalletImportProps) {
  const { token } = useAuth();
  const [chain, setChain] = useState<string>('ethereum');
  const [address, setAddress] = useState<string>('');
  const [label, setLabel] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [web3Active, setWeb3Active] = useState(false);

  const handleWeb3Activate = () => {
    setWeb3Active(true);
    triggerWeb3Load();
  };

  const chains = [
    { id: 'ethereum', name: 'Ethereum', icon: 'Ξ' },
    { id: 'polygon', name: 'Polygon', icon: '◊' },
    { id: 'bsc', name: 'BNB Chain', icon: 'B' },
    { id: 'bitcoin', name: 'Bitcoin', icon: '₿' },
    { id: 'solana', name: 'Solana', icon: '◎' },
    { id: 'avalanche', name: 'Avalanche', icon: 'A' },
    { id: 'arbitrum', name: 'Arbitrum', icon: 'Ⓐ' },
    { id: 'optimism', name: 'Optimism', icon: 'Ⓞ' },
    { id: 'base', name: 'Base', icon: 'B' },
    { id: 'tron', name: 'Tron', icon: 'T' },
  ];

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!address.trim()) { setError('Please enter a wallet address'); return; }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await apiFetch('/br/wallet/import-blockchain', {
        method: 'POST', token,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chain, address: address.trim(), label: label.trim() || null }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Import failed');
      }

      const data = await response.json();
      setResult(data);
      setAddress('');
      setLabel('');
      if (onSuccess) onSuccess(data);
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to import wallet';
      setError(errorMsg);
      if (onError) onError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border rounded-[2.5rem] p-8 shadow-xl transition-colors duration-300" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg shadow-brand-green-500/10" style={{ background: 'var(--bg2)', color: 'var(--accent)' }}>
          <Wallet className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>Import Wallet</h2>
          <p className="text-[12px]" style={{ color: 'var(--text3)' }}>Automatic tracking for 10+ blockchains</p>
        </div>
      </div>

      {result ? (
        <div className="bg-[#6af0c8]/5 border border-[#6af0c8]/20 rounded-2xl p-6 mb-4 animate-in fade-in">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-6 h-6 text-[#6af0c8] flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-[14px] font-bold text-[#6af0c8]">Import Successful</h3>
              <div className="mt-3 grid grid-cols-2 gap-4">
                <div className="p-3 border rounded-xl" style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}>
                  <p className="text-[10px] uppercase font-bold tracking-wider opacity-60" style={{ color: 'var(--text)' }}>Transactions</p>
                  <p className="text-lg font-bold" style={{ color: 'var(--text)' }}>{result.transactions_count}</p>
                </div>
                <div className="p-3 border rounded-xl" style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}>
                  <p className="text-[10px] uppercase font-bold tracking-wider opacity-60" style={{ color: 'var(--text)' }}>Assets</p>
                  <p className="text-lg font-bold" style={{ color: 'var(--text)' }}>{result.assets?.length || 0}</p>
                </div>
              </div>
              <button
                onClick={() => setResult(null)}
                className="mt-6 flex items-center gap-2 text-xs font-bold text-brand-green-500 hover:underline"
              >
                <Plus size={14} />
                Import another wallet
              </button>
            </div>
          </div>
        </div>
      ) : (
        <form onSubmit={handleImport} className="space-y-6">
          
          {/* WalletConnect Section */}
          <div className="p-6 rounded-3xl border-2 border-dashed border-brand-green-500/20 bg-brand-green-500/5 flex flex-col items-center gap-4">
            {!web3Active ? (
              <button
                type="button"
                onClick={handleWeb3Activate}
                className="flex items-center gap-3 px-6 py-3 bg-brand-green-500/10 text-brand-green-500 rounded-2xl font-bold hover:bg-brand-green-500/20 transition-all border border-brand-green-500/20"
              >
                <Wallet className="w-5 h-5" />
                Connect with WalletConnect / MetaMask
              </button>
            ) : (
              <React.Suspense fallback={<Loader2 className="animate-spin text-brand-green-500" />}>
                <WalletConnectButton />
              </React.Suspense>
            )}
            <p className="text-[10px] text-center opacity-60" style={{ color: 'var(--text)' }}>
              Automatically imports your address and signs a read-only request.
            </p>
          </div>

          <div className="relative flex items-center py-4">
            <div className="flex-grow border-t border-dashed" style={{ borderColor: 'var(--border)' }}></div>
            <span className="flex-shrink mx-4 text-[10px] font-bold uppercase tracking-widest opacity-40" style={{ color: 'var(--text)' }}>OR ENTER MANUALLY</span>
            <div className="flex-grow border-t border-dashed" style={{ borderColor: 'var(--border)' }}></div>
          </div>

          {/* Chain selector */}
          <div>
            <label className="block text-[10px] font-bold uppercase tracking-widest mb-3 ml-1" style={{ color: 'var(--text3)' }}>
              Select Blockchain
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
              {chains.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setChain(c.id)}
                  className={`p-3 rounded-2xl border text-center transition-all group ${
                    chain === c.id
                      ? 'border-brand-green-500 bg-brand-green-500/10 text-brand-green-500 shadow-lg shadow-brand-green-500/5'
                      : 'hover:bg-brand-green-500/5'
                  }`}
                  style={chain !== c.id ? { background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text2)' } : undefined}
                >
                  <div className={`text-xl mb-1 transition-transform group-hover:scale-110 ${chain === c.id ? 'opacity-100' : 'opacity-40'}`}>{c.icon}</div>
                  <div className="text-[10px] font-bold tracking-tight">{c.name}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Address */}
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="block text-[10px] font-bold uppercase tracking-widest ml-1" style={{ color: 'var(--text3)' }}>
                Wallet Address
              </label>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder={
                  chain === 'bitcoin' ? '1A1z7agoat...'
                  : chain === 'solana' ? 'So11111111111111...'
                  : chain === 'tron' ? 'TWJvjBhVH...'
                  : '0x742d35Cc6634C0532925a3b844Bc9e7595f...'
                }
                className="w-full px-4 py-3.5 border rounded-2xl text-[13px] transition-all focus:outline-none focus:border-brand-green-500"
                style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                disabled={loading}
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-[10px] font-bold uppercase tracking-widest ml-1" style={{ color: 'var(--text3)' }}>
                Label (Optional)
              </label>
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="e.g. My Ledger Account"
                className="w-full px-4 py-3.5 border rounded-2xl text-[13px] transition-all focus:outline-none focus:border-brand-green-500"
                style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                disabled={loading}
              />
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-danger/10 border border-danger/20 rounded-xl px-4 py-3 flex items-center gap-2 animate-shake">
              <AlertCircle className="w-4 h-4 text-danger flex-shrink-0" />
              <p className="text-[12px] font-bold text-danger">{error}</p>
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !address.trim()}
            className="w-full bg-brand-green-500 text-brand-dark py-4 rounded-2xl text-[14px] font-black shadow-xl shadow-brand-green-500/20 hover:bg-brand-green-400 disabled:opacity-40 transition-all flex items-center justify-center gap-3 active:scale-[0.98]"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-5 h-5" />}
            {loading ? 'Processing...' : 'Add Wallet Manual'}
          </button>

          {/* Security Banner */}
          <div className="p-4 rounded-2xl flex items-start gap-4" style={{ background: 'var(--bg2)' }}>
            <div className="p-2 rounded-lg bg-brand-green-500/10 text-brand-green-500">
              <CheckCircle2 size={16} />
            </div>
            <p className="text-[11px] font-medium leading-relaxed" style={{ color: 'var(--text3)' }}>
              We only require read access to your public transaction history. Your private keys and seed phrases are never accessed or stored.
            </p>
          </div>
        </form>
      )}
    </div>
  );
}
