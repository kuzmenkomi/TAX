import { useState, useEffect } from 'react';
import { Puzzle, RefreshCw, AlertCircle, CheckCircle2, Server, Globe, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import apiV1 from '../api/v1';

interface Plugin {
  name: string;
  version: string;
  supported_chains: string[];
  supported_events: string[];
}

export function PluginManager() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloading, setReloading] = useState(false);

  const fetchPlugins = async () => {
    try {
      setLoading(true);
      const data = await apiV1.plugins.list();
      setPlugins(data.plugins || []);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPlugins(); }, []);

  const handleReload = async () => {
    try {
      setReloading(true);
      await apiV1.plugins.reload();
      await fetchPlugins();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setReloading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-syne font-bold tracking-tight flex items-center gap-3" style={{ color: 'var(--text)' }}>
            <Puzzle className="w-6 h-6 text-brand-green-500" />
            Integrations & Plugins
          </h1>
          <p className="text-[14px] mt-1" style={{ color: 'var(--text3)' }}>Expand platform capabilities with community DeFi integrations.</p>
        </div>
        <button onClick={handleReload} disabled={reloading || loading}
          className="flex items-center justify-center gap-2 px-5 py-2.5 bg-brand-green-500 text-brand-dark rounded-xl text-[12px] font-black shadow-lg shadow-brand-green-500/20 hover:bg-brand-green-400 transition-all disabled:opacity-50 active:scale-95">
          <RefreshCw className={`w-4 h-4 ${reloading ? 'animate-spin' : ''}`} />
          Force Reload
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="px-5 py-3 bg-danger/10 border border-danger/20 rounded-2xl flex items-center gap-3 animate-shake">
          <AlertCircle className="w-5 h-5 text-danger flex-shrink-0" />
          <p className="text-[13px] font-bold text-danger">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="relative">
            <Loader2 className="w-10 h-10 text-brand-green-500 animate-spin" />
            <Puzzle className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-brand-green-500/30" size={16} />
          </div>
          <p className="text-xs font-black uppercase tracking-widest opacity-40" style={{ color: 'var(--text)' }}>Scanning integration forest</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <AnimatePresence mode="popLayout">
            {plugins.map((plugin, idx) => (
              <motion.div 
                key={plugin.name} 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05, duration: 0.4 }}
                className="border rounded-[2rem] p-6 shadow-sm flex flex-col transition-all hover:scale-[1.01]" 
                style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                
                <div className="flex justify-between items-start mb-6">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-accent/10 rounded-2xl flex items-center justify-center text-accent">
                      <Puzzle size={24} />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold flex items-center gap-2" style={{ color: 'var(--text)' }}>
                        {plugin.name}
                        <CheckCircle2 className="w-4 h-4 text-brand-green-500" />
                      </h3>
                      <p className="text-[10px] font-black opacity-40 font-mono mt-0.5" style={{ color: 'var(--text)' }}>V{plugin.version}</p>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 bg-brand-green-500/10 text-brand-green-500 text-[9px] font-black uppercase tracking-widest rounded-lg border border-brand-green-500/20">
                    Active Module
                  </span>
                </div>

                <div className="space-y-6 flex-1">
                  <div>
                    <h4 className="text-[10px] font-black uppercase tracking-[2px] opacity-40 mb-3 ml-1 flex items-center gap-2" style={{ color: 'var(--text)' }}>
                      <Globe className="w-3.5 h-3.5" /> Discovery Chains
                    </h4>
                    <div className="flex gap-1.5 flex-wrap">
                      {plugin.supported_chains.map((chain) => (
                        <span key={chain} className="px-3 py-1 text-[10px] font-bold rounded-lg border uppercase tracking-wider" style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text2)' }}>
                          {chain}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-[10px] font-black uppercase tracking-[2px] opacity-40 mb-3 ml-1 flex items-center gap-2" style={{ color: 'var(--text)' }}>
                      <Server className="w-3.5 h-3.5" /> Event Signatures
                    </h4>
                    <div className="flex gap-1.5 flex-wrap">
                      {plugin.supported_events.map((event) => (
                        <span key={event} className="px-3 py-1 bg-accent/10 text-accent border border-accent/20 text-[10px] font-black rounded-lg uppercase tracking-widest">
                          {event}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {plugins.length === 0 && (
            <div className="col-span-full border rounded-[2.5rem] p-16 text-center shadow-inner" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <Puzzle className="w-12 h-12 mx-auto mb-4 opacity-10" style={{ color: 'var(--text)' }} />
              <p className="text-[14px] font-bold mb-2" style={{ color: 'var(--text)' }}>No active plugins detected.</p>
              <p className="text-[12px] opacity-60 max-w-sm mx-auto mb-6" style={{ color: 'var(--text)' }}>
                Install new modules in your backend directory to start tracking advanced DeFi protocols.
              </p>
              <code className="text-[11px] font-mono px-3 py-1.5 rounded-lg border" style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text3)' }}>
                backend/app/integrations/plugins
              </code>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
