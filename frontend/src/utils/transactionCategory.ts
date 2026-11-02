export type TransactionCategory = 'TRADE' | 'TRANSFER' | 'INCOME' | 'OTHER';

const TRADE_TYPES = new Set([
  'BUY',
  'SELL',
  'SWAP',
  'TRADE',
  'LIQUIDATION',
  'FUTURES_PNL',
]);

const TRANSFER_TYPES = new Set([
  'TRANSFER',
  'RECEIVE',
  'BRIDGE',
  'TOKEN_TRANSFER',
  'NFT_TRANSFER',
  'APPROVE',
  'WRAP',
  'UNWRAP',
  'DEPOSIT',
  'WITHDRAWAL',
  'LP_ADD',
  'LP_REMOVE',
  'DEFI_LP_ADD',
  'DEFI_LP_REMOVE',
  'MINT',
  'NFT_MINT',
  'BURN',
]);

const INCOME_TYPES = new Set([
  'INCOME',
  'AIRDROP',
  'REWARD',
  'INTEREST',
  'STAKING',
  'STAKING_REWARD',
  'FARMING_REWARD',
  'LENDING',
  'LENDING_INTEREST',
  'MINING',
  'MINING_REWARD',
  'FORK',
  'CLAIM',
]);

export function getTransactionCategory(tx: { type?: string; category?: string } | null | undefined): TransactionCategory {
  const apiCategory = String(tx?.category || '').toUpperCase();
  if (apiCategory === 'TRADE' || apiCategory === 'TRANSFER' || apiCategory === 'INCOME') {
    return apiCategory;
  }

  const type = String(tx?.type || '').toUpperCase();

  if (INCOME_TYPES.has(type) || /REWARD|INTEREST|INCOME|AIRDROP|MINING|STAK|FARM|FORK|CLAIM/.test(type)) {
    return 'INCOME';
  }
  if (TRADE_TYPES.has(type) || /BUY|SELL|SWAP|TRADE|LIQUIDATION|FUTURES|PERP/.test(type)) {
    return 'TRADE';
  }
  if (TRANSFER_TYPES.has(type) || /TRANSFER|RECEIVE|DEPOSIT|WITHDRAW|BRIDGE|APPROVE|WRAP|UNWRAP|LP_|MINT|BURN/.test(type)) {
    return 'TRANSFER';
  }

  return 'OTHER';
}

export type TransactionDisplayType = 'buy' | 'sell' | 'transfer' | 'income' | 'other';

export function getDisplayTransactionType(tx: { type?: string; category?: string } | null | undefined): TransactionDisplayType {
  const rawType = String(tx?.type || '').toUpperCase();
  if (rawType.includes('SELL')) return 'sell';
  if (rawType.includes('BUY') || rawType === 'DEPOSIT' || rawType === 'RECEIVE') return 'buy';

  const category = getTransactionCategory(tx);
  if (category === 'INCOME') return 'income';
  if (category === 'TRANSFER') return 'transfer';
  if (category === 'TRADE') return rawType.includes('SELL') ? 'sell' : 'buy';
  return 'other';
}
