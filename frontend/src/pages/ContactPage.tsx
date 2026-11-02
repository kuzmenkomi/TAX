import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, MessageSquare, Send, ChevronLeft, Globe, Clock } from 'lucide-react';

export function ContactPage() {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/support/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          message: formData.message,
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || 'Something went wrong. Please try again.');
      }

      setSubmitted(true);
      setFormData({ name: '', email: '', message: '' });
    } catch (err: any) {
      setError(err.message || 'Could not send your message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex flex-col transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      {/* Header */}
      <header className="py-6 px-6 md:px-12 border-b" style={{ background: 'var(--nav-bg)', borderColor: 'var(--border)' }}>
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

      {/* Hero Section */}
      <section className="py-20 px-6 border-b" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-syne font-bold mb-6 tracking-tight" style={{ color: 'var(--text)' }}>How can we help?</h1>
          <p className="text-xl font-medium max-w-2xl mx-auto" style={{ color: 'var(--text2)' }}>
            Our team of engineers and crypto enthusiasts is here to support your journey.
          </p>
        </div>
      </section>

      {/* Main Content */}
      <main className="flex-1 -mt-12 pb-24 px-6">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Contact Info Cards */}
          <div className="lg:col-span-1 space-y-6">
            <div className="p-8 rounded-[2.5rem] shadow-xl border" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-6" style={{ background: 'var(--bg2)' }}>
                <Mail className="text-brand-green-500" size={24} />
              </div>
              <h3 className="text-xl font-bold mb-2 tracking-tight" style={{ color: 'var(--text)' }}>Support</h3>
              <p className="text-sm font-medium mb-2" style={{ color: 'var(--text3)' }}>Email us anytime for technical assistance.</p>
              <a href="mailto:support@declairo.com" className="text-brand-green-500 font-bold hover:underline">support@declairo.com</a>
              <div className="flex items-center gap-2 mt-3" style={{ color: 'var(--text3)' }}>
                <Clock size={14} />
                <span className="text-xs font-medium">Response within 24 hours</span>
              </div>
            </div>

            <div className="p-8 rounded-[2.5rem] shadow-xl border" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-6" style={{ background: 'var(--bg2)' }}>
                <Globe className="text-brand-green-500" size={24} />
              </div>
              <h3 className="text-xl font-bold mb-2 tracking-tight" style={{ color: 'var(--text)' }}>Community</h3>
              <p className="text-sm font-medium mb-4" style={{ color: 'var(--text3)' }}>Join our community for updates and announcements.</p>
              <div className="flex gap-3">
                <a href="https://twitter.com/declairo" target="_blank" rel="noopener noreferrer" className="w-10 h-10 rounded-xl flex items-center justify-center transition-all hover:bg-brand-green-500 hover:text-brand-dark" style={{ background: 'var(--bg2)', color: 'var(--text2)' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.261 5.636 5.903-5.636zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                </a>
                <a href="https://discord.gg/declairo" target="_blank" rel="noopener noreferrer" className="w-10 h-10 rounded-xl flex items-center justify-center transition-all hover:bg-brand-green-500 hover:text-brand-dark" style={{ background: 'var(--bg2)', color: 'var(--text2)' }}>
                  <MessageSquare size={18} />
                </a>
                <a href="https://t.me/declairo" target="_blank" rel="noopener noreferrer" className="w-10 h-10 rounded-xl flex items-center justify-center transition-all hover:bg-brand-green-500 hover:text-brand-dark" style={{ background: 'var(--bg2)', color: 'var(--text2)' }}>
                  <Send size={18} />
                </a>
              </div>
            </div>
            
            <div className="bg-brand-green-500 p-8 rounded-[2.5rem] shadow-2xl shadow-brand-green-500/20 text-brand-dark">
              <h3 className="text-xl font-bold mb-2 tracking-tight">Partnerships</h3>
              <p className="font-medium mb-2 opacity-80 text-sm">Interested in integrating Declairo into your exchange, wallet, or platform?</p>
              <a href="mailto:support@declairo.com" className="block text-brand-dark/70 text-xs font-bold mb-6 hover:text-brand-dark transition-colors">support@declairo.com</a>
              <a href="mailto:support@declairo.com" className="w-full block text-center bg-brand-dark text-white py-3 rounded-2xl font-bold text-sm hover:opacity-90 transition-opacity">
                Apply Here
              </a>
            </div>
          </div>

          {/* Contact Form */}
          <div className="lg:col-span-2 rounded-[3rem] shadow-2xl border p-10 md:p-16" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
            <h2 className="text-3xl font-bold mb-8 tracking-tight" style={{ color: 'var(--text)' }}>Send us a message</h2>
            
            {submitted ? (
              <div className="p-10 rounded-[2rem] text-center" style={{ background: 'var(--bg2)' }}>
                <div className="w-16 h-16 bg-brand-green-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-brand-green-500/20">
                  <Send className="text-brand-dark" size={32} />
                </div>
                <h3 className="text-2xl font-bold mb-2 tracking-tight" style={{ color: 'var(--text)' }}>Message Sent!</h3>
                <p style={{ color: 'var(--text2)' }}>We'll get back to you within 24 hours.</p>
                <button 
                  onClick={() => setSubmitted(false)}
                  className="mt-8 text-brand-green-500 font-bold hover:underline"
                >
                  Send another message
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-widest pl-1" style={{ color: 'var(--text3)' }}>Full Name</label>
                    <input 
                      type="text" 
                      required
                      placeholder="Jane Doe"
                      className="w-full px-6 py-4 rounded-2xl border outline-none transition-all font-medium focus:border-brand-green-500"
                      style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold uppercase tracking-widest pl-1" style={{ color: 'var(--text3)' }}>Email Address</label>
                    <input 
                      type="email" 
                      required
                      placeholder="jane@example.com"
                      className="w-full px-6 py-4 rounded-2xl border outline-none transition-all font-medium focus:border-brand-green-500"
                      style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold uppercase tracking-widest pl-1" style={{ color: 'var(--text3)' }}>Message</label>
                  <textarea 
                    required
                    rows={6}
                    placeholder="Tell us what you need..."
                    className="w-full px-6 py-4 rounded-2xl border outline-none transition-all font-medium resize-none focus:border-brand-green-500"
                    style={{ background: 'var(--bg2)', borderColor: 'var(--border)', color: 'var(--text)' }}
                    value={formData.message}
                    onChange={(e) => setFormData({...formData, message: e.target.value})}
                  ></textarea>
                </div>
                {error && (
                  <div className="px-5 py-4 rounded-2xl border border-red-500/30 bg-red-500/10 text-red-500 text-sm font-medium">
                    ⚠️ {error}
                  </div>
                )}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full md:w-auto bg-brand-green-500 hover:bg-brand-green-400 text-brand-dark px-12 py-4 rounded-xl font-bold text-sm transition-all shadow-xl shadow-brand-green-500/10 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-3"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      Sending...
                    </>
                  ) : (
                    'Send Message'
                  )}
                </button>
              </form>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-12 px-6 border-t text-center text-sm font-medium" style={{ borderColor: 'var(--border)' }}>
        <p style={{ color: 'var(--text3)' }}>© 2026 Declairo. All rights reserved. · <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a></p>
      </footer>
    </div>
  );
}
