import React from 'react';
import { CheckCircle, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useI18n } from '../i18n/I18nContext';

export function HeroSection() {
  const { t } = useI18n();

  return (
    <div className="relative overflow-hidden">
      {/* Top Dark Section */}
      <div className="bg-brand-dark pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto flex flex-col items-center text-center">
          <div className="bg-brand-green-600/20 text-brand-green-500 px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-[0.2em] mb-8 border border-brand-green-500/30">
            {t('landing.badge')}
          </div>
          <Link to="/" className="mb-12 transform hover:scale-105 transition-transform duration-500">
            <span className="text-5xl md:text-7xl font-black text-white tracking-tighter">Latam<span className="text-brand-green-500">Tax</span></span>
          </Link>
        </div>
      </div>

      {/* Split Transition / Content Section */}
      <div className="bg-background pt-16 pb-24 px-6 relative">
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h1 className="text-5xl md:text-7xl font-black text-brand-dark mb-8 leading-[1.1] tracking-tight">
            Crypto Taxes Made <span className="inline-block relative">
              <span className="relative z-10 text-brand-green-700 px-3 md:px-5">Simple</span>
              <span className="absolute inset-0 bg-brand-green-500/20 rounded-2xl -rotate-1 scale-110"></span>
            </span> for Brazil
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-500 mb-12 max-w-2xl mx-auto leading-relaxed font-medium">
            {t('landing.subtitle')}
          </p>

          <div className="flex flex-col sm:flex-row gap-5 justify-center items-center mb-16">
            <Link to="/register" className="bg-brand-green-600 text-white px-10 py-5 rounded-2xl font-black text-xl hover:bg-brand-green-700 transition-all shadow-2xl shadow-brand-green-600/30 active:scale-95 text-center">
              {t('landing.getStarted')}
            </Link>
            <a href="#features" className="flex items-center gap-3 px-10 py-5 text-brand-dark font-black hover:bg-muted-100 rounded-2xl transition-all border-2 border-muted-200">
              {t('landing.seeReport')}
              <ArrowRight size={20} className="text-brand-green-600" />
            </a>
          </div>

          <div className="flex flex-wrap justify-center gap-10 items-center opacity-40 grayscale group-hover:grayscale-0 transition-all duration-700">
            {['The New York Times', 'Forbes', 'Bloomberg', 'CoinDesk'].map((logo, i) => (
              <span key={i} className="text-brand-dark font-black text-sm tracking-widest">{logo}</span>
            ))}
          </div>
        </div>
        
        {/* Background Decor */}
        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-brand-dark to-transparent opacity-10"></div>
      </div>
    </div>
  );
}
