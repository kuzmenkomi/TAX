import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, MessageSquare, Send, ChevronLeft, Globe } from 'lucide-react';

export function ContactPage() {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    // Simulate API call
    setTimeout(() => setSubmitted(false), 5000);
  };

  return (
    <div className="min-h-screen flex flex-col transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      {/* Header */}
      <header className="py-6 px-6 md:px-12 border-b" style={{ background: 'var(--nav-bg)', borderColor: 'var(--border)' }}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
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
              <p className="text-sm font-medium mb-4" style={{ color: 'var(--text3)' }}>Email us for technical assistance.</p>
              <a href="mailto:support@declairo.app" className="text-brand-green-500 font-bold hover:underline">support@declairo.app</a>
            </div>

            <div className="p-8 rounded-[2.5rem] shadow-xl border" style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}>
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-6" style={{ background: 'var(--bg2)' }}>
                <Globe className="text-brand-green-500" size={24} />
              </div>
              <h3 className="text-xl font-bold mb-2 tracking-tight" style={{ color: 'var(--text)' }}>Social Hub</h3>
              <p className="text-sm font-medium mb-4" style={{ color: 'var(--text3)' }}>Join our community for updates.</p>
              <div className="flex gap-4">
                <a href="#" className="w-10 h-10 rounded-xl flex items-center justify-center transition-colors" style={{ background: 'var(--bg2)', color: 'var(--text2)' }}>
                  <Send size={18} />
                </a>
                <a href="#" className="w-10 h-10 rounded-xl flex items-center justify-center transition-colors" style={{ background: 'var(--bg2)', color: 'var(--text2)' }}>
                  <MessageSquare size={18} />
                </a>
              </div>
            </div>
            
            <div className="bg-brand-green-500 p-8 rounded-[2.5rem] shadow-2xl shadow-brand-green-500/20 text-brand-dark">
              <h3 className="text-xl font-bold mb-4 tracking-tight">Partnerships</h3>
              <p className="font-medium mb-6 opacity-80">Interested in integrating Declairo in your exchange or wallet?</p>
              <button className="w-full bg-brand-dark text-white py-3 rounded-2xl font-bold text-sm hover:opacity-90 transition-opacity">
                Apply Here
              </button>
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
                <button 
                  type="submit"
                  className="w-full md:w-auto bg-brand-green-500 hover:bg-brand-green-400 text-brand-dark px-12 py-4 rounded-xl font-bold text-sm transition-all shadow-xl shadow-brand-green-500/10 active:scale-95"
                >
                  Send Message
                </button>
              </form>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-12 px-6 border-t text-center text-sm font-medium" style={{ borderColor: 'var(--border)' }}>
        <p style={{ color: 'var(--text3)' }}>© 2026 Declairo. All rights reserved.</p>
      </footer>
    </div>
  );
}
