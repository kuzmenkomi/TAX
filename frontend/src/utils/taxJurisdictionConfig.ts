/**
 * Tax Center UI options per jurisdiction (country code).
 */

export type RegionalToggle = {
  id: string;
  label: string;
  description: string;
  defaultOn: boolean;
};

export type TaxReportCard = {
  name: string;
  icon: string;
  desc: string;
  format: string;
};

export type TaxJurisdictionUiConfig = {
  code: string;
  name: string;
  currencyLabel: string;
  regionalToggles: RegionalToggle[];
  reports: TaxReportCard[];
  complianceLabel: string;
  complianceLimit?: string;
  methods: { id: string; label: string }[];
};

const DEFAULT_METHODS = [
  { id: 'FIFO', label: 'FIFO (Recommended)' },
  { id: 'LIFO', label: 'LIFO' },
  { id: 'HIFO', label: 'HIFO' },
  { id: 'WEIGHTED_AVERAGE', label: 'Weighted Average' },
];

const CONFIGS: Record<string, TaxJurisdictionUiConfig> = {
  BR: {
    code: 'BR',
    name: 'Brazil',
    currencyLabel: 'BRL',
    regionalToggles: [
      {
        id: 'ptax',
        label: 'Brazil — PTAX Official',
        description: 'Receita Federal standard',
        defaultOn: true,
      },
      {
        id: 'auto_classify',
        label: 'Auto-Classification',
        description: 'Detect rewards and airdrops',
        defaultOn: false,
      },
    ],
    reports: [
      { name: 'IRPF Summary', icon: '📊', desc: 'Ready for DIRPF software.', format: 'PDF + XML' },
      { name: 'Transaction History', icon: '📋', desc: 'Full CSV audit trail.', format: 'CSV' },
      { name: 'Income Report', icon: '🏦', desc: 'Rewards and airdrops.', format: 'PDF + CSV' },
    ],
    complianceLabel: 'Monthly Exemption (BR)',
    complianceLimit: 'R$ 35,000.00',
    methods: DEFAULT_METHODS,
  },
  US: {
    code: 'US',
    name: 'United States',
    currencyLabel: 'USD',
    regionalToggles: [
      {
        id: 'wash_sale',
        label: 'Track wash-sale windows',
        description: 'IRS-style loss disallowance notes (informational)',
        defaultOn: false,
      },
      {
        id: 'auto_classify',
        label: 'Auto-Classification',
        description: 'Staking, mining, and airdrop income',
        defaultOn: true,
      },
    ],
    reports: [
      { name: 'Form 8949 Summary', icon: '📊', desc: 'Capital gains and losses.', format: 'PDF + CSV' },
      { name: 'Schedule D Preview', icon: '📋', desc: 'Net short/long-term totals.', format: 'PDF' },
      { name: 'Income Events', icon: '🏦', desc: 'Ordinary income from crypto.', format: 'CSV' },
    ],
    complianceLabel: 'Federal reporting (US)',
    methods: DEFAULT_METHODS,
  },
  MX: {
    code: 'MX',
    name: 'Mexico',
    currencyLabel: 'MXN',
    regionalToggles: [
      {
        id: 'auto_classify',
        label: 'Auto-Classification',
        description: 'Detect taxable crypto income',
        defaultOn: false,
      },
    ],
    reports: [
      { name: 'ISR Crypto Summary', icon: '📊', desc: 'Annual gains overview.', format: 'PDF + CSV' },
      { name: 'Transaction History', icon: '📋', desc: 'Full audit trail.', format: 'CSV' },
    ],
    complianceLabel: 'SAT compliance (MX)',
    methods: DEFAULT_METHODS,
  },
  AR: {
    code: 'AR',
    name: 'Argentina',
    currencyLabel: 'ARS',
    regionalToggles: [
      {
        id: 'parallel_rate',
        label: 'Argentina — Dólar Blue / parallel',
        description: 'AFIP alternative valuation',
        defaultOn: false,
      },
      {
        id: 'auto_classify',
        label: 'Auto-Classification',
        description: 'Detect rewards and airdrops',
        defaultOn: false,
      },
    ],
    reports: [
      { name: 'Ganancias Summary', icon: '📊', desc: 'Capital gains overview.', format: 'PDF + CSV' },
      { name: 'Bienes Personales', icon: '📋', desc: 'Holdings snapshot.', format: 'PDF' },
    ],
    complianceLabel: 'AFIP compliance (AR)',
    methods: DEFAULT_METHODS,
  },
};

const FALLBACK = CONFIGS.BR;

export function getTaxJurisdictionConfig(code: string): TaxJurisdictionUiConfig {
  const key = (code || 'BR').toUpperCase();
  if (CONFIGS[key]) return CONFIGS[key];
  return {
    ...FALLBACK,
    code: key,
    name: key,
    currencyLabel: key,
    regionalToggles: [
      {
        id: 'auto_classify',
        label: 'Auto-Classification',
        description: 'Detect rewards and airdrops',
        defaultOn: false,
      },
    ],
    reports: [
      { name: 'Tax Summary', icon: '📊', desc: 'Capital gains overview.', format: 'PDF + CSV' },
      { name: 'Transaction History', icon: '📋', desc: 'Full CSV audit trail.', format: 'CSV' },
    ],
    complianceLabel: `Compliance (${key})`,
    methods: DEFAULT_METHODS,
  };
}
