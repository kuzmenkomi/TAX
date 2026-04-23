import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, ShieldAlert, ChevronLeft } from 'lucide-react';

export function TermsPage() {
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
              <FileText className="text-brand-green-500" size={32} />
            </div>
            <h1 className="text-4xl md:text-5xl font-syne font-bold mb-4 tracking-tight" style={{ color: 'var(--text)' }}>Terms of Service</h1>
            <p className="font-medium leading-relaxed" style={{ color: 'var(--text2)' }}>
              Please read these terms carefully before using the Declairo platform.
            </p>
          </div>

          <div className="p-10 md:p-16 space-y-12">
            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-3 font-syne" style={{ color: 'var(--text)' }}>
                <span className="text-brand-green-500">1.</span> Acceptance of Terms
              </h2>
              <div className="leading-relaxed font-medium" style={{ color: 'var(--text2)' }}>
                <p>
                  By creating an account or using the Declairo platform, you agree to be bound by these Terms of Service.
                  If you do not agree to these terms, please do not use our services.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-3 font-syne" style={{ color: 'var(--text)' }}>
                <span className="text-brand-green-500">2.</span> Description of Service
              </h2>
              <div className="leading-relaxed font-medium" style={{ color: 'var(--text2)' }}>
                <p>
                  Declairo provides a software-as-a-service (SaaS) platform for tracking cryptocurrency transactions and estimating
                  potential tax liabilities according to regional regulations (e.g., Brazil, Mexico, Argentina).
                  Our service is a tool for data organization, not a substitute for professional advice.
                </p>
              </div>
            </section>

            <section className="bg-danger/5 border border-danger/20 p-8 rounded-2xl">
              <h2 className="text-2xl font-bold text-danger mb-6 flex items-center gap-3 font-syne">
                <ShieldAlert className="w-8 h-8" />
                3. No Professional Advice
              </h2>
              <div className="space-y-6">
                <div>
                  <h3 className="font-bold mb-2 text-sm uppercase tracking-widest" style={{ color: 'var(--text)' }}>Not a Tax Professional</h3>
                  <p className="leading-relaxed" style={{ color: 'var(--text2)' }}>
                    Declairo is not a law firm, a tax advisor, or a certified public accountant.
                  </p>
                </div>
                <div>
                  <h3 className="font-bold mb-2 text-sm uppercase tracking-widest" style={{ color: 'var(--text)' }}>Estimates Only</h3>
                  <p className="leading-relaxed" style={{ color: 'var(--text2)' }}>
                    All calculations and AI consultant responses are estimates based on the data you provide.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-3 font-syne" style={{ color: 'var(--text)' }}>
                <span className="text-brand-green-500">4.</span> Limitation of Liability
              </h2>
              <div className="leading-relaxed font-medium space-y-4" style={{ color: 'var(--text2)' }}>
                <p>To the maximum extent permitted by law, Declairo shall not be liable for any direct, indirect, incidental, or consequential damages, including but not limited to:</p>
                <ul className="space-y-2 list-disc pl-6">
                  <li>Inaccurate tax calculations due to missing or incorrect data.</li>
                  <li>Financial losses from cryptocurrency trading or investments.</li>
                  <li>Penalties, fines, or interest charges imposed by tax authorities.</li>
                  <li>Losses resulting from unauthorized access to your account due to weak passwords.</li>
                </ul>
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
        <div className="flex justify-center gap-6 mb-4">
          <Link to="/privacy" className="hover:text-brand-green-500 transition-colors" style={{ color: 'var(--text3)' }}>Privacy Policy</Link>
          <Link to="/contact" className="hover:text-brand-green-500 transition-colors" style={{ color: 'var(--text3)' }}>Contact Us</Link>
        </div>
        <p style={{ color: 'var(--text3)' }}>© 2026 Declairo. All rights reserved.</p>
      </footer>
    </div>
  );
};