import { Upload, BarChart3, Zap, ShieldCheck, Globe, Database } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';

export function FeaturesSection() {
  const { t } = useI18n();

  const features = [
    {
      icon: Upload,
      titleKey: 'landing.hero.import',
      descKey: 'landing.hero.importDesc',
      accent: 'var(--accent)'
    },
    {
      icon: Zap,
      titleKey: 'landing.hero.sync',
      descKey: 'landing.hero.syncDesc',
      accent: '#4d7aff'
    },
    {
      icon: BarChart3,
      titleKey: 'landing.hero.dashboard',
      descKey: 'landing.hero.dashboardDesc',
      accent: '#f0a86a'
    },
    {
      icon: ShieldCheck,
      title: 'Institutional Grade',
      desc: 'SOC2 Type II compliant encryption ensures your financial integrity is never compromised.',
      accent: 'var(--accent)'
    },
    {
      icon: Globe,
      title: 'Multi-Jurisdiction',
      desc: 'Native support for taxation rules in Brazil, Mexico, Argentina, and 40+ other regions.',
      accent: '#4d7aff'
    },
    {
      icon: Database,
      title: 'Audit-Trail Logging',
      desc: 'Every calculation is backed by a cryptographically verifiable trail for maximum compliance.',
      accent: '#f0a86a'
    }
  ];

  return (
    <div id="features" className="py-24 px-6 relative overflow-hidden transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      {/* Visual background accents */}
      <div className="absolute top-[20%] right-[-10%] w-[500px] h-[500px] rounded-full bg-brand-green-500/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-brand-blue-500/5 blur-[120px] pointer-events-none" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Section Title */}
        <div className="text-center mb-24">
          <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-black uppercase tracking-widest mb-6">
             Capabilities Matrix
          </div>
          <h2 className="text-4xl md:text-6xl font-syne font-black mb-8 tracking-tight leading-none" style={{ color: 'var(--text)' }}>
            Institutional Suite
          </h2>
          <p className="text-xl font-medium opacity-60 max-w-2xl mx-auto italic leading-relaxed" style={{ color: 'var(--text)' }}>
            From bulk imports to complex DeFi audit logs, we provide the infrastructure needed for precise fiscal settlement.
          </p>
        </div>

        {/* Features Grayscale/Color Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <div
                key={i}
                className="group relative rounded-[2.5rem] p-10 border transition-all duration-500 overflow-hidden shadow-sm hover:shadow-2xl hover:-translate-y-2"
                style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
              >
                {/* Hover Glow Effect */}
                <div 
                  className="absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-0 group-hover:opacity-10 transition-opacity duration-700"
                  style={{ background: feature.accent }}
                />
                
                <div 
                  className="w-16 h-16 rounded-2xl flex items-center justify-center mb-8 transition-all duration-500 group-hover:scale-110 shadow-lg"
                  style={{ background: 'var(--bg2)', border: '1px solid var(--border)' }}
                >
                  <Icon size={30} style={{ color: feature.accent }} className="transition-transform group-hover:rotate-12" />
                </div>

                <h3 className="text-2xl font-black mb-4 tracking-tight" style={{ color: 'var(--text)' }}>
                  {feature.titleKey ? t(feature.titleKey) : feature.title}
                </h3>
                
                <p className="text-[15px] font-medium opacity-70 leading-relaxed" style={{ color: 'var(--text)' }}>
                  {feature.descKey ? t(feature.descKey) : feature.desc}
                </p>

                <div className="mt-8 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                   <div className="w-1.5 h-1.5 rounded-full" style={{ background: feature.accent }} />
                   <span className="text-[10px] font-black uppercase tracking-widest" style={{ color: 'var(--text)' }}>Verified Protocol</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
