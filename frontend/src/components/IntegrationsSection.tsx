import { ArrowRight, Globe, Layers, Zap } from 'lucide-react';

const integrations = [
  'Binance', 'Coinbase', 'Kraken', 'OKX', 'Bybit', 'Kucoin',
  'Uniswap', 'OpenSea', 'Lido', 'Compound', 'Aave', 'MetaMask',
  'Ethereum', 'Polygon', 'Solana', 'Bitcoin', 'Arbitrum', 'Optimism',
  'Base', 'Avalanche', 'BNB Chain', 'Fantom', 'Harmony', 'Celo',
];

export function IntegrationsSection() {
  return (
    <div id="integrations" className="py-24 px-6 relative overflow-hidden transition-colors duration-300" style={{ background: 'var(--bg2)' }}>
      {/* Background patterns */}
      <div className="absolute top-0 left-0 w-full h-full opacity-[0.03] pointer-events-none select-none overflow-hidden font-syne font-black text-[120px] leading-none text-brand-green-500 whitespace-nowrap">
        DATA FLOW DATA FLOW DATA FLOW DATA FLOW DATA FLOW DATA FLOW DATA FLOW DATA FLOW
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-black uppercase tracking-widest mb-4">
             Network Connectivity
          </div>
          <h2 className="text-4xl md:text-5xl font-syne font-black mb-6 tracking-tight leading-none" style={{ color: 'var(--text)' }}>
            Institutional Liquidity Map
          </h2>
          <p className="text-xl font-medium opacity-60 max-w-2xl mx-auto italic leading-relaxed" style={{ color: 'var(--text)' }}>
            Native indexing of 500+ centralized exchanges, hardware wallets, and decentralized protocols.
          </p>
        </div>

        {/* Integration Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-16">
          {integrations.map((name, i) => (
            <div
              key={i}
              className="group relative rounded-2xl p-5 text-center font-bold transition-all duration-300 border hover:-translate-y-1 hover:shadow-xl shadow-sm overflow-hidden"
              style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
            >
               {/* Hover Accent */}
               <div className="absolute inset-0 bg-brand-green-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
               
               <span className="relative z-10 text-sm tracking-tight opacity-60 group-hover:opacity-100 group-hover:text-brand-green-500 transition-all font-syne" style={{ color: 'var(--text)' }}>
                 {name}
               </span>
            </div>
          ))}
        </div>

        {/* Action Interface */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-12 border-t" style={{ borderColor: 'var(--border)' }}>
          {[
            { icon: Globe, title: 'CEX Connectivity', desc: 'Secure OAuth and API read-only tunnels for all major exchanges.' },
            { icon: Layers, title: 'Multi-Chain Indexing', desc: 'Full archival node support for Ethereum, Solana, and 50+ L1/L2s.' },
            { icon: Zap, title: 'Real-time Sync', desc: 'Latency-optimized data streams for sub-second transaction tracking.' },
          ].map((item, i) => (
            <div key={i} className="flex gap-5">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 shadow-lg" style={{ background: 'var(--bg)', border: '1px solid var(--border)' }}>
                 <item.icon size={22} className="text-brand-green-500" />
              </div>
              <div>
                <h4 className="font-bold text-sm tracking-tight mb-1" style={{ color: 'var(--text)' }}>{item.title}</h4>
                <p className="text-xs font-medium opacity-40 leading-relaxed" style={{ color: 'var(--text)' }}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* View All Callout */}
        <div className="mt-16 text-center">
          <button
            className="group px-8 py-4 rounded-xl border font-black text-[12px] uppercase tracking-widest transition-all hover:bg-brand-green-500 hover:text-brand-dark hover:border-brand-green-500 hover:shadow-xl hover:shadow-brand-green-500/20 active:scale-95 flex items-center justify-center gap-3 mx-auto"
            style={{ color: 'var(--text)', borderColor: 'var(--border)' }}
          >
            Explore 500+ Integrations
            <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
}
