import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle2, Loader2, Trash2, RotateCw, Plus, Shield, ArrowRightLeft } from 'lucide-react';
import { apiFetch } from '../api/client';
import { useAuth } from '../auth/AuthContext';

interface Exchange {
  id: string;
  name: string;
  tier: number;
}

interface ConnectedExchange {
  id: number;
  exchange_name: string;
  label: string | null;
  status: string;
  last_synced: string | null;
}

export function ExchangeManager() {
  const { token } = useAuth();
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [connectedExchanges, setConnectedExchanges] = useState<ConnectedExchange[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');

  const [selectedExchange, setSelectedExchange] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [passphrase, setPassphrase] = useState('');
  const [label, setLabel] = useState('');
  const [connecting, setConnecting] = useState(false);

  const handleOAuth = async (provider: string) => {
    setConnecting(true);
    setMessage('');
    try {
      const response = await apiFetch(`/oauth/${provider}/initiate`, { token });
      if (response.ok) {
        const data = await response.json();
        // Save state to sessionStorage for verification after redirect
        sessionStorage.setItem('oauth_state', data.state);
        sessionStorage.setItem('oauth_provider', provider);
        // Redirect to provider
        window.location.href = data.url;
      } else {
        setMessage('✗ Failed to initiate OAuth');
        setConnecting(false);
      }
    } catch (error) {
      setMessage(`✗ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setConnecting(false);
    }
  };

  useEffect(() => {
    if (!token) { setLoading(false); return; }
    loadExchanges();
  }, [token]);

  const loadExchanges = async () => {
    try {
      const res1 = await apiFetch('/br/exchanges');
      if (res1.ok) setExchanges(await res1.json());
      const res2 = await apiFetch('/br/exchanges/my', { token });
      if (res2.ok) setConnectedExchanges(await res2.json());
      setLoading(false);
    } catch {
      setLoading(false);
    }
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedExchange || !apiKey || !apiSecret) {
      setMessage('Please fill in all required fields');
      return;
    }
    setConnecting(true);
    setMessage('');
    try {
      const response = await apiFetch('/br/exchange/connect', {
        method: 'POST', token,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exchange_name: selectedExchange, api_key: apiKey, api_secret: apiSecret, passphrase: passphrase || null, label: label || null }),
      });
      if (response.ok) {
        const data = await response.json();
        setMessage(`✓ Connected to ${data.exchange_name}`);
        setSelectedExchange(''); setApiKey(''); setApiSecret(''); setPassphrase(''); setLabel('');
        setShowForm(false);
        await loadExchanges();
      } else {
        const error = await response.json();
        setMessage(`✗ Connection failed: ${error.detail}`);
      }
    } catch (error) {
      setMessage(`✗ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async (exchangeId: number, name: string) => {
    if (!confirm(`Disconnect ${name}? Your API credentials will be deleted.`)) return;
    try {
      const response = await apiFetch(`/br/exchange/${exchangeId}`, { method: 'DELETE', token });
      if (response.ok) { setMessage(`✓ Disconnected ${name}`); await loadExchanges(); }
    } catch (error) {
      setMessage(`✗ Failed to disconnect: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleSync = async (exchangeId: number, name: string) => {
    setSyncing(true); setMessage('');
    try {
      const response = await apiFetch(`/br/exchange/${exchangeId}/sync`, { method: 'POST', token });
      if (response.ok) {
        const data = await response.json();
        setMessage(`✓ Synced ${name}: ${data.transactions_found} transactions found`);
        await loadExchanges();
      } else { setMessage(`✗ Sync failed`); }
    } catch (error) {
      setMessage(`✗ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally { setSyncing(false); }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-brand-green-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      {/* Header Container */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>Exchanges</h1>
          <p className="text-[13px] mt-0.5" style={{ color: 'var(--text3)' }}>Connect your exchange accounts to sync trades automatically</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-brand-green-500 text-brand-dark rounded-xl text-[12px] font-bold shadow-lg shadow-brand-green-500/20 hover:bg-brand-green-400 transition-all active:scale-95"
        >
          {showForm ? 'Close Form' : (
            <>
              <Plus className="w-3.5 h-3.5" />
              Add Exchange
            </>
          )}
        </button>
      </div>

      {/* Status message */}
      {message && (
        <div className={`px-4 py-3 rounded-xl border animate-fade-in ${
          message.startsWith('✓')
            ? 'bg-[#6af0c8]/10 text-[#6af0c8] border-[#6af0c8]/20'
            : 'bg-danger/10 text-danger border-danger/20'
        }`}>
          <div className="flex items-center gap-2">
            {message.startsWith('✓') ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span className="text-xs font-semibold">{message}</span>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Connected exchanges list - Left Column */}
        <div className="lg:col-span-2 space-y-6">
          <div className="border rounded-[2rem] overflow-hidden shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <div className="px-6 py-5 border-b flex items-center justify-between" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <h2 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text2)' }}>Connected Accounts</h2>
              <span className="px-2.5 py-1 bg-brand-green-500/10 text-brand-green-500 rounded-full text-[10px] font-bold border border-brand-green-500/20">
                {connectedExchanges.length} Total
              </span>
            </div>

            {connectedExchanges.length > 0 ? (
              <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
                {connectedExchanges.map((ex) => (
                  <div key={ex.id} className="flex items-center justify-between px-6 py-5 transition-colors group">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-bold" style={{ color: 'var(--text)' }}>{ex.exchange_name}</p>
                        <span className={`px-2 py-0.5 text-[9px] font-bold rounded-md uppercase tracking-wider ${
                          ex.status === 'synced' || ex.status === 'connected'
                            ? 'bg-[#6af0c8]/10 text-[#6af0c8]'
                            : 'bg-warning/10 text-warning'
                        }`}>
                          {ex.status}
                        </span>
                      </div>
                      {ex.label && <p className="text-[11px] mt-0.5" style={{ color: 'var(--text3)' }}>{ex.label}</p>}
                      {ex.last_synced && (
                        <p className="text-[10px] mt-1 opacity-70" style={{ color: 'var(--text3)' }}>
                          Synced: {new Date(ex.last_synced).toLocaleString()}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleSync(ex.id, ex.exchange_name)}
                        disabled={syncing}
                        className="p-2.5 bg-brand-blue-500/10 text-brand-blue-500 rounded-xl hover:bg-brand-blue-500/20 disabled:opacity-50 transition-all"
                        title="Sync"
                      >
                        <RotateCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
                      </button>
                      <button
                        onClick={() => handleDisconnect(ex.id, ex.exchange_name)}
                        className="p-2.5 bg-danger/10 text-danger rounded-xl hover:bg-danger/20 transition-all"
                        title="Disconnect"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-20 px-6">
                <div className="w-16 h-16 border rounded-3xl flex items-center justify-center mx-auto mb-4" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                  <ArrowRightLeft className="w-8 h-8 opacity-20" style={{ color: 'var(--text)' }} />
                </div>
                <p className="text-sm font-medium" style={{ color: 'var(--text3)' }}>No exchange accounts connected yet</p>
                <button onClick={() => setShowForm(true)} className="mt-4 text-brand-green-500 text-xs font-bold hover:underline">
                  Connect your first exchange →
                </button>
              </div>
            )}
          </div>

          {/* Supported exchanges list */}
          <div className="border rounded-[2rem] p-6 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <h3 className="text-sm font-bold uppercase tracking-widest mb-4" style={{ color: 'var(--text2)' }}>Currently Supported</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {exchanges.slice(0, 11).map((ex) => (
                <div key={ex.id} className="p-4 border rounded-2xl transition-all hover:scale-[1.02]" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                  <p className="text-xs font-bold truncate" style={{ color: 'var(--text)' }}>{ex.name}</p>
                  <p className="text-[9px] mt-1" style={{ color: ex.tier === 1 ? 'var(--accent)' : 'var(--text3)' }}>
                    {ex.tier === 1 ? 'High Priority' : 'Supported'}
                  </p>
                </div>
              ))}
              {exchanges.length > 11 && (
                <div className="p-4 border border-dashed rounded-2xl flex items-center justify-center" style={{ borderColor: 'var(--border)' }}>
                  <p className="text-[10px] font-bold" style={{ color: 'var(--text3)' }}>+{exchanges.length - 11} more</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Form area - Right Column */}
        <div className="lg:col-span-1">
          {showForm ? (
            <div className="border rounded-[2rem] p-8 shadow-xl sticky top-6 animate-in slide-in-from-right-4" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-brand-green-500/10 rounded-xl flex items-center justify-center">
                  <Plus className="text-brand-green-500" size={20} />
                </div>
                <h3 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text)' }}>Connect API</h3>
              </div>
              
              <form onSubmit={handleConnect} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-widest pl-1" style={{ color: 'var(--text3)' }}>Exchange</label>
                  <select
                    value={selectedExchange}
                    onChange={(e) => setSelectedExchange(e.target.value)}
                    className="w-full px-4 py-3 border rounded-xl text-sm transition-all focus:outline-none focus:border-brand-green-500/50"
                    style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                    disabled={connecting}
                  >
                    <option value="">Choose exchange...</option>
                    {exchanges.map((ex) => (
                      <option key={ex.id} value={ex.id}>{ex.name}</option>
                    ))}
                  </select>
                </div>
                
                {selectedExchange === 'coinbase' ? (
                  <div className="py-4 space-y-4">
                    <button
                      type="button"
                      onClick={() => handleOAuth('coinbase')}
                      disabled={connecting}
                      className="w-full bg-brand-blue-500 text-white py-3.5 rounded-xl font-bold text-sm shadow-lg shadow-brand-blue-500/20 hover:bg-brand-blue-400 disabled:opacity-40 transition-all flex items-center justify-center gap-2"
                    >
                      {connecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                      Connect with Coinbase (Recommended)
                    </button>
                    <div className="flex items-center gap-2 px-2">
                      <div className="h-px flex-1 bg-border opacity-20"></div>
                      <span className="text-[10px] font-bold uppercase tracking-widest text-text3">or use API keys</span>
                      <div className="h-px flex-1 bg-border opacity-20"></div>
                    </div>
                    <div className="space-y-4 opacity-50 focus-within:opacity-100 transition-opacity">
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-bold uppercase tracking-widest pl-1" style={{ color: 'var(--text3)' }}>API Key</label>
                        <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
                          placeholder="Enter key"
                          className="w-full px-4 py-3 border rounded-xl text-sm transition-all focus:outline-none focus:border-brand-green-500/50"
                          style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                          disabled={connecting} />
                      </div>
                      
                      <div className="space-y-1.5">
                        <label className="text-[10px] font-bold uppercase tracking-widest pl-1" style={{ color: 'var(--text3)' }}>API Secret</label>
                        <input type="password" value={apiSecret} onChange={(e) => setApiSecret(e.target.value)}
                          placeholder="Enter secret"
                          className="w-full px-4 py-3 border rounded-xl text-sm transition-all focus:outline-none focus:border-brand-green-500/50"
                          style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                          disabled={connecting} />
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold uppercase tracking-widest pl-1" style={{ color: 'var(--text3)' }}>API Key</label>
                      <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
                        placeholder="Enter key"
                        className="w-full px-4 py-3 border rounded-xl text-sm transition-all focus:outline-none focus:border-brand-green-500/50"
                        style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                        disabled={connecting} />
                    </div>
                    
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold uppercase tracking-widest pl-1" style={{ color: 'var(--text3)' }}>API Secret</label>
                      <input type="password" value={apiSecret} onChange={(e) => setApiSecret(e.target.value)}
                        placeholder="Enter secret"
                        className="w-full px-4 py-3 border rounded-xl text-sm transition-all focus:outline-none focus:border-brand-green-500/50"
                        style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                        disabled={connecting} />
                    </div>
                  </>
                )}

                <div className="space-y-1.5 pt-2">
                  <button type="submit" disabled={connecting || !selectedExchange || !apiKey || !apiSecret}
                    className="w-full bg-brand-green-500 text-brand-dark py-3.5 rounded-xl font-bold text-sm shadow-lg shadow-brand-green-500/20 hover:bg-brand-green-400 disabled:opacity-40 transition-all flex items-center justify-center gap-2">
                    {connecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                    {connecting ? 'Connecting...' : 'Securely Connect'}
                  </button>
                  <button type="button" onClick={() => setShowForm(false)}
                    className="w-full py-3 text-xs font-bold uppercase tracking-widest opacity-60 hover:opacity-100 transition-opacity" style={{ color: 'var(--text)' }}>
                    Cancel
                  </button>
                </div>
              </form>

              <div className="mt-8 p-4 rounded-xl border border-dashed flex items-start gap-3" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                <Shield className="w-4 h-4 text-brand-green-500 flex-shrink-0 mt-0.5" />
                <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text3)' }}>
                  Encryption active. We use read-only keys to protect your assets. Passphrase needed for OKX/Coinbase.
                </p>
              </div>
            </div>
          ) : (
            <div className="border rounded-[2rem] p-8 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <h3 className="text-sm font-bold uppercase tracking-widest mb-6" style={{ color: 'var(--text2)' }}>Quick Guide</h3>
              <div className="space-y-6">
                {[
                  { step: '01', title: 'Generate Keys', desc: 'Go to your exchange API settings and create read-only keys.' },
                  { step: '02', title: 'Set Permissions', desc: 'Ensure "Transfer" is disabled. Only "Read" is required.' },
                  { step: '03', title: 'Connect App', desc: 'Paste keys here and we will handle the rest.' },
                ].map((item) => (
                  <div key={item.step} className="flex gap-4">
                    <span className="text-2xl font-black opacity-10" style={{ color: 'var(--text)' }}>{item.step}</span>
                    <div>
                      <h4 className="text-xs font-bold mb-1" style={{ color: 'var(--text)' }}>{item.title}</h4>
                      <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text3)' }}>{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
