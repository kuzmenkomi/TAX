import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronLeft, AlertTriangle } from 'lucide-react';

const SECTIONS = [
  { id: 'general', title: 'General Disclaimer' },
  { id: 'no-advisor', title: 'Not a Tax or Legal Advisor' },
  { id: 'estimates', title: 'Estimates Only' },
  { id: 'latam-complexity', title: 'LATAM Regulatory Complexity' },
  { id: 'ai-disclaimer', title: 'AI Advisory Disclaimer' },
  { id: 'market-data', title: 'Market & Price Data' },
  { id: 'user-responsibility', title: 'User Responsibility' },
  { id: 'third-party', title: 'Third-Party Data & Exchanges' },
  { id: 'no-liability', title: 'No Liability for Tax Outcomes' },
  { id: 'defi-nft', title: 'DeFi, NFTs & Emerging Assets' },
  { id: 'investment', title: 'Not Investment Advice' },
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

export function DisclaimerPage() {
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
              If you have any questions about this disclaimer or our services, please feel free to{' '}
              <Link to="/contact" className="text-brand-green-500 hover:underline">contact us</Link>.
            </p>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          {/* Warning banner */}
          <div className="mb-10 text-sm leading-relaxed opacity-70 italic">
            <p style={{ color: 'var(--text)' }}>
              <Bold>This disclaimer is an important legal document.</Bold> By using Declairo, you acknowledge that you have read and understood its contents. Please read it carefully before relying on any information provided by the Service.
            </p>
          </div>

          <h1 className="text-4xl font-syne font-bold tracking-tight mb-10" style={{ color: 'var(--text)' }}>
            Declairo Disclaimer
          </h1>

          <Section id="general" title="General Disclaimer">
            <p>The information, content, reports, calculations, outputs, AI-generated responses, educational materials, and any other content provided by Declairo through its website, platform, mobile applications, APIs, or any related service (collectively, the "Service") is provided for <Bold>general informational and educational purposes only</Bold>. Nothing in or through the Service constitutes, or should be construed as, professional tax advice, legal advice, accounting advice, financial planning advice, investment advice, or any other form of professional advice regulated by any professional licensing authority in any jurisdiction.</p>
            <p>Declairo is a technology platform. It is not a law firm, accounting firm, tax consultancy, financial advisory firm, or any other type of regulated professional services provider. No attorney-client, accountant-client, or advisor-client relationship is formed between you and Declairo by your use of the Service, your submission of a contact form, your use of the AI Fiscal Advisor feature, or through any other interaction with the Service.</p>
            <p>You should not act or refrain from acting based on any information provided through the Service without first seeking the advice of a qualified professional (such as a licensed <em>contador</em>, <em>asesor fiscal</em>, or tax attorney) who is familiar with the specific laws and regulations applicable to your individual situation and jurisdiction.</p>
          </Section>

          <Section id="no-advisor" title="Not a Tax or Legal Advisor">
            <p>Declairo is a software tool, not a licensed tax advisor, attorney, accountant, or financial planner. No one at Declairo is authorized to practice law or provide legal advice, and nothing in the Service creates an attorney-client relationship. Specifically:</p>
            <UL items={[
              'The Service does not constitute a "tax preparation service" as defined under applicable law in any jurisdiction. Declairo does not prepare or file tax returns on your behalf.',
              'The reports generated by the Service are reference documents only. They are not certified or audited financial statements, and Declairo does not attest to their accuracy.',
              'The AI Fiscal Advisor responses are generated by an artificial intelligence system and are not reviewed or approved by a licensed tax professional before being displayed to you.',
              'Any characterization of a transaction as "taxable," "non-taxable," "capital gain," "ordinary income," or any other tax classification within the Service is an automated estimate and does not constitute a legal determination.',
              'Declairo does not represent any user before any tax authority, court, tribunal, or administrative body.',
            ]} />
            <p>We strongly recommend that you engage a licensed tax professional who specializes in cryptocurrency taxation in your specific jurisdiction (Receita Federal in Brazil, SAT in Mexico, AFIP in Argentina, DIAN in Colombia, SII in Chile, etc.) before making any tax-related decisions or filing any tax declarations.</p>
          </Section>

          <Section id="estimates" title="Estimates Only — No Guarantee of Accuracy">
            <p>ALL TAX CALCULATIONS, CAPITAL GAIN/LOSS ESTIMATES, COST BASIS COMPUTATIONS, TAXABLE EVENT CLASSIFICATIONS, HOLDING PERIOD DETERMINATIONS, AND ANY OTHER FINANCIAL OUTPUTS GENERATED BY DECLAIRO ARE ESTIMATES ONLY AND DO NOT CONSTITUTE GUARANTEED, ACCURATE, OR FINAL TAX DETERMINATIONS.</p>
            <p>The accuracy of any estimate produced by the Service depends entirely on the accuracy, completeness, and timeliness of the data you provide. Estimates may be inaccurate or incomplete for numerous reasons, including but not limited to:</p>
            <UL items={[
              'Missing transactions: if you have not imported all of your cryptocurrency transactions from all wallets and exchanges, your cost basis calculations will be incorrect, potentially resulting in significantly over- or under-reported gains.',
              'Incorrect transaction data: errors in data provided by blockchain explorers, exchange APIs, or manual entries will directly affect the accuracy of calculations.',
              'Stale price data: historical cryptocurrency price data used for cost basis calculations is sourced from third-party providers and may not reflect the exact price at which a transaction occurred.',
              'Unsupported transaction types: certain complex transaction types — including multi-hop DeFi swaps, cross-chain bridges, liquidity pool impermanent loss, NFT royalties, play-to-earn gaming rewards, perpetual contract funding rates, and others — may not be correctly classified or may be excluded from calculations entirely.',
              'Regulatory interpretation: Declairo applies one interpretation of applicable tax rules. Tax authorities may interpret the same rules differently, and those interpretations may change following audits, administrative rulings, or court decisions.',
              'Timing of rule updates: Declairo may not immediately update its calculation engine following changes to applicable law or regulatory guidance. Laws such as Brazil\'s Lei 14.754/2023, Mexico\'s Resolución Miscelánea Fiscal 2024, and Argentina\'s Ley 27.743/2024 may be updated by regulation at any time.',
            ]} />
            <p>Declairo does not guarantee that any output produced by the Service will be accepted or approved by any tax authority. The use of a Declairo report does not protect you from tax authority enforcement actions, audits, assessments of additional tax, penalties, or interest.</p>
          </Section>

          <Section id="latam-complexity" title="LATAM Regulatory Complexity">
            <p>Cryptocurrency taxation in Latin America is among the most complex and rapidly evolving in the world. Each country in the region has adopted distinct approaches to taxing crypto assets, and regulatory frameworks continue to develop. Declairo provides tools that attempt to reflect these rules, but users must understand the following country-specific considerations:</p>
            <p><Bold>Brazil (Receita Federal):</Bold> Brazil has one of the most developed crypto tax frameworks in LATAM. Key regulations include: Instrução Normativa RFB nº 1.888/2019 (mandatory monthly reporting for transactions above R$30,000 to the Receita Federal); Lei nº 14.754/2023 (effective January 1, 2024, taxing overseas income including crypto held on foreign exchanges at a flat rate of 15%); and Instrução Normativa RFB nº 2.180/2024 (supplementary rules). Capital gains are taxed progressively at 15%–22.5% under Lei 8.981/1995 as applied to crypto. Declairo's calculations attempt to reflect these rules but cannot guarantee alignment with the Receita Federal's interpretation in any given audit.</p>
            <p><Bold>Mexico (SAT):</Bold> Cryptocurrency is generally treated as property under Mexican law. Gains from disposal are subject to the Impuesto Sobre la Renta (ISR) under the Ley del ISR. The SAT has issued guidance through the Resolución Miscelánea Fiscal (RMF) and has specific obligations for Fintech entities under Ley Fintech (Ley nº 446/2018). Individual taxpayers must include crypto gains in their annual Declaración Anual. The applicable rate depends on the individual's income bracket.</p>
            <p><Bold>Argentina (AFIP):</Bold> Argentina has a complex tax treatment for crypto assets. AFIP Resolución General nº 4.614/2019 established reporting obligations. Gains from crypto may be subject to Impuesto a las Ganancias (income tax) and/or Bienes Personales (personal property tax). The Ley 27.743/2024 (Ley Bases) introduced new provisions affecting certain crypto arrangements. Argentina's economic instability and frequent regulatory changes make this jurisdiction particularly challenging.</p>
            <p><Bold>Colombia (DIAN):</Bold> DIAN Resolución 000013/2022 established reporting requirements for virtual asset service providers. Crypto gains are treated as income and subject to the Impuesto sobre la Renta y Complementarios. Colombia is actively developing a comprehensive virtual asset regulatory framework.</p>
            <p><Bold>Chile (SII):</Bold> The Servicio de Impuestos Internos (SII) issued Circular nº 28/2022 clarifying the tax treatment of cryptocurrencies. Gains are generally classified as capital gains or ordinary income depending on the nature of the activity. Chile's Ley Fintech (Ley 21.521/2023) creates additional compliance requirements for certain crypto businesses.</p>
            <p>Declairo's platform attempts to reflect these regulatory frameworks to the best of our ability and as of the "Last updated" date shown. However, <Bold>we cannot guarantee complete, current, or jurisdiction-specific accuracy</Bold>, and regulations may change without advance notice. Users should always verify applicable rules with a qualified local tax professional.</p>
          </Section>

          <Section id="ai-disclaimer" title="AI Advisory Feature — Important Limitations">
            <p>Declairo offers an "AI Fiscal Advisor" feature that generates responses to user questions about cryptocurrency taxation using a large language model (LLM). Users must understand the following important limitations of this feature:</p>
            <UL items={[
              'The AI Fiscal Advisor responses are generated automatically by a machine learning model and are NOT reviewed, approved, or certified by any licensed tax professional, attorney, or accountant before being displayed.',
              'LLMs may generate plausible-sounding but factually incorrect information — a phenomenon known as "hallucination." Tax law is particularly sensitive to errors, as incorrect advice could lead to incorrect tax filings, penalties, and interest.',
              'The AI\'s training data has a knowledge cutoff and may not reflect recent changes in law, regulatory guidance, or administrative practice. New regulations such as Brazil\'s Lei 14.754/2023 and IN RFB 2.180/2024, Mexico\'s RMF 2024, or Argentina\'s Ley 27.743/2024 may not be fully reflected.',
              'The AI cannot assess your complete personal tax situation, including your total income, applicable exemptions and deductions, treaty benefits, or prior year tax positions.',
              'Responses from the AI Fiscal Advisor DO NOT constitute professional tax or legal advice. You should treat AI responses as a starting point for research and discussion with a qualified professional, not as final guidance.',
              'Declairo is not responsible for any decision made or action taken based on AI-generated content.',
            ]} />
          </Section>

          <Section id="market-data" title="Market and Price Data">
            <p>Declairo uses historical and real-time cryptocurrency price data obtained from third-party providers including CoinGecko, CoinMarketCap, and others. This price data is used to calculate the fair market value of cryptocurrency at the time of each transaction, which directly affects cost basis and capital gains calculations.</p>
            <UL items={[
              'Price data may not be available for all cryptocurrencies, tokens, or NFTs, particularly for less liquid assets, newly launched tokens, or assets on emerging blockchains.',
              'Historical price data may contain gaps, errors, or inconsistencies, particularly for dates before major data providers began tracking a given asset.',
              'Prices may differ across exchanges, and the "correct" price for tax purposes may depend on regulatory guidance in your jurisdiction (e.g., the Receita Federal may have specific guidance on how to value crypto received as income).',
              'For DeFi tokens, LP positions, NFTs, and other complex assets, accurate fair market value determination may require specialist analysis that Declairo cannot provide automatically.',
            ]} />
          </Section>

          <Section id="user-responsibility" title="User Responsibility">
            <p>You are solely and entirely responsible for:</p>
            <UL items={[
              'Ensuring that all transaction data imported into Declairo is accurate, complete, and up to date, including transactions on all wallets, exchanges, DeFi protocols, NFT marketplaces, and any other platforms where you have held or transacted in crypto assets.',
              'Reviewing all calculations, reports, and outputs generated by the Service for accuracy and completeness before using them for any purpose, including tax filing.',
              'Engaging a qualified tax professional to review your Declairo reports before filing any tax declaration with the Receita Federal, SAT, AFIP, DIAN, SII, or any other authority.',
              'Filing all required tax declarations and information reports on time and in the correct format required by your jurisdiction.',
              'Paying all taxes owed, including any applicable penalties or interest for late or incorrect filings.',
              'Maintaining records of all your cryptocurrency transactions in accordance with the record-keeping requirements of your jurisdiction (typically 5–6 years in most LATAM countries).',
              'Reporting all required information to your national tax authority, including any mandatory information reporting obligations (e.g., the monthly DIRBI report required by IN RFB 1.888/2019 in Brazil for transactions exceeding R$30,000).',
            ]} />
          </Section>

          <Section id="third-party" title="Third-Party Data and Exchange Integrations">
            <p>Declairo integrates with third-party cryptocurrency exchanges, blockchain networks, and data providers via APIs and public blockchain explorers. Declairo does not control the accuracy, availability, completeness, or timeliness of data provided by these third parties. Specific risks include:</p>
            <UL items={[
              'Exchange API limitations: some exchanges do not provide complete historical transaction data through their APIs, particularly for transactions older than 1–3 years. Missing historical data will result in incorrect cost basis calculations.',
              'Blockchain explorer data: public blockchain explorers may have indexing errors, missing data for certain token standards, or delays in reflecting the most recent on-chain state.',
              'Exchange delistings and closures: if an exchange where you held assets has closed or delisted certain trading pairs, complete transaction history may be unavailable.',
              'DeFi protocol interactions: interactions with decentralized finance protocols (lending, borrowing, liquidity pools, yield farming, etc.) are often complex and may not be automatically categorized correctly by Declairo.',
            ]} />
          </Section>

          <Section id="no-liability" title="No Liability for Tax Outcomes">
            <p>DECLAIRO SHALL NOT BE LIABLE FOR ANY PENALTIES, FINES, INTEREST CHARGES, BACK TAXES, AUDIT COSTS, LEGAL FEES, OR ANY OTHER ADVERSE OUTCOME RESULTING FROM:</p>
            <UL items={[
              'Your tax filings, even if those filings were prepared in whole or in part using reports or calculations generated by the Service.',
              'Any audit, examination, inquiry, or enforcement action by the Receita Federal, SAT, AFIP, DIAN, SII, COAF, or any other governmental or regulatory authority.',
              'Incorrect or missing transaction data that resulted in inaccurate calculations.',
              'Regulatory changes that affected the accuracy of calculations after they were generated.',
              'Your reliance on AI Fiscal Advisor responses or any other content from the Service.',
              'Failure to file required information reports (e.g., IN RFB 1.888/2019 monthly reporting in Brazil).',
              'Any financial decisions made based on information obtained through the Service.',
            ]} />
            <p>The use of Declairo does not constitute a "defense" for purposes of any tax penalty abatement claim based on reasonable cause or good faith reliance, as Declairo is not a tax professional and its outputs have not been reviewed by one.</p>
          </Section>

          <Section id="defi-nft" title="DeFi, NFTs, and Emerging Asset Classes">
            <p>Decentralized finance (DeFi) protocols, non-fungible tokens (NFTs), blockchain gaming assets (play-to-earn), liquid staking derivatives, real-world asset (RWA) tokenization, and other emerging crypto asset classes present unique and unresolved tax challenges. Regulatory guidance on these asset classes is limited, rapidly evolving, and highly inconsistent across LATAM jurisdictions. Specifically:</p>
            <UL items={[
              'Liquidity pool deposits and withdrawals may be treated as taxable disposals in some jurisdictions and as non-taxable movements in others.',
              'Staking rewards may be treated as income at the time of receipt, or as capital gains upon eventual disposal, depending on jurisdiction and applicable guidance.',
              'NFT transactions may involve complex royalty, licensing, or intellectual property considerations that are outside the scope of Declairo\'s automated calculations.',
              'DeFi lending collateralization events, liquidations, and margin calls may or may not constitute taxable events under applicable law.',
              'Cross-chain bridge transactions, layer-2 withdrawals, and wrapped asset conversions may be treated inconsistently across jurisdictions.',
            ]} />
            <p>Declairo makes reasonable efforts to classify these transaction types, but the classifications used may not align with the eventual regulatory or judicial interpretation in your jurisdiction. For these complex transaction types, professional advice is especially important.</p>
          </Section>

          <Section id="investment" title="Not Investment Advice">
            <p>Nothing on the Declairo platform, including portfolio performance metrics, unrealized gain/loss displays, tax optimization suggestions, or any other content, constitutes investment advice. Declairo does not recommend the purchase, sale, or holding of any cryptocurrency, token, or other financial asset. Cryptocurrency investments involve significant risk, including the risk of total loss. Past performance is not indicative of future results. You should make investment decisions based on your own research and in consultation with a licensed financial advisor or investment broker registered in your jurisdiction.</p>
            <p>In Brazil, investment advice is regulated by the Comissão de Valores Mobiliários (CVM) under Resolução CVM nº 19/2021 and related instruments. In Mexico, by the CNBV. In Colombia, by the AMC. Declairo is not registered with any of these bodies and does not provide services regulated by them.</p>
          </Section>

          <Section id="contact" title="Contact Us">
            <p>If you have questions about this disclaimer or the limitations of the Service, we encourage you to contact us before relying on any Service output:</p>
            <div className="p-5 rounded-xl border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
              <p className="font-semibold mb-1" style={{ color: 'var(--text)' }}>Declairo — Legal & Compliance</p>
              <p>Email: <a href="mailto:support@declairo.com" className="text-brand-green-500 hover:underline">support@declairo.com</a></p>
              <p className="mt-1">For professional tax advice in your jurisdiction, please consult a licensed <em>contador</em>, <em>asesor fiscal</em>, or tax attorney familiar with cryptocurrency regulations.</p>
            </div>
          </Section>

          <div className="mt-6 flex flex-wrap gap-4 text-xs" style={{ color: 'var(--text3)' }}>
            <Link to="/privacy" className="hover:text-brand-green-500 transition-colors">Privacy Policy</Link>
            <Link to="/terms" className="hover:text-brand-green-500 transition-colors">Terms of Service</Link>
            <Link to="/security" className="hover:text-brand-green-500 transition-colors">Security</Link>
            <Link to="/contact" className="hover:text-brand-green-500 transition-colors">Contact</Link>
          </div>
          <p className="text-xs mt-3 mb-8" style={{ color: 'var(--text3)' }}>© 2026 Declairo. All rights reserved.</p>
        </main>
      </div>
    </div>
  );
}
