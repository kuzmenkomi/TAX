type RunLike = {
  run_id?: number;
  id?: number;
  format?: string;
  created_at?: string;
  rows_processed?: number;
};

export type CsvImportSource = {
  id: string;
  runId: number | null;
  provider: string;
  name: string;
  createdAt: string | null;
  sourceType: 'csv';
  transaction_count: number;
};

const PROVIDER_LABELS: Record<string, string> = {
  native: 'CSV Import',
  csv: 'CSV Import',
  binance: 'Binance',
  coinbase: 'Coinbase',
  kraken: 'Kraken',
  okx: 'OKX',
  bybit: 'Bybit',
  kucoin: 'KuCoin',
};

export function isOnchainRunFormat(format?: string | null): boolean {
  return String(format || '').toLowerCase().startsWith('onchain:');
}

function formatProviderName(provider: string): string {
  const normalized = provider.trim().toLowerCase();
  if (PROVIDER_LABELS[normalized]) return PROVIDER_LABELS[normalized];
  if (!normalized) return 'CSV Import';
  return normalized
    .split(/[_:\-\s]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function formatCsvImportDateTime(createdAt: string | null, runId?: number): string {
  if (!createdAt) return runId != null ? `Import #${runId}` : 'CSV Import';
  const when = new Date(createdAt);
  if (Number.isNaN(when.getTime())) return runId != null ? `Import #${runId}` : 'CSV Import';
  const datePart = when.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  const timePart = when.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });
  return `${datePart} ${timePart}`;
}

function formatImportLabel(providerKey: string, createdAt: string | null, runId: number): string {
  const providerLabel = formatProviderName(providerKey);
  if (!createdAt) return `${providerLabel} · Import #${runId}`;
  return `${providerLabel} · ${formatCsvImportDateTime(createdAt)}`;
}

/** One sidebar row per CSV upload (analysis run), including multiple files from the same exchange. */
export function buildCsvImportSources(runs: RunLike[] = []): CsvImportSource[] {
  const sources: CsvImportSource[] = [];

  runs.forEach((run) => {
    const format = String(run?.format || '').trim().toLowerCase();
    if (isOnchainRunFormat(format)) return;

    const runId = Number(run?.run_id ?? run?.id ?? 0) || null;
    if (!runId) return;

    const providerKey = format || 'csv';
    const createdAt = run?.created_at ?? null;

    sources.push({
      id: `csv_${runId}`,
      runId,
      provider: providerKey,
      name: formatImportLabel(providerKey, createdAt, runId),
      createdAt,
      sourceType: 'csv',
      transaction_count: Number(run.rows_processed ?? 0),
    });
  });

  return sources.sort(
    (a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime(),
  );
}
