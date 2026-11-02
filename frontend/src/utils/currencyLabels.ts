/** Display names for portfolio base currencies by ISO jurisdiction code. */
const CURRENCY_BY_JURISDICTION: Record<string, string> = {
  BR: 'Brazilian Real',
  US: 'US Dollar',
  MX: 'Mexican Peso',
  AR: 'Argentine Peso',
  CO: 'Colombian Peso',
  PE: 'Peruvian Sol',
  CL: 'Chilean Peso',
  GT: 'Guatemalan Quetzal',
  EC: 'US Dollar',
  UY: 'Uruguayan Peso',
  CR: 'Costa Rican Colón',
  HN: 'Honduran Lempira',
  BO: 'Bolivian Boliviano',
};

export function currencyLabelForJurisdiction(code: string): string {
  return CURRENCY_BY_JURISDICTION[code.toUpperCase()] ?? 'US Dollar';
}
