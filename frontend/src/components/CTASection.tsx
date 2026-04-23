import { CheckCircle, ArrowRight } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';
import { Link } from 'react-router-dom';

export function CTASection() {
  const { t } = useI18n();

  return (
    <div className="py-24 px-6 relative overflow-hidden" style={{ background: 'var(--bg2)', borderTop: '1px solid var(--border)' }}>
      {/* Background Decor */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-brand-green-500 opacity-5 rounded-full -translate-y-1/2 translate-x-1/2 blur-[120px]" />
      <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-brand-blue-500 opacity-5 rounded-full translate-y-1/2 -translate-x-1/2 blur-[80px]" />
      
      <div className="max-w-5xl mx-auto text-center relative z-10">
        <h2 className="text-4xl md:text-6xl font-syne font-black mb-8 tracking-tight leading-[1.1]" style={{ color: 'var(--text)' }}>
          {t('landing.calculate')}
        </h2>
        <p className="text-xl md:text-2xl mb-12 max-w-2xl mx-auto font-medium leading-relaxed opacity-70" style={{ color: 'var(--text)' }}>
          Join 700,000+ crypto investors who trust us with their taxes. Institutional precision, consumer simplicity.
        </p>

        {/* Features list */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16 max-w-3xl mx-auto">
          {[
            'No credit card required',
            'Instant tax forms',
            'No obligations'
          ].map((feature, i) => (
            <div key={i} className="flex items-center gap-4 justify-center group">
              <div className="w-10 h-10 rounded-2xl flex items-center justify-center transition-all bg-brand-green-500/10 border border-brand-green-500/20 group-hover:scale-110">
                <CheckCircle size={18} className="text-brand-green-500" />
              </div>
              <span className="font-bold text-sm tracking-tight opacity-80" style={{ color: 'var(--text)' }}>{feature}</span>
            </div>
          ))}
        </div>

        {/* Primary CTA Group */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
          <Link 
            to="/register"
            className="w-full sm:w-auto bg-brand-green-500 text-brand-dark px-12 py-5 rounded-[2.5rem] font-black text-xl hover:bg-brand-green-400 transition-all shadow-2xl shadow-brand-green-500/30 active:scale-95 flex items-center justify-center gap-3"
          >
            {t('landing.getStarted')}
            <ArrowRight size={20} />
          </Link>
          
          <Link 
            to="/login"
            className="w-full sm:w-auto px-10 py-5 rounded-[2.5rem] font-black text-xl border transition-all hover:bg-brand-green-500/5 active:scale-95"
            style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
          >
            Login
          </Link>
        </div>

        <p className="text-xs font-black uppercase tracking-[0.3em] mt-12 opacity-30" style={{ color: 'var(--text)' }}>
          Professional Node Infrastructure · Instant Settlement
        </p>
      </div>
    </div>
  );
}
