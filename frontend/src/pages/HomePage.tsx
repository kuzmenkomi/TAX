import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, CheckCircle, ArrowRight, Sun, Moon, BarChart3, ShieldCheck, Zap, Globe, Star, Quote, HelpCircle, Wallet, LayoutGrid, ChevronDown } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { LandingCard3D } from '../components/LandingCard3D';
import { ExchangeLogo } from '../components/ExchangeLogo';
import { useScrollReveal } from '../hooks/useScrollReveal';
import { useI18n } from '../i18n/I18nContext';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { ThemeToggle } from '../components/ThemeToggle';

const integrations = [
    { name: 'Binance', domain: 'binance.com', icon: 'B', color: 'bg-[#f0b90b] text-black' },
    { name: 'Coinbase', domain: 'coinbase.com', icon: 'C', color: 'bg-[#0052ff] text-white' },
    { name: 'MetaMask', domain: 'metamask.io', icon: 'M', color: 'bg-[#e2761b]/10' },
    { name: 'Bitso', domain: 'bitso.com', icon: 'B', color: 'bg-[var(--accent)] text-black' },
    { name: 'Lemon', domain: 'lemon.me', icon: 'L', color: 'bg-[#ccff00] text-black' },
    { name: 'Belo', domain: 'belo.app', icon: 'B', color: 'bg-[#6d28d9] text-white' },
    { name: 'Buenbit', domain: 'buenbit.com', icon: 'B', color: 'bg-[#00d1ff] text-black' },
    { name: 'Orionx', domain: 'orionx.com', icon: 'O', color: 'bg-[#1a1c20] text-white' },
    { name: 'Phantom', domain: 'phantom.app', icon: 'P', color: 'bg-[#9945ff]/10' },
    { name: 'Ledger', domain: 'ledger.com', icon: 'L', color: 'bg-[#142533] text-white' }
];

const howItWorksSteps = [
    { title: 'Connect wallets', desc: 'Securely link your exchanges, wallets, and protocols. We do the rest.', icon: <Zap /> },
    { title: 'Review transactions', desc: 'Our algorithm auto-categorizes every trade and transfer for maximum accuracy.', icon: <BarChart3 /> },
    { title: 'Download reports', desc: 'Get IRS and global-compliant tax forms in seconds.', icon: <CheckCircle /> }
];

const testimonials = [
    { name: 'Rafael M.', location: 'Sao Paulo, Brazil', role: 'DeFi trader', text: 'Declairo pulled together activity from six exchanges and made filing fast.', stars: 5 },
    { name: 'Mariana L.', location: 'CDMX, Mexico', role: 'HODLer', text: 'Finally a tool that understands local tax rules and makes reports simple.', stars: 5 },
    { name: 'Javier O.', location: 'Bogota, Colombia', role: 'Active trader', text: 'The LATAM support and cost-basis options saved me a lot of manual work.', stars: 4 },
    { name: 'Ana C.', location: 'Buenos Aires, Argentina', role: 'NFT collector', text: 'Tax-loss insights helped me catch savings I would have completely missed.', stars: 5 },
    { name: 'Pedro F.', location: 'Rio de Janeiro', role: 'Certified Accountant', text: 'Bulk exports and clear reports save hours for every client I manage.', stars: 5 },
    { name: 'Lucas G.', location: 'Santiago, Chile', role: 'Casual investor', text: 'Fast, clean, and much easier to trust than spreadsheet-based workflows.', stars: 5 },
    { name: 'Valentina R.', location: 'Lima, Peru', role: 'Algo trader', text: 'Wallet syncing handled staking and DeFi activity without extra cleanup.', stars: 5 }
];

const pricingPlans = [
    { name: 'Free', price: '0', description: 'For Beginners', features: ['25 transactions', 'Up to 5 wallets', 'Tax Report Preview', 'Portfolio tracking'], disabled: true },
    { name: 'Starter', price: '19.99', description: 'Most Popular', features: ['150 transactions', 'Up to 15 wallets', 'PDF Tax Report', 'Email Support'], popular: true },
    { name: 'Trader', price: '49.99', description: 'For Active Users', features: ['1000 transactions', 'Unlimited wallets', 'Basic DeFi & NFT', 'Priority Support'] },
    { name: 'Expert', price: '99.99', description: 'For Pros', features: ['3000 transactions', 'Unlimited wallets', 'High-Volume CSV Support', 'Loss Harvesting'] }
];

export function HomePage() {
    const { t } = useI18n();
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const testimonialScrollerRef = useRef<HTMLDivElement | null>(null);
    const pricingScrollerRef = useRef<HTMLDivElement | null>(null);
    const [activeTestimonialIndex, setActiveTestimonialIndex] = useState(0);
    const [activePricingIndex, setActivePricingIndex] = useState(0);
    const [showStickyMobileCta, setShowStickyMobileCta] = useState(false);
    useScrollReveal();

    useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard', { replace: true });
        }
    }, [isAuthenticated, navigate]);

    useEffect(() => {
        const updateStickyCta = () => {
            if (typeof window === 'undefined') return;
            const isMobile = window.innerWidth < 768;
            setShowStickyMobileCta(isMobile && window.scrollY > window.innerHeight * 0.8);
        };

        updateStickyCta();
        window.addEventListener('scroll', updateStickyCta, { passive: true });
        window.addEventListener('resize', updateStickyCta);
        return () => {
            window.removeEventListener('scroll', updateStickyCta);
            window.removeEventListener('resize', updateStickyCta);
        };
    }, []);

    const scrollToTestimonial = (index: number) => {
        const container = testimonialScrollerRef.current;
        if (!container) return;
        container.scrollTo({ left: container.clientWidth * index, behavior: 'smooth' });
        setActiveTestimonialIndex(index);
    };

    const scrollToPricing = (index: number) => {
        const container = pricingScrollerRef.current;
        if (!container) return;
        container.scrollTo({ left: container.clientWidth * index, behavior: 'smooth' });
        setActivePricingIndex(index);
    };

    return (
        <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] transition-colors duration-300 landing-grid pb-24 md:pb-0" style={{ overflowX: 'hidden' }}>

            {/* Header / Nav */}
            <nav className="fixed top-0 left-0 right-0 z-[100] flex items-center justify-between gap-3 px-4 sm:px-6 md:px-12 py-3 md:py-4 bg-[var(--nav-bg)] backdrop-blur-xl border-b border-[var(--border)]">
                <Link to="/" className="logo flex min-w-0 items-center gap-2 text-[var(--text)] no-underline font-syne font-extrabold text-lg sm:text-xl tracking-tight">
                    <img src="/logo.webp" alt="Declairo Logo" className="w-[24px] h-[24px] object-contain" />
                    <span className="truncate">Declairo</span>
                </Link>

                <div className="hidden md:flex items-center gap-8">
                    <a href="#how" className="text-sm font-semibold text-[var(--text2)] hover:text-[var(--text)] transition-colors no-underline">How it works</a>
                    <a href="#features" className="text-sm font-semibold text-[var(--text2)] hover:text-[var(--text)] transition-colors no-underline">Features</a>
                    <a href="#pricing" className="text-sm font-semibold text-[var(--text2)] hover:text-[var(--text)] transition-colors no-underline">Pricing</a>
                    <Link to="/blog" className="text-sm font-semibold text-[var(--text2)] hover:text-[var(--text)] transition-colors no-underline">Blog</Link>
                </div>

                <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                    <LanguageSwitcher />
                    <ThemeToggle />
                    <Link to="/login" className="text-sm font-bold px-4 py-2 rounded-lg transition-all hidden md:block" style={{ color: 'var(--text)' }}>Login</Link>
                    <Link to="/register" className="bg-brand-green-500 hover:bg-brand-green-600 text-brand-dark text-xs sm:text-sm font-bold px-3 sm:px-5 py-2 sm:py-2.5 rounded-xl shadow-lg shadow-brand-green-600/20 transition-all hover:scale-[1.02] whitespace-nowrap">
                        <span className="sm:hidden">Start free</span>
                        <span className="hidden sm:inline">Get started free</span>
                    </Link>
                </div>
            </nav>

            {/* Hero Section */}
            <header className="relative pt-28 sm:pt-32 pb-14 sm:pb-20 px-4 sm:px-6 md:px-12 min-h-[auto] md:min-h-[85vh] flex flex-col md:flex-row items-center gap-10 md:gap-12 max-w-7xl mx-auto overflow-visible">
                <div className="flex-1 max-w-[660px] text-center md:text-left">
                    <div className="badge inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-bold uppercase tracking-widest mb-6">
                        <span className="w-1.5 h-1.5 rounded-full bg-brand-green-500 sm:animate-pulse" />
                        2026 Tax Season Ready
                    </div>
                    <h1 className="font-['Syne'] text-[clamp(34px,11vw,72px)] font-extrabold leading-[0.95] tracking-[-0.03em] mb-5 sm:mb-6">
                        Know exactly <br />
                        how much <br />
                        <span className="bg-gradient-to-r from-brand-green-400 to-brand-blue-500 bg-clip-text text-transparent">crypto tax</span> <br />
                        you owe
                    </h1>
                    <p className="text-[var(--text2)] text-base sm:text-lg leading-relaxed max-w-[480px] mb-8 font-light mx-auto text-center md:text-left md:mx-0">
                        <span className="sm:hidden">Declairo automatically calculates your crypto taxes across all wallets.</span>
                        <span className="hidden sm:inline">Declairo automatically calculates your crypto taxes across all wallets, exchanges and DeFi protocols ? and generates ready-to-file reports in minutes.</span>
                    </p>
                    <div className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-3 sm:gap-4 justify-center md:justify-start">
                        <Link to="/register" className="w-full sm:w-auto text-center bg-brand-green-500 hover:bg-brand-green-600 text-brand-dark px-6 sm:px-8 py-4 rounded-xl font-bold text-base shadow-2xl shadow-brand-green-600/30 transition-all hover:-translate-y-1">
                            Calculate my taxes →
                        </Link>
                        <button className="hidden sm:flex w-full sm:w-auto items-center justify-center gap-2 px-6 py-4 font-semibold text-sm transition-colors group" style={{ color: 'var(--text2)' }}>
                            <span className="w-8 h-8 rounded-full border flex items-center justify-center group-hover:bg-brand-green-500/10 transition-colors" style={{ borderColor: 'var(--border)' }}>▶</span>
                            Watch demo (2 min)
                        </button>
                    </div>

                    <div className="hidden sm:flex flex-wrap justify-center md:justify-start gap-6 sm:gap-8 mt-10 sm:mt-12">
                        <div className="stat">
                            <div className="font-['Syne'] text-2xl font-bold text-brand-green-500">10K+</div>
                            <div className="text-[var(--text3)] text-[10px] font-bold uppercase tracking-wider">Active users</div>
                        </div>
                        <div className="stat">
                            <div className="font-['Syne'] text-2xl font-bold text-brand-green-500">$4M+</div>
                            <div className="text-[var(--text3)] text-[10px] font-bold uppercase tracking-wider">Taxes calculated</div>
                        </div>
                        <div className="stat">
                            <div className="font-['Syne'] text-2xl font-bold text-brand-green-500">300+</div>
                            <div className="text-[var(--text3)] text-[10px] font-bold uppercase tracking-wider">Exchanges</div>
                        </div>
                    </div>
                </div>

                <div className="hidden md:flex md:flex-1 justify-center">
                    <LandingCard3D />
                </div>
            </header>

            {/* Exchanges / Integrations Section */}
            <section className="py-16 md:py-20 border-y border-[var(--border)] bg-[var(--bg2)] overflow-hidden">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-12 text-center">
                    <div className="text-brand-green-500 text-[10px] font-bold uppercase tracking-[0.2em] mb-4">Integrations</div>
                    <h2 className="font-['Syne'] text-3xl md:text-4xl font-bold mb-12 reveal">Works with 100+ exchanges & any wallet</h2>

                    <div className="hidden md:flex flex-wrap justify-center gap-3 sm:gap-4 reveal">
                        {integrations.map((ex, i) => (
                            <div key={i} className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-[var(--surface)] border border-[var(--border)] shadow-[var(--card-shadow)] hover:border-brand-green-500/50 transition-all cursor-default group">
                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs overflow-hidden ${ex.color}`}>
                                    <ExchangeLogo
                                        domain={ex.domain}
                                        className="w-full h-full object-contain"
                                        alt={ex.name}
                                        fallback={<span className="text-xs font-bold">{ex.icon}</span>}
                                    />
                                </div>
                                <span className="font-bold text-sm text-[var(--text2)] group-hover:text-[var(--text)] transition-colors">{ex.name}</span>
                            </div>
                        ))}
                        <div className="px-5 py-3 rounded-2xl bg-brand-green-500/10 border border-dashed border-brand-green-500/30 text-brand-green-500 font-bold text-sm flex items-center">
                            + 90 more
                        </div>
                    </div>

                    <div className="md:hidden space-y-3 reveal">
                        {[integrations.slice(0, 5), integrations.slice(5)].map((row, rowIndex) => (
                            <div key={rowIndex} className="overflow-hidden rounded-full border border-[var(--border)] bg-[var(--surface)]/50 py-2">
                                <div className={`flex w-max gap-3 px-3 ${rowIndex === 1 ? 'animate-marquee-reverse' : 'animate-marquee'} [animation-duration:22s]`}>
                                    {[...row, ...row].map((ex, i) => (
                                        <div key={`${rowIndex}-${i}`} className="flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--surface)] px-3 py-2 shadow-[var(--card-shadow)]">
                                            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold overflow-hidden ${ex.color}`}>
                                                <ExchangeLogo
                                                    domain={ex.domain}
                                                    className="w-full h-full object-contain"
                                                    alt={ex.name}
                                                    fallback={<span>{ex.icon}</span>}
                                                />
                                            </div>
                                            <span className="text-xs font-bold text-[var(--text2)] whitespace-nowrap">{ex.name}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section id="how" className="py-16 md:py-24 px-4 sm:px-6 md:px-12 max-w-7xl mx-auto relative z-10">
                <div className="reveal text-center mb-12 md:mb-16">
                    <div className="text-brand-green-500 text-[11px] font-bold uppercase tracking-[0.2em] mb-3">Workflow</div>
                    <h2 className="font-['Syne'] text-[clamp(28px,3.5vw,46px)] font-bold tracking-tight">Three steps to tax freedom</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
                    {howItWorksSteps.map((step, i) => (
                        <div key={i} className="reveal border p-6 sm:p-8 rounded-[2rem] sm:rounded-[2.5rem] md:hover:scale-[1.02] transition-all group relative overflow-hidden" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                            <div className="absolute top-4 right-8 font-['Syne'] text-[80px] font-extrabold select-none opacity-5 transition-opacity group-hover:opacity-10" style={{ color: 'var(--text)' }}>{i + 1}</div>
                            <div className="w-12 h-12 rounded-xl bg-brand-green-500/10 border border-brand-green-500/20 flex items-center justify-center text-brand-green-500 mb-6 group-hover:bg-brand-green-500 group-hover:text-brand-dark transition-all">
                                {step.icon}
                            </div>
                            <h3 className="text-xl font-bold mb-3">{step.title}</h3>
                            <p className="text-[var(--text2)] text-sm leading-relaxed">{step.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Testimonials Section */}
            <section className="py-16 md:py-24 px-4 sm:px-6 md:px-12 bg-gradient-to-b from-transparent to-[var(--bg2)] relative z-10" style={{ overflowX: 'hidden' }}>
                <div className="max-w-7xl mx-auto">
                    <div className="text-brand-green-500 text-[10px] font-bold uppercase tracking-[0.2em] mb-4">User Reviews</div>
                    <h2 className="font-['Syne'] text-[clamp(28px,3.5vw,46px)] font-bold tracking-tight mb-12 reveal">Trusted by 10K+ crypto investors</h2>

                    <div className="hidden md:block relative py-10" style={{ overflow: 'hidden', marginLeft: '-1rem', marginRight: '-1rem', maskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)', WebkitMaskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)' }}>
                        <div className="flex gap-6 animate-marquee hover:[animation-play-state:paused] w-fit">
                            {[...testimonials, ...testimonials].map((t, i) => (
                                <div key={i} className="flex-shrink-0 w-[280px] sm:w-[320px] md:w-[350px] p-5 sm:p-6 md:p-8 rounded-[2rem] sm:rounded-[2.5rem] bg-[var(--surface)] border border-[var(--border)] shadow-[var(--card-shadow)] hover:border-brand-green-500/30 transition-all flex flex-col justify-between group">
                                    <div>
                                        <div className="flex gap-1 text-brand-green-500 mb-6">
                                            {[...Array(t.stars)].map((_, s) => <Star key={s} size={14} fill="currentColor" />)}
                                            {t.stars < 5 && <Star size={14} className="opacity-30" />}
                                        </div>
                                        <p className="text-[var(--text2)] text-[15px] leading-relaxed italic mb-8">"{t.text}"</p>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-green-500 to-brand-blue-500 flex items-center justify-center font-bold text-brand-dark">
                                            {t.name[0]}
                                        </div>
                                        <div>
                                            <div className="font-bold text-sm">{t.name}</div>
                                            <div className="text-[10px] text-[var(--text3)] uppercase tracking-wider">{t.location} - {t.role}</div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="md:hidden">
                        <div
                            ref={testimonialScrollerRef}
                            className="mobile-testimonials-scroller -mx-4 flex snap-x snap-mandatory overflow-x-auto px-4 pb-4 no-scrollbar"
                            onScroll={(event) => {
                                const container = event.currentTarget;
                                const nextIndex = Math.round(container.scrollLeft / container.clientWidth);
                                if (nextIndex !== activeTestimonialIndex) {
                                    setActiveTestimonialIndex(nextIndex);
                                }
                            }}
                        >
                            {testimonials.map((testimonial, index) => (
                                <div key={testimonial.name} className="min-w-full snap-center pr-4">
                                    <div className="flex h-full min-h-[280px] flex-col justify-between rounded-[2rem] border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--card-shadow)]">
                                        <div>
                                            <div className="mb-5 flex gap-1 text-brand-green-500">
                                                {[...Array(testimonial.stars)].map((_, starIndex) => <Star key={starIndex} size={14} fill="currentColor" />)}
                                                {testimonial.stars < 5 && <Star size={14} className="opacity-30" />}
                                            </div>
                                            <p className="mb-8 text-[15px] italic leading-relaxed text-[var(--text2)]">"{testimonial.text}"</p>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-brand-green-500 to-brand-blue-500 font-bold text-brand-dark">
                                                {testimonial.name[0]}
                                            </div>
                                            <div>
                                                <div className="text-sm font-bold">{testimonial.name}</div>
                                                <div className="text-[10px] uppercase tracking-wider text-[var(--text3)]">{testimonial.location} - {testimonial.role}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-2 flex items-center justify-center gap-2">
                            {testimonials.map((testimonial, index) => (
                                <button
                                    key={`${testimonial.name}-dot`}
                                    type="button"
                                    aria-label={`Show testimonial ${index + 1}`}
                                    className={`h-2.5 rounded-full transition-all ${activeTestimonialIndex === index ? 'w-6 bg-brand-green-500' : 'w-2.5 bg-[var(--border)]'}`}
                                    onClick={() => scrollToTestimonial(index)}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="py-16 md:py-24 px-4 sm:px-6 md:px-12 max-w-7xl mx-auto relative z-10 border-t border-[var(--border)]">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-16 items-center">
                    <div className="reveal">
                        <div className="text-brand-green-500 text-[11px] font-bold uppercase tracking-[0.2em] mb-3">Capabilities</div>
                        <h2 className="font-['Syne'] text-[clamp(28px,3.5vw,46px)] font-bold tracking-tight mb-6">Built for traders, investors, and HODLers alike.</h2>
                        <p className="text-[var(--text2)] text-base sm:text-lg font-light mb-8 sm:mb-12">Declairo is the most comprehensive crypto tax tool for the modern investor, supporting everything from simple swaps to complex DeFi strategies.</p>

                        <div className="space-y-6">
                            {[
                                { title: 'Bank-grade security', desc: 'Read-only access with AES-256 encryption. Your keys never leave your device.', icon: <ShieldCheck /> },
                                { title: 'Global jurisdiction support', desc: 'Automated rules for US, Brazil, Argentina  and 40+ other countries.', icon: <Globe /> },
                                { title: 'Tax-loss harvesting', desc: 'Real-time monitoring of your P&L to find opportunities to reduce your tax bill.', icon: <Zap /> }
                            ].map((feat, i) => (
                                <div key={i} className="flex gap-4 p-4 rounded-2xl hover:bg-brand-green-500/5 transition-all">
                                    <div className="w-10 h-10 rounded-lg flex items-center justify-center text-brand-green-500 shrink-0" style={{ background: 'var(--surface2)' }}>
                                        {feat.icon}
                                    </div>
                                    <div>
                                        <h4 className="font-bold mb-1">{feat.title}</h4>
                                        <p className="text-sm text-[var(--text2)] leading-relaxed">{feat.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="hidden md:flex reveal relative justify-center perspective-1000 group/card">
                        <div className="card-3d w-full max-w-[440px] rounded-[3rem] bg-[var(--surface)] border border-[var(--border)] flex flex-col items-center overflow-hidden shadow-[var(--card-shadow)] animate-float-3d-delayed" style={{ transformStyle: 'preserve-3d' }}>
                            <div className="p-10 w-full" style={{ transform: 'translateZ(50px)' }}>
                                <div className="flex justify-between items-center mb-10">
                                    <h3 className="font-['Syne'] text-xl font-bold text-[var(--text)]">Portfolio Distribution</h3>
                                    <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-[var(--text3)]">•••</div>
                                </div>

                                <div className="relative w-56 h-56 mx-auto mb-10">
                                    <svg viewBox="0 0 36 36" className="w-full h-full">
                                        {/* Background Circle */}
                                        <path stroke="currentColor" strokeWidth="2.5" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" style={{ color: 'rgba(255,255,255,0.05)' }} />

                                        {/* BTC (45%) */}
                                        <path className="text-brand-green-500" stroke="currentColor" strokeWidth="3" strokeDasharray="45, 100" strokeLinecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />

                                        {/* ETH (25%) */}
                                        <path className="text-brand-blue-500" stroke="currentColor" strokeWidth="3" strokeDasharray="25, 100" strokeDashoffset="-45" strokeLinecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />

                                        {/* SOL (15%) */}
                                        <path className="text-purple-500" stroke="currentColor" strokeWidth="3" strokeDasharray="15, 100" strokeDashoffset="-70" strokeLinecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />

                                        {/* USDC (10%) */}
                                        <path className="text-blue-300" stroke="currentColor" strokeWidth="3" strokeDasharray="10, 100" strokeDashoffset="-85" strokeLinecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                    </svg>
                                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                                        <span className="text-[10px] text-[var(--text3)] uppercase font-black tracking-widest mb-1">Total Assets</span>
                                        <span className="font-['Syne'] text-3xl font-bold tracking-tight">$124,840</span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-y-4 gap-x-8">
                                    {[
                                        { label: 'Bitcoin', val: '45%', color: 'bg-brand-green-500' },
                                        { label: 'Ethereum', val: '25%', color: 'bg-brand-blue-500' },
                                        { label: 'Solana', val: '15%', color: 'bg-purple-500' },
                                        { label: 'USDC', val: '10%', color: 'bg-blue-300' },
                                        { label: 'Others', val: '5%', color: 'bg-white/20' }
                                    ].map((asset, idx) => (
                                        <div key={idx} className="flex items-center gap-2.5">
                                            <div className={`w-1.5 h-1.5 rounded-full ${asset.color} shadow-[0_0_8px_rgba(0,0,0,0.5)]`}></div>
                                            <span className="text-[11px] text-[var(--text2)] font-bold">{asset.label} ({asset.val})</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Tax Methods Section */}
            <section id="methods" className="py-24 px-6 md:px-12 max-w-7xl mx-auto border-t border-[var(--border)]">
                <div className="text-center mb-16 reveal">
                    <div className="text-brand-green-500 text-[10px] font-bold uppercase tracking-[0.2em] mb-4">Tax Calculation</div>
                    <h2 className="font-['Syne'] text-[clamp(28px,3.5vw,46px)] font-bold tracking-tight mb-6">Every method. You choose.</h2>
                    <p className="text-[var(--text2)] max-w-2xl mx-auto">Advanced investors know that the calculation method matters. Declairo supports all of them — switch anytime.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 reveal">
                    {[
                        { id: 'FIFO', title: 'First In, First Out', desc: 'The oldest coins are sold first. Most common default method, required by many tax authorities.', best: 'Best for: long-term holders' },
                        { id: 'LIFO', title: 'Last In, First Out', desc: 'Most recently acquired coins are sold first. Can minimize gains in rising markets.', best: 'Best for: active traders' },
                        { id: 'HIFO', title: 'Highest In, First Out', desc: 'Sells highest-cost basis first to minimize capital gains. Maximum tax efficiency.', best: 'Best for: tax optimization' },
                        { id: 'AVCO', title: 'Average Cost', desc: 'Uses the average cost across all purchases. Simple, consistent, required in some jurisdictions.', best: 'Best for: Brazil & LATAM defaults' }
                    ].map((m, i) => (
                        <div key={i} className="p-8 rounded-[2.5rem] bg-[var(--surface)] border border-[var(--border)] shadow-[var(--card-shadow)] hover:bg-[var(--bg2)] transition-all">
                            <div className="inline-block px-3 py-1 rounded-lg bg-brand-dark text-brand-green-500 text-[10px] font-black tracking-widest mb-6">{m.id}</div>
                            <h3 className="text-lg font-bold mb-3">{m.title}</h3>
                            <p className="text-sm text-[var(--text2)] leading-relaxed mb-6">{m.desc}</p>
                            <div className="text-[11px] font-bold text-brand-green-500">{m.best}</div>
                        </div>
                    ))}
                </div>
            </section>

            {/* FAQ Section */}
            <section className="py-24 px-6 md:px-12 max-w-7xl mx-auto">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-16">
                    <div className="reveal">
                        <div className="text-brand-green-500 text-[10px] font-bold uppercase tracking-[0.2em] mb-4">FAQ</div>
                        <h2 className="font-['Syne'] text-4xl font-bold tracking-tight mb-6">Questions? We've got answers.</h2>
                        <p className="text-[var(--text2)] mb-8">Can't find what you need? Our support team replies within 24 hours.</p>
                        <Link to="/contact" className="inline-flex items-center gap-2 text-brand-green-500 font-bold hover:gap-3 transition-all">
                            Contact center <ArrowRight size={16} />
                        </Link>
                    </div>

                    <div className="lg:col-span-2 space-y-4 reveal">
                        {[
                            { q: `Is Declairo free to use?`, a: `Yes — you can connect your wallets, import all transactions, and preview your tax summary for free. You only pay when you want to download the official tax report. Plans start at $19.99/year.` },
                            { q: `Which exchanges and wallets are supported?`, a: `Declairo supports 100+ integrations including Binance, Coinbase, Kraken, MetaMask, Phantom, Ledger, and all major Latin American platforms. If yours isn't listed, you can import via CSV.` },
                            { q: `Is it safe to connect my wallet?`, a: `Completely. We use read-only API connections — Declairo can never move or access your funds. All data is encrypted with AES-256 and your private keys never leave your device.` },
                            { q: `I have thousands of DeFi transactions. Can you handle that?`, a: `Absolutely. Our algorithm automatically classifies swaps, liquidity pool events, staking rewards, NFT trades, and bridge transactions — no matter the volume.` },
                            { q: `Which Latin American tax authorities are supported?`, a: `We generate compliant reports for Brazil (Receita Federal / GCAP), Mexico (SAT), Colombia (DIAN), Argentina (AFIP), Chile (SII), and 40+ other jurisdictions globally.` }
                        ].map((faq, i) => (
                            <details key={i} className="group border border-[var(--border)] rounded-2xl bg-[var(--surface)] shadow-[var(--card-shadow)] overflow-hidden transition-all">
                                <summary className="flex items-center justify-between p-6 cursor-pointer list-none">
                                    <span className="font-bold text-[var(--text)]">{faq.q}</span>
                                    <span className="text-brand-green-500 transition-transform group-open:rotate-45 font-light text-2xl">+</span>
                                </summary>
                                <div className="p-6 pt-0 text-sm text-[var(--text2)] leading-relaxed border-t border-[var(--border)]/50">
                                    {faq.a}
                                </div>
                            </details>
                        ))}
                    </div>
                </div>
            </section>

            {/* Pricing Section */}
            <section id="pricing" className="py-16 md:py-24 px-4 sm:px-6 md:px-12 bg-gradient-to-b from-transparent to-brand-green-500/5 relative z-10">
                <div className="max-w-7xl mx-auto text-center mb-16 reveal">
                    <div className="text-brand-green-500 text-[11px] font-bold uppercase tracking-[0.2em] mb-3">Plans</div>
                    <h2 className="font-['Syne'] text-[clamp(28px,3.5vw,46px)] font-bold tracking-tight mb-4">Crypto taxes without the stress</h2>
                    <p className="text-[var(--text2)]">Everything you need to calculate and file your crypto taxes with confidence.</p>
                </div>

                <div className="hidden md:grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 max-w-7xl mx-auto">
                    {pricingPlans.map((plan, i) => (
                        <div key={i} className={`reveal relative p-6 sm:p-8 rounded-[2rem] sm:rounded-[2.5rem] border transition-all hover:-translate-y-2 shadow-[var(--card-shadow)] ${plan.popular ? 'bg-gradient-to-br from-[var(--surface)] to-brand-green-500/10 border-brand-green-500/30 ring-1 ring-brand-green-500/20' : 'bg-[var(--surface)] border-[var(--border)]'}`}>
                            {plan.popular && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand-green-500 text-brand-dark text-[9px] font-black uppercase px-4 py-1 rounded-full shadow-lg">Popular</div>
                            )}
                            <div className="text-[var(--text3)] text-[10px] font-black uppercase tracking-widest mb-2">{plan.name}</div>
                            <div className="text-[11px] text-[var(--text2)] italic mb-4 font-medium">{plan.description}</div>
                            <div className="flex items-baseline gap-1 mb-6">
                                <span className="text-xl text-[var(--text2)] font-bold">$</span>
                                <span className="font-['Outfit'] text-4xl font-black text-[var(--text)] tracking-tight">{plan.price}</span>
                                <span className="text-[10px] text-[var(--text3)] ml-1">/ tax year</span>
                            </div>
                            <ul className="space-y-4 mb-8">
                                {plan.features.map((f, fi) => {
                                    const isNegative = false; // Portfolio tracking replaces No export
                                    return (
                                        <li key={fi} className={`flex items-start gap-3 text-[13px] font-medium ${isNegative ? 'opacity-40 line-through text-[var(--text3)]' : 'text-[var(--text2)]'}`}>
                                            {isNegative ? (
                                                <span className="text-[#ff4d6a] shrink-0 font-black text-xs mt-0.5">✕</span>
                                            ) : (
                                                <CheckCircle size={16} className="text-brand-green-500 shrink-0 mt-0.5" />
                                            )}
                                            {f}
                                        </li>
                                    );
                                })}
                            </ul>
                            <Link to="/register" className={`block text-center py-4 rounded-xl font-bold text-sm transition-all ${plan.popular ? 'bg-brand-green-500 hover:bg-brand-green-600 text-brand-dark shadow-xl shadow-brand-green-600/20' : 'hover:opacity-80'}`} style={!plan.popular ? { background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)', border: '1px solid var(--border)' } : undefined}>
                                {plan.name === 'Free' ? 'Get started free' : 'Choose ' + plan.name}
                            </Link>
                        </div>
                    ))}
                </div>

                <div className="md:hidden">
                    <div
                        ref={pricingScrollerRef}
                        className="-mx-4 flex snap-x snap-mandatory overflow-x-auto px-4 pb-4 no-scrollbar"
                        onScroll={(event) => {
                            const container = event.currentTarget;
                            const nextIndex = Math.round(container.scrollLeft / container.clientWidth);
                            if (nextIndex !== activePricingIndex) {
                                setActivePricingIndex(nextIndex);
                            }
                        }}
                    >
                        {pricingPlans.map((plan, i) => (
                            <div key={plan.name} className="min-w-full snap-center pr-4">
                                <div className={`relative h-full rounded-[2rem] border p-6 shadow-[var(--card-shadow)] ${plan.popular ? 'bg-gradient-to-br from-[var(--surface)] to-brand-green-500/10 border-brand-green-500/30 ring-1 ring-brand-green-500/20' : 'bg-[var(--surface)] border-[var(--border)]'}`}>
                                    {plan.popular && (
                                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand-green-500 px-4 py-1 text-[9px] font-black uppercase text-brand-dark shadow-lg">Popular</div>
                                    )}
                                    <div className="mb-2 text-[10px] font-black uppercase tracking-widest text-[var(--text3)]">{plan.name}</div>
                                    <div className="mb-4 text-[11px] italic font-medium text-[var(--text2)]">{plan.description}</div>
                                    <div className="mb-6 flex items-baseline gap-1">
                                        <span className="text-xl font-bold text-[var(--text2)]">$</span>
                                        <span className="font-['Outfit'] text-4xl font-black tracking-tight text-[var(--text)]">{plan.price}</span>
                                        <span className="ml-1 text-[10px] text-[var(--text3)]">/ tax year</span>
                                    </div>
                                    <ul className="mb-8 space-y-4">
                                        {plan.features.map((feature, featureIndex) => (
                                            <li key={featureIndex} className="flex items-start gap-3 text-[13px] font-medium text-[var(--text2)]">
                                                <CheckCircle size={16} className="mt-0.5 shrink-0 text-brand-green-500" />
                                                {feature}
                                            </li>
                                        ))}
                                    </ul>
                                    <Link
                                        to="/register"
                                        className={`block rounded-xl py-4 text-center text-sm font-bold transition-all ${plan.popular ? 'bg-brand-green-500 text-brand-dark shadow-xl shadow-brand-green-600/20' : 'border border-[var(--border)] bg-[var(--bg2)] text-[var(--text)]'}`}
                                    >
                                        {plan.name === 'Free' ? 'Get started free' : 'Choose ' + plan.name}
                                    </Link>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="mt-2 flex items-center justify-center gap-2">
                        {pricingPlans.map((plan, index) => (
                            <button
                                key={`${plan.name}-dot`}
                                type="button"
                                aria-label={`Show pricing plan ${index + 1}`}
                                className={`h-2.5 rounded-full transition-all ${activePricingIndex === index ? 'w-6 bg-brand-green-500' : 'w-2.5 bg-[var(--border)]'}`}
                                onClick={() => scrollToPricing(index)}
                            />
                        ))}
                    </div>

                </div>
            </section>

            {/* Final CTA Section */}
            <section className="hidden md:block py-16 md:py-20 relative overflow-hidden bg-gradient-to-br from-brand-green-500 to-brand-blue-600 text-brand-dark reveal">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.2),transparent)] pointer-events-none" />
                <div className="max-w-4xl mx-auto px-4 sm:px-6 md:px-12 relative z-10 text-center">
                    <div className="text-[9px] font-black uppercase tracking-[0.3em] mb-4 opacity-60">Ready to file?</div>
                    <h2 className="font-['Syne'] text-3xl md:text-5xl font-bold tracking-tighter mb-6">Your crypto taxes, done in minutes.</h2>
                    <p className="text-base font-medium mb-10 opacity-80 max-w-xl mx-auto">Join 10,000+ investors across Latin America who already use Declairo. Free to start — no credit card required.</p>

                    <div className="flex flex-col sm:flex-row flex-wrap justify-center gap-3 sm:gap-4">
                        <Link to="/register" className="w-full sm:w-auto text-center bg-brand-dark text-white px-8 py-4 rounded-xl font-bold text-base hover:scale-105 transition-all shadow-2xl">
                            Calculate my taxes →
                        </Link>
                        <button className="w-full sm:w-auto bg-white/20 backdrop-blur-md text-brand-dark border border-white/30 px-8 py-4 rounded-xl font-bold text-base hover:bg-white/30 transition-all">
                            Watch demo
                        </button>
                    </div>

                    <div className="mt-10 flex flex-wrap justify-center gap-6 text-[10px] font-black uppercase tracking-widest opacity-60">
                        <span>✓ Free plan available</span>
                        <span>✓ No subscription</span>
                        <span>✓ IRS & LATAM compliant</span>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-16 md:py-20 px-4 sm:px-6 border-t border-[var(--border)] relative z-10">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-10 md:gap-12">
                    <div className="w-full md:w-auto text-center md:text-left">
                        <Link to="/" className="logo inline-flex md:flex items-center justify-center gap-2 text-[var(--text)] no-underline font-syne font-extrabold text-2xl tracking-tight mb-6">
                            <img src="/logo.webp" alt="Declairo Logo" className="w-[32px] h-[32px] object-contain" />
                            Declairo
                        </Link>
                        <p className="hidden md:block max-w-[300px] mx-auto md:mx-0 text-[var(--text3)] text-sm leading-relaxed mb-8">
                            Providing professional tax tools to a new generation of crypto investors.
                        </p>
                        <div className="flex flex-col items-center gap-3 text-sm text-[var(--text3)] md:hidden">
                            <div className="flex items-center justify-center gap-6">
                                <Link to="/privacy" className="hover:text-brand-green-500 transition-colors">Privacy Policy</Link>
                                <Link to="/terms" className="hover:text-brand-green-500 transition-colors">Terms of Service</Link>
                            </div>
                            <div className="flex items-center justify-center gap-5 text-center">
                                <Link to="/disclaimer" className="hover:text-brand-green-500 transition-colors">Disclaimer</Link>
                                <Link to="/security" className="hover:text-brand-green-500 transition-colors">Security</Link>
                                <Link to="/contact" className="hover:text-brand-green-500 transition-colors">Contact center</Link>
                            </div>
                        </div>
                    </div>

                    <div className="hidden md:grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 sm:gap-10 md:gap-12 w-full md:w-auto">
                        <div>
                            <h4 className="font-bold text-sm uppercase tracking-widest text-[var(--text2)] mb-6">Product</h4>
                            <ul className="space-y-4 text-sm text-[var(--text3)]">
                                <li><a href="#how" className="hover:text-brand-green-500 transition-colors">How it works</a></li>
                                <li><a href="#features" className="hover:text-brand-green-500 transition-colors">Features</a></li>
                                <li><a href="#pricing" className="hover:text-brand-green-500 transition-colors">Pricing</a></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-bold text-sm uppercase tracking-widest text-[var(--text2)] mb-6">Legal</h4>
                            <ul className="space-y-4 text-sm text-[var(--text3)]">
                                <li><Link to="/privacy" className="hover:text-brand-green-500 transition-colors">Privacy Policy</Link></li>
                                <li><Link to="/terms" className="hover:text-brand-green-500 transition-colors">Terms of Service</Link></li>
                                <li><Link to="/disclaimer" className="hover:text-brand-green-500 transition-colors">Disclaimer</Link></li>
                                <li><Link to="/security" className="hover:text-brand-green-500 transition-colors">Security</Link></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-bold text-sm uppercase tracking-widest text-[var(--text2)] mb-6">Support</h4>
                            <ul className="space-y-4 text-sm text-[var(--text3)]">
                                <li><a href="mailto:support@declairo.com" className="hover:text-brand-green-500 transition-colors">support@declairo.com</a></li>
                                <li><Link to="/contact" className="hover:text-brand-green-500 transition-colors">Contact center</Link></li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div className="max-w-7xl mx-auto mt-20 pt-8 border-t border-[var(--border)] text-center text-[var(--text3)] text-xs">
                    © 2026 Declairo. All rights reserved. Not financial advice.
                </div>
            </footer>

            {showStickyMobileCta && (
                <div className="fixed inset-x-0 bottom-0 z-[120] px-4 pt-3 pb-[calc(1rem+env(safe-area-inset-bottom))] md:hidden">
                    <div className="mobile-sticky-cta-shell mx-auto max-w-md rounded-[1.25rem] border border-brand-green-500/20 bg-[color:rgba(8,15,25,0.92)] p-3 shadow-[0_20px_60px_rgba(0,0,0,0.35)] backdrop-blur-xl">
                        <Link
                            to="/register"
                            className="mobile-sticky-cta-button flex w-full items-center justify-center rounded-[1rem] bg-brand-green-500 px-5 py-4 text-base font-bold text-brand-dark shadow-lg shadow-brand-green-600/20"
                        >
                            Start calculation
                        </Link>
                    </div>
                </div>
            )}
        </div>
    );
}
