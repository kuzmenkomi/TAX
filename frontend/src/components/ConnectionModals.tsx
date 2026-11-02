import { useState, useRef } from 'react';
import { X, Zap, Upload, Wallet, ShieldCheck, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import apiV1 from '../api/v1';
import { cn } from '../utils/cn';
import { useAppContext } from '../context/AppContext';
import { UpgradeModal } from './UpgradeModal';

const EXCHANGE_OPTIONS = [
  { id: 'binance',  label: 'Binance',  hasPassphrase: false },
  { id: 'coinbase', label: 'Coinbase', hasPassphrase: false },
  { id: 'kraken',   label: 'Kraken',   hasPassphrase: false },
  { id: 'okx',      label: 'OKX',      hasPassphrase: true  },
  { id: 'bybit',    label: 'Bybit',    hasPassphrase: false },
  { id: 'kucoin',   label: 'KuCoin',   hasPassphrase: true  },
];

const CHAIN_OPTIONS = [
  { id: 'eth',  label: 'Ethereum'  },
  { id: 'btc',  label: 'Bitcoin'   },
  { id: 'sol',  label: 'Solana'    },
  { id: 'pol',  label: 'Polygon'   },
  { id: 'arb',  label: 'Arbitrum'  },
  { id: 'bnb',  label: 'BNB Chain' },
];

/* ── shared components ── */
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-[10px] font-bold tracking-[1.5px] uppercase mb-[6px]" style={{ color: 'var(--text3)' }}>{label}</p>
      {children}
    </div>
  );
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className="fi w-full" />;
}

function StatusMsg({ ok, msg }: { ok: boolean; msg: string }) {
  return (
    <div className="flex items-center gap-[8px] p-[10px] rounded-[10px] text-[12px]"
      style={{ background: ok ? 'rgba(16, 185, 129,0.08)' : 'rgba(255,77,106,0.08)', border: `1px solid ${ok ? 'rgba(16, 185, 129,0.2)' : 'rgba(255,77,106,0.2)'}`, color: ok ? 'var(--accent)' : '#ff4d6a' }}>
      {ok ? <CheckCircle size={14} /> : <AlertCircle size={14} />} {msg}
    </div>
  );
}

function Overlay({ onClose, children }: { onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-[400] flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)' }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      {children}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   CONNECT EXCHANGE MODAL (Revamped High-Fidelity)
   ══════════════════════════════════════════════════════════════ */
export function ConnectExchangeModal({ onClose, onSuccess, initialTab = 'api' }: { onClose: () => void; onSuccess: () => void; initialTab?: 'api' | 'csv' }) {
  const [activeTab, setActiveTab] = useState<'api' | 'csv'>(initialTab);
  const [view, setView] = useState<'form' | 'connecting' | 'success'>('form');
  const [exchange, setExchange] = useState('binance');
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [passphrase, setPassphrase] = useState('');
  const [label, setLabel] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [successData, setSuccessData] = useState<{ txCount: number; balance: number; duplicate?: boolean } | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [upgradeOpen, setUpgradeOpen] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const { bumpDataVersion, setAnalyzeResult } = useAppContext();

  const selectedOption = EXCHANGE_OPTIONS.find(e => e.id === exchange) || EXCHANGE_OPTIONS[0];

  const handleConnect = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (activeTab === 'api') {
      if (!apiKey.trim() || !apiSecret.trim()) {
        setStatus({ ok: false, msg: 'API Key and Secret are required.' });
        return;
      }
    } else {
      if (!file) {
        setStatus({ ok: false, msg: 'Please select a CSV file.' });
        return;
      }
    }

    setStatus(null);
    setView('connecting');
    setCurrentStep(1);

    try {
      // Step 1: Validation
      await new Promise(r => setTimeout(r, 800));
      setCurrentStep(2);

      let result: any;
      if (activeTab === 'api') {
        result = await apiV1.exchange.connect(exchange, apiKey.trim(), apiSecret.trim(), passphrase.trim() || undefined, label.trim() || undefined);
        setCurrentStep(3);
        await new Promise(r => setTimeout(r, 600));
        setCurrentStep(4);
        setSuccessData({ txCount: result.transaction_count || 0, balance: result.balance || 0 });
      } else {
        result = await apiV1.analysis.upload(file!, { format: exchange, accounting_method: 'FIFO' });
        setAnalyzeResult(result);
        setCurrentStep(3);
        await new Promise(r => setTimeout(r, 600));
        setCurrentStep(4);
        const imported = result.duplicate
          ? (result.rows_processed ?? 0)
          : (result.tx_imported ?? result.rows_processed ?? 0);
        setSuccessData({ txCount: imported, balance: 0, duplicate: Boolean(result.duplicate) });
      }

      bumpDataVersion();
      await new Promise(r => setTimeout(r, 400));
      setView('success');
    } catch (err: any) {
      setView('form');
      setStatus({ ok: false, msg: err.message || 'Operation failed. Please try again.' });
    }
  };

  const modalStyles = `
    .ex-modal { background: var(--card); border: 1px solid var(--border2); border-radius: 16px; width: 440px; box-shadow: 0 24px 64px rgba(0,0,0,.3); overflow: hidden; font-family: 'DM Sans', sans-serif; position: relative; transition: background 0.3s, border-color 0.3s; }
    :root.light .ex-modal { box-shadow: 0 24px 64px rgba(0,0,0,.1); }
    
    .ex-header { display: flex; align-items: center; gap: 14px; padding: 22px 24px 18px; border-bottom: 1px solid var(--border); position: relative; }
    .ex-icon { width: 42px; height: 42px; background: var(--accent-dim); border-radius: 11px; display: flex; align-items: center; justify-content: center; color: var(--accent); flex-shrink: 0; }
    .ex-title { font-size: 18px; font-weight: 700; letter-spacing: -0.3px; color: var(--text); }
    .ex-sub { font-size: 12px; color: var(--text2); margin-top: 2px; }
    
    .ex-close { position: absolute; right: 18px; top: 18px; width: 28px; height: 28px; border-radius: 7px; background: var(--card2); border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text2); transition: all .12s; }
    .ex-close:hover { background: var(--card3); color: var(--text); }
    
    .ex-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 4px; padding: 18px 24px 0; }
    .ex-chip { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 10px 8px; border-radius: 10px; border: 1px solid var(--border2); background: var(--card2); cursor: pointer; transition: all .15s; font-size: 12px; font-weight: 500; color: var(--text2); }
    .ex-chip:hover { border-color: var(--accent); color: var(--text); background: var(--card3); }
    .ex-chip.active { border-color: var(--accent); background: var(--accent-dim); color: var(--text); }
    
    .ex-logo { width: 28px; height: 28px; border-radius: 7px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 800; background: rgba(0,0,0,0.05); }
    :root.light .ex-logo { background: rgba(0,0,0,0.05); }
    
    .ex-tabs { display: grid; grid-template-columns: 1fr 1fr; background: var(--card2); border-radius: 10px; padding: 3px; gap: 3px; margin: 18px 24px; }
    .ex-tab { display: flex; align-items: center; justify-content: center; gap: 7px; padding: 9px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; color: var(--text2); transition: all .15s; }
    .ex-tab:hover { color: var(--text); }
    .ex-tab.active { background: var(--card); color: var(--text); box-shadow: 0 1px 4px rgba(0,0,0,.15); }
    
    .ex-badge { font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 700; background: var(--accent-dim); color: var(--accent); }
    .ex-panel { padding: 0 24px; }
    .ex-field { margin-bottom: 14px; }
    .ex-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .7px; color: var(--text3); margin-bottom: 8px; }
    
    .ex-input-wrap { position: relative; }
    .ex-input { width: 100%; background: var(--card2); border: 1px solid var(--border2); border-radius: 9px; padding: 11px 14px; color: var(--text); font-size: 13px; outline: none; transition: border-color .15s; }
    .ex-input:focus { border-color: var(--accent); }
    
    .ex-paste { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: var(--card3); border: 1px solid var(--border2); border-radius: 6px; padding: 3px 9px; font-size: 11px; font-weight: 600; color: var(--text2); cursor: pointer; transition: color .12s; }
    .ex-paste:hover { color: var(--text); }
    
    .ex-drop { border: 2px dashed var(--border2); border-radius: 10px; padding: 28px 20px; text-align: center; cursor: pointer; transition: all .15s; background: var(--card2); margin-bottom: 14px; }
    .ex-drop:hover { border-color: var(--accent); background: var(--accent-dim); }
    
    .ex-file { display: flex; align-items: center; gap: 10px; background: var(--accent-dim); border: 1px solid var(--accent); border-radius: 9px; padding: 10px 14px; margin-bottom: 14px; }
    .ex-sec { margin: 0 24px 16px; background: var(--accent-dim); border: 1px solid var(--accent); opacity: 0.6; border-radius: 8px; padding: 10px 12px; display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text2); line-height: 1.4; }
    
    .ex-btn { width: 100%; padding: 13px; background: var(--accent); color: #000; font-size: 14px; font-weight: 700; border: none; border-radius: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: opacity .15s; }
    .ex-btn:hover { opacity: .88; }
    .ex-btn:disabled { opacity: .4; cursor: not-allowed; }
    
    .ex-step { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text2); text-align: left; }
    .ex-step.done { color: var(--text); }
    .ex-step.active { color: var(--text); }
    .ex-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--border2); }
    .ex-step.done .ex-dot { background: var(--accent); }
    .ex-step.active .ex-dot { background: var(--warning); box-shadow: 0 0 6px var(--warning); }
    
    .ex-sstat { background: var(--card2); border: 1px solid var(--border); border-radius: 9px; padding: 12px; text-align: center; }
    .ex-sval { font-size: 20px; font-weight: 700; font-family: 'DM Mono', monospace; color: var(--accent); }
    .ex-slbl { font-size: 11px; color: var(--text2); margin-top: 3px; }
    .ex-hint { background: var(--card2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; margin-bottom: 14px; font-size: 12px; color: var(--text2); display: flex; gap: 8px; align-items: flex-start; }
  `;

  return (
    <Overlay onClose={onClose}>
      <style>{modalStyles}</style>
      <div className="ex-modal animate-in fade-in zoom-in duration-300">
        {view === 'form' && (
          <>
            <div className="ex-header">
              <div className="ex-icon"><Zap size={20} fill="currentColor" /></div>
              <div>
                <div className="ex-title">Connect Exchange</div>
                <div className="ex-sub">Read-only API keys — no withdrawal access</div>
              </div>
              <button className="ex-close" onClick={onClose}><X size={14} /></button>
            </div>

            <div className="ex-grid">
              {EXCHANGE_OPTIONS.map(opt => (
                <div key={opt.id} className={cn('ex-chip', exchange === opt.id && 'active')} onClick={() => setExchange(opt.id)}>
                  <div className="ex-logo">{opt.label.charAt(0)}</div>
                  {opt.label}
                </div>
              ))}
            </div>

            <div className="ex-tabs">
              <div className={cn('ex-tab', activeTab === 'api' && 'active')} onClick={() => setActiveTab('api')}>
                <Zap size={14} /> API Keys <span className="ex-badge">Auto-sync</span>
              </div>
              <div className={cn('ex-tab', activeTab === 'csv' && 'active')} onClick={() => setActiveTab('csv')}>
                <Upload size={14} /> CSV Import
              </div>
            </div>

            <div className="ex-panel">
              {activeTab === 'api' ? (
                <>
                  <div className="ex-field">
                    <div className="ex-label">API Key</div>
                    <div className="ex-input-wrap">
                      <input className="ex-input" type="text" placeholder="Paste your API key" value={apiKey} onChange={e => setApiKey(e.target.value)} />
                      <button className="ex-paste" onClick={async () => setApiKey(await navigator.clipboard.readText())}>Paste</button>
                    </div>
                  </div>
                  <div className="ex-field">
                    <div className="ex-label">API Secret</div>
                    <div className="ex-input-wrap">
                      <input className="ex-input" type="password" placeholder="Paste your API secret" value={apiSecret} onChange={e => setApiSecret(e.target.value)} />
                      <button className="ex-paste" onClick={async () => setApiSecret(await navigator.clipboard.readText())}>Paste</button>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <input type="file" ref={fileRef} className="hidden" accept=".csv,.xlsx" onChange={e => e.target.files?.[0] && setFile(e.target.files[0])} />
                  {!file ? (
                    <div className="ex-drop" onClick={() => fileRef.current?.click()}>
                      <Upload size={28} className="mx-auto mb-2 text-[#5a6672]" />
                      <div className="font-semibold text-[13px]">Drop your CSV file here</div>
                      <div className="text-[12px] text-[#5a6672]">or <span className="text-[var(--accent)] underline">browse files</span></div>
                    </div>
                  ) : (
                    <div className="ex-file">
                      <Upload size={16} className="text-[var(--accent)]" />
                      <span className="flex-1 text-[13px] font-medium truncate">{file.name}</span>
                      <button className="text-[#5a6672] hover:text-[#ff4d6a]" onClick={() => setFile(null)}><X size={14} /></button>
                    </div>
                  )}
                  <div className="ex-hint">
                    <AlertCircle size={14} className="text-[#f5a623] shrink-0 mt-0.5" />
                    <span>Export your trade history from {selectedOption.label}.</span>
                  </div>
                </>
              )}
              <div className="ex-field">
                <div className="ex-label">Label (optional)</div>
                <input className="ex-input" type="text" placeholder={`e.g. My ${selectedOption.label}`} value={label} onChange={e => setLabel(e.target.value)} />
              </div>
            </div>

            {status && (
              <div className="mx-6 mb-4 space-y-2">
                <StatusMsg ok={status.ok} msg={status.msg} />
                {!status.ok && (status.msg.toLowerCase().includes('limit') || status.msg.toLowerCase().includes('upgrade')) && (
                  <button 
                    onClick={() => setUpgradeOpen(true)}
                    className="w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-[11px] font-bold bg-[var(--accent)] text-black hover:opacity-90 transition-all cursor-pointer"
                  >
                    <Zap size={12} fill="currentColor" /> Upgrade Plan
                  </button>
                )}
              </div>
            )}

            <div className="ex-sec">
              <ShieldCheck size={14} className="text-[var(--accent)] shrink-0" />
              Keys are encrypted at rest. Read-only access.
            </div>

            <div className="p-[0_24px_22px]">
              <button className="ex-btn" onClick={() => handleConnect()} disabled={activeTab === 'api' ? (!apiKey || !apiSecret) : !file}>
                <Zap size={16} fill="currentColor" /> Connect Exchange
              </button>
            </div>
          </>
        )}

        {view === 'connecting' && (
          <div className="p-[48px_24px] text-center">
            <div className="w-11 h-11 border-3 border-[#252c32] border-t-[var(--accent)] rounded-full animate-spin mx-auto mb-5" />
            <div className="text-[16px] font-semibold mb-2">Connecting to {selectedOption.label}…</div>
            <div className="w-full mt-6">
              {[
                { id: 1, label: 'Validating credentials' },
                { id: 2, label: 'Fetching transactions' },
                { id: 3, label: 'Calculating data' },
                { id: 4, label: 'Finalizing' }
              ].map(step => (
                <div key={step.id} className={cn('ex-step', currentStep > step.id ? 'done' : currentStep === step.id ? 'active' : '')}>
                  <div className="ex-dot" /> {step.label}
                </div>
              ))}
            </div>
          </div>
        )}

        {view === 'success' && (
          <div className="p-[32px_24px_28px] text-center">
            <div className="w-14 h-14 background-[rgba(16, 185, 129,0.12)] rounded-2xl flex items-center justify-center text-[var(--accent)] mx-auto mb-4" style={{ background: 'rgba(16, 185, 129,0.12)' }}>
              <CheckCircle size={26} />
            </div>
            <h3 className="text-[18px] font-bold mb-2">{selectedOption.label} Connected!</h3>
            <p className="text-[13px] text-[#5a6672] mb-6">
              {successData?.duplicate ? 'This file was already imported earlier.' : 'Transactions imported and ready.'}
            </p>
            <div className="grid grid-cols-2 gap-2.5 mb-5 w-full">
              <div className="ex-sstat">
                <div className="ex-sval">{successData?.txCount.toLocaleString()}</div>
                <div className="ex-slbl">Transactions</div>
              </div>
              <div className="ex-sstat">
                <div className="ex-sval">${successData?.balance.toLocaleString() || '0'}</div>
                <div className="ex-slbl">Value</div>
              </div>
            </div>
            <button className="ex-btn" onClick={() => { onSuccess(); onClose(); }}>Go to Dashboard →</button>
          </div>
        )}
      </div>
      <UpgradeModal 
        isOpen={upgradeOpen} 
        onClose={() => setUpgradeOpen(false)} 
        currentPlan="free" 
      />
    </Overlay>
  );
}

/* ══════════════════════════════════════════════════════════════
   ADD WALLET MODAL
   ══════════════════════════════════════════════════════════════ */
export function AddWalletModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [chain, setChain] = useState('eth');
  const [address, setAddress] = useState('');
  const [label, setLabel] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const { bumpDataVersion } = useAppContext();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!address.trim()) { setStatus({ ok: false, msg: 'Please enter a wallet address.' }); return; }
    setLoading(true); setStatus(null);
    try {
      await apiV1.wallet.connect(chain, address.trim(), label.trim() || undefined);
      setStatus({ ok: true, msg: 'Wallet added!' });
      bumpDataVersion();
      setTimeout(() => { onSuccess(); onClose(); }, 1200);
    } catch (err: any) {
      setStatus({ ok: false, msg: err.message || 'Could not add wallet.' });
    } finally { setLoading(false); }
  }

  return (
    <Overlay onClose={onClose}>
      <div className="relative w-full max-w-[440px] rounded-[20px] p-[28px] animate-in fade-in zoom-in duration-200"
        style={{ background: 'var(--card)', border: '1px solid var(--border2)' }}>
        <button onClick={onClose} className="absolute top-[14px] right-[14px] w-[28px] h-[28px] rounded-full flex items-center justify-center transition-all"
          style={{ background: 'var(--card2)', border: '1px solid var(--border)', color: 'var(--text2)' }}>
          <X size={14} />
        </button>
        
        <div className="flex items-center gap-[10px] mb-[20px]">
          <div className="w-[36px] h-[36px] rounded-[10px] flex items-center justify-center" style={{ background: 'rgba(16, 185, 129,0.08)', border: '1px solid rgba(16, 185, 129,0.2)' }}>
            <Wallet size={18} className="text-[var(--accent)]" />
          </div>
          <div>
            <h2 className="font-syne font-black text-[17px]" style={{ color: 'var(--text)' }}>Add Wallet</h2>
            <p className="text-[11px]" style={{ color: 'var(--text2)' }}>Public address only</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-[14px]">
          <Field label="Blockchain">
            <div className="grid grid-cols-3 gap-[6px]">
              {CHAIN_OPTIONS.map(c => (
                <button key={c.id} type="button" onClick={() => setChain(c.id)}
                  className={cn('py-[8px] px-[10px] rounded-[8px] text-[11px] font-bold transition-all border', chain === c.id
                    ? 'border-[rgba(16, 185, 129,0.4)] bg-[rgba(16, 185, 129,0.08)] text-[var(--accent)]'
                    : 'border-[var(--border)] bg-[var(--card2)] text-[var(--text2)] hover:border-[var(--border2)]')}>
                  {c.label}
                </button>
              ))}
            </div>
          </Field>

          <Field label="Wallet Address">
            <Input value={address} onChange={e => setAddress(e.target.value)} placeholder="0x…" autoComplete="off" />
          </Field>

          <Field label="Label (optional)">
            <Input value={label} onChange={e => setLabel(e.target.value)} placeholder="e.g. Cold storage" />
          </Field>

          {status && <StatusMsg ok={status.ok} msg={status.msg} />}

          <button type="submit" disabled={loading}
            className="conn-cta-primary w-full justify-center py-[12px] disabled:opacity-50 disabled:cursor-not-allowed">
            {loading ? <><Loader size={15} className="animate-spin" /> Adding...</> : <><Wallet size={15} /> Add Wallet</>}
          </button>
        </form>
      </div>
    </Overlay>
  );
}
