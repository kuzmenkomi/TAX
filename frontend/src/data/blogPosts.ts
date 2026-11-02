export interface BlogPost {
  slug: string;
  title: string;
  metaDescription: string;
  category: string;
  date: string;
  isoDate: string;
  readTime: string;
  author: { name: string; role: string };
  heroImage: string;
  excerpt: string;
  content: string;
  tags: string[];
  relatedSlugs: string[];
  language: 'en' | 'pt';
}

export const BLOG_POSTS: BlogPost[] = [
  {
    slug: 'crypto-tax-guide-2026',
    title: 'The Complete Crypto Tax Guide for 2026: Everything You Need to Know',
    metaDescription: 'Stay compliant with the latest crypto tax regulations in 2026. Learn about capital gains, income tax, and how to report your trades accurately.',
    category: 'Tax Guides',
    date: 'May 12, 2026',
    isoDate: '2026-05-12T00:00:00Z',
    readTime: '12 min read',
    author: { name: 'Alex Rivera', role: 'Head of Tax Compliance' },
    heroImage: '/blog-images/hero-tax-guide.png',
    excerpt: 'As crypto regulations evolve globally, staying ahead of tax requirements is more critical than ever. This guide covers everything from basic reporting to complex DeFi scenarios.',
    language: 'en',
    tags: ['Tax', 'Compliance', '2026'],
    relatedSlugs: ['fifo-vs-lifo-vs-hifo', 'crypto-tax-loss-harvesting'],
    content: `
      <h2>Introduction to 2026 Crypto Taxes</h2>
      <p>The landscape of cryptocurrency taxation has undergone significant changes heading into 2026. Tax authorities worldwide, including the IRS and various LATAM agencies, have implemented stricter reporting requirements for digital assets.</p>
      
      <h3>Capital Gains vs. Income</h3>
      <p>Most crypto transactions are classified as either capital gains/losses or ordinary income. Selling Bitcoin for a profit? That is a capital gain. Earning staking rewards? That is usually treated as income at the fair market value on the day you received it.</p>
      
      <h3>Essential Reporting Requirements</h3>
      <p>In 2026, you must report all "disposals" of cryptocurrency. This includes selling for fiat, trading one coin for another, and even using crypto to buy goods or services.</p>
      
      <div class="cta-box">
        <h4>Stress-free tax filing?</h4>
        <p>Declairo automatically calculates these gains for you. <a href="/register">Start for free</a>.</p>
      </div>
    `
  },
  {
    slug: 'guia-impostos-crypto-brasil-2026',
    title: 'Guia de Impostos sobre Criptomoedas no Brasil 2026: Receita Federal e GCAP',
    metaDescription: 'Saiba como declarar suas criptomoedas no Brasil em 2026. Entenda as regras da Receita Federal, o uso do GCAP e as isenções mensais.',
    category: 'Country Specific',
    date: '10 de Maio, 2026',
    isoDate: '2026-05-10T00:00:00Z',
    readTime: '10 min de leitura',
    author: { name: 'Lucas Silva', role: 'Especialista Tributário LATAM' },
    heroImage: '/blog-images/hero-country.png',
    excerpt: 'A Receita Federal do Brasil endureceu as regras para ativos digitais. Saiba como navegar no GCAP e evitar multas na sua declaração anual.',
    language: 'pt',
    tags: ['Brasil', 'Receita Federal', 'Impostos'],
    relatedSlugs: ['crypto-tax-guide-2026'],
    content: `
      <h2>Regras da Receita Federal para 2026</h2>
      <p>Para os investidores brasileiros, a declaração de criptoativos não é mais opcional. A Instrução Normativa 1.888 continua sendo o pilar, mas novas diretrizes sobre ativos no exterior mudaram o jogo este ano.</p>
      
      <h3>Isenção de R$ 35.000,00</h3>
      <p>Ainda existe a isenção para vendas totais mensais abaixo de R$ 35.000,00? Sim, mas cuidado com as permutas (troca de uma crypto por outra), que agora são monitoradas de perto.</p>
      
      <h3>O Papel do GCAP</h3>
      <p>O Programa de Apuração de Ganhos de Capital (GCAP) deve ser alimentado mensalmente caso você ultrapasse os limites de isenção, gerando o DARF para pagamento imediato.</p>
    `
  },
  {
    slug: 'defi-yield-farming-taxes-explained',
    title: 'DeFi Yield Farming Taxes: How to Report Staking & LP Rewards',
    metaDescription: 'Deep dive into the complex world of DeFi taxation. Learn how to handle liquidity pools, staking rewards, and governance tokens on your tax return.',
    category: 'DeFi & NFT',
    date: 'May 8, 2026',
    isoDate: '2026-05-08T00:00:00Z',
    readTime: '15 min read',
    author: { name: 'Sarah Chen', role: 'DeFi Research Lead' },
    heroImage: '/blog-images/hero-defi.png',
    excerpt: 'DeFi moves fast, but tax laws are catching up. Understanding the difference between a taxable event and a simple deposit is key to saving money.',
    language: 'en',
    tags: ['DeFi', 'Staking', 'Yield Farming'],
    relatedSlugs: ['crypto-tax-guide-2026'],
    content: `
      <h2>The Complexity of DeFi</h2>
      <p>DeFi interactions often involve multiple smart contract calls, each potentially being a taxable event. When you deposit assets into a Liquidity Pool (LP), are you "selling" those assets for an LP token? Most tax authorities say yes.</p>
      
      <h3>Staking Rewards</h3>
      <p>Rewards earned from staking are typically taxed as income. The challenge is tracking the cost basis for hundreds of micro-transactions if you claim rewards daily.</p>
    `
  }
];
