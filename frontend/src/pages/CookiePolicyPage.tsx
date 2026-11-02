import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';

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

function UL({ items }: { items: React.ReactNode[] }) {
  return (
    <ul className="list-disc pl-5 space-y-2">
      {items.map((item, i) => <li key={i}>{item}</li>)}
    </ul>
  );
}

function Bold({ children }: { children: React.ReactNode }) {
  return <strong style={{ color: 'var(--text)' }}>{children}</strong>;
}

export function CookiePolicyPage() {
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
              If you have any questions about our Cookie Policy or data practices, please feel free to{' '}
              <Link to="/contact" className="text-brand-green-500 hover:underline">contact us</Link>.
            </p>
            <div className="pt-4 border-t space-y-2 text-xs" style={{ borderColor: 'var(--border)' }}>
              <Link to="/privacy" className="block hover:text-brand-green-500 transition-colors" style={{ color: 'var(--text3)' }}>Privacy Policy</Link>
              <Link to="/terms" className="block hover:text-brand-green-500 transition-colors" style={{ color: 'var(--text3)' }}>Terms of Service</Link>
              <Link to="/disclaimer" className="block hover:text-brand-green-500 transition-colors" style={{ color: 'var(--text3)' }}>Disclaimer</Link>
              <Link to="/security" className="block hover:text-brand-green-500 transition-colors" style={{ color: 'var(--text3)' }}>Security</Link>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          <h1 className="text-4xl font-syne font-bold tracking-tight mb-10" style={{ color: 'var(--text)' }}>
            Declairo Cookie Policy
          </h1>

          <Section id="what-are-cookies" title="What Are Cookies?">
            <p>Cookies are small text files that are placed on your computer, smartphone, or other device when you visit a website. They are widely used by website operators to make websites work efficiently, to improve user experience, and to provide reporting information. Cookies set by the website operator (in this case, Declairo) are called "first-party cookies." Cookies set by parties other than the website operator are called "third-party cookies." Third-party cookies enable third-party features or functionality to be provided through or on the website (e.g., embedded analytics or payment processors).</p>
            <p>This Cookie Policy explains what cookies and similar tracking technologies Declairo uses, why we use them, and your rights to control their use. This policy should be read alongside our <Link to="/privacy" className="text-brand-green-500 hover:underline">Privacy Policy</Link>, which provides broader information about how we collect and process personal data.</p>
          </Section>

          <Section id="why-we-use" title="Why We Use Cookies">
            <p>Declairo uses cookies and similar technologies for the following purposes:</p>
            <UL items={[
              <><Bold>Authentication and security:</Bold> To keep you logged in securely between page navigations, to detect and prevent fraudulent account access, and to remember your session state.</>,
              <><Bold>Functionality and preferences:</Bold> To remember your settings and preferences such as your chosen display language, UI theme (light or dark), and dashboard layout, so you do not need to re-configure these on each visit.</>,
              <><Bold>Performance and analytics:</Bold> To understand how users interact with our Service, which pages are visited most frequently, where errors occur, and how we can improve the platform. We use privacy-preserving analytics that do not share data with advertising networks.</>,
              <><Bold>Security and fraud prevention:</Bold> To help protect against cross-site request forgery (CSRF), session hijacking, and other security threats by associating requests with authenticated sessions.</>,
            ]} />
            <p>We do <Bold>not</Bold> use cookies for advertising, behavioral profiling, cross-site tracking, retargeting, or any other purpose that would share your data with advertising platforms such as Meta, Google Ads, or programmatic ad networks.</p>
          </Section>

          <Section id="types" title="Types of Cookies We Use">
            <p className="font-semibold" style={{ color: 'var(--text)' }}>1. Strictly Necessary Cookies</p>
            <p>These cookies are essential for the Declairo platform to function and cannot be switched off in our systems. They are usually only set in response to actions you take, such as logging in, setting your preferences, or completing a form. Without these cookies, core services such as account authentication, session management, and security cannot be provided.</p>
            <div className="overflow-x-auto mt-3">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th className="text-left py-2 pr-4 font-bold" style={{ color: 'var(--text)' }}>Cookie Name</th>
                    <th className="text-left py-2 pr-4 font-bold" style={{ color: 'var(--text)' }}>Purpose</th>
                    <th className="text-left py-2 pr-4 font-bold" style={{ color: 'var(--text)' }}>Duration</th>
                    <th className="text-left py-2 font-bold" style={{ color: 'var(--text)' }}>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: 'auth_session', purpose: 'Stores an encrypted authentication token (JWT) to keep you logged in across page navigations.', duration: 'Session / 30 days (if "Remember me" selected)', type: 'First-party, httpOnly, Secure' },
                    { name: 'csrf_token', purpose: 'Cross-Site Request Forgery protection token. Validates that form submissions originate from the Declairo platform.', duration: 'Session', type: 'First-party, Secure' },
                    { name: 'declairo_theme', purpose: 'Stores your UI theme preference (light or dark mode).', duration: '1 year', type: 'First-party' },
                    { name: 'declairo_lang', purpose: 'Stores your selected language preference (e.g., pt-BR, es, en).', duration: '1 year', type: 'First-party' },
                  ].map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td className="py-3 pr-4 font-mono text-brand-green-500">{row.name}</td>
                      <td className="py-3 pr-4" style={{ color: 'var(--text2)' }}>{row.purpose}</td>
                      <td className="py-3 pr-4 whitespace-nowrap" style={{ color: 'var(--text2)' }}>{row.duration}</td>
                      <td className="py-3" style={{ color: 'var(--text2)' }}>{row.type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="font-semibold mt-6" style={{ color: 'var(--text)' }}>2. Functional Cookies</p>
            <p>These cookies allow us to remember choices you make and provide enhanced, more personalized features. They may be set by us or by third-party providers whose services we have added to our pages. If you disable these cookies, some or all of these features may not function properly.</p>
            <div className="overflow-x-auto mt-3">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th className="text-left py-2 pr-4 font-bold" style={{ color: 'var(--text)' }}>Cookie Name</th>
                    <th className="text-left py-2 pr-4 font-bold" style={{ color: 'var(--text)' }}>Purpose</th>
                    <th className="text-left py-2 pr-4 font-bold" style={{ color: 'var(--text)' }}>Duration</th>
                    <th className="text-left py-2 font-bold" style={{ color: 'var(--text)' }}>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: 'declairo_dashboard_layout', purpose: 'Stores your dashboard layout and widget configuration preferences.', duration: '6 months', type: 'First-party' },
                    { name: 'declairo_onboarding_step', purpose: 'Tracks your onboarding progress to resume from where you left off.', duration: '30 days', type: 'First-party' },
                  ].map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td className="py-3 pr-4 font-mono text-brand-green-500">{row.name}</td>
                      <td className="py-3 pr-4" style={{ color: 'var(--text2)' }}>{row.purpose}</td>
                      <td className="py-3 pr-4 whitespace-nowrap" style={{ color: 'var(--text2)' }}>{row.duration}</td>
                      <td className="py-3" style={{ color: 'var(--text2)' }}>{row.type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="font-semibold mt-6" style={{ color: 'var(--text)' }}>3. Analytics Cookies</p>
            <p>We use privacy-preserving analytics to understand how users interact with the Service. Our analytics solution is self-hosted and does not share any identifiable data with third-party advertising networks. The analytics data collected is aggregated and anonymized before processing.</p>
            <div className="overflow-x-auto mt-3">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th className="text-left py-2 pr-4 font-bold" style={{ color: 'var(--text)' }}>Cookie Name</th>
                    <th className="text-left py-2 pr-4 font-bold" style={{ color: 'var(--text)' }}>Purpose</th>
                    <th className="text-left py-2 pr-4 font-bold" style={{ color: 'var(--text)' }}>Duration</th>
                    <th className="text-left py-2 font-bold" style={{ color: 'var(--text)' }}>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: '_declairo_analytics', purpose: 'Anonymized session identifier used to understand usage patterns and page performance. IP addresses are anonymized before storage.', duration: '13 months', type: 'First-party, anonymized' },
                  ].map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td className="py-3 pr-4 font-mono text-brand-green-500">{row.name}</td>
                      <td className="py-3 pr-4" style={{ color: 'var(--text2)' }}>{row.purpose}</td>
                      <td className="py-3 pr-4 whitespace-nowrap" style={{ color: 'var(--text2)' }}>{row.duration}</td>
                      <td className="py-3" style={{ color: 'var(--text2)' }}>{row.type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="font-semibold mt-6" style={{ color: 'var(--text)' }}>4. Payment Processor Cookies (Third-Party)</p>
            <p>When you access the subscription or billing section of the Service, cookies may be set by Stripe, Inc., our payment processor. These cookies are governed by <a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer" className="text-brand-green-500 hover:underline">Stripe's Privacy Policy</a>. Stripe is PCI DSS Level 1 certified. We do not have access to or control over the cookies set by Stripe.</p>
          </Section>

          <Section id="similar-technologies" title="Similar Tracking Technologies">
            <p>In addition to cookies, we may use the following similar technologies:</p>
            <UL items={[
              <><Bold>Local Storage and Session Storage:</Bold> Browser-based storage mechanisms used to store user interface preferences (e.g., sidebar collapsed state, active tab) locally on your device. This data is not transmitted to our servers and is cleared when you clear your browser data.</>,
              <><Bold>HttpOnly and Secure flags:</Bold> Our authentication cookies use the <code className="text-xs bg-[var(--bg2)] px-1 rounded">HttpOnly</code> flag to prevent JavaScript access (protecting against XSS attacks) and the <code className="text-xs bg-[var(--bg2)] px-1 rounded">Secure</code> flag to ensure transmission only over HTTPS.</>,
              <><Bold>SameSite attribute:</Bold> Our session cookies use the <code className="text-xs bg-[var(--bg2)] px-1 rounded">SameSite=Strict</code> or <code className="text-xs bg-[var(--bg2)] px-1 rounded">SameSite=Lax</code> attribute to help prevent cross-site request forgery (CSRF) attacks.</>,
            ]} />
            <p>We do not use browser fingerprinting, pixel tags, web beacons, or any form of cross-site tracking technology for advertising purposes.</p>
          </Section>

          <Section id="legal-basis" title="Legal Basis for Cookie Processing">
            <p>The legal basis for our use of cookies depends on the category of cookie and your jurisdiction:</p>
            <UL items={[
              <><Bold>Strictly necessary cookies:</Bold> Processed on the basis of our legitimate interest in providing a functional and secure service (LGPD Art. 7(IX); GDPR Art. 6(1)(f)), and as necessary for the performance of our contract with you (LGPD Art. 7(V); GDPR Art. 6(1)(b)). These cookies do not require your consent.</>,
              <><Bold>Functional and analytics cookies:</Bold> Processed on the basis of your consent (LGPD Art. 7(I); GDPR Art. 6(1)(a)). You may withdraw this consent at any time by adjusting your browser settings or by contacting us.</>,
              <><Bold>Third-party payment cookies (Stripe):</Bold> Processed under Stripe's own legal basis as an independent data controller. We recommend reviewing <a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer" className="text-brand-green-500 hover:underline">Stripe's Privacy Policy</a> for details.</>,
            ]} />
          </Section>

          <Section id="your-choices" title="Your Cookie Choices and Controls">
            <p>You have the following options to control the use of cookies:</p>
            <p className="font-semibold" style={{ color: 'var(--text)' }}>Browser Settings</p>
            <p>Most web browsers allow you to control cookies through their settings. You can typically set your browser to: refuse all cookies; accept only first-party cookies; delete cookies when you close your browser; or notify you when a cookie is being set. Please note that disabling strictly necessary cookies will prevent you from logging in to and using the Declairo platform.</p>
            <p>For instructions on managing cookies in your specific browser:</p>
            <UL items={[
              <><a href="https://support.google.com/chrome/answer/95647" target="_blank" rel="noopener noreferrer" className="text-brand-green-500 hover:underline">Google Chrome</a></>,
              <><a href="https://support.mozilla.org/en-US/kb/enable-and-disable-cookies-website-preferences" target="_blank" rel="noopener noreferrer" className="text-brand-green-500 hover:underline">Mozilla Firefox</a></>,
              <><a href="https://support.apple.com/guide/safari/manage-cookies-sfri11471/mac" target="_blank" rel="noopener noreferrer" className="text-brand-green-500 hover:underline">Apple Safari</a></>,
              <><a href="https://support.microsoft.com/en-us/microsoft-edge/delete-cookies-in-microsoft-edge-63947406-40ac-c3b8-57b9-2a946a29ae09" target="_blank" rel="noopener noreferrer" className="text-brand-green-500 hover:underline">Microsoft Edge</a></>,
            ]} />
            <p className="font-semibold mt-4" style={{ color: 'var(--text)' }}>Account Settings</p>
            <p>You can manage certain cookie-related preferences (such as theme and language preferences) through your Declairo account settings. These changes apply only to Declairo cookies and do not affect third-party cookies.</p>
            <p className="font-semibold mt-4" style={{ color: 'var(--text)' }}>Opt-Out of Analytics</p>
            <p>Since our analytics are self-hosted and privacy-preserving, standard analytics opt-out tools (such as the Google Analytics Opt-out Browser Add-on) do not apply to our analytics. To opt out of our internal analytics, please contact us at <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a> and we will exclude your sessions from analytics processing.</p>
          </Section>

          <Section id="data-transfers" title="International Transfers of Cookie Data">
            <p>Data collected through cookies may be processed on servers located in the United States (Amazon Web Services, us-east-1 region). For users in Brazil, the EEA, or the UK, such transfers are governed by the safeguards described in our <Link to="/privacy" className="text-brand-green-500 hover:underline">Privacy Policy</Link> (International Transfers section), including Standard Contractual Clauses (SCCs) and contractual mechanisms consistent with LGPD Art. 33.</p>
          </Section>

          <Section id="retention" title="Cookie Retention Periods">
            <p>Cookies are retained for the periods specified in the tables above. Session cookies are automatically deleted when you close your browser. Persistent cookies remain on your device until they expire or until you delete them using your browser settings.</p>
            <p>We periodically review our cookie list and remove cookies that are no longer necessary. The cookie list in this policy reflects all cookies in use as of the "Last updated" date.</p>
          </Section>

          <Section id="changes" title="Changes to This Cookie Policy">
            <p>We may update this Cookie Policy from time to time to reflect changes in our use of cookies, applicable law, or for other operational, legal, or regulatory reasons. When we make material changes, we will update the "Last updated" date at the top of this page and, where required by law, notify you by email or through a prominent notice on the platform.</p>
            <p>We encourage you to periodically review this page to stay informed about our use of cookies and related technologies.</p>
          </Section>

          <Section id="contact" title="Contact Us">
            <p>If you have any questions or concerns about our use of cookies or this Cookie Policy, please contact us:</p>
            <div className="p-5 rounded-xl border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <p className="font-semibold mb-1" style={{ color: 'var(--text)' }}>Declairo — Privacy & Data Contact</p>
              <p>Email: <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a></p>
              <p className="mt-1">Please include "Cookie Policy Inquiry" in the subject line.</p>
              <p className="mt-1">We aim to respond within 15 business days.</p>
            </div>
          </Section>

          <div className="mt-6 flex flex-wrap gap-4 text-xs" style={{ color: 'var(--text3)' }}>
            <Link to="/privacy" className="hover:text-brand-green-500 transition-colors">Privacy Policy</Link>
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
