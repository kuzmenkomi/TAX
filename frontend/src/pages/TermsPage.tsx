import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';

const SECTIONS = [
  { id: 'acceptance', title: 'Acceptance of Terms' },
  { id: 'description', title: 'Description of Service' },
  { id: 'eligibility', title: 'Eligibility' },
  { id: 'account', title: 'Account Registration' },
  { id: 'acceptable-use', title: 'Acceptable Use' },
  { id: 'no-advice', title: 'No Professional Advice' },
  { id: 'subscription', title: 'Subscription & Payment' },
  { id: 'ip', title: 'Intellectual Property' },
  { id: 'third-party', title: 'Third-Party Services' },
  { id: 'disclaimer-warranties', title: 'Disclaimer of Warranties' },
  { id: 'limitation', title: 'Limitation of Liability' },
  { id: 'indemnification', title: 'Indemnification' },
  { id: 'termination', title: 'Termination' },
  { id: 'governing-law', title: 'Governing Law' },
  { id: 'changes', title: 'Changes to Terms' },
  { id: 'contact', title: 'Contact' },
];

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24 pb-10 mb-10 border-b last:border-b-0" style={{ borderColor: 'var(--border)' }}>
      <h2 className="text-xl font-bold mb-4 font-syne" style={{ color: 'var(--text)' }}>{title}</h2>
      <div className="text-sm leading-7 space-y-4" style={{ color: 'var(--text)' }}>
        {children}
      </div>
    </section>
  );
}

function UL({ items }: { items: string[] }) {
  return (
    <ul className="list-disc pl-5 space-y-2">
      {items.map((item, i) => <li key={i}>{item}</li>)}
    </ul>
  );
}

function Bold({ children }: { children: React.ReactNode }) {
  return <strong style={{ color: 'var(--text)' }}>{children}</strong>;
}

export function TermsPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>
      {/* Header */}
      <header className="py-5 px-6 md:px-12 border-b sticky top-0 z-50 backdrop-blur-xl"
        style={{ background: 'var(--nav-bg)', borderColor: 'var(--border)' }}>
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <button onClick={() => navigate(-1)} className="flex items-center gap-2 hover:opacity-80 transition-opacity" style={{ color: 'var(--text)' }}>
            <ChevronLeft size={18} />
            <span className="font-bold text-sm">Back</span>
          </button>
          <div className="flex items-center gap-3">
            <img src="/logo.webp" alt="Declairo" className="w-7 h-7 object-contain" />
            <span className="font-syne font-extrabold text-lg tracking-tight" style={{ color: 'var(--text)' }}>Declairo</span>
          </div>
        </div>
      </header>

      <div className="flex-1 max-w-6xl mx-auto w-full px-6 py-12 flex gap-16">
        {/* Left sidebar */}
        <aside className="hidden lg:block w-56 shrink-0">
          <div className="sticky top-28 space-y-4">
            <p className="text-xs font-bold" style={{ color: 'var(--text)' }}>Last updated: May 8, 2026</p>
            <p className="text-xs leading-relaxed" style={{ color: 'var(--text3)' }}>
              If you have any questions about our Terms of Service or legal matters, please feel free to{' '}
              <Link to="/contact" className="text-brand-green-500 hover:underline">contact us</Link>.
            </p>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          <h1 className="text-4xl font-syne font-bold tracking-tight mb-10" style={{ color: 'var(--text)' }}>
            Declairo Terms of Service
          </h1>

          <Section id="acceptance" title="Acceptance of These Terms of Service">
            <p>Declairo Tecnologia Ltda. ("Declairo," "we," "us," or "our") provides its cryptocurrency tax tracking and reporting services (described below) and related content to you through our website(s) located at declairo.com (the "Site") and through our applications and related technologies ("Apps"), and collectively, such Apps and the Site, including any updates or new features, functionality, and technology (collectively, the "Service"). All access and use of the Service is subject to the terms and conditions contained in these Terms of Service (as amended from time to time, these "Terms of Service" or "ToS"). By accessing, browsing, or otherwise using the Service, or by clicking a button or checking a box marked "I agree," you signify that you have read, understood, and agree to be bound by these Terms of Service and to the collection and use of your information as set forth in the Declairo Privacy Policy, whether or not you are a registered user of our Service.</p>
            <p>Declairo reserves the right to modify these Terms of Service and will provide notice of these changes as described below. These Terms of Service apply to all visitors, users, and others who access the Service ("Users"). PLEASE READ THESE TERMS OF SERVICE CAREFULLY TO ENSURE THAT YOU UNDERSTAND EACH PROVISION. THESE TERMS OF SERVICE CONTAIN A MANDATORY INDIVIDUAL ARBITRATION AND CLASS ACTION/JURY TRIAL WAIVER PROVISION IN THE GOVERNING LAW SECTION BELOW THAT REQUIRES THE USE OF ARBITRATION ON AN INDIVIDUAL BASIS TO RESOLVE DISPUTES, RATHER THAN JURY TRIALS OR CLASS ACTIONS.</p>
            <p><Bold>Important notice:</Bold> Declairo is not a tax advisor, attorney, certified accountant, or financial institution. All outputs, calculations, and AI-generated responses are estimates provided for informational purposes only and do not constitute professional advice. Always consult a licensed <em>contador</em>, <em>asesor fiscal</em>, or qualified tax professional familiar with cryptocurrency regulations in your jurisdiction before filing any tax declaration.</p>
          </Section>

          <Section id="description" title="Description of Service">
            <p>Declairo provides a SaaS platform that helps cryptocurrency holders in Latin America and globally to:</p>
            <UL items={[
              'Aggregate transaction data from blockchain wallets and centralized/decentralized exchanges via read-only connections.',
              'Calculate estimated cryptocurrency capital gains and losses using applicable cost basis methods (FIFO, LIFO, Specific Identification where permitted by local law).',
              'Generate estimated tax liability reports designed to assist in compliance with local regulations, including but not limited to: Brazil\'s Lei nº 14.754/2023 (taxation of crypto assets and overseas income), Instrução Normativa RFB nº 1.888/2019 (mandatory reporting obligations), Instrução Normativa RFB nº 2.180/2024 (updates on crypto reporting), SAT Mexico\'s Ley del Impuesto Sobre la Renta (ISR) as applied to digital assets, Argentina\'s AFIP Resolución General nº 4.614/2019 and Ley 27.743/2024 (Ley Bases provisions on crypto), Colombia\'s DIAN Resolución 000013/2022, and Chile\'s SII Circular nº 28/2022.',
              'Provide AI-assisted tax guidance through an advisory chat interface (informational only — see Section 6).',
              'Export reports in PDF, CSV, and jurisdiction-specific formats for reference when preparing tax declarations.',
            ]} />
            <p>The Service is a data organization and estimation tool. It is explicitly NOT a tax filing service, a tax advice service, or a legal advice service. Declairo does not file tax returns on your behalf and is not responsible for the accuracy of any information you submit to a tax authority.</p>
          </Section>

          <Section id="eligibility" title="Eligibility">
            <p>By using the Service, you represent and warrant that: (a) you are at least 18 years of age and have the legal capacity to enter into binding contracts in your jurisdiction; (b) you are not a person barred from using the Service under the laws of your jurisdiction or any applicable jurisdiction; (c) you are not located in, or a national or resident of, any country subject to comprehensive sanctions administered by OFAC, the UN Security Council, or equivalent bodies; and (d) your use of the Service does not violate any applicable law or regulation.</p>
            <p>If you are using the Service on behalf of a legal entity (e.g., a company or partnership), you represent that you are authorized to bind that entity to these Terms of Service, and references to "you" in these Terms of Service shall refer to both you and that entity.</p>
          </Section>

          <Section id="account" title="Account Registration and Security">
            <p>To access most features of the Service, you must create an account. When you create an account, you agree to: (a) provide accurate, current, and complete information; (b) maintain and promptly update your account information; (c) maintain the security of your account by using a strong, unique password and not sharing your credentials with any third party; (d) promptly notify Declairo of any unauthorized use of your account or any other security breach at support@declairo.com; and (e) take responsibility for all activities that occur under your account, whether or not authorized by you.</p>
            <p>Declairo will not be liable for any loss or damage arising from your failure to comply with these obligations. You may not transfer your account to another party without Declairo's prior written consent.</p>
            <p>We may require additional identity verification for compliance purposes under anti-money laundering (AML) frameworks applicable in Brazil (Lei nº 9.613/1998 as amended by Lei nº 12.683/2012; COAF Resolução nº 36/2021) or equivalent regulations in other LATAM jurisdictions.</p>
          </Section>

          <Section id="acceptable-use" title="Acceptable Use Policy">
            <p>You agree to use the Service only for lawful purposes and in a manner consistent with these Terms of Service. You expressly agree NOT to:</p>
            <UL items={[
              'Use the Service to facilitate, plan, or assist with tax evasion, money laundering, terrorist financing, or any other illegal activity.',
              'Import false, fabricated, or intentionally misleading transaction data in order to generate inaccurate tax reports.',
              'Reverse-engineer, decompile, disassemble, or attempt to derive the source code of the Service or any part thereof.',
              'Use the Service to transmit any unsolicited commercial email (spam), malware, or any other harmful, disruptive, or unauthorized materials.',
              'Access the Service using automated means (bots, scrapers, crawlers) without prior written consent from Declairo.',
              'Circumvent, disable, or interfere with security-related features of the Service, including features that prevent copying, or features that enforce limitations on use.',
              'Impersonate any person or entity, misrepresent your affiliation with any person or entity, or use the Service to mislead any third party.',
              'Resell, sublicense, or commercialize access to the Service or any outputs of the Service without a separate written agreement with Declairo.',
              'Use the Service in any way that could damage, disable, overburden, or impair the Service or its infrastructure.',
              'Attempt to gain unauthorized access to any portion of the Service, other user accounts, or computer systems connected to the Service.',
            ]} />
            <p>Violation of this Acceptable Use Policy may result in immediate suspension or termination of your account, without refund, and may subject you to civil and/or criminal liability.</p>
          </Section>

          <Section id="no-advice" title="No Professional Advice — Important Disclaimer">
            <p className="text-xl font-syne font-bold tracking-tight" style={{ color: 'var(--text)' }}>
              Declairo is not a tax advisor, attorney, certified public accountant (CPA), contador público, assessor tributário, or financial advisor. The Service does not provide tax advice, legal advice, accounting advice, or financial advice.
            </p>
            <p>The information provided through the Service, including all calculations, reports, AI-generated responses, educational content, and other outputs, is for <Bold>informational purposes only</Bold> and does not constitute professional advice of any kind. Specifically:</p>
            <UL items={[
              'All tax calculations are estimates based solely on the transaction data you import and the tax rules programmed into our system at the time of calculation. These rules may not be current, may not reflect recent regulatory guidance or court decisions, and may not account for your individual circumstances.',
              'The AI Fiscal Advisor feature generates responses using a large language model. These responses may be incomplete, inaccurate, or outdated. They do not constitute professional tax or legal advice and should never be relied upon as a substitute for consultation with a qualified human professional.',
              'Declairo is not responsible for any errors, omissions, or inaccuracies in the information provided through the Service, nor for any actions taken or not taken based on such information.',
              'The characterization of any transaction as taxable or non-taxable, the calculation of cost basis, the determination of holding periods, and the classification of income type (capital gain, ordinary income, staking reward, etc.) are all estimates that may differ from the position taken by your national tax authority.',
              'Cryptocurrency tax law in Latin America is rapidly evolving. Rules applicable in Brazil under Lei 14.754/2023 may differ significantly from those in Mexico, Argentina, Colombia, or Chile, and may change at any time without notice to Declairo.',
            ]} />
            <p>You are solely responsible for ensuring that your tax filings are accurate, complete, and compliant with all applicable laws. We strongly recommend that you engage a licensed tax professional familiar with cryptocurrency in your jurisdiction before submitting any tax return.</p>
          </Section>

          <Section id="subscription" title="Subscription Plans and Payment">
            <p><Bold>Free Plan:</Bold> Declairo offers a free tier with limited features. Free plan users may import up to 25 transactions, view estimated portfolio performance, and access a tax preview. Tax report export is not available on the free plan.</p>
            <p><Bold>Paid Plans:</Bold> Paid subscription plans ("Starter," "Trader," "Whale," or as otherwise named) are offered on an annual basis. By subscribing to a paid plan, you authorize Declairo (through its payment processor, Stripe, Inc.) to charge your designated payment method the applicable annual fee on a recurring basis.</p>
            <p><Bold>Pricing:</Bold> Current pricing is available at declairo.com/pricing. Declairo reserves the right to change pricing at any time with at least 30 days' notice to existing subscribers. Price changes will not apply to the current billing period.</p>
            <p><Bold>Billing:</Bold> Your subscription will automatically renew at the end of each billing period unless you cancel prior to the renewal date. You may cancel your subscription at any time through Settings → Subscription, or by contacting support@declairo.com. Cancellation takes effect at the end of the current billing period; you will retain access until that date.</p>
            <p><Bold>Refunds:</Bold> We offer a full refund within 7 days of initial purchase if you have not generated or exported any tax reports. After 7 days, or if you have generated reports, refunds are at Declairo's sole discretion. To request a refund, contact support@declairo.com. Partial refunds for unused portions of annual plans are not available absent extraordinary circumstances.</p>
            <p><Bold>Taxes on Payments:</Bold> All fees are exclusive of applicable taxes (VAT, ISS, PIS/COFINS, or similar). You are responsible for all applicable taxes on payments to Declairo in your jurisdiction.</p>
            <p><Bold>Failed Payments:</Bold> If a payment fails, Declairo will attempt to retry the charge. If payment cannot be collected within 14 days, your account will be downgraded to the free plan and you may lose access to paid features and stored reports.</p>
          </Section>

          <Section id="ip" title="Intellectual Property">
            <p><Bold>Declairo's Intellectual Property:</Bold> All content, design elements, source code, algorithms, trademarks, logos, and trade names included in or made available through the Service are the exclusive property of Declairo or its licensors and are protected by copyright, trademark, and other applicable intellectual property laws. You may not copy, reproduce, modify, distribute, display, or create derivative works from any content from the Service without Declairo's prior written consent.</p>
            <p><Bold>Your Data:</Bold> You retain all ownership rights in the transaction data, wallet addresses, and other data you provide to the Service ("User Data"). By using the Service, you grant Declairo a limited, non-exclusive, worldwide, royalty-free license to process, display, and store your User Data solely for the purpose of providing and improving the Service. This license terminates upon account deletion, subject to retention obligations described in the Privacy Policy.</p>
            <p><Bold>Feedback:</Bold> If you provide Declairo with feedback, suggestions, or ideas about the Service ("Feedback"), you grant Declairo a worldwide, perpetual, irrevocable, royalty-free license to use such Feedback for any purpose, including improving the Service and developing new products, without any obligation to compensate you.</p>
          </Section>

          <Section id="third-party" title="Third-Party Services and Links">
            <p>The Service integrates with third-party services and APIs, including cryptocurrency exchanges (Binance, Coinbase, Bybit, Bitso, Mercado Bitcoin, Ripio, Belo, etc.), blockchain data providers, and price aggregators. Declairo is not responsible for the accuracy, availability, or security of any data provided by these third-party services. Your use of third-party services is governed by those services' own terms of service and privacy policies.</p>
            <p>The Service may contain links to third-party websites or resources. These links are provided for your convenience only. Declairo does not endorse and is not responsible for the content, products, or services on or available from those websites. You access third-party websites at your own risk.</p>
          </Section>

          <Section id="disclaimer-warranties" title="Disclaimer of Warranties">
            <p>THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED. TO THE FULLEST EXTENT PERMITTED BY APPLICABLE LAW, DECLAIRO EXPRESSLY DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:</p>
            <UL items={[
              'Implied warranties of merchantability, fitness for a particular purpose, and non-infringement.',
              'Any warranty that the Service will be uninterrupted, error-free, secure, or free of viruses or other harmful components.',
              'Any warranty that the information provided through the Service, including tax calculations, will be accurate, complete, current, or suitable for any purpose.',
              'Any warranty that defects or errors in the Service will be corrected.',
              'Any warranty that the Service will meet your requirements or expectations.',
            ]} />
            <p>Some jurisdictions do not allow the exclusion of implied warranties, so the above exclusions may not apply to you in full. In such cases, Declairo's warranties are limited to the minimum extent permitted by applicable law.</p>
          </Section>

          <Section id="limitation" title="Limitation of Liability">
            <p>TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, DECLAIRO AND ITS OFFICERS, DIRECTORS, EMPLOYEES, AGENTS, AND LICENSORS SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, PUNITIVE, OR EXEMPLARY DAMAGES, INCLUDING BUT NOT LIMITED TO:</p>
            <UL items={[
              'Fines, penalties, interest, or back taxes assessed by the Receita Federal, SAT, AFIP, DIAN, SII, or any other tax authority as a result of inaccurate or incomplete tax reports generated by the Service.',
              'Financial losses resulting from cryptocurrency trading, investment decisions, or any other financial transactions.',
              'Loss of profits, revenue, data, goodwill, or other intangible losses.',
              'Costs of procuring substitute goods or services.',
              'Unauthorized access to or alteration of your transmissions or data.',
              'Losses arising from service interruptions, server failures, or data loss.',
            ]} />
            <p>IN NO EVENT SHALL DECLAIRO'S AGGREGATE LIABILITY TO YOU FOR ALL CLAIMS ARISING OUT OF OR RELATED TO THESE TERMS OF SERVICE OR THE SERVICE EXCEED THE GREATER OF: (A) THE TOTAL AMOUNT PAID BY YOU TO DECLAIRO IN THE 12 MONTHS IMMEDIATELY PRECEDING THE CLAIM; OR (B) US$100.</p>
            <p>These limitations apply regardless of the theory of liability (contract, tort, negligence, strict liability, or otherwise) and regardless of whether Declairo has been advised of the possibility of such damages. Some jurisdictions do not permit certain limitations of liability, in which case the above limitations will apply to the maximum extent permitted by law.</p>
          </Section>

          <Section id="indemnification" title="Indemnification">
            <p>You agree to defend, indemnify, and hold harmless Declairo and its officers, directors, employees, agents, licensors, and service providers from and against any claims, liabilities, damages, judgments, awards, losses, costs, expenses, or fees (including reasonable attorneys' fees) arising out of or relating to: (a) your violation of these Terms of Service; (b) your User Data or your use of the Service; (c) your violation of any third party's rights, including intellectual property rights; (d) your violation of applicable law; or (e) any tax filings or financial decisions made by you based on information obtained through the Service.</p>
          </Section>

          <Section id="termination" title="Termination">
            <p><Bold>By You:</Bold> You may terminate your account at any time by going to Settings → Account → Delete Account, or by contacting support@declairo.com. Upon termination, your right to use the Service will immediately cease.</p>
            <p><Bold>By Declairo:</Bold> Declairo may suspend or terminate your account and your access to the Service immediately and without notice if: (a) you violate these Terms of Service, particularly the Acceptable Use Policy; (b) we are required to do so by law; (c) we reasonably believe your use of the Service poses a security risk or legal liability; or (d) we decide to discontinue the Service.</p>
            <p><Bold>Effect of Termination:</Bold> Upon termination, all provisions of these Terms of Service that by their nature should survive termination shall survive, including ownership provisions, warranty disclaimers, indemnity, and limitations of liability. Declairo will not be liable to you or any third party for termination of your access to the Service.</p>
          </Section>

          <Section id="governing-law" title="Governing Law and Dispute Resolution">
            <p><Bold>Governing Law:</Bold> These Terms of Service shall be governed by and construed in accordance with the laws of the Federative Republic of Brazil, without regard to its conflict of law provisions, for users based in Brazil. For users in other LATAM jurisdictions, these terms shall be governed by Brazilian law as the law of the country of Declairo's principal operations, to the extent not inconsistent with any mandatory local law protections you may have.</p>
            <p><Bold>For EEA/UK users:</Bold> Nothing in these Terms of Service affects your rights as a consumer under the mandatory laws of your country of residence.</p>
            <p><Bold>Informal Resolution:</Bold> Before initiating any formal dispute resolution, you agree to attempt to resolve any dispute informally by contacting Declairo at support@declairo.com. Declairo will attempt to resolve the dispute within 30 days of receiving written notice.</p>
            <p><Bold>Arbitration:</Bold> If informal resolution fails, any dispute, claim, or controversy arising out of or relating to these Terms of Service or the Service shall be finally settled by binding arbitration administered by the Centro Brasileiro de Mediação e Arbitragem (CBMA) in accordance with its rules, with the seat of arbitration in São Paulo, Brazil, and proceedings conducted in Portuguese (or English by mutual agreement). The arbitration decision shall be final and binding. YOU WAIVE ANY RIGHT TO A JURY TRIAL AND ANY RIGHT TO PARTICIPATE IN A CLASS ACTION LAWSUIT OR CLASS-WIDE ARBITRATION. For users in jurisdictions where mandatory arbitration clauses are prohibited or limited (e.g., certain consumer protection contexts in Brazil under the CDC), you retain all rights to bring claims before the competent courts.</p>
            <p><Bold>Applicable Courts:</Bold> For disputes not subject to arbitration, you consent to the exclusive jurisdiction of the courts of São Paulo, Brazil, except where mandatory local laws give you the right to bring claims in the courts of your country of residence.</p>
          </Section>

          <Section id="changes" title="Changes to These Terms">
            <p>Declairo reserves the right to modify these Terms of Service at any time. We will provide notice of material changes by: (a) posting the new Terms of Service on this page with an updated "Last updated" date; (b) sending an email notification to your registered email address at least 15 days before the effective date of the changes; and (c) displaying a prominent in-app notice. Your continued use of the Service after the effective date of the modified Terms of Service constitutes your acceptance of the modified terms. If you do not agree to the modified terms, you must stop using the Service and may delete your account.</p>
          </Section>

          <Section id="contact" title="Contact">
            <p>If you have any questions about these Terms of Service or the Service itself, please contact us:</p>
            <div className="p-5 rounded-xl border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <p className="font-semibold mb-1" style={{ color: 'var(--text)' }}>Declairo — Legal Contact</p>
              <p>Email: <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a></p>
              <p className="mt-1">Please include "Terms of Service Inquiry" in the subject line.</p>
            </div>
          </Section>

          <div className="mt-6 flex flex-wrap gap-4 text-xs" style={{ color: 'var(--text3)' }}>
            <Link to="/privacy" className="hover:text-brand-green-500 transition-colors">Privacy Policy</Link>
            <Link to="/disclaimer" className="hover:text-brand-green-500 transition-colors">Disclaimer</Link>
            <Link to="/security" className="hover:text-brand-green-500 transition-colors">Security</Link>
            <Link to="/contact" className="hover:text-brand-green-500 transition-colors">Contact</Link>
          </div>
          <p className="text-xs mt-3 mb-8" style={{ color: 'var(--text3)' }}>© 2026 Declairo. All rights reserved.</p>
        </main>
      </div>
    </div>
  );
}
