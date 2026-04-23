import { Star, Quote } from 'lucide-react';

const testimonials = [
  {
    name: 'Alex Chen',
    role: 'Quantitative Trader',
    avatar: 'AC',
    stars: 5,
    text: 'This platform saved me weeks of manual reconciliation. Tracking 5,000+ DeFi swaps used to be a nightmare, now it is automated. Best decision ever.'
  },
  {
    name: 'Sarah Miller',
    role: 'Liquidity Provider',
    avatar: 'SM',
    stars: 5,
    text: 'Software that actually understands AMMs and yield farming. The reconciliation accuracy is unmatched. Customer support is incredible too.'
  },
  {
    name: 'John Rodriguez',
    role: 'Whale Collector',
    avatar: 'JR',
    stars: 5,
    text: 'The NFT basis-cost calculations are game-changing. My tax advisor was genuinely impressed with the level of detail in the audit trail.'
  },
  {
    name: 'Emma Wilson',
    role: 'HODL Portfolio Mgr',
    avatar: 'EW',
    stars: 5,
    text: 'The LIFO/FIFO matching algorithm is insanely accurate. I audited it manually for a month and it got every single event perfect.'
  },
];

export function TestimonialsSection() {
  return (
    <div className="py-24 px-6 relative overflow-hidden transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      {/* Visual background decor */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-brand-green-500/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-brand-blue-500/10 rounded-full blur-[80px] pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-black uppercase tracking-widest mb-4">
             Network Trust
          </div>
          <h2 className="text-4xl md:text-5xl font-syne font-black mb-6 tracking-tight leading-none" style={{ color: 'var(--text)' }}>
            Verified User Sentiment
          </h2>
          <p className="text-xl font-medium opacity-60 max-w-2xl mx-auto italic" style={{ color: 'var(--text)' }}>
            Trusted by the world's most sophisticated on-chain investors.
          </p>
        </div>

        {/* Grid Array */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {testimonials.map((t, i) => (
            <div
              key={i}
              className="group relative rounded-[2rem] p-8 border transition-all duration-500 hover:shadow-2xl hover:-translate-y-2 flex flex-col h-full overflow-hidden"
              style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
            >
              <div className="absolute top-6 right-8 opacity-[0.03] group-hover:opacity-10 transition-opacity">
                <Quote size={64} style={{ color: 'var(--text)' }} />
              </div>

              {/* Stars Scale */}
              <div className="flex gap-1.5 mb-6">
                {Array(t.stars)
                  .fill(0)
                  .map((_, j) => (
                    <Star
                      key={j}
                      size={14}
                      className="fill-brand-green-500 text-brand-green-500 drop-shadow-[0_0_8px_var(--accent)]"
                    />
                  ))}
              </div>

              {/* Main Insight */}
              <p className="font-medium text-[15px] leading-relaxed mb-8 flex-1 italic" style={{ color: 'var(--text)' }}>
                "{t.text}"
              </p>

              {/* Profile Context */}
              <div className="flex items-center gap-4 pt-6 border-t" style={{ borderColor: 'var(--border)' }}>
                <div 
                  className="w-12 h-12 rounded-xl flex items-center justify-center font-syne font-black text-xs shadow-inner"
                  style={{ background: 'var(--bg2)', color: 'var(--accent)' }}
                >
                  {t.avatar}
                </div>
                <div>
                  <p className="font-bold text-[14px] leading-none mb-1" style={{ color: 'var(--text)' }}>
                    {t.name}
                  </p>
                  <p className="text-[10px] font-black uppercase tracking-widest opacity-40 leading-none" style={{ color: 'var(--text)' }}>
                    {t.role}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
