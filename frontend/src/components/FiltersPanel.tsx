import { useState } from 'react';
import { ChevronDown, X, Settings } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

export interface FilterState {
  sortBy: 'ascending' | 'descending';
  accounts: string[];
  assets: string[];
  dateRange: { from: string; to: string } | null;
  blockchainAddresses: string[];
  transactionTypes: string[];
}

interface FiltersPanelProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
}

const ACCOUNTS = ['Binance', 'Coinbase', 'Kraken', 'Metamask', 'Ledger', 'Phantom', 'Wallet Connect'];
const ASSETS = ['Bitcoin (BTC)', 'Ethereum (ETH)', 'Solana (SOL)', 'Cardano (ADA)', 'USDC', 'USDT', 'AVAX', 'Polygon (MATIC)'];
const TRANSACTION_TYPES = ['Buy', 'Sell', 'Transfer', 'Deposit', 'Withdrawal', 'Swap', 'Reward', 'Airdrop'];

export function FiltersPanel({ filters, onFiltersChange }: FiltersPanelProps) {
  const { t } = useI18n();
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [blockchainInput, setBlockchainInput] = useState('');

  const toggleAccount = (account: string) => {
    const updated = filters.accounts.includes(account)
      ? filters.accounts.filter(a => a !== account)
      : [...filters.accounts, account];
    onFiltersChange({ ...filters, accounts: updated });
  };

  const toggleAsset = (asset: string) => {
    const updated = filters.assets.includes(asset)
      ? filters.assets.filter(a => a !== asset)
      : [...filters.assets, asset];
    onFiltersChange({ ...filters, assets: updated });
  };

  const toggleTransactionType = (type: string) => {
    const updated = filters.transactionTypes.includes(type)
      ? filters.transactionTypes.filter(t => t !== type)
      : [...filters.transactionTypes, type];
    onFiltersChange({ ...filters, transactionTypes: updated });
  };

  const addBlockchainAddress = () => {
    if (blockchainInput.trim()) {
      onFiltersChange({ ...filters, blockchainAddresses: [...filters.blockchainAddresses, blockchainInput.trim()] });
      setBlockchainInput('');
    }
  };

  const removeBlockchainAddress = (address: string) => {
    onFiltersChange({ ...filters, blockchainAddresses: filters.blockchainAddresses.filter(a => a !== address) });
  };

  const clearAllFilters = () => {
    onFiltersChange({ sortBy: 'ascending', accounts: [], assets: [], dateRange: null, blockchainAddresses: [], transactionTypes: [] });
  };

  const activeFiltersCount = filters.accounts.length + filters.assets.length +
    filters.blockchainAddresses.length + filters.transactionTypes.length + (filters.dateRange ? 1 : 0);

  // Shared dropdown button style
  const dropdownBtnClass = "w-full px-4 py-3 border rounded-xl flex items-center justify-between transition-all text-xs font-bold active:scale-[0.98]";
  const dropdownPanelClass = "mt-2 border rounded-2xl shadow-xl z-20 overflow-hidden animate-in fade-in zoom-in-95 duration-200";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <Settings className="w-4 h-4 opacity-40" style={{ color: 'var(--text)' }} />
          <h2 className="text-sm font-black uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Manage View</h2>
          {activeFiltersCount > 0 && (
            <span className="px-2 py-0.5 rounded bg-brand-green-500 text-brand-dark text-[10px] font-black">
              {activeFiltersCount}
            </span>
          )}
        </div>
        {activeFiltersCount > 0 && (
          <button onClick={clearAllFilters} className="text-brand-green-500 text-[11px] font-black uppercase tracking-widest hover:underline decoration-2">
            Reset
          </button>
        )}
      </div>

      {/* Sort by */}
      <div>
        <label className="block text-[10px] font-black uppercase tracking-widest opacity-40 mb-2 ml-1" style={{ color: 'var(--text)' }}>Ordering</label>
        <div className="relative">
          <button onClick={() => setOpenDropdown(openDropdown === 'sort' ? null : 'sort')} 
            className={dropdownBtnClass}
            style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}>
            <span className="capitalize">{filters.sortBy}</span>
            <ChevronDown className={`w-4 h-4 opacity-40 transition-transform ${openDropdown === 'sort' ? 'rotate-180' : ''}`} />
          </button>
          {openDropdown === 'sort' && (
            <div className={`absolute top-full left-0 right-0 ${dropdownPanelClass}`} style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              {['ascending', 'descending'].map(option => (
                <button key={option} onClick={() => { onFiltersChange({ ...filters, sortBy: option as 'ascending' | 'descending' }); setOpenDropdown(null); }}
                  className={`w-full text-left px-5 py-3 text-[12px] font-bold capitalize transition-colors ${
                    filters.sortBy === option ? 'bg-brand-green-500 text-brand-dark' : 'hover:bg-brand-green-500/10'
                  }`}
                  style={filters.sortBy !== option ? { color: 'var(--text2)' } : undefined}>
                  {option}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Accounts */}
      <div>
        <label className="block text-[10px] font-black uppercase tracking-widest opacity-40 mb-2 ml-1" style={{ color: 'var(--text)' }}>
          Portfolio Sources
        </label>
        <button onClick={() => setOpenDropdown(openDropdown === 'accounts' ? null : 'accounts')} 
          className={dropdownBtnClass}
          style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}>
          <span className="truncate">{filters.accounts.length > 0 ? `${filters.accounts.length} Selected` : 'All Sources'}</span>
          <ChevronDown className={`w-4 h-4 opacity-40 transition-transform ${openDropdown === 'accounts' ? 'rotate-180' : ''}`} />
        </button>
        {openDropdown === 'accounts' && (
          <div className={`${dropdownPanelClass} p-3 space-y-1`} style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            {ACCOUNTS.map(account => (
              <label key={account} className="flex items-center gap-3 cursor-pointer p-3 hover:bg-brand-green-500/5 rounded-xl text-[12px] font-bold group transition-colors">
                <input type="checkbox" checked={filters.accounts.includes(account)} onChange={() => toggleAccount(account)}
                  className="w-4 h-4 rounded border-border bg-transparent checked:bg-brand-green-500" />
                <span className={filters.accounts.includes(account) ? 'text-brand-green-500' : ''} style={!filters.accounts.includes(account) ? { color: 'var(--text2)' } : undefined}>{account}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Assets */}
      <div>
        <label className="block text-[10px] font-black uppercase tracking-widest opacity-40 mb-2 ml-1" style={{ color: 'var(--text)' }}>
          Cryptocurrencies
        </label>
        <button onClick={() => setOpenDropdown(openDropdown === 'assets' ? null : 'assets')} 
          className={dropdownBtnClass}
          style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}>
          <span className="truncate">{filters.assets.length > 0 ? `${filters.assets.length} Selected` : 'All Assets'}</span>
          <ChevronDown className={`w-4 h-4 opacity-40 transition-transform ${openDropdown === 'assets' ? 'rotate-180' : ''}`} />
        </button>
        {openDropdown === 'assets' && (
          <div className={`${dropdownPanelClass} p-3 space-y-1 max-h-72 overflow-y-auto custom-scrollbar`} style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            {ASSETS.map(asset => (
              <label key={asset} className="flex items-center gap-3 cursor-pointer p-3 hover:bg-brand-green-500/5 rounded-xl text-[12px] font-bold group transition-colors">
                <input type="checkbox" checked={filters.assets.includes(asset)} onChange={() => toggleAsset(asset)}
                  className="w-4 h-4 rounded border-border bg-transparent checked:bg-brand-green-500" />
                <span className={filters.assets.includes(asset) ? 'text-brand-green-500' : ''} style={!filters.assets.includes(asset) ? { color: 'var(--text2)' } : undefined}>{asset}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Date Range */}
      <div>
        <label className="block text-[10px] font-black uppercase tracking-widest opacity-40 mb-2 ml-1" style={{ color: 'var(--text)' }}>Fiscal Period</label>
        <button onClick={() => setOpenDropdown(openDropdown === 'date' ? null : 'date')} 
          className={dropdownBtnClass}
          style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}>
          <span className="truncate">
            {filters.dateRange ? `${filters.dateRange.from} → ${filters.dateRange.to}` : 'Select Window'}
          </span>
          <ChevronDown className={`w-4 h-4 opacity-40 transition-transform flex-shrink-0 ${openDropdown === 'date' ? 'rotate-180' : ''}`} />
        </button>
        {openDropdown === 'date' && (
          <div className={`${dropdownPanelClass} p-5 space-y-4`} style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <div>
              <label className="text-[10px] font-black uppercase tracking-widest opacity-40 block mb-2" style={{ color: 'var(--text)' }}>Start Date</label>
              <input type="date" value={filters.dateRange?.from || ''}
                onChange={(e) => onFiltersChange({ ...filters, dateRange: { from: e.target.value, to: filters.dateRange?.to || '' } })}
                className="w-full px-4 py-3 border rounded-xl text-[12px] font-bold focus:outline-none focus:border-brand-green-500"
                style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }} />
            </div>
            <div>
              <label className="text-[10px] font-black uppercase tracking-widest opacity-40 block mb-2" style={{ color: 'var(--text)' }}>End Date</label>
              <input type="date" value={filters.dateRange?.to || ''}
                onChange={(e) => onFiltersChange({ ...filters, dateRange: { from: filters.dateRange?.from || '', to: e.target.value } })}
                className="w-full px-4 py-3 border rounded-xl text-[12px] font-bold focus:outline-none focus:border-brand-green-500"
                style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }} />
            </div>
          </div>
        )}
      </div>

      {/* Transaction Type */}
      <div>
        <label className="block text-[10px] font-black uppercase tracking-widest opacity-40 mb-2 ml-1" style={{ color: 'var(--text)' }}>
          Activity Class
        </label>
        <button onClick={() => setOpenDropdown(openDropdown === 'type' ? null : 'type')} 
          className={dropdownBtnClass}
          style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}>
          <span className="truncate">{filters.transactionTypes.length > 0 ? `${filters.transactionTypes.length} Selected` : 'All Activity'}</span>
          <ChevronDown className={`w-4 h-4 opacity-40 transition-transform ${openDropdown === 'type' ? 'rotate-180' : ''}`} />
        </button>
        {openDropdown === 'type' && (
          <div className={`${dropdownPanelClass} p-3 space-y-1`} style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            {TRANSACTION_TYPES.map(type => (
              <label key={type} className="flex items-center gap-3 cursor-pointer p-3 hover:bg-brand-green-500/5 rounded-xl text-[12px] font-bold group transition-colors">
                <input type="checkbox" checked={filters.transactionTypes.includes(type)} onChange={() => toggleTransactionType(type)}
                  className="w-4 h-4 rounded border-border bg-transparent checked:bg-brand-green-500" />
                <span className={filters.transactionTypes.includes(type) ? 'text-brand-green-500' : ''} style={!filters.transactionTypes.includes(type) ? { color: 'var(--text2)' } : undefined}>{type}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Blockchain Address */}
      <div>
        <label className="block text-[10px] font-black uppercase tracking-widest opacity-40 mb-2 ml-1" style={{ color: 'var(--text)' }}>
          On-chain Filter
        </label>
        <div className="flex gap-2">
          <input type="text" placeholder="Wallet address..." value={blockchainInput}
            onChange={(e) => setBlockchainInput(e.target.value)}
            onKeyPress={(e) => { if (e.key === 'Enter') addBlockchainAddress(); }}
            className="flex-1 px-4 py-3 border rounded-xl text-[12px] font-bold placeholder:opacity-30 focus:outline-none focus:border-brand-green-500"
            style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }} />
          <button onClick={addBlockchainAddress}
            className="px-4 py-3 bg-brand-green-500 text-brand-dark text-[11px] font-black rounded-xl hover:bg-brand-green-400 transition-all shadow-lg shadow-brand-green-500/20 active:scale-95">
            ADD
          </button>
        </div>
        {filters.blockchainAddresses.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            {filters.blockchainAddresses.map(address => (
              <div key={address} className="inline-flex items-center gap-2 px-3 py-1.5 bg-brand-green-500/10 text-brand-green-500 rounded-lg text-[10px] font-black border border-brand-green-500/20 animate-in zoom-in-95">
                <span className="truncate max-w-[120px] font-mono tracking-tight" title={address}>{address}</span>
                <button onClick={() => removeBlockchainAddress(address)} className="hover:text-danger flex-shrink-0 transition-colors">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
