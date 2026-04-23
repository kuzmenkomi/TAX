import React, { useState } from 'react';
import { ChevronDown, Plus, Minus } from 'lucide-react';
import { cn } from '../utils/cn';

const faqs = [
  {
    q: 'What is crypto tax software?',
    a: 'Crypto tax software automatically calculates your capital gains, losses, and income from digital asset transactions across all exchanges and wallets. It generates regional-compliant forms (Schedule D, Form 8949, etc.) for your tax return.'
  },
  {
    q: 'Do I need to report crypto gains under $600?',
    a: 'Yes, most jurisdictions require reporting all capital gains regardless of the amount. Thresholds usually only apply to 1099-K reporting from exchanges. Always check your local tax authority guidelines.'
  },
  {
    q: 'Which accounting method should I use?',
    a: 'Common methods include FIFO (First In, First Out), LIFO (Last In, First Out), and Specific Identification. FIFO is generally the most conservative and globally accepted method. You can toggle these in our Control Panel.'
  },
  {
    q: 'Can I import from DeFi and NFT platforms?',
    a: 'Yes! Declairo supports on-chain data from Ethereum, Polygon, Solana, and all major L2s. This includes yield farming, staking rewards, liquidity pool swaps, and NFT trades.'
  },
  {
    q: 'Is my data secure?',
    a: 'Absolutely. We use bank-grade AES-256 encryption. We only request read-only access to your transaction history — we never have access to your private keys or the ability to move funds.'
  },
  {
    q: 'How much does it cost?',
    a: 'Portfolio tracking and transaction monitoring are free. Generation of official tax reports starts at $99/tax year. We also offer institutional enterprise plans for high-volume traders.'
  },
];

export function FAQSection() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div id="faq" className="py-24 px-6 transition-colors duration-300" style={{ background: 'var(--bg)' }}>
      <div className="max-w-4xl mx-auto">
        {/* Header Area */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full bg-brand-green-500/10 border border-brand-green-500/20 text-brand-green-500 text-[10px] font-black uppercase tracking-widest mb-4">
             Intelligence Hub
          </div>
          <h2 className="text-4xl md:text-5xl font-syne font-black mb-6 tracking-tight leading-tight" style={{ color: 'var(--text)' }}>
            Institutional Knowledge Base
          </h2>
          <p className="text-lg font-medium opacity-60 max-w-2xl mx-auto italic" style={{ color: 'var(--text)' }}>
            Everything you need to know about navigating the complexities of digital asset taxation.
          </p>
        </div>

        {/* Accordion Array */}
        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <div
              key={i}
              className={cn(
                "border rounded-[2rem] overflow-hidden transition-all duration-300 shadow-sm",
                open === i ? "shadow-xl scale-[1.01]" : "hover:border-brand-green-500/30"
              )}
              style={{ 
                background: open === i ? 'var(--bg2)' : 'var(--surface)', 
                borderColor: open === i ? 'var(--accent)' : 'var(--border)' 
              }}
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full px-8 py-6 flex items-center justify-between transition-colors text-left"
              >
                <div className="flex items-center gap-6">
                   <span className="text-xs font-black text-brand-green-500 opacity-40 font-mono">0{i+1}</span>
                   <span className="font-bold text-[17px] tracking-tight" style={{ color: 'var(--text)' }}>
                     {faq.q}
                   </span>
                </div>
                <div className={cn(
                  "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
                  open === i ? "bg-brand-green-500 text-brand-dark rotate-180" : "bg-brand-green-500/10 text-brand-green-500"
                )}>
                  {open === i ? <Minus size={20} /> : <Plus size={20} />}
                </div>
              </button>

              <div className={cn(
                "grid transition-all duration-300 ease-in-out",
                open === i ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
              )}>
                <div className="overflow-hidden">
                   <div className="px-8 pb-8 pt-2 pl-20">
                      <p className="text-[15px] leading-relaxed font-medium opacity-70" style={{ color: 'var(--text)' }}>
                        {faq.a}
                      </p>
                   </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
