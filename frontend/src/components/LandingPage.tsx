import React from 'react';
import { HeroSection } from './HeroSection';
import { FeaturesSection } from './FeaturesSection';
import { IntegrationsSection } from './IntegrationsSection';
import { TestimonialsSection } from './TestimonialsSection';
import { FAQSection } from './FAQSection';
import { CTASection } from './CTASection';
import { Link } from 'react-router-dom';

export function LandingPage() {
  return (
    <div className="bg-background">
      {/* Sticky Nav */}
      <nav className="fixed top-0 left-0 right-0 z-[100] flex items-center justify-between px-6 md:px-12 py-4 bg-brand-dark/90 backdrop-blur-xl border-b border-white/5">
        <Link to="/" className="flex items-center gap-2 text-white no-underline font-syne font-extrabold text-xl tracking-tight">
          <img src="/logo.webp" alt="Declairo Logo" className="w-6 h-6 object-contain" />
          Declairo
        </Link>
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-sm font-semibold text-white/60 hover:text-white transition-colors no-underline">Features</a>
          <a href="#integrations" className="text-sm font-semibold text-white/60 hover:text-white transition-colors no-underline">Integrations</a>
          <a href="#faq" className="text-sm font-semibold text-white/60 hover:text-white transition-colors no-underline">FAQ</a>
          <Link to="/contact" className="text-sm font-semibold text-white/60 hover:text-white transition-colors no-underline">Contact</Link>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="text-sm font-bold px-4 py-2 rounded-lg text-white/70 hover:text-white transition-all hidden md:block">Login</Link>
          <Link to="/register" className="bg-brand-green-500 hover:bg-brand-green-600 text-brand-dark text-sm font-bold px-5 py-2.5 rounded-xl shadow-lg shadow-brand-green-600/20 transition-all hover:scale-[1.02]">
            Get started free
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <HeroSection />

      {/* Features */}
      <FeaturesSection />

      {/* Integrations */}
      <IntegrationsSection />

      {/* Testimonials */}
      <TestimonialsSection />

      {/* FAQ */}
      <FAQSection />

      {/* Final CTA */}
      <CTASection />

      {/* Footer */}
      <footer className="bg-brand-dark text-white/50 py-20 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-10">
            <div>
              <h4 className="font-bold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="hover:text-green-400 transition-colors">How It Works</a></li>
                <li><a href="#integrations" className="hover:text-green-400 transition-colors">Integrations</a></li>
                <li><a href="#features" className="hover:text-green-400 transition-colors">Features</a></li>
                <li><a href="#faq" className="hover:text-green-400 transition-colors">FAQ</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Tools</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/login" className="hover:text-green-400 transition-colors">Tax Calculator</Link></li>
                <li><Link to="/login" className="hover:text-green-400 transition-colors">Portfolio Tracker</Link></li>
                <li><Link to="/login" className="hover:text-green-400 transition-colors">P&L Calculator</Link></li>
                <li><Link to="/register" className="hover:text-green-400 transition-colors">Get Started Free</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/contact" className="hover:text-green-400 transition-colors">About Us</Link></li>
                <li><Link to="/contact" className="hover:text-green-400 transition-colors">Contact</Link></li>
                <li><a href="mailto:support@declairo.com" className="hover:text-green-400 transition-colors">Partnerships</a></li>
                <li><a href="mailto:support@declairo.com" className="hover:text-green-400 transition-colors">support@declairo.com</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/terms" className="hover:text-green-400 transition-colors">Terms of Service</Link></li>
                <li><Link to="/privacy" className="hover:text-green-400 transition-colors">Privacy Policy</Link></li>
                <li><Link to="/disclaimer" className="hover:text-green-400 transition-colors">Disclaimer</Link></li>
                <li><Link to="/security" className="hover:text-green-400 transition-colors">Security</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-700 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm">© 2026 Declairo. All rights reserved.</p>
            <div className="flex gap-6 mt-4 md:mt-0">
              <a href="https://twitter.com/declairo" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-green-400 transition-colors">Twitter</a>
              <a href="https://discord.gg/declairo" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-green-400 transition-colors">Discord</a>
              <a href="https://t.me/declairo" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-green-400 transition-colors">Telegram</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
