// ============================================================
// API Client — подключение к FastAPI бэкенду
// Backend URL: http://localhost:8000
// ============================================================

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '') + '/api/v1';

export const API_BASE_URL = BASE_URL;

export function apiUrl(path: string): string {
  if (/^https?:\/\//.test(path)) return path;
  return `${BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

export async function apiFetch(
  path: string,
  init: RequestInit & { token?: string | null } = {},
): Promise<Response> {
  const { token, headers, ...rest } = init;
  const nextHeaders = new Headers(headers);

  if (token) {
    nextHeaders.set('Authorization', `Bearer ${token}`);
  }

  return fetch(apiUrl(path), {
    ...rest,
    headers: nextHeaders,
  });
}

// ---- Типы данных из бэкенда ----

export interface PnLEntry {
  asset?: string;
  symbol?: string;
  realized_pnl?: number;
  unrealized_pnl?: number;
  total_gain?: number;
  total_loss?: number;
  short_term_gain?: number;
  long_term_gain?: number;
  [key: string]: unknown;
}

export interface MatchEntry {
  buy_date?: string;
  sell_date?: string;
  asset?: string;
  symbol?: string;
  amount?: number;
  buy_price?: number;
  sell_price?: number;
  gain_loss?: number;
  holding_period_days?: number;
  [key: string]: unknown;
}

export interface DataIssue {
  code?: string;
  severity?: string;
  message?: string;
  row_index?: number;
  [key: string]: unknown;
}

export interface AnalyzeResult {
  status: string;
  filename: string | string[];
  rows_processed: number;
  matches_found: number;
  matches: MatchEntry[];
  pnl: PnLEntry[] | Record<string, unknown>;
  issues?: DataIssue[];
  analysis_run_id?: number;
  quote_currency?: string;
  use_ptax?: boolean;
  monthly_sales_brl?: Record<string, number>;
  isencao_threshold_brl?: number;
  darf?: {
    month: string;
    sales_brl: number;
    code: string;
    taxable: boolean;
    amount_brl: number;
    due_date: string;
    message_pt: string;
  } | null;
  offshore_onshore?: {
    offshore_sales_brl: number;
    onshore_sales_brl: number;
    offshore_gain_brl: number;
    onshore_gain_brl: number;
    offshore_tax_rate: number;
    offshore_tax_brl: number;
    onshore_tax_rate: number;
    onshore_tax_brl: number;
    decripto_required: boolean;
    decripto_threshold_brl: number;
    decripto_alert: string;
    latest_month: string;
    latest_month_onshore_sales_brl: number;
    latest_month_offshore_sales_brl: number;
  };
  tax_savings_opportunities?: Array<{
    asset: string;
    estimated_loss_brl: number;
    estimated_tax_saving_brl: number;
    message_pt: string;
  }>;
  p2p_self_custody_count?: number;
  accounting_method?: string;
  income_events?: Record<string, number> | { total?: number };
}

export interface HealthStatus {
  status: string;
}

// ---- API функции ----

/**
 * Проверка что бэкенд живой (с retry logic)
 */
export async function checkHealth(): Promise<HealthStatus> {
  let lastError: Error | null = null;
  const MAX_RETRIES = 2;
  
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);
      
      const res = await apiFetch('/health', {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' }
      });
      clearTimeout(timeoutId);
      
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      
      const data = await res.json();
      return data as HealthStatus;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      // Если это последняя попытка, бросаем ошибку
      if (attempt === MAX_RETRIES) {
        throw lastError;
      }
      
      // Ждем перед следующей попыткой
      await new Promise(resolve => setTimeout(resolve, 300 * (attempt + 1)));
    }
  }
  
  throw lastError || new Error('Backend недоступен');
}

/**
 * Загрузка CSV файла на /analyze-upload
 * Это главный endpoint твоего бэкенда
 */
export async function analyzeUpload(params: {
  file: File;
  format?: string;
  accounting_method?: string;
  max_amount_diff?: number;
  max_time_diff_seconds?: number;
  api_key?: string;
  country?: string;
  quote_currency?: string;
  use_ptax?: boolean;
  token?: string | null;
}): Promise<AnalyzeResult> {
  const formData = new FormData();
  formData.append('file', params.file);
  formData.append('format', params.format ?? 'native');
  formData.append('accounting_method', params.accounting_method ?? 'FIFO');
  formData.append('country', params.country ?? 'br');
  formData.append('quote_currency', params.quote_currency ?? 'BRL');
  formData.append('use_ptax', String(Boolean(params.use_ptax)));
  formData.append('max_amount_diff', String(params.max_amount_diff ?? 0.01));
  formData.append('max_time_diff_seconds', String(params.max_time_diff_seconds ?? 3600));
  if (params.api_key) formData.append('api_key', params.api_key);

  const headers: Record<string, string> = {};
  if (params.token) {
    headers['Authorization'] = `Bearer ${params.token}`;
  }

  const res = await apiFetch('/analyze-upload', {
    method: 'POST',
    body: formData,
    token: params.token,
    headers,
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Ошибка бэкенда: ${err}`);
  }

  return res.json();
}

export async function analyzeUploadMulti(params: {
  files: File[];
  format?: string;
  accounting_method?: string;
  country?: string;
  quote_currency?: string;
  use_ptax?: boolean;
  token?: string | null;
}): Promise<AnalyzeResult> {
  const formData = new FormData();
  for (const f of params.files) {
    formData.append('files', f);
  }
  formData.append('format', params.format ?? 'native');
  formData.append('accounting_method', params.accounting_method ?? 'FIFO');
  formData.append('country', params.country ?? 'br');
  formData.append('quote_currency', params.quote_currency ?? 'BRL');
  formData.append('use_ptax', String(Boolean(params.use_ptax)));
  formData.append('max_amount_diff', '0.01');
  formData.append('max_time_diff_seconds', '3600');

  const headers: Record<string, string> = {};
  if (params.token) headers['Authorization'] = `Bearer ${params.token}`;

  const res = await apiFetch('/analyze-upload-multi', {
    method: 'POST',
    body: formData,
    token: params.token,
    headers,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Multi-upload failed');
  }
  return res.json();
}

export interface SyncExchangeBody {
  provider?: string;
  api_key: string;
  api_secret: string;
  symbols?: string[];
  accounting_method?: string;
  quote_currency?: string;
  country?: string;
  limit_per_symbol?: number;
  use_ptax?: boolean;
}

export async function syncExchange(
  token: string,
  body: SyncExchangeBody,
): Promise<AnalyzeResult> {
  const res = await apiFetch('/sync-exchange', {
    method: 'POST',
    token,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Exchange sync failed');
  }
  return res.json();
}

export async function brBinanceSyncAnalyze(
  token: string,
  body: SyncExchangeBody,
): Promise<AnalyzeResult> {
  return syncExchange(token, body);
}

export async function syncWallet(
  token: string,
  body: {
    chain: 'ethereum' | 'polygon' | 'solana';
    address: string;
    accounting_method?: string;
    quote_currency?: string;
    country?: string;
    use_ptax?: boolean;
    etherscan_api_key?: string;
    polygonscan_api_key?: string;
  },
): Promise<AnalyzeResult> {
  const res = await apiFetch('/sync-wallet', {
    method: 'POST',
    token,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Wallet sync failed');
  }
  return res.json();
}

export async function downloadBrExport(token: string, runId: number): Promise<Blob> {
  const res = await apiFetch(`/exports/br/${runId}`, {
    token,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Export failed');
  }
  return res.blob();
}

export async function downloadGcapExport(token: string, runId: number): Promise<Blob> {
  const res = await apiFetch(`/exports/gcap/${runId}`, {
    token,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'GCAP export failed');
  }
  return res.blob();
}

export async function downloadDecriptoExport(token: string, runId: number): Promise<Blob> {
  const res = await apiFetch(`/exports/decripto/${runId}`, {
    token,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'DeCripto export failed');
  }
  return res.blob();
}

export async function downloadDirpfExport(token: string, runId: number): Promise<Blob> {
  const res = await apiFetch(`/exports/dirpf/${runId}`, {
    token,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'DIRPF export failed');
  }
  return res.blob();
}

export interface RunHistoryItem {
  run_id: number;
  created_at: string;
  accounting_method: string;
  format: string;
  quote_currency: string;
  realized_pnl: number;
}

export async function getRunHistory(token: string): Promise<RunHistoryItem[]> {
  const res = await apiFetch('/br/runs', {
    token,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Run history failed');
  }
  const payload = await res.json();
  return (payload?.runs ?? []) as RunHistoryItem[];
}

export async function downloadAuditPdf(token: string, runId: number): Promise<Blob> {
  const res = await apiFetch(`/exports/audit/${runId}`, {
    token,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Audit export failed');
  }
  return res.blob();
}

export async function analyzeOnchainWallet(
  token: string,
  body: {
    chain: 'ethereum' | 'polygon' | 'solana';
    address: string;
    accounting_method?: string;
    quote_currency?: string;
    country?: string;
    use_ptax?: boolean;
    etherscan_api_key?: string;
    polygonscan_api_key?: string;
  },
): Promise<AnalyzeResult> {
  const res = await apiFetch('/br/wallet/onchain-analyze', {
    method: 'POST',
    token,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'On-chain analyze failed');
  }
  return res.json();
}

export interface BrPortfolio {
  id: number;
  country_code: string;
  name: string;
  base_currency: string;
}

export async function bootstrapBrPortfolio(token: string): Promise<BrPortfolio> {
  const res = await apiFetch('/br/portfolio', {
    method: 'GET',
    token,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Portfolio bootstrap failed');
  }
  return res.json();
}

/**
 * Сохранение выбора пользователя из onboarding
 */
export async function completeOnboarding(
  token: string,
  countryCode: string,
  taxStructure: string,
  portfolioSize: string
): Promise<{ status: string; portfolio_id: number; country_code: string; tax_structure: string; portfolio_size: string }> {
  const res = await apiFetch('/onboarding', {
    method: 'POST',
    token,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      country_code: countryCode,
      tax_structure: taxStructure,
      portfolio_size: portfolioSize,
    }),
  });

  if (!res.ok) {
    // Handle 403 Forbidden - email not verified
    if (res.status === 403) {
      const data = await res.json().catch(() => ({}));
      const detail = data.detail || 'Email verification required';
      
      const error = new Error(detail);
      (error as any).status = 403;
      (error as any).isEmailNotVerified = true;
      throw error;
    }
    
    const err = await res.text();
    throw new Error(err || 'Onboarding save failed');
  }

  return res.json();
}

/**
 * Email verification with token
 */
export async function verifyEmail(token: string): Promise<{ status: string; message: string }> {
  const res = await apiFetch('/auth/verify-email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ token }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Email verification failed');
  }

  return res.json();
}

/**
 * Request password reset (sends email)
 */
export async function requestPasswordReset(email: string): Promise<{ status: string; message: string }> {
  const res = await apiFetch('/auth/password-reset-request', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Password reset request failed');
  }

  return res.json();
}

/**
 * Reset password with token
 */
export async function resetPassword(token: string, newPassword: string): Promise<{ status: string; message: string }> {
  const res = await apiFetch('/auth/password-reset', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      token,
      new_password: newPassword,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Password reset failed');
  }

  return res.json();
}
