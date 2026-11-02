import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Building2, MapPin, FileText, CheckCircle, ArrowRight, AlertCircle, Mail, Globe, Sparkles, User } from 'lucide-react';
import { useI18n } from '../i18n/I18nContext';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { useAuth } from '../auth/AuthContext';
import { useToast } from '../context/ToastContext';
import apiV1 from '../api/v1';
import { ThemeToggle } from '../components/ThemeToggle';

type OnboardingStep = 'country' | 'structure' | 'portfolio' | 'complete';

export function OnboardingPage() {
  const navigate = useNavigate();
  const { t } = useI18n();
  useAuth();
  const { addToast } = useToast();
  const [step, setStep] = useState<OnboardingStep>('country');
  const [country, setCountry] = useState('BR');
  const [taxStructure, setTaxStructure] = useState('individual');
  const [portfolioSize, setPortfolioSize] = useState('small');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEmailNotVerified, setIsEmailNotVerified] = useState(false);

  const handleNext = async () => {
    if (step === 'country') {
      setStep('structure');
    } else if (step === 'structure') {
      setStep('portfolio');
    } else if (step === 'portfolio') {
      setLoading(true);
      setError(null);
      setIsEmailNotVerified(false);
      try {
        await apiV1.auth.completeOnboarding(country, taxStructure, portfolioSize);
        addToast('Onboarding completed! 🎉', 'success', 3000);
        setStep('complete');
        localStorage.setItem('activeTab', 'dashboard');
        setTimeout(() => {
          navigate('/dashboard', { replace: true });
        }, 2000);
      } catch (err) {
        const isEmailVerificationError = (err as any)?.isEmailNotVerified === true || 
                                         (err instanceof Error && err.message.includes('verify your email'));
        
        if (isEmailVerificationError) {
          setIsEmailNotVerified(true);
          setError('📧 Please verify your email address first');
          addToast('Check your email for verification link', 'warning', 6000);
          setTimeout(() => {
            navigate('/verify-email-resend', { replace: true });
          }, 2000);
        } else {
          const message = err instanceof Error ? err.message : 'Failed to save onboarding';
          setError(message);
          addToast(message, 'error', 5000);
        }
        setLoading(false);
      }
    }
  };

  const progress = {
    country: 25,
    structure: 50,
    portfolio: 75,
    complete: 100,
  };

  return (
    <div className="min-h-screen relative overflow-hidden flex flex-col transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      {/* Header */}
      <header 
        className="relative z-50 flex items-center justify-between px-6 md:px-12 py-6 border-b backdrop-blur-md"
        style={{ borderColor: 'var(--border)', background: 'var(--nav-bg)' }}
      >
        <Link to="/" className="flex items-center gap-2 no-underline font-syne font-extrabold text-xl tracking-tight hover:opacity-80 transition-opacity" style={{ color: 'var(--text)' }}>
          <div className="w-1.5 h-1.5 rounded-full bg-brand-green-500 shadow-[0_0_10px_var(--accent)]" />
          Declairo
        </Link>
        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
      </header>
 
      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 py-12 relative z-10">
        <div className="w-full max-w-2xl animate-fade-in">
          
          {/* Progress Section */}
          <div className="mb-12">
            <div className="flex items-center justify-between mb-3 px-1">
              <span className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: 'var(--text3)' }}>
                Step {step === 'country' ? 1 : step === 'structure' ? 2 : step === 'portfolio' ? 3 : 4} of 3
              </span>
              <span className="text-[10px] font-bold text-brand-green-500 uppercase tracking-[0.1em]">{progress[step]}% {t('common.complete')}</span>
            </div>
            <div className="h-1 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
              <div
                className="h-full bg-brand-green-500 transition-all duration-700 ease-out shadow-[0_0_15px_var(--accent)]"
                style={{ width: `${progress[step]}%` }}
              />
            </div>
          </div>
   
          {/* Main Card */}
          <div 
            className="border rounded-[2.5rem] shadow-2xl overflow-hidden relative"
            style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-brand-green-500/5 rounded-full blur-3xl" />
            
            <div className="p-10 md:p-14">
              {error && (
                <div className={`mb-8 p-5 rounded-2xl flex items-start gap-4 border ${isEmailNotVerified ? 'bg-orange-500/10 border-orange-500/20' : 'bg-danger/10 border-danger/20'} animate-shake`}>
                  {isEmailNotVerified ? <Mail className="w-5 h-5 text-orange-500" /> : <AlertCircle className="w-5 h-5 text-danger" />}
                  <div className="flex-1">
                    <p className={`text-sm font-bold tracking-tight ${isEmailNotVerified ? 'text-orange-500' : 'text-danger'}`}>{error}</p>
                    {isEmailNotVerified && <p className="text-xs text-orange-500/70 mt-1 font-medium italic">Check your inbox or spam folder.</p>}
                  </div>
                </div>
              )}
              
              {/* Step Content */}
              <div className="min-h-[300px]">
                {step === 'country' && (
                  <div className="space-y-8 animate-fade-in">
                    <div>
                      <h1 className="text-3xl md:text-4xl font-syne font-bold mb-3 tracking-tight" style={{ color: 'var(--text)' }}>
                        {t('onboarding.countryTitle')}
                      </h1>
                      <p className="text-sm leading-relaxed max-w-md" style={{ color: 'var(--text2)' }}>
                        {t('onboarding.countrySubtitle')}
                      </p>
                    </div>
    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {[
                        { code: 'BR', name: 'Brasil', flag: '🇧🇷' },
                        { code: 'MX', name: 'México', flag: '🇲🇽' },
                        { code: 'AR', name: 'Argentina', flag: '🇦🇷' },
                        { code: 'CL', name: 'Chile', flag: '🇨🇱' },
                        { code: 'CO', name: 'Colombia', flag: '🇨🇴' },
                      ].map(c => (
                        <button
                          key={c.code}
                          onClick={() => setCountry(c.code)}
                          className={`group relative p-4 rounded-xl border transition-all duration-300 flex items-center gap-4 ${
                            country === c.code
                              ? 'border-brand-green-500/50 bg-brand-green-500/10 shadow-[0_0_20px_rgba(106,240,200,0.1)]'
                              : 'hover:border-brand-green-500/20'
                          }`}
                          style={{
                            background: country === c.code ? undefined : 'var(--bg2)',
                            borderColor: country === c.code ? undefined : 'var(--border)',
                          }}
                        >
                          <span className="text-2xl grayscale-[0.2] transition-transform group-hover:scale-110">{c.flag}</span>
                          <span className="text-sm font-bold uppercase tracking-wider" style={{ color: country === c.code ? 'var(--text)' : 'var(--text2)' }}>{c.name}</span>
                          {country === c.code && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-green-500 shadow-[0_0_8px_var(--accent)]" />}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
    
                {step === 'structure' && (
                  <div className="space-y-8 animate-fade-in">
                    <div>
                      <h1 className="text-3xl md:text-4xl font-syne font-bold mb-3 tracking-tight" style={{ color: 'var(--text)' }}>
                        {t('onboarding.structureTitle')}
                      </h1>
                      <p className="text-sm leading-relaxed max-w-md" style={{ color: 'var(--text2)' }}>
                        {t('onboarding.structureSubtitle')}
                      </p>
                    </div>
    
                    <div className="space-y-3">
                      {[
                        { id: 'individual', name: 'Persona física', desc: 'Inversionista individual', icon: <User className="w-5 h-5"/> },
                        { id: 'business', name: 'Empresa / SME', desc: 'Compañía o negocio corporativo', icon: <Building2 className="w-5 h-5"/> },
                        { id: 'fund', name: 'Institutional', desc: 'Fondo o vehículo de inversión', icon: <Sparkles className="w-5 h-5"/> },
                      ].map(item => (
                        <button
                          key={item.id}
                          onClick={() => setTaxStructure(item.id)}
                          className={`w-full p-5 rounded-2xl border transition-all duration-300 flex items-center justify-between ${
                            taxStructure === item.id
                              ? 'border-brand-green-500/50 bg-brand-green-500/10 shadow-[0_0_20px_rgba(106,240,200,0.1)]'
                              : 'hover:border-brand-green-500/20'
                          }`}
                          style={{
                            background: taxStructure === item.id ? undefined : 'var(--bg2)',
                            borderColor: taxStructure === item.id ? undefined : 'var(--border)',
                          }}
                        >
                          <div className="flex items-center gap-5">
                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl transition-colors ${taxStructure === item.id ? 'bg-brand-green-500 text-brand-dark' : ''}`} style={taxStructure !== item.id ? { background: 'var(--surface2)', color: 'var(--text3)' } : undefined}>
                              {item.icon}
                            </div>
                            <div className="text-left">
                              <div className="text-sm font-bold uppercase tracking-wider" style={{ color: taxStructure === item.id ? 'var(--text)' : 'var(--text2)' }}>{item.name}</div>
                              <div className="text-xs font-medium opacity-40" style={{ color: 'var(--text3)' }}>{item.desc}</div>
                            </div>
                          </div>
                          {taxStructure === item.id && <div className="w-2 h-2 rounded-full bg-brand-green-500 shadow-[0_0_10px_var(--accent)]" />}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
    
                {step === 'portfolio' && (
                  <div className="space-y-8 animate-fade-in">
                    <div>
                      <h1 className="text-3xl md:text-4xl font-syne font-bold mb-3 tracking-tight" style={{ color: 'var(--text)' }}>
                        {t('onboarding.portfolioTitle')}
                      </h1>
                      <p className="text-sm leading-relaxed max-w-md" style={{ color: 'var(--text2)' }}>
                        {t('onboarding.portfolioSubtitle')}
                      </p>
                    </div>
    
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {[
                        { id: 'small', label: 'Under $10K', value: 'small' },
                        { id: 'medium', label: '$10K - $100K', value: 'medium' },
                        { id: 'large', label: '$100K - $1M', value: 'large' },
                        { id: 'xlarge', label: 'Over $1M', value: 'xlarge' },
                      ].map(item => (
                        <button
                          key={item.id}
                          onClick={() => setPortfolioSize(item.value)}
                          className={`p-5 rounded-xl border text-center transition-all duration-300 ${
                            portfolioSize === item.value
                              ? 'border-brand-green-500/50 bg-brand-green-500/10 font-bold'
                              : 'hover:border-brand-green-500/20'
                          }`}
                          style={{
                            background: portfolioSize === item.value ? undefined : 'var(--bg2)',
                            borderColor: portfolioSize === item.value ? undefined : 'var(--border)',
                            color: portfolioSize === item.value ? 'var(--text)' : 'var(--text2)',
                          }}
                        >
                          <span className="text-[13px] tracking-tight">{item.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
    
                {step === 'complete' && (
                  <div className="text-center py-10 space-y-8 animate-fade-in">
                    <div className="flex justify-center">
                      <div className="w-20 h-20 bg-brand-green-500/10 rounded-full flex items-center justify-center animate-bounce">
                        <CheckCircle className="w-10 h-10 text-brand-green-500 shadow-[0_0_20px_var(--accent)]" />
                      </div>
                    </div>
                    <div>
                      <h1 className="text-3xl md:text-4xl font-syne font-bold mb-3 tracking-tight" style={{ color: 'var(--text)' }}>
                        {t('onboarding.completeTitle')}
                      </h1>
                      <p className="text-lg" style={{ color: 'var(--text2)' }}>
                        {t('onboarding.completeSubtitle')}
                      </p>
                    </div>
                    <div className="flex items-center justify-center gap-3 text-brand-green-500 font-bold text-xs uppercase tracking-widest">
                      <div className="w-1.5 h-1.5 rounded-full bg-brand-green-500 animate-ping"></div>
                      {t('onboarding.redirecting')}
                    </div>
                  </div>
                )}
              </div>
   
              {/* Action Buttons */}
              {step !== 'complete' && (
                <div className="mt-12 pt-8 border-t flex gap-4 justify-between items-center" style={{ borderColor: 'var(--border)' }}>
                  <div>
                    {step !== 'country' && (
                      <button
                        onClick={() => {
                          if (step === 'structure') setStep('country');
                          else if (step === 'portfolio') setStep('structure');
                        }}
                        className="px-6 py-3 font-bold text-xs uppercase tracking-widest transition-colors hover:opacity-80"
                        style={{ color: 'var(--text2)' }}
                      >
                        Atrás
                      </button>
                    )}
                  </div>
                  <button
                    onClick={handleNext}
                    disabled={loading}
                    className="px-8 py-3.5 bg-brand-green-500 hover:bg-brand-green-400 text-brand-dark font-bold rounded-xl flex items-center gap-2.5 transition-all shadow-xl shadow-brand-green-500/10 active:scale-95 disabled:opacity-50"
                  >
                    {loading ? (
                       <div className="w-4 h-4 border-2 border-brand-dark/20 border-t-brand-dark rounded-full animate-spin" />
                    ) : (
                      <>
                        Continuar
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
