import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, ArrowRight, ChevronLeft } from 'lucide-react';

export function PrivacyPage() {
  return (
    <div className="min-h-screen flex flex-col transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      {/* Header */}
      <header className="py-6 px-6 md:px-12 border-b" style={{ background: 'var(--nav-bg)', borderColor: 'var(--border)' }}>
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity" style={{ color: 'var(--text)' }}>
            <ChevronLeft size={20} />
            <span className="font-bold text-sm">Back to Home</span>
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-brand-green-500 rounded-xl flex items-center justify-center shadow-lg shadow-brand-green-500/20">
              <span className="text-brand-dark font-black text-sm">L</span>
            </div>
            <span className="font-syne font-extrabold text-xl tracking-tight" style={{ color: 'var(--text)' }}>
              Tax<span className="text-brand-green-500">Flow</span>
            </span>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 py-16 px-6 relative z-10">
        <article className="max-w-3xl mx-auto rounded-[2rem] shadow-2xl border overflow-hidden" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
          <div className="p-10 md:p-16 border-b relative overflow-hidden" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-brand-green-500/5 rounded-full blur-3xl pointer-events-none" />
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6 border" style={{ background: 'var(--bg)', borderColor: 'var(--border)' }}>
              <ShieldCheck className="text-brand-green-500" size={32} />
            </div>
            <h1 className="text-4xl md:text-5xl font-syne font-bold mb-4 tracking-tight" style={{ color: 'var(--text)' }}>Privacy Policy</h1>
            <p className="font-medium leading-relaxed" style={{ color: 'var(--text2)' }}>
              Your data is your shield. Here's how we protect it at Declairo.
            </p>
          </div>

          <div className="p-10 md:p-16 space-y-12">
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-3 font-syne" style={{ color: 'var(--text)' }}>
                <span className="text-brand-green-500">1.</span> Introduction
              </h2>
              <div className="leading-relaxed font-medium space-y-4" style={{ color: 'var(--text2)' }}>
                <p>
                  Welcome to Declairo. We value your privacy and are committed to protecting your personal and financial data. 
                  This Privacy Policy explains how we collect, use, and safeguard your information.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-3 font-syne" style={{ color: 'var(--text)' }}>
                <span className="text-brand-green-500">2.</span> Data We Collect
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="p-6 rounded-2xl border transition-colors" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                  <h3 className="font-bold mb-2 text-sm uppercase tracking-widest" style={{ color: 'var(--text)' }}>Account</h3>
                  <p className="text-xs" style={{ color: 'var(--text3)' }}>Email address and encrypted security tokens.</p>
                </div>
                <div className="p-6 rounded-2xl border transition-colors" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                  <h3 className="font-bold mb-2 text-sm uppercase tracking-widest" style={{ color: 'var(--text)' }}>Financial</h3>
                  <p className="text-xs" style={{ color: 'var(--text3)' }}>Public addresses and transaction history data.</p>
                </div>
                <div className="p-6 rounded-2xl border transition-colors" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
                  <h3 className="font-bold mb-2 text-sm uppercase tracking-widest" style={{ color: 'var(--text)' }}>Technical</h3>
                  <p className="text-xs" style={{ color: 'var(--text3)' }}>Encrypted session logs and usage metadata.</p>
                </div>
              </div>
              <div className="bg-danger/5 border-l-4 border-danger p-6 rounded-r-2xl">
                <p className="text-danger font-black uppercase text-[10px] tracking-widest mb-2">SECURE NOTE</p>
                <p className="font-bold leading-relaxed text-sm" style={{ color: 'var(--text)' }}>
                  We NEVER ask for, collect, or store your Private Keys or Seed Phrases.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-3 font-syne" style={{ color: 'var(--text)' }}>
                <span className="text-brand-green-500">3.</span> Security Measures
              </h2>
              <div className="leading-relaxed font-medium" style={{ color: 'var(--text2)' }}>
                <p>
                  All sensitive communication is encrypted via TLS 1.3, and data is stored using AES-256 standards. 
                  We prioritize your anonymity and minimize data retention where possible.
                </p>
              </div>
            </section>
          </div>

          <div className="p-10 border-t text-center" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
            <p className="text-xs font-medium" style={{ color: 'var(--text3)' }}>
              Last Updated: April 14, 2026 • Declairo Inc.
            </p>
          </div>
        </article>
      </main>

      {/* Footer */}
      <footer className="py-12 px-6 border-t text-center text-sm font-medium" style={{ borderColor: 'var(--border)' }}>
        <p style={{ color: 'var(--text3)' }}>© 2026 Declairo. All rights reserved.</p>
      </footer>
    </div>
  );
}
