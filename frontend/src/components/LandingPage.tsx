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
                <li><a href="#features" className="hover:text-green-400">How It Works</a></li>
                <li><a href="#faq" className="hover:text-green-400">Pricing</a></li>
                <li><a href="#features" className="hover:text-green-400">Features</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Tools</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/login" className="hover:text-green-400">Tax Calculator</Link></li>
                <li><Link to="/login" className="hover:text-green-400">Portfolio Tracker</Link></li>
                <li><Link to="/login" className="hover:text-green-400">P&L Calculator</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/contact" className="hover:text-green-400">About</Link></li>
                <li><Link to="/contact" className="hover:text-green-400">Blog</Link></li>
                <li><Link to="/contact" className="hover:text-green-400">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/terms" className="hover:text-green-400">Terms</Link></li>
                <li><Link to="/privacy" className="hover:text-green-400">Privacy</Link></li>
                <li><Link to="/terms" className="hover:text-green-400">Security</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-700 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm">© 2026 Declairo. All rights reserved.</p>
            <div className="flex gap-6 mt-4 md:mt-0">
              <a href="https://twitter.com/declairo" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-green-400">Twitter</a>
              <a href="https://discord.gg/declairo" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-green-400">Discord</a>
              <a href="https://github.com/declairo" target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-green-400">GitHub</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
