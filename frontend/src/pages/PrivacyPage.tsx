import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';

const SECTIONS = [
  { id: 'who-we-are', title: 'Who We Are' },
  { id: 'information-collected', title: 'Information We Collect' },
  { id: 'how-we-use', title: 'How We Use Your Information' },
  { id: 'legal-basis', title: 'Legal Basis (LGPD / GDPR)' },
  { id: 'data-sharing', title: 'Data Sharing' },
  { id: 'international', title: 'International Transfers' },
  { id: 'retention', title: 'Data Retention' },
  { id: 'security', title: 'Security' },
  { id: 'your-rights', title: 'Your Rights' },
  { id: 'cookies', title: 'Cookies & Tracking' },
  { id: 'minors', title: 'Minors' },
  { id: 'changes', title: 'Changes to This Policy' },
  { id: 'contact', title: 'Contact Us' },
];

function SideNav({ active }: { active: string }) {
  return (
    <nav className="space-y-1">
      {SECTIONS.map(s => (
        <a
          key={s.id}
          href={`#${s.id}`}
          className="block text-xs py-1 transition-colors hover:text-brand-green-500"
          style={{ color: active === s.id ? 'var(--accent)' : 'var(--text3)' }}
        >
          {s.title}
        </a>
      ))}
    </nav>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24 py-8 border-b last:border-b-0" style={{ borderColor: 'var(--border)' }}>
      <h2 className="text-lg font-bold mb-4 font-syne" style={{ color: 'var(--text)' }}>
        {title}
      </h2>
      <div className="text-sm leading-relaxed space-y-3" style={{ color: 'var(--text)' }}>
        {children}
      </div>
    </section>
  );
}

function P({ children }: { children: React.ReactNode }) {
  return <p>{children}</p>;
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

export function PrivacyPage() {
  const navigate = useNavigate();
  const [active] = useState('');

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
              If you have any questions about our Privacy Policy or information practices, please feel free to{' '}
              <Link to="/contact" className="text-brand-green-500 hover:underline">contact us</Link>.
            </p>
            <p className="text-xs leading-relaxed" style={{ color: 'var(--text3)' }}>
              For more information about our cookie policy, please see our{' '}
              <Link to="/cookie-policy" className="text-brand-green-500 hover:underline">cookie policy page</Link>.
            </p>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          <h1 className="text-4xl font-syne font-bold tracking-tight mb-10" style={{ color: 'var(--text)' }}>
            Declairo Privacy Policy
          </h1>

          <Section id="who-we-are" title="Who We Are">
            <P>Declairo ("Declairo," "we," "us," or "our") is a financial technology company providing a cryptocurrency tax reporting and portfolio tracking platform focused on Latin America. We operate the website declairo.com and all related services, mobile experiences, APIs, and applications (collectively, the "Services").</P>
            <P>Our registered contact for data protection purposes is reachable at <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a>. For users in Brazil, we process your personal data in compliance with the <Bold>Lei Geral de Proteção de Dados (LGPD – Lei nº 13.709/2018)</Bold> and its 2021 enforcement regulations. For users in the European Economic Area or the United Kingdom, the <Bold>General Data Protection Regulation (GDPR – EU 2016/679)</Bold> and the UK GDPR apply.</P>
            <P>This Privacy Policy applies to all visitors, registered users, and anyone who accesses or uses our Services, regardless of their location.</P>
          </Section>

          <Section id="information-collected" title="Information We Collect">
            <P>We collect information you provide directly to us, information generated automatically by your use of our Services, and information we receive from third parties.</P>
            <p className="font-semibold" style={{ color: 'var(--text)' }}>A. Information You Provide Directly</p>
            <UL items={[
              'Account registration data: email address, full name (optional), and password hash (we never store your plain-text password). If you register via Google OAuth, we receive your name, email, and profile picture from Google.',
              'Wallet and exchange data: public blockchain addresses you add, API keys you provide for exchange integrations (stored with AES-256 encryption at rest), and any manual transaction entries.',
              'Identity verification data (if required by applicable law): government-issued ID, proof of address, or tax identification number (CPF in Brazil, RFC in Mexico, CUIT in Argentina), collected only when legally mandated.',
              'Support communications: messages, attachments, and metadata you send to our support team.',
              'Payment information: handled exclusively by Stripe. Declairo does not store card numbers, CVVs, or bank account details. We store only a Stripe customer ID and subscription status.',
              'Survey, feedback, and promotion data: responses to optional surveys or participation in referral programs.',
            ]} />
            <p className="font-semibold mt-4" style={{ color: 'var(--text)' }}>B. Information Generated Automatically</p>
            <UL items={[
              'Log data: IP addresses, browser type and version, operating system, referring URLs, pages visited, timestamps, and session duration.',
              'Device data: device identifiers, screen resolution, language preferences, and time zone.',
              'Usage analytics: features accessed, report generation events, export actions, and error events — used to improve product reliability.',
              'Cookies and similar technologies: session authentication tokens, user preference cookies, and performance measurement cookies (see the Cookies section below for full detail).',
            ]} />
            <p className="font-semibold mt-4" style={{ color: 'var(--text)' }}>C. Information from Third Parties</p>
            <UL items={[
              'Public blockchain data: transaction history and token balances retrieved from public nodes and explorers (Etherscan, Tronscan, BscScan, etc.). This data is publicly available by design.',
              'Exchange APIs: read-only transaction history from cryptocurrency exchanges (Binance, Coinbase, Bitso, Mercado Bitcoin, etc.) via API keys you authorize.',
              'Price data providers: historical and real-time cryptocurrency prices from CoinGecko, CoinMarketCap, and similar services, used to calculate cost basis and gains.',
              'Identity verification services: third-party KYC providers when identity verification is required.',
            ]} />
            <div className="p-4 rounded-xl text-sm font-semibold" style={{ background: 'var(--accent-dim)', color: 'var(--text)' }}>
              🔒 We never ask for, collect, store, or transmit your private keys, seed phrases, wallet passwords, or any credential that would allow us to move or access your funds.
            </div>
          </Section>

          <Section id="how-we-use" title="How We Use Your Information">
            <P>We use the information we collect for the following purposes, always limited to what is necessary and proportionate:</P>
            <UL items={[
              'Providing the Services: creating and managing your account, importing and aggregating transaction data, calculating estimated tax obligations based on your jurisdiction\'s rules (e.g., Receita Federal Instrução Normativa 1888/2019, Lei 14.754/2023 for overseas income, SAT LGSM Mexico, AFIP RG 4614/2019 Argentina), and generating downloadable tax reports.',
              'Tax calculation engine: applying the applicable cost basis methods (FIFO for most LATAM jurisdictions; specific identification where permitted), calculating capital gains, identifying taxable events including DeFi income, staking rewards, NFT disposals, and airdrops.',
              'Customer support: responding to your inquiries, resolving disputes, and troubleshooting technical issues.',
              'Service communications: sending transactional emails such as account verification, password resets, billing receipts, and security alerts. You cannot opt out of strictly necessary transactional messages.',
              'Product improvement: analyzing aggregated usage patterns to identify bugs, improve performance, and develop new features. All analytics data is anonymized or pseudonymized before processing.',
              'Security and fraud prevention: detecting unauthorized access, preventing abuse of our APIs, and protecting the integrity of our platform. We use IP reputation, rate limiting, and behavioral analysis for this purpose.',
              'Legal compliance: fulfilling obligations under applicable law, responding to valid legal requests from governmental authorities, and exercising our legal rights.',
              'Marketing communications (opt-in only): sending product updates, educational content about cryptocurrency taxation, and promotional offers. You may unsubscribe at any time via the link in each email or by contacting support@declairo.com.',
            ]} />
            <P>We do not use your personal data to train third-party AI models. We do not sell, rent, or trade your personal data to any third party for their own marketing purposes.</P>
          </Section>

          <Section id="legal-basis" title="Legal Basis for Processing (LGPD / GDPR)">
            <P>For users in Brazil (LGPD) and the EEA/UK (GDPR), we rely on the following legal bases for processing your personal data:</P>
            <UL items={[
              'Performance of a contract (LGPD Art. 7 V; GDPR Art. 6(1)(b)): Processing your account data and transaction data is necessary to provide the Services you subscribed to.',
              'Legitimate interests (LGPD Art. 7 IX; GDPR Art. 6(1)(f)): We process usage analytics, security logs, and fraud detection data based on our legitimate interest in operating a secure, reliable, and improving service. We conduct balancing tests to ensure our interests do not override your rights.',
              'Legal obligation (LGPD Art. 7 II; GDPR Art. 6(1)(c)): When required by applicable law (e.g., anti-money laundering regulations, requests from the Receita Federal, COAF, or similar authorities).',
              'Consent (LGPD Art. 7 I; GDPR Art. 6(1)(a)): For optional marketing communications and, where applicable, non-essential cookies. You may withdraw consent at any time without affecting the lawfulness of prior processing.',
              'Protection of credit (LGPD Art. 7 X): In limited circumstances related to payment processing and fraud prevention.',
            ]} />
            <P>Brazilian users additionally benefit from all rights guaranteed under the LGPD, including the right to petition the Autoridade Nacional de Proteção de Dados (ANPD), established by Decree nº 10.474/2020 and further regulated by ANPD Resolution CD/ANPD nº 4/2023.</P>
          </Section>

          <Section id="data-sharing" title="Data Sharing and Disclosure">
            <P>We share your personal data only in the following strictly defined circumstances:</P>
            <p className="font-semibold" style={{ color: 'var(--text)' }}>Service Providers (Data Processors)</p>
            <P>We engage trusted third-party companies that process personal data on our behalf under Data Processing Agreements (DPAs) that require them to use data only as instructed by us and to maintain appropriate security measures. These include:</P>
            <UL items={[
              'Cloud infrastructure: Amazon Web Services (AWS) for server hosting and storage.',
              'Transactional email: Brevo (formerly Sendinblue) for sending service emails.',
              'Payment processing: Stripe, Inc. — PCI DSS Level 1 certified, which processes all payment data independently under its own privacy policy.',
              'Analytics: aggregated, anonymized analytics only — no third-party behavioral tracking SDKs with access to identifiable data.',
              'Error monitoring: Sentry for application error tracking (IP and user IDs may be included in error payloads; covered under DPA).',
            ]} />
            <p className="font-semibold mt-4" style={{ color: 'var(--text)' }}>Legal Disclosures</p>
            <P>We may disclose your personal data when required by a valid legal process, including court orders, subpoenas, or requests from governmental authorities (e.g., Receita Federal, Ministério Público, COAF, or equivalent in other LATAM jurisdictions). Where legally permitted, we will notify you before disclosure.</P>
            <p className="font-semibold mt-4" style={{ color: 'var(--text)' }}>Business Transfers</p>
            <P>In the event of a merger, acquisition, reorganization, or sale of all or substantially all of our assets, your personal data may be transferred to the successor entity. We will provide at least 30 days' advance notice via email and prominent in-app notice before your data is subject to any different privacy policy.</P>
            <p className="font-semibold mt-4" style={{ color: 'var(--text)' }}>No Sale of Personal Data</p>
            <P>We do not sell personal data. This includes sales as defined under the California Consumer Privacy Act (CCPA) as amended by the CPRA, the LGPD, and any other applicable data protection law.</P>
          </Section>

          <Section id="international" title="International Data Transfers">
            <P>Declairo operates primarily in Latin America but uses cloud infrastructure located in the United States (AWS us-east-1). When personal data of users located in the EEA, UK, or Brazil is transferred to servers in the United States, we ensure appropriate safeguards are in place:</P>
            <UL items={[
              'Standard Contractual Clauses (SCCs) as adopted by the European Commission (Decision 2021/914) for EEA user data transferred to the US.',
              'International Data Transfer Agreements (IDTAs) for UK users post-Brexit.',
              'Contractual clauses equivalent to those required by LGPD Art. 33 for Brazilian user data, pending finalization of Brazil\'s adequacy framework under ANPD Resolution CD/ANPD nº 19/2024.',
            ]} />
            <P>You may request a copy of the relevant transfer mechanisms by contacting <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a>.</P>
          </Section>

          <Section id="retention" title="Data Retention">
            <P>We retain your personal data for as long as your account is active or as needed to provide the Services, comply with legal obligations, resolve disputes, and enforce agreements.</P>
            <UL items={[
              'Account data: retained for the duration of your account plus 5 years after deletion, as required by Brazilian tax law (Código Tributário Nacional, Art. 173) for potential auditing purposes.',
              'Transaction history: retained for 6 years from the date of each transaction, consistent with the Brazilian statute of limitations (decadencial e prescricional) for tax assessments under CTN Art. 150 and 173.',
              'Support communications: retained for 3 years after case closure.',
              'Marketing data: retained until you withdraw consent or unsubscribe.',
              'Anonymized analytics: retained indefinitely as they cannot be linked to individual users.',
            ]} />
            <P>Upon account deletion, we will delete or irreversibly anonymize your personal data within 30 days, except where longer retention is required by law. You may request deletion at any time through Settings → Account → Delete Account, or by emailing <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a>.</P>
          </Section>

          <Section id="security" title="Security">
            <P>We implement a comprehensive, defense-in-depth security program to protect your personal data:</P>
            <UL items={[
              'Encryption at rest: AES-256 encryption for all databases and stored files, including exchange API keys which are encrypted with a separate key management system.',
              'Encryption in transit: TLS 1.3 enforced for all client-server communications; HSTS headers with a minimum 1-year max-age.',
              'Password security: Bcrypt hashing with a cost factor of 12; passwords are never stored in plain text.',
              'Access controls: principle of least privilege applied to all internal systems; role-based access controls (RBAC) for our engineering and support teams.',
              'Infrastructure security: virtual private cloud (VPC) isolation, Web Application Firewall (WAF), DDoS mitigation, and automated vulnerability scanning.',
              'Security monitoring: centralized logging, real-time anomaly detection, and 24/7 alert systems for suspicious activity.',
              'Incident response: a formal Incident Response Plan (IRP) with defined escalation procedures. In the event of a data breach affecting your data, we will notify you and the relevant supervisory authority (ANPD in Brazil, lead DPA in the EEA) within the timeframes required by applicable law (72 hours under GDPR; within a reasonable period under LGPD Art. 48).',
            ]} />
            <P>No system is completely immune from security threats. We encourage you to use a strong, unique password, enable two-factor authentication when available, and keep your API keys confidential.</P>
          </Section>

          <Section id="your-rights" title="Your Rights">
            <P>Depending on your jurisdiction, you have the following rights regarding your personal data. To exercise any right, contact us at <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a>. We will respond within 30 days (extendable to 60 days for complex requests, with notice).</P>
            <p className="font-semibold" style={{ color: 'var(--text)' }}>Rights under LGPD (Brazilian users — Art. 18)</p>
            <UL items={[
              'Confirmation of the existence of processing.',
              'Access to your personal data.',
              'Correction of incomplete, inaccurate, or outdated data.',
              'Anonymization, blocking, or deletion of unnecessary or excessive data.',
              'Portability to another service provider, upon request, in a machine-readable format.',
              'Deletion of data processed with your consent.',
              'Information about third parties with whom your data has been shared.',
              'Information about the possibility of not providing consent and the consequences thereof.',
              'Revocation of consent at any time.',
              'Review of automated decisions affecting your interests (LGPD Art. 20).',
              'Filing a complaint with the ANPD.',
            ]} />
            <p className="font-semibold mt-4" style={{ color: 'var(--text)' }}>Rights under GDPR (EEA/UK users)</p>
            <UL items={[
              'Right of access (Art. 15).',
              'Right to rectification (Art. 16).',
              'Right to erasure / "right to be forgotten" (Art. 17).',
              'Right to restriction of processing (Art. 18).',
              'Right to data portability (Art. 20).',
              'Right to object to processing based on legitimate interests or direct marketing (Art. 21).',
              'Right not to be subject to solely automated decision-making with legal effects (Art. 22).',
              'Right to lodge a complaint with your national supervisory authority.',
            ]} />
          </Section>

          <Section id="cookies" title="Cookies and Tracking Technologies">
            <P>We use the following categories of cookies and similar technologies:</P>
            <UL items={[
              'Strictly necessary cookies: session authentication tokens (JWT stored in httpOnly cookies) required for you to log in and use the platform. These cannot be disabled without breaking core functionality.',
              'Functional cookies: user preference storage (language, theme selection, dashboard layout). These persist for up to 1 year.',
              'Analytics cookies: we use a self-hosted, privacy-preserving analytics solution. No data is shared with third-party advertising networks. Analytics data is anonymized at collection.',
            ]} />
            <P>We do not use advertising cookies, cross-site tracking pixels, Meta Pixel, Google Ads tags, or any third-party behavioral targeting technology. You can manage cookie preferences through your browser settings. Note that disabling strictly necessary cookies will prevent you from accessing your account.</P>
          </Section>

          <Section id="minors" title="Minors">
            <P>The Services are not directed to individuals under 18 years of age (or the applicable age of majority in your jurisdiction). We do not knowingly collect personal data from minors. If you become aware that a minor has provided us with personal data without parental consent, please contact us at <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a> and we will take steps to delete such information promptly.</P>
          </Section>

          <Section id="changes" title="Changes to This Privacy Policy">
            <P>We may update this Privacy Policy from time to time to reflect changes in our practices, technology, legal requirements, or other factors. When we make material changes, we will:</P>
            <UL items={[
              'Update the "Last updated" date at the top of this page.',
              'Send an email notification to all registered users at least 15 days before the changes take effect.',
              'Display a prominent notice within the Declairo platform.',
              'For changes that significantly affect your rights, we will request your re-consent where required by law.',
            ]} />
            <P>Your continued use of the Services after the effective date constitutes acceptance of the updated Privacy Policy. If you do not agree to the updated terms, you must stop using the Services and may delete your account.</P>
          </Section>

          <Section id="contact" title="Contact Us">
            <P>For any privacy-related questions, requests to exercise your rights, or concerns about our data practices, please contact us:</P>
            <div className="p-5 rounded-xl border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <p className="font-semibold mb-1" style={{ color: 'var(--text)' }}>Declairo — Data Protection Contact</p>
              <p>Email: <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a></p>
              <p className="mt-1">For LGPD requests, please include "LGPD Request" in the subject line.</p>
              <p className="mt-1">For GDPR requests, please include "GDPR Request" in the subject line.</p>
              <p className="mt-1">We aim to respond within 15 business days.</p>
            </div>
            <P>Brazilian users may also submit complaints to the Autoridade Nacional de Proteção de Dados (ANPD) at <a href="https://www.gov.br/anpd" target="_blank" rel="noopener noreferrer" className="text-brand-green-500 hover:underline">www.gov.br/anpd</a>. EEA users may contact their national data protection authority.</P>
          </Section>

          <div className="mt-6 flex flex-wrap gap-4 text-xs" style={{ color: 'var(--text3)' }}>
            <Link to="/terms" className="hover:text-brand-green-500 transition-colors">Terms of Service</Link>
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
