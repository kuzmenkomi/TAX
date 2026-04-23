import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Lock, CheckCircle, ArrowRight, Sun, Moon, BarChart3, ShieldCheck, Zap, Globe } from 'lucide-react';
import { LandingCanvas } from '../components/LandingCanvas';
import { LandingCard3D } from '../components/LandingCard3D';
import { useScrollReveal } from '../hooks/useScrollReveal';
import { useI18n } from '../i18n/I18nContext';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { ThemeToggle } from '../components/ThemeToggle';

export function HomePage() {
    const { t } = useI18n();
    useScrollReveal();

    return (
        <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] transition-colors duration-300 landing-grid">
            <LandingCanvas />
            
            {/* Header / Nav */}
            <nav className="fixed top-0 left-0 right-0 z-[100] flex items-center justify-between px-6 md:px-12 py-4 bg-[var(--nav-bg)] backdrop-blur-xl border-b border-[var(--border)]">
                <Link to="/" className="logo flex items-center gap-2 text-[var(--text)] no-underline font-syne font-extrabold text-xl tracking-tight">
                    <div className="logo-dot w-1.5 h-1.5 rounded-full bg-brand-green-500 shadow-[0_0_12px_var(--accent)]" />
                    Declairo
                </Link>

                <div className="hidden md:flex items-center gap-8">
                    <a href="#how" className="text-sm font-semibold text-[var(--text2)] hover:text-[var(--text)] transition-colors no-underline">How it works</a>
                    <a href="#features" className="text-sm font-semibold text-[var(--text2)] hover:text-[var(--text)] transition-colors no-underline">Features</a>
                    <a href="#pricing" className="text-sm font-semibold text-[var(--text2)] hover:text-[var(--text)] transition-colors no-underline">Pricing</a>
                </div>

                <div className="flex items-center gap-4">
                    <LanguageSwitcher />
                    <ThemeToggle />
                    <Link to="/login" className="text-sm font-bold px-4 py-2 rounded-lg transition-all hidden md:block" style={{ color: 'var(--text)' }}>Login</Link>
                    <Link to="/register" className="bg-brand-green-500 hover:bg-brand-green-600 text-brand-dark text-sm font-bold px-5 py-2.5 rounded-xl shadow-lg shadow-brand-green-600/20 transition-all hover:scale-[1.02]">
                        Get started free
                    </Link>
                </div>
            </nav>

            {/* Hero Section */}
            <header className="relative pt-32 pb-20 px-6 md:px-12 min-h-[85vh] flex flex-col md:flex-row items-center gap-12 max-w-7xl mx-auto overflow-visible">
                <div className="flex-1 max-w-[660px]">
                    <div className="badge inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-bold uppercase tracking-widest mb-6">
                        <span className="w-1.5 h-1.5 rounded-full bg-brand-green-500 animate-pulse" />
                        2025 Tax Season Ready
                    </div>
                    <h1 className="font-['Syne'] text-[clamp(40px,5.5vw,72px)] font-extrabold leading-[1.0] tracking-[-0.03em] mb-6">
                        Know exactly <br />
                        how much <br />
                        <span className="bg-gradient-to-r from-brand-green-400 to-brand-blue-500 bg-clip-text text-transparent">crypto tax</span> <br />
                        you owe
                    </h1>
                    <p className="text-[var(--text2)] text-lg leading-relaxed max-w-[480px] mb-8 font-light">
                        Declairo automatically calculates your crypto taxes across all wallets, exchanges and DeFi protocols — and generates ready-to-file reports in minutes.
                    </p>
                    <div className="flex flex-wrap items-center gap-4">
                        <Link to="/register" className="bg-brand-green-500 hover:bg-brand-green-600 text-brand-dark px-8 py-4 rounded-xl font-bold text-base shadow-2xl shadow-brand-green-600/30 transition-all hover:-translate-y-1">
                            Calculate my taxes →
                        </Link>
                        <button className="flex items-center gap-2 px-6 py-4 font-semibold text-sm transition-colors group" style={{ color: 'var(--text2)' }}>
                            <span className="w-8 h-8 rounded-full border flex items-center justify-center group-hover:bg-brand-green-500/10 transition-colors" style={{ borderColor: 'var(--border)' }}>▶</span>
                            Watch demo (2 min)
                        </button>
                    </div>
                    
                    <div className="flex gap-8 mt-12">
                        <div className="stat">
                            <div className="font-['Syne'] text-2xl font-bold text-brand-green-500">250K+</div>
                            <div className="text-[var(--text3)] text-[10px] font-bold uppercase tracking-wider">Active users</div>
                        </div>
                        <div className="stat">
                            <div className="font-['Syne'] text-2xl font-bold text-brand-green-500">$4B+</div>
                            <div className="text-[var(--text3)] text-[10px] font-bold uppercase tracking-wider">Taxes calculated</div>
                        </div>
                        <div className="stat">
                            <div className="font-['Syne'] text-2xl font-bold text-brand-green-500">300+</div>
                            <div className="text-[var(--text3)] text-[10px] font-bold uppercase tracking-wider">Exchanges</div>
                        </div>
                    </div>
                </div>
                
                <LandingCard3D />
            </header>

            {/* How It Works Section */}
            <section id="how" className="py-24 px-6 md:px-12 max-w-7xl mx-auto relative z-10">
                <div className="reveal text-center mb-16">
                    <div className="text-brand-green-500 text-[11px] font-bold uppercase tracking-[0.2em] mb-3">Workflow</div>
                    <h2 className="font-['Syne'] text-[clamp(28px,3.5vw,46px)] font-bold tracking-tight">Three steps to tax freedom</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                        { title: 'Connect wallets', desc: 'Securely link your exchanges, wallets, and protocols. We do the rest.', icon: <Zap /> },
                        { title: 'Review transactions', desc: 'Our AI auto-categorizes every trade and transfer for maximum accuracy.', icon: <BarChart3 /> },
                        { title: 'Download reports', desc: 'Get IRS and LatAm compliant tax forms (PDF, CSV, or XML) in seconds.', icon: <CheckCircle /> }
                    ].map((step, i) => (
                        <div key={i} className="reveal border p-8 rounded-[2.5rem] hover:scale-[1.02] transition-all group relative overflow-hidden" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
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

            {/* Features Section */}
            <section id="features" className="py-24 px-6 md:px-12 max-w-7xl mx-auto relative z-10 border-t border-[var(--border)]">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                    <div className="reveal">
                        <div className="text-brand-green-500 text-[11px] font-bold uppercase tracking-[0.2em] mb-3">Capabilities</div>
                        <h2 className="font-['Syne'] text-[clamp(28px,3.5vw,46px)] font-bold tracking-tight mb-6">Built for traders, degens, and HODLers alike.</h2>
                        <p className="text-[var(--text2)] text-lg font-light mb-12">Declairo is the most comprehensive crypto tax tool in Latin America, supporting everything from simple swaps to complex DeFi strategies.</p>
                        
                        <div className="space-y-6">
                            {[
                                { title: 'Bank-grade security', desc: 'Read-only access with AES-256 encryption. Your keys never leave your device.', icon: <ShieldCheck /> },
                                { title: 'Global jurisdiction support', desc: 'Automated rules for US, UK, Brazil, Mexico, and 40+ other countries.', icon: <Globe /> },
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

                    <div className="reveal relative flex justify-center">
                        <div className="w-full max-w-[440px] aspect-square rounded-[3rem] bg-gradient-to-br from-brand-green-500/10 to-brand-blue-500/10 border border-[var(--border)] flex items-center justify-center overflow-hidden">
                             <div className="p-8 w-full">
                                <h3 className="font-['Syne'] text-xl font-bold mb-8 text-center text-[var(--text)]">Portfolio Distribution</h3>
                                <div className="relative w-48 h-48 mx-auto mb-8">
                                    <svg viewBox="0 0 36 36" className="w-full h-full drop-shadow-[0_0_20px_rgba(16,185,129,0.3)]">
                                        <path stroke="currentColor" strokeWidth="3" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" style={{ color: 'var(--border)' }} />
                                        <path className="text-brand-green-500" stroke="currentColor" strokeWidth="3" strokeDasharray="60, 100" strokeLinecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                        <path className="text-brand-blue-500" stroke="currentColor" strokeWidth="3" strokeDasharray="30, 100" strokeDashoffset="-60" strokeLinecap="round" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                    </svg>
                                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                                        <span className="text-[10px] text-[var(--text3)] uppercase font-bold tracking-widest">Total Value</span>
                                        <span className="font-['Syne'] text-xl font-bold">$124K</span>
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-brand-green-500"></div>
                                        <span className="text-xs text-[var(--text2)] font-medium">Bitcoin (60%)</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-brand-blue-500"></div>
                                        <span className="text-xs text-[var(--text2)] font-medium">Ethereum (30%)</span>
                                    </div>
                                </div>
                             </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Pricing Section */}
            <section id="pricing" className="py-24 px-6 md:px-12 bg-gradient-to-b from-transparent to-brand-green-500/5 relative z-10">
                <div className="max-w-7xl mx-auto text-center mb-16 reveal">
                    <div className="text-brand-green-500 text-[11px] font-bold uppercase tracking-[0.2em] mb-3">Plans</div>
                    <h2 className="font-['Syne'] text-[clamp(28px,3.5vw,46px)] font-bold tracking-tight mb-4">Simple, transparent pricing</h2>
                    <p className="text-[var(--text2)]">Pay Once per tax year. No subscriptions, no surprises.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
                    {[
                        { name: 'Starter', price: '49', features: ['Up to 250 transactions', '5 wallets / exchanges', 'Tax report (PDF)', 'Email support'] },
                        { name: 'Pro', price: '99', features: ['Unlimited transactions', 'Unlimited wallets', 'Advanced DeFi & NFT', 'Priority support'], popular: true },
                        { name: 'Business', price: '249', features: ['Everything in Pro', 'Multi-year history', 'CPA collaboration', 'Dedicated account manager'] }
                    ].map((plan, i) => (
                        <div key={i} className={`reveal relative p-8 rounded-[2.5rem] border transition-all hover:-translate-y-2 ${plan.popular ? 'bg-gradient-to-br from-[var(--surface)] to-brand-green-500/10 border-brand-green-500/30' : 'bg-[var(--surface)] border-[var(--border)]'}`}>
                            {plan.popular && (
                                <div className="absolute top-4 right-4 bg-brand-green-500 text-brand-dark text-[9px] font-black uppercase px-2.5 py-1 rounded-full">Popular</div>
                            )}
                            <div className="text-[var(--text3)] text-xs font-black uppercase tracking-widest mb-4">{plan.name}</div>
                            <div className="flex items-baseline gap-1 mb-6">
                                <span className="text-xl text-[var(--text2)] font-bold">$</span>
                                <span className="font-['Outfit'] text-5xl font-black text-[var(--text)] tracking-tight">{plan.price}</span>
                                <span className="text-xs text-[var(--text3)] ml-1">/ tax year</span>
                            </div>
                            <ul className="space-y-4 mb-8">
                                {plan.features.map((f, fi) => (
                                    <li key={fi} className="flex items-center gap-3 text-sm text-[var(--text2)] font-medium">
                                        <CheckCircle size={16} className="text-brand-green-500" />
                                        {f}
                                    </li>
                                ))}
                            </ul>
                            <Link to="/register" className={`block text-center py-4 rounded-xl font-bold text-sm transition-all ${plan.popular ? 'bg-brand-green-500 hover:bg-brand-green-600 text-brand-dark shadow-xl shadow-brand-green-600/20' : 'hover:opacity-80'}`} style={!plan.popular ? { background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)', border: '1px solid var(--border)' } : undefined}>
                                Get started
                            </Link>
                        </div>
                    ))}
                </div>
            </section>

            {/* Footer */}
            <footer className="py-20 px-6 border-t border-[var(--border)] relative z-10">
                <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-12">
                    <div>
                        <Link to="/" className="logo flex items-center gap-2 text-[var(--text)] no-underline font-syne font-extrabold text-2xl tracking-tight mb-6">
                            <div className="logo-dot w-1.5 h-1.5 rounded-full bg-brand-green-500 shadow-[0_0_12px_var(--accent)]" />
                            Declairo
                        </Link>
                        <p className="max-w-[300px] text-[var(--text3)] text-sm leading-relaxed mb-8">
                            Empowering the next generation of crypto investors in Latin America with professional tax tools.
                        </p>
                    </div>
                    
                    <div className="grid grid-cols-2 lg:grid-cols-3 gap-12">
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
                                <li><Link to="/security" className="hover:text-brand-green-500 transition-colors">Security</Link></li>
                            </ul>
                        </div>
                        <div>
                            <h4 className="font-bold text-sm uppercase tracking-widest text-[var(--text2)] mb-6">Support</h4>
                            <ul className="space-y-4 text-sm text-[var(--text3)]">
                                <li><a href="mailto:support@declairo.app" className="hover:text-brand-green-500 transition-colors">support@declairo.app</a></li>
                                <li><Link to="/contact" className="hover:text-brand-green-500 transition-colors">Contact center</Link></li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div className="max-w-7xl mx-auto mt-20 pt-8 border-t border-[var(--border)] text-center text-[var(--text3)] text-xs">
                    © 2026 Declairo. All rights reserved. Not financial advice.
                </div>
            </footer>
        </div>
    );
}
