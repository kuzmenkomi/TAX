import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ChevronLeft, ShieldCheck, Lock, Eye, Server, KeyRound,
  Globe, AlertTriangle, CheckCircle, FileText, Mail
} from 'lucide-react';

const pillars = [
  {
    icon: KeyRound,
    title: 'AES-256 Encryption',
    desc: 'All sensitive data — including API keys, wallet addresses, and personal information — is encrypted at rest using AES-256, the same standard used by banks and governments worldwide.',
    accent: 'var(--accent)',
  },
  {
    icon: Lock,
    title: 'TLS 1.3 in Transit',
    desc: 'Every byte transmitted between your browser and our servers is protected by TLS 1.3. All HTTP traffic is automatically redirected to HTTPS with strict HSTS headers.',
    accent: '#0077ff',
  },
  {
    icon: Eye,
    title: 'Read-Only Access Only',
    desc: 'We only ever request read-only API permissions from exchanges. Declairo is physically incapable of moving, trading, or withdrawing any of your funds.',
    accent: '#a78bfa',
  },
  {
    icon: Server,
    title: 'Isolated Infrastructure',
    desc: 'Our backend runs in isolated, containerized environments with strict network segmentation. Each service communicates only with its authorized peers.',
    accent: '#f59e0b',
  },
  {
    icon: ShieldCheck,
    title: 'Zero Private Key Storage',
    desc: 'We never ask for, store, or transmit your seed phrases or private keys. Our system operates entirely on public blockchain data and exchange read APIs.',
    accent: 'var(--accent)',
  },
  {
    icon: Globe,
    title: 'GDPR & LGPD Compliant',
    desc: 'Declairo is fully compliant with GDPR (EU), LGPD (Brazil), and other regional data protection regulations. You can request data deletion at any time.',
    accent: '#0077ff',
  },
];

const practices = [
  { text: 'Passwords hashed with bcrypt (cost factor 12)' },
  { text: 'JWT tokens with short expiry and secure rotation' },
  { text: 'Rate limiting on all authentication endpoints' },
  { text: 'SQL injection protection via parameterized queries' },
  { text: 'XSS protection with Content-Security-Policy headers' },
  { text: 'CSRF protection on all state-modifying requests' },
  { text: 'Secrets managed via environment variables — never in code' },
  { text: 'Automated dependency vulnerability scanning (Dependabot)' },
  { text: 'Regular penetration testing by third-party security firms' },
  { text: 'Audit logs for all sensitive actions in the platform' },
];

const faqs = [
  {
    q: 'Can Declairo access my funds or make trades on my behalf?',
    a: 'No. We only request read-only API scopes from exchanges. Even if our systems were fully compromised, an attacker could not initiate any transactions. This is a hard technical constraint, not just a policy.',
  },
  {
    q: 'Do you store my private keys or seed phrases?',
    a: 'Absolutely not. Declairo is a tax reporting tool that works with transaction history data. We never ask for, collect, or store private keys or seed phrases. If any product asks you for this, it is a scam.',
  },
  {
    q: 'Where is my data stored?',
    a: 'User data is stored in encrypted databases within isolated cloud environments. We use reputable infrastructure providers with SOC 2 Type II certifications and enforce strict access controls internally.',
  },
  {
    q: 'How do you handle a security breach?',
    a: 'We have an incident response plan in place. In the event of a confirmed breach, we will notify affected users within 72 hours, describe the scope of impact, and outline remediation steps — in compliance with GDPR and LGPD notification requirements.',
  },
  {
    q: 'Can I delete my data?',
    a: 'Yes. You can request complete deletion of your account and all associated data at any time by emailing support@declairo.com. We will process the request within 30 days.',
  },
];

export function SecurityPage() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex flex-col transition-colors duration-300" style={{ background: 'var(--bg)' }}>

      {/* Header */}
      <header className="py-6 px-6 md:px-12 border-b sticky top-0 z-50 backdrop-blur-xl" style={{ background: 'var(--nav-bg)', borderColor: 'var(--border)' }}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <button onClick={() => navigate(-1)} className="flex items-center gap-2 hover:opacity-80 transition-opacity" style={{ color: 'var(--text)' }}>
            <ChevronLeft size={20} />
            <span className="font-bold text-sm">Back</span>
          </button>
          <div className="flex items-center gap-3">
            <img src="/logo.webp" alt="Declairo Logo" className="w-8 h-8 object-contain" />
            <span className="font-syne font-extrabold text-xl tracking-tight" style={{ color: 'var(--text)' }}>
              Declairo
            </span>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative py-24 px-6 overflow-hidden border-b" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-[-80px] right-[-80px] w-[400px] h-[400px] rounded-full bg-brand-green-500/10 blur-[100px]" />
          <div className="absolute bottom-[-60px] left-[-60px] w-[300px] h-[300px] rounded-full bg-brand-blue-500/10 blur-[80px]" />
        </div>
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-black uppercase tracking-widest mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-green-500 animate-pulse" />
            Security First
          </div>
          <h1 className="text-5xl md:text-7xl font-syne font-bold mb-6 tracking-tight" style={{ color: 'var(--text)' }}>
            Your data is safe<br />
            <span className="text-brand-green-500">with Declairo</span>
          </h1>
          <p className="text-xl font-medium max-w-2xl mx-auto leading-relaxed" style={{ color: 'var(--text)' }}>
            We built Declairo with security as a first principle, not an afterthought. Here's exactly how we protect your financial data.
          </p>
        </div>
      </section>

      <main className="flex-1 pb-24 px-6">
        <div className="max-w-6xl mx-auto">

          {/* Core Pillars */}
          <section className="py-20">
            <div className="text-center mb-16">
              <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-black uppercase tracking-widest mb-4">
                Core Principles
              </div>
              <h2 className="text-4xl md:text-5xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>
                Six pillars of security
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {pillars.map((p, i) => {
                const Icon = p.icon;
                return (
                  <div
                    key={i}
                    className="group relative p-8 rounded-[2rem] border transition-all duration-500 hover:shadow-2xl hover:-translate-y-1 overflow-hidden"
                    style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
                  >
                    <div className="absolute top-0 right-0 w-32 h-32 rounded-full blur-3xl opacity-0 group-hover:opacity-10 transition-opacity duration-700" style={{ background: p.accent }} />
                    <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6 border transition-all duration-300 group-hover:scale-110" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                      <Icon size={26} style={{ color: p.accent }} />
                    </div>
                    <h3 className="text-lg font-bold mb-3 tracking-tight" style={{ color: 'var(--text)' }}>{p.title}</h3>
                    <p className="text-sm font-medium leading-relaxed" style={{ color: 'var(--text)' }}>{p.desc}</p>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Read-Only Banner */}
          <section className="rounded-[2.5rem] overflow-hidden border mb-20" style={{ borderColor: 'var(--border)' }}>
            <div className="bg-brand-green-500 p-12 md:p-16 text-brand-dark">
              <div className="max-w-3xl">
                <div className="inline-flex items-center gap-2 bg-black/10 px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest mb-6">
                  <Lock size={12} />
                  Hard Technical Guarantee
                </div>
                <h2 className="text-3xl md:text-4xl font-syne font-bold mb-4 tracking-tight">
                  We can never move your money
                </h2>
                <p className="text-lg font-medium opacity-80 leading-relaxed">
                  Declairo connects to your exchanges using <strong>read-only API keys</strong>. This means we can only see your transaction history — we are technically incapable of placing orders, withdrawing funds, or making any changes to your account. Even in the worst case scenario, your assets remain 100% safe.
                </p>
              </div>
            </div>
            <div className="p-10 md:p-12 grid grid-cols-1 md:grid-cols-3 gap-8" style={{ background: 'var(--surface)' }}>
              {[
                { icon: Eye, label: 'Read transaction history', allowed: true },
                { icon: CheckCircle, label: 'Calculate your tax liability', allowed: true },
                { icon: FileText, label: 'Generate tax reports', allowed: true },
                { icon: AlertTriangle, label: 'Place trades or orders', allowed: false },
                { icon: AlertTriangle, label: 'Withdraw or transfer funds', allowed: false },
                { icon: AlertTriangle, label: 'Modify account settings', allowed: false },
              ].map((item, i) => {
                const Icon = item.icon;
                return (
                  <div key={i} className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${item.allowed ? 'bg-brand-green-500/10' : 'bg-red-500/10'}`}>
                      <Icon size={18} className={item.allowed ? 'text-brand-green-500' : 'text-red-500'} />
                    </div>
                    <span className={`text-sm font-semibold ${item.allowed ? '' : 'line-through opacity-50'}`} style={{ color: 'var(--text)' }}>
                      {item.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Security Practices */}
          <section className="mb-20">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
              <div>
                <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-black uppercase tracking-widest mb-6">
                  Security Practices
                </div>
                <h2 className="text-3xl md:text-4xl font-syne font-bold mb-4 tracking-tight" style={{ color: 'var(--text)' }}>
                  What we do to keep you safe
                </h2>
                <p className="text-base font-medium leading-relaxed" style={{ color: 'var(--text)' }}>
                  Security at Declairo is a continuous process. Our engineering team applies industry-leading practices across every layer of our stack.
                </p>
              </div>
              <div className="space-y-3">
                {practices.map((p, i) => (
                  <div key={i} className="flex items-start gap-4 p-4 rounded-2xl border transition-all hover:border-brand-green-500/30" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                    <div className="w-6 h-6 rounded-lg bg-brand-green-500/10 flex items-center justify-center shrink-0 mt-0.5">
                      <CheckCircle size={14} className="text-brand-green-500" />
                    </div>
                    <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>{p.text}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Vulnerability Disclosure */}
          <section className="mb-20 p-10 md:p-12 rounded-[2rem] border" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <div className="flex flex-col md:flex-row items-start gap-8">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center shrink-0 border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                <AlertTriangle size={28} className="text-brand-green-500" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-syne font-bold mb-3 tracking-tight" style={{ color: 'var(--text)' }}>
                  Responsible Disclosure
                </h2>
                <p className="text-base font-medium leading-relaxed mb-6" style={{ color: 'var(--text)' }}>
                  If you discover a security vulnerability in Declairo, please report it responsibly. We take all security reports seriously and will investigate promptly. Do not publicly disclose the vulnerability before we have had a chance to address it.
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <a
                    href="mailto:support@declairo.com"
                    className="inline-flex items-center gap-3 bg-brand-green-500 text-brand-dark px-6 py-3 rounded-xl font-bold text-sm hover:bg-brand-green-400 transition-all"
                  >
                    <Mail size={16} />
                    support@declairo.com
                  </a>
                  <div className="flex items-center gap-3 px-6 py-3 rounded-xl border text-sm font-medium" style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>
                    <CheckCircle size={16} className="text-brand-green-500" />
                    We respond within 48 hours
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* FAQ */}
          <section className="mb-20">
            <div className="text-center mb-12">
              <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-black uppercase tracking-widest mb-4">
                Security FAQ
              </div>
              <h2 className="text-3xl md:text-4xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>
                Common questions
              </h2>
            </div>
            <div className="space-y-4 max-w-4xl mx-auto">
              {faqs.map((faq, i) => (
                <div key={i} className="p-8 rounded-[1.5rem] border" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
                  <h3 className="text-base font-bold mb-3 tracking-tight" style={{ color: 'var(--text)' }}>
                    <span className="text-brand-green-500 font-mono text-sm mr-3">0{i + 1}</span>
                    {faq.q}
                  </h3>
                  <p className="text-sm font-medium leading-relaxed pl-8" style={{ color: 'var(--text)' }}>{faq.a}</p>
                </div>
              ))}
            </div>
          </section>

          {/* CTA */}
          <section className="text-center py-16 border-t" style={{ borderColor: 'var(--border)' }}>
            <ShieldCheck size={40} className="text-brand-green-500 mx-auto mb-6" />
            <h2 className="text-3xl font-syne font-bold mb-4 tracking-tight" style={{ color: 'var(--text)' }}>
              Still have security questions?
            </h2>
            <p className="text-base font-medium mb-8 max-w-xl mx-auto" style={{ color: 'var(--text)' }}>
              Our team is happy to answer any questions about our security architecture, data practices, or compliance posture.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/contact"
                className="inline-flex items-center gap-2 bg-brand-green-500 hover:bg-brand-green-400 text-brand-dark px-8 py-4 rounded-xl font-bold text-sm transition-all"
              >
                <Mail size={16} />
                Contact our team
              </Link>
              <Link
                to="/privacy"
                className="inline-flex items-center gap-2 px-8 py-4 rounded-xl font-bold text-sm border transition-all hover:border-brand-green-500/40"
                style={{ borderColor: 'var(--border)', color: 'var(--text)' }}
              >
                <FileText size={16} />
                Read our Privacy Policy
              </Link>
            </div>
          </section>

        </div>
      </main>

      {/* Footer */}
      <footer className="py-12 px-6 border-t text-center text-sm font-medium" style={{ borderColor: 'var(--border)' }}>
        <p style={{ color: 'var(--text3)' }}>
          © 2026 Declairo. All rights reserved. ·{' '}
          <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a>
        </p>
      </footer>
    </div>
  );
}
