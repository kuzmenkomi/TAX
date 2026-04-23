import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { apiFetch } from '../api/client';
import { BlockchainWalletImport } from '../components/BlockchainWalletImport';
import { AlertCircle, Check, Loader2 } from 'lucide-react';

interface ImportedWallet {
  wallet_id: number;
  chain: string;
  address: string;
  transactions_count: number;
}

export function BlockchainImportPage() {
  const { token } = useAuth();
  const [wallets, setWallets] = useState<ImportedWallet[]>([]);
  const [loading, setLoading] = useState(true);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!token) { setLoading(false); return; }
    const loadWallets = async () => {
      try {
        const response = await apiFetch('/br/connections', { token });
        if (response.ok) {
          const data = await response.json();
          setWallets(data.wallets || []);
        }
      } catch (error) {
        console.error('Failed to load wallets:', error);
      } finally {
        setLoading(false);
      }
    };
    loadWallets();
  }, [token]);

  const handleSuccess = (result: any) => {
    setSuccessMessage(
      `✓ Successfully imported ${result.transactions_count} transactions from ${result.chain}`
    );
    setErrorMessage('');
    setTimeout(() => { window.location.reload(); }, 2000);
  };

  const handleError = (error: string) => {
    setErrorMessage(error);
    setSuccessMessage('');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-brand-green-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>Wallets</h1>
        <p className="text-[14px] mt-1" style={{ color: 'var(--text3)' }}>
          Connect your crypto wallets from 10+ blockchains for automatic transaction tracking
        </p>
      </div>

      {/* Status messages */}
      {successMessage && (
        <div className="px-5 py-3 rounded-2xl text-[13px] font-bold border flex items-center gap-3 animate-fade-in" style={{ background: 'var(--bg2)', borderColor: '#6af0c833', color: '#6af0c8' }}>
          <Check className="w-4 h-4 flex-shrink-0" />
          {successMessage}
        </div>
      )}
      {errorMessage && (
        <div className="px-5 py-3 rounded-2xl text-[13px] font-bold border flex items-center gap-3 animate-fade-in" style={{ background: 'var(--bg2)', borderColor: 'rgba(240, 106, 106, 0.2)', color: 'var(--danger)' }}>
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {errorMessage}
        </div>
      )}

      {/* Import Form */}
      <BlockchainWalletImport onSuccess={handleSuccess} onError={handleError} />

      {/* Imported wallets table container */}
      {wallets.length > 0 && (
        <div className="border rounded-[2.5rem] overflow-hidden shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
          <div className="px-8 py-5 border-b" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
            <h2 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Your Imported Wallets</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                  <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-[2px] text-left" style={{ color: 'var(--text3)' }}>Chain</th>
                  <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-[2px] text-left" style={{ color: 'var(--text3)' }}>Address</th>
                  <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-[2px] text-left" style={{ color: 'var(--text3)' }}>Transactions</th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: 'var(--border)' }}>
                {wallets.map((wallet) => (
                  <tr key={`${wallet.chain}-${wallet.wallet_id}`} className="hover:bg-brand-green-500/5 transition-colors group">
                    <td className="px-8 py-5">
                      <span className="text-[11px] font-bold px-3 py-1.5 rounded-full uppercase tracking-wider" style={{ background: 'var(--bg2)', color: 'var(--accent)' }}>
                        {wallet.chain}
                      </span>
                    </td>
                    <td className="px-8 py-5 text-[12px] font-mono opacity-80" style={{ color: 'var(--text2)' }}>
                      {wallet.address.length > 40
                        ? `${wallet.address.substring(0, 20)}...${wallet.address.substring(wallet.address.length - 8)}`
                        : wallet.address}
                    </td>
                    <td className="px-8 py-5">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-brand-green-500 shadow-[0_0_8px_var(--accent)]" />
                        <span className="text-[13px] font-bold" style={{ color: 'var(--text)' }}>{wallet.transactions_count}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Supported chains Grid */}
      <div className="border rounded-[2.5rem] p-8" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
        <h3 className="text-sm font-bold uppercase tracking-widest mb-6" style={{ color: 'var(--text2)' }}>Supported Blockchains</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {[
            { name: 'Ethereum', icon: 'Ξ' },
            { name: 'Polygon', icon: '◊' },
            { name: 'BNB Chain', icon: 'B' },
            { name: 'Bitcoin', icon: '₿' },
            { name: 'Solana', icon: '◎' },
            { name: 'Avalanche', icon: 'A' },
            { name: 'Arbitrum', icon: 'Ⓐ' },
            { name: 'Optimism', icon: 'Ⓞ' },
            { name: 'Base', icon: 'B' },
            { name: 'Tron', icon: 'T' },
          ].map((chain) => (
            <div key={chain.name} className="border rounded-2xl p-4 text-center transition-all hover:scale-[1.05]" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <div className="text-2xl mb-2 opacity-40 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--text)' }}>{chain.icon}</div>
              <p className="text-[11px] font-bold" style={{ color: 'var(--text2)' }}>{chain.name}</p>
            </div>
          ))}
        </div>
      </div>

      {/* FAQ Cards */}
      <div className="border rounded-[2.5rem] p-8 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
        <h3 className="text-sm font-bold uppercase tracking-widest mb-6" style={{ color: 'var(--text2)' }}>Frequently Asked Questions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {[
            ['📊 How often are wallets synced?', 'Currently, transactions are fetched once during import. Coming soon: automatic daily sync for all connected addresses.'],
            ['🔐 Is my wallet safe?', 'Absolutely. We only use public blockchain data. We never ask for, collect, or store your private keys or seed phrases.'],
            ['💰 Which tokens are supported?', 'All primary tokens (ERC-20, BEP-20, etc.) and native chain coins are automatically tracked and valued.'],
            ['⚙️ What about DeFi and swaps?', 'Our engine recognizes complex protocols. Swaps on Uniswap, Aave, and others are identified automatically.'],
          ].map(([q, a]) => (
            <div key={q as string} className="space-y-2">
              <p className="text-sm font-bold flex items-center gap-2" style={{ color: 'var(--text)' }}>
                <span className="w-1.5 h-1.5 rounded-full bg-brand-green-500" />
                {q}
              </p>
              <p className="text-xs leading-relaxed pl-3.5" style={{ color: 'var(--text3)' }}>{a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
