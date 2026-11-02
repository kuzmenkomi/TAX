import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, Loader2, Clock, AlertCircle, 
  CheckCircle2, Settings, Info, Shield, 
  Database, Zap, ToggleLeft, ToggleRight, 
  ExternalLink 
} from 'lucide-react';
import apiV1, { apiFetch } from '../api/v1';

interface ConnectionSyncInfo {
  id: number;
  chain?: string;
  exchange_name?: string;
  address?: string;
  sync_status: string;
  auto_sync_enabled: boolean;
  last_synced_at: string | null;
  next_sync_at: string | null;
  last_error: string | null;
}

interface SyncJob {
  id: string;
  name: string;
  next_run_time: string | null;
}

interface FullSyncStatus {
  scheduler_running: boolean;
  jobs: SyncJob[];
  wallets: ConnectionSyncInfo[];
  exchanges: ConnectionSyncInfo[];
}

export function SyncSettings() {
  const [status, setStatus] = useState<FullSyncStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [manualSyncing, setManualSyncing] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchFullStatus();
    const interval = setInterval(fetchFullStatus, 15000); // Higher frequency for 'Live' feel
    return () => clearInterval(interval);
  }, []);

  const fetchFullStatus = async () => {
    try {
      const [sysRes, detailRes] = await Promise.all([
        apiFetch('/br/sync/status', { useAuth: true }),
        apiFetch('/sync-settings/status', { useAuth: true })
      ]);
      
      if (sysRes.ok && detailRes.ok) {
        const sysData = await sysRes.json();
        const detailData = await detailRes.json();
        setStatus({
          scheduler_running: sysData.scheduler_running,
          jobs: sysData.jobs,
          wallets: detailData.wallets,
          exchanges: detailData.exchanges
        });
      }
    } catch (error) {
      console.error('Sync status fetch failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleAutoSync = async (type: 'wallet' | 'exchange', id: number, current: boolean) => {
    setActionLoading(`${type}-${id}`);
    try {
      const res = await apiFetch(`/sync-settings/${type}/${id}/auto-sync`, {
        method: 'PATCH',
        body: JSON.stringify({ enabled: !current })
      });
      if (res.ok) {
        fetchFullStatus();
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleManualSync = async (endpoint: string, label: string) => {
    setManualSyncing(true);
    setMessage('');
    try {
      const response = await apiFetch(endpoint, { method: 'POST' });
      if (response.ok) {
        setMessage(`✓ ${label} triggered successfully.`);
        setTimeout(fetchFullStatus, 2000);
      }
    } catch (error) {
      setMessage(`✗ Error: ${error instanceof Error ? error.message : 'Unknown'}`);
    } finally {
      setManualSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-brand-green-500" />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>Synchronization Engine</h1>
          <p className="text-[14px] mt-1" style={{ color: 'var(--text3)' }}>Enterprise-grade background ingestion and data reconciliation</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 rounded-full border border-emerald-500/20">
          <Zap className="w-4 h-4 text-emerald-500" />
          <span className="text-[11px] font-black uppercase text-emerald-500 tracking-wider">Live Sync Active</span>
        </div>
      </div>

      {/* Main Status Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Connection Monitor */}
        <div className="lg:col-span-2 space-y-6">
          <div className="border rounded-[2.5rem] p-8 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <h2 className="text-sm font-bold uppercase tracking-widest mb-8 flex items-center gap-3" style={{ color: 'var(--text2)' }}>
              <Database className="w-5 h-5 opacity-40" />
              Connection Monitor
            </h2>

            <div className="space-y-4">
               {/* Wallets */}
               {status?.wallets.map(w => (
                <div key={`w-${w.id}`} className="flex items-center justify-between p-5 bg-black/5 rounded-3xl border border-white/5">
                  <div className="flex items-center gap-4">
                    <div className={`w-3 h-3 rounded-full ${w.sync_status === 'syncing' ? 'bg-emerald-400 animate-pulse' : w.sync_status === 'error' ? 'bg-red-400' : 'bg-white/20'}`} />
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-[14px] font-bold uppercase" style={{ color: 'var(--text)' }}>{w.chain}</p>
                        <span className="text-[10px] opacity-40 font-mono tracking-tighter" style={{ color: 'var(--text)' }}>{w.address?.slice(0, 10)}...</span>
                      </div>
                      <p className="text-[10px] opacity-60" style={{ color: 'var(--text3)' }}>
                        {w.sync_status === 'syncing' ? 'Processing blocks...' : `Last sync: ${w.last_synced_at ? new Date(w.last_synced_at).toLocaleString() : 'Never'}`}
                      </p>
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => toggleAutoSync('wallet', w.id, w.auto_sync_enabled)}
                    disabled={!!actionLoading}
                    className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                  >
                    {w.auto_sync_enabled ? <ToggleRight className="text-emerald-500 w-6 h-6" /> : <ToggleLeft className="text-white/20 w-6 h-6" />}
                    <span className="text-[10px] uppercase font-black tracking-widest" style={{ color: 'var(--text2)' }}>
                      {w.auto_sync_enabled ? 'Auto' : 'Manual'}
                    </span>
                  </button>
                </div>
              ))}

              {/* Exchanges */}
              {status?.exchanges.map(e => (
                <div key={`e-${e.id}`} className="flex items-center justify-between p-5 bg-black/5 rounded-3xl border border-white/5">
                  <div className="flex items-center gap-4">
                    <div className={`w-3 h-3 rounded-full ${e.sync_status === 'syncing' ? 'bg-emerald-400 animate-pulse' : e.sync_status === 'error' ? 'bg-red-400' : 'bg-white/20'}`} />
                    <div>
                      <p className="text-[14px] font-bold uppercase" style={{ color: 'var(--text)' }}>{e.exchange_name}</p>
                      <p className="text-[10px] opacity-60" style={{ color: 'var(--text3)' }}>
                        {e.sync_status === 'syncing' ? 'API Ingestion...' : `Next check: ${e.next_sync_at ? new Date(e.next_sync_at).toLocaleTimeString() : 'TBD'}`}
                      </p>
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => toggleAutoSync('exchange', e.id, e.auto_sync_enabled)}
                    disabled={!!actionLoading}
                    className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                  >
                    {e.auto_sync_enabled ? <ToggleRight className="text-emerald-500 w-6 h-6" /> : <ToggleLeft className="text-white/20 w-6 h-6" />}
                    <span className="text-[10px] uppercase font-black tracking-widest" style={{ color: 'var(--text2)' }}>
                      {e.auto_sync_enabled ? 'Auto' : 'Manual'}
                    </span>
                  </button>
                </div>
              ))}

              {(!status?.wallets.length && !status?.exchanges.length) && (
                <div className="py-12 text-center opacity-30 italic text-[13px]" style={{ color: 'var(--text)' }}>
                  No active data pipelines configured.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Global Scheduler Info */}
        <div className="space-y-6">
          <div className="border rounded-[2.5rem] p-8 shadow-sm" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
             <h2 className="text-sm font-bold uppercase tracking-widest mb-6 flex items-center gap-3" style={{ color: 'var(--text2)' }}>
              <Settings className="w-5 h-5 opacity-40" />
              Engine Health
            </h2>

            {status?.scheduler_running ? (
              <div className="p-5 bg-emerald-500/10 border border-emerald-500/20 rounded-3xl mb-6">
                <CheckCircle2 className="w-6 h-6 text-emerald-500 mb-2" />
                <p className="text-[13px] font-bold text-emerald-500">Worker Pool Healthy</p>
                <p className="text-[10px] opacity-70 mt-1" style={{ color: 'var(--text)' }}>High-performance background threads are processing tasks.</p>
              </div>
            ) : (
              <div className="p-5 bg-amber-500/10 border border-amber-500/20 rounded-3xl mb-6">
                <AlertCircle className="w-6 h-6 text-amber-500 mb-2" />
                <p className="text-[13px] font-bold text-amber-500">Engine Paused</p>
              </div>
            )}

            <div className="space-y-3">
              <p className="text-[10px] font-black uppercase opacity-40 tracking-widest ml-1" style={{ color: 'var(--text)' }}>Core Jobs</p>
              {status?.jobs.map(job => (
                <div key={job.id} className="p-4 border rounded-2xl bg-black/5" style={{ borderColor: 'var(--border)' }}>
                  <p className="text-[11px] font-bold" style={{ color: 'var(--text)' }}>{job.name}</p>
                  <p className="text-[9px] opacity-50" style={{ color: 'var(--text3)' }}>Loop frequency: 10m</p>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Manual Override */}
          <div className="border rounded-[2.5rem] p-8 shadow-sm" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
            <h2 className="text-sm font-bold uppercase tracking-widest mb-6" style={{ color: 'var(--text2)' }}>Manual Override</h2>
            <div className="space-y-2">
              {[
                { endpoint: '/br/sync/wallets', label: 'Flush Wallets' },
                { endpoint: '/br/sync/prices', label: 'Recalc Prices' },
                { endpoint: '/br/sync/exchanges', label: 'Flush APIs' },
              ].map(({ endpoint, label }) => (
                <button
                  key={endpoint}
                  onClick={() => handleManualSync(endpoint, label)}
                  disabled={manualSyncing}
                  className="w-full flex items-center justify-between px-6 py-4 rounded-2xl bg-white/5 border border-white/5 hover:border-emerald-500/30 transition-all text-[11px] font-black uppercase tracking-widest"
                  style={{ color: 'var(--text)' }}
                >
                  {label}
                  {manualSyncing ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3 opacity-40" />}
                </button>
              ))}
            </div>
            {message && <p className="mt-4 text-[10px] font-bold text-emerald-500 text-center">{message}</p>}
          </div>
        </div>
      </div>

      {/* Corporate Compliance / Tech Architecture */}
      <div className="border rounded-[2.5rem] p-10 grid grid-cols-1 md:grid-cols-4 gap-8" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
        {[
          { icon: Zap, title: 'Worker Pool', desc: 'Syncs are processed in parallel using 10 dedicated high-performance threads.' },
          { icon: Shield, title: 'Atomic Locking', desc: 'Database-level state locks prevent data corruption and sync overlaps.' },
          { icon: Database, title: 'Incremental Ingestion', desc: 'We only fetch data since your last block, reducing latency by 90%.' },
          { icon: Info, title: 'Audit Ready', desc: 'Every synchronization event is logged with transaction hash and block metadata.' },
        ].map((feat, i) => (
          <div key={i} className="space-y-3">
            <div className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center">
              <feat.icon className="w-5 h-5 opacity-50" style={{ color: 'var(--text)' }} />
            </div>
            <h3 className="text-[12px] font-black uppercase tracking-wider" style={{ color: 'var(--text)' }}>{feat.title}</h3>
            <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text3)' }}>{feat.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
