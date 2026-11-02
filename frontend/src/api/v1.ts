/**
 * Declairo API v1 Client
 * Unified client for authentication, portfolio, wallets, exchanges, sync, and reconciliation.
 * 
 * All paths are relative to /api/v1
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const API_PREFIX = '/api/v1';

// ============================================================
// TYPES & INTERFACES
// ============================================================

export interface HealthStatus {
  status: string;
}

export interface AuthTokenResponse {
  access_token: string | null;
  refresh_token: string | null;
  token_type: string;
  user: {
    id: string;
    email: string;
    created_at: string;
  } | null;
  requires_two_factor?: boolean;
  two_factor_token?: string | null;
}

export interface CurrentUser {
  id: string;
  email: string;
  created_at?: string;
  is_active?: boolean;
  is_email_verified?: boolean;
  role?: string;
  two_factor_enabled?: boolean;
  jurisdiction_code?: string;
  jurisdiction_name?: string;
  impersonation?: Record<string, unknown> | null;
  /** ISO8601; support may impersonate only while now < this time (customer-controlled). */
  allow_support_until?: string | null;
  support_access_active?: boolean;
}

export interface Portfolio {
  id: string;
  user_id: string;
  total_value_usd: number;
  total_value_brl: number;
  unrealized_pnl_usd: number;
  unrealized_pnl_brl: number;
  total_gain_usd: number;
  total_gain_brl: number;
  asset_count: number;
  updated_at: string;
}

/** Row from GET /portfolio/summary `positions` (backend PortfolioPosition). */
export interface PortfolioPositionRow {
  asset: string;
  quantity: number;
  avg_cost_usd?: number;
  current_price_usd?: number;
  cost_basis_usd?: number;
  current_value_usd?: number;
  unrealized_pnl_usd?: number;
  unrealized_pnl_pct?: number;
}

/**
 * GET /portfolio/summary — backend DashboardResponse.
 * Optional fields cover empty dashboards and older client expectations.
 */
export interface PortfolioSummary {
  portfolio_id?: number;
  total_cost_basis_usd?: number;
  total_current_value_usd?: number;
  total_unrealized_pnl_usd?: number;
  total_unrealized_pnl_pct?: number;
  positions?: PortfolioPositionRow[];
  last_updated?: string | null;
  parallel_rate?: number;
  total_current_value_ars_blue?: number;
  is_parallel?: boolean;
  /** Legacy / alternate shape */
  total_value_usd?: number;
  total_value_brl?: number;
  unrealized_pnl?: {
    amount_usd: number;
    amount_brl: number;
    percentage: number;
  };
  by_blockchain?: Record<string, number>;
  by_exchange?: Record<string, number>;
  by_asset?: Record<string, { value_usd: number; percentage: number }>;
}

export interface BlockchainWallet {
  id: string;
  user_id: string;
  blockchain: string;
  address: string;
  balance_usd: number;
  balance_brl: number;
  sync_status: 'pending' | 'syncing' | 'completed' | 'failed';
  last_sync_at: string | null;
  created_at: string;
}

export interface Transaction {
  id: string;
  from_address?: string;
  to_address?: string;
  hash?: string;
  blockchain: string;
  token: string;
  amount: number;
  value_usd: number;
  value_brl?: number;
  timestamp: string;
  type: string;
  category?: 'TRADE' | 'TRANSFER' | 'INCOME' | 'OTHER';
  status: 'pending' | 'completed' | 'failed';
  source?: 'csv' | 'wallet';
  source_method?: 'csv' | 'wallet' | 'api';
  import_format?: string;
  run_id?: number | null;
  wallet_id?: string | number | null;
  connection_id?: string | number | null;
  fee?: number;
}

export interface ExchangeConnection {
  id: number;
  user_id?: string;
  exchange?: string;
  exchange_name?: string;
  label?: string | null;
  api_key_encrypted?: boolean;
  is_active?: boolean;
  last_sync_at: string | null;
  last_synced?: string | null;
  created_at?: string;
  status?: string;
  transaction_count?: number;
  balance?: number;
}

export interface SyncJob {
  id: string;
  user_id: string;
  job_type: 'wallet_sync' | 'exchange_sync' | 'price_update';
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface SyncStatus {
  scheduler_running: boolean;
  jobs: SyncJob[];
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
  sell_tx_id?: string | number;
  [key: string]: unknown;
}

export interface DataIssue {
  id: number;
  run_id: number;
  tx_index: number;
  asset: string;
  amount: number;
  issue_type: string;
  severity: string;
  description: string;
  resolved: boolean;
  [key: string]: unknown;
}

export interface TaxSavingsOpportunity {
  asset?: string;
  message_pt?: string;
  [key: string]: unknown;
}

export interface AnalyzeResult {
  status: string;
  filename: string | string[];
  rows_processed: number;
  matches_found: number;
  matches?: MatchEntry[];       // legacy — may not be present
  lot_matches?: MatchEntry[];   // buy→sell tax pairs (primary)
  transfer_matches?: MatchEntry[]; // wallet-to-wallet transfers
  pnl: any;
  issues?: DataIssue[];
  analysis_run_id?: number;
  quote_currency?: string;
  use_ptax?: boolean;
  accounting_method?: string;
  income_events?: { total?: number; [key: string]: unknown };
  monthly_sales_brl?: Record<string, number>;
  isencao_threshold_brl?: number;
  offshore_onshore?: {
    decripto_required?: boolean;
    decripto_alert?: string;
    [key: string]: unknown;
  };
  tax_savings_opportunities?: TaxSavingsOpportunity[];
  duplicate?: boolean;
  tx_imported?: number;
  tx_skipped?: number;
}

export interface RunHistoryItem {
  id?: number;
  run_id?: number;
  filename?: string;
  created_at?: string;
  accounting_method?: string;
  realized_pnl?: number | null;
  quote_currency?: string | null;
  format?: string;
  rows_processed?: number;
  [key: string]: unknown;
}

export interface PluginInfo {
  name: string;
  version: string;
  supported_chains: string[];
  supported_events: string[];
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

export function getApiUrl(path: string): string {
  if (/^https?:\/\//.test(path)) return path;
  return `${BASE_URL}${API_PREFIX}${path.startsWith('/') ? path : `/${path}`}`;
}

const CSRF_COOKIE = 'csrf_token';

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

/** @deprecated Auth uses httpOnly cookies; tokens are not in localStorage. */
export function getToken(): string | null {
  return null;
}

/** @deprecated */
export function getRefreshToken(): string | null {
  return null;
}

/** @deprecated No-op; session is cookie-based. */
export function setToken(_token: string, _refreshToken?: string): void {}

/** @deprecated No-op; session is cookie-based. */
export function clearToken(): void {}

function csrfHeader(): Record<string, string> {
  const t = getCookie(CSRF_COOKIE);
  return t ? { 'X-CSRF-Token': t } : {};
}

interface FetchOptions extends RequestInit {
  useAuth?: boolean;
  token?: string | null;
}

let refreshSessionPromise: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  if (refreshSessionPromise) {
    return refreshSessionPromise;
  }
  refreshSessionPromise = (async () => {
    try {
      const refreshHeaders = new Headers({ 'Content-Type': 'application/json' });
      Object.entries(csrfHeader()).forEach(([k, v]) => refreshHeaders.set(k, v));
      const refreshRes = await fetch(getApiUrl('/auth/refresh'), {
        method: 'POST',
        credentials: 'include',
        headers: refreshHeaders,
        body: JSON.stringify({}),
      });
      return refreshRes.ok;
    } catch {
      return false;
    } finally {
      refreshSessionPromise = null;
    }
  })();
  return refreshSessionPromise;
}

function buildHeaders(fetchOptions: RequestInit, useAuth: boolean, explicitToken: string | null | undefined): Headers {
  const headers = new Headers(fetchOptions.headers);
  const isForm = fetchOptions.body instanceof FormData;
  if (!headers.has('Content-Type') && !isForm) {
    headers.set('Content-Type', 'application/json');
  }
  Object.entries(csrfHeader()).forEach(([k, v]) => {
    if (!headers.has(k)) headers.set(k, v);
  });
  const token = explicitToken ?? null;
  if (useAuth && token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return headers;
}

export async function apiFetch(
  path: string,
  options: FetchOptions = {},
): Promise<Response> {
  const { useAuth = true, token: explicitToken, ...fetchOptions } = options;

  // For FormData (file uploads): proactively refresh session BEFORE sending,
  // since FormData body stream is consumed on first read and cannot be retried.
  const isFormData = fetchOptions.body instanceof FormData;
  if (isFormData && useAuth && !path.includes('/auth/refresh')) {
    await refreshSession();
  }

  const doFetch = async () => {
    try {
      return await fetch(getApiUrl(path), {
        ...fetchOptions,
        credentials: 'include',
        headers: buildHeaders(fetchOptions, useAuth, explicitToken),
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : '';
      if (message === 'Failed to fetch') {
        throw new Error('Unable to reach the server. Please check your connection or backend status and try again.');
      }
      throw error;
    }
  };

  let response = await doFetch();

  if (response.status === 401 && useAuth && !path.includes('/auth/refresh') && !isFormData) {
    const ok = await refreshSession();
    if (ok) {
      response = await doFetch();
    }
  }

  return response;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    let errorMessage = errorData.detail || errorData.error || errorData.message || 'API Error';
    if (typeof errorMessage === 'object' && errorMessage !== null) {
      const detailObj = errorMessage as Record<string, any>;
      errorMessage = detailObj.message || detailObj.error || JSON.stringify(detailObj);
    }
    if (Array.isArray(errorMessage)) {
      errorMessage = errorMessage.map((e: any) => e.msg || JSON.stringify(e)).join(', ');
    }
    throw new Error(String(errorMessage));
  }
  return response.json();
}

// ============================================================
// API MODULES
// ============================================================

export const auth = {
  async register(email: string, password: string) {
    const res = await apiFetch('/auth/register', {
      method: 'POST',
      useAuth: false,
      body: JSON.stringify({ email, password }),
    });
    return handleResponse<AuthTokenResponse>(res);
  },

  async login(email: string, password: string) {
    const res = await apiFetch('/auth/login', {
      method: 'POST',
      useAuth: false,
      body: JSON.stringify({ email, password }),
    });
    return handleResponse<AuthTokenResponse>(res);
  },

  async completeLoginTwoFactor(twoFactorToken: string, code: string) {
    const res = await apiFetch('/auth/login/2fa', {
      method: 'POST',
      useAuth: false,
      body: JSON.stringify({ two_factor_token: twoFactorToken, code }),
    });
    return handleResponse<AuthTokenResponse>(res);
  },

  async refresh(_refreshToken?: string): Promise<AuthTokenResponse> {
    const res = await apiFetch('/auth/refresh', {
      method: 'POST',
      useAuth: false,
      body: JSON.stringify({}),
    });
    return handleResponse<AuthTokenResponse>(res);
  },

  async logout(): Promise<void> {
    const res = await apiFetch('/auth/logout', { method: 'POST' });
    if (!res.ok && res.status !== 401) {
      await handleResponse(res);
    }
  },

  async me(): Promise<CurrentUser> {
    const res = await apiFetch('/auth/me');
    return handleResponse<CurrentUser>(res);
  },

  async updateSupportAccess(allow: boolean): Promise<{
    allow_support_until: string | null;
    support_access_active: boolean;
  }> {
    const res = await apiFetch('/auth/me/support-access', {
      method: 'PATCH',
      body: JSON.stringify({ allow }),
    });
    return handleResponse(res);
  },

  async verifyEmail(token: string): Promise<{ message?: string }> {
    const res = await apiFetch('/auth/verify-email', {
      method: 'POST',
      useAuth: false,
      body: JSON.stringify({ token }),
    });
    return handleResponse<{ message?: string }>(res);
  },

  async health(): Promise<HealthStatus> {
    const response = await apiFetch('/auth/health', { useAuth: false });
    return handleResponse<HealthStatus>(response);
  },

  async completeOnboarding(
    countryCode: string,
    taxStructure: string,
    portfolioSize: string
  ) {
    const res = await apiFetch('/onboarding', {
      method: 'POST',
      body: JSON.stringify({
        country_code: countryCode,
        tax_structure: taxStructure,
        portfolio_size: portfolioSize,
      }),
    });
    return handleResponse(res);
  },

  async requestPasswordReset(email: string) {
    const res = await apiFetch('/auth/password-reset-request', {
      method: 'POST',
      useAuth: false,
      body: JSON.stringify({ email }),
    });
    return handleResponse(res);
  },

  async resetPassword(token: string, password: string) {
    const res = await apiFetch('/auth/password-reset', {
      method: 'POST',
      useAuth: false,
      body: JSON.stringify({ token, new_password: password }),
    });
    return handleResponse(res);
  },
};

export const portfolio = {
  async getSummary(params?: { tax_year?: number }): Promise<PortfolioSummary> {
    const qs = params
      ? `?${new URLSearchParams(
          Object.entries(params)
            .filter(([, value]) => value !== undefined && value !== null)
            .map(([key, value]) => [key, String(value)]),
        )}`
      : '';
    const res = await apiFetch(`/portfolio/summary${qs}`);
    return handleResponse<PortfolioSummary>(res);
  },

  async get(): Promise<Portfolio> {
    const res = await apiFetch('/portfolio');
    return handleResponse<Portfolio>(res);
  },

  async bootstrapBr(): Promise<any> {
    const res = await apiFetch('/br/portfolio');
    return handleResponse(res);
  }
};

export const wallet = {
  async list(): Promise<any> {
    const res = await apiFetch('/br/connections');
    return handleResponse(res);
  },

  async connect(chain: string, address: string, label?: string) {
    const res = await apiFetch('/br/wallet', {
      method: 'POST',
      body: JSON.stringify({ chain, address, label }),
    });
    return handleResponse(res);
  },

  async importBlockchain(chain: string, address: string, label?: string) {
    const res = await apiFetch('/br/wallet/import-blockchain', {
      method: 'POST',
      body: JSON.stringify({ chain, address, label }),
    });
    return handleResponse(res);
  },

  async getTransactions(
    walletId?: string,
    limit = 100,
    offset = 0,
    category?: 'TRADE' | 'TRANSFER' | 'INCOME' | 'OTHER',
    runId?: number,
  ): Promise<Transaction[]> {
    const params = new URLSearchParams();
    if (walletId) params.append('wallet_id', walletId);
    if (runId != null) params.append('run_id', String(runId));
    if (category) params.append('category', category);
    params.append('limit', String(limit));
    params.append('offset', String(offset));
    const res = await apiFetch(`/br/wallet/transactions?${params}`);
    return handleResponse<Transaction[]>(res);
  },

  async sync(walletId: number) {
    const res = await apiFetch(`/br/wallet/${walletId}/sync`, { method: 'POST' });
    return handleResponse(res);
  },

  async disconnect(walletId: number) {
    const res = await apiFetch(`/br/wallet/${walletId}`, { method: 'DELETE' });
    return handleResponse(res);
  }
};

export const exchange = {
  async listSupported(): Promise<any[]> {
    const res = await apiFetch('/br/exchanges');
    return handleResponse(res);
  },

  async listMy(): Promise<ExchangeConnection[]> {
    const res = await apiFetch('/br/exchanges/my');
    return handleResponse<ExchangeConnection[]>(res);
  },

  async connect(exchangeName: string, apiKey: string, apiSecret: string, passphrase?: string, label?: string) {
    const res = await apiFetch('/br/exchange/connect', {
      method: 'POST',
      body: JSON.stringify({ exchange_name: exchangeName, api_key: apiKey, api_secret: apiSecret, passphrase, label }),
    });
    return handleResponse(res);
  },

  async disconnect(exchangeId: number) {
    const res = await apiFetch(`/br/exchange/${exchangeId}`, { method: 'DELETE' });
    return handleResponse(res);
  },

  async sync(exchangeId: number) {
    const res = await apiFetch(`/br/exchange/${exchangeId}/sync`, { method: 'POST' });
    return handleResponse(res);
  }
};

export const sync = {
  async getStatus(): Promise<SyncStatus> {
    const res = await apiFetch('/br/sync/status');
    return handleResponse<SyncStatus>(res);
  },

  async getDetailedStatus(): Promise<any> {
    const res = await apiFetch('/sync-settings/status');
    return handleResponse(res);
  },

  async toggleAutoSync(type: 'wallet' | 'exchange', id: number, enabled: boolean) {
    const res = await apiFetch(`/sync-settings/${type}/${id}/auto-sync`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled }),
    });
    return handleResponse(res);
  },

  async enqueue(type: 'exchange' | 'wallet', id: number) {
    const res = await apiFetch('/br/sync/enqueue', {
      method: 'POST',
      body: JSON.stringify({ connection_type: type, connection_id: id }),
    });
    return handleResponse(res);
  },

  async triggerAllWallets() {
    return handleResponse(await apiFetch('/br/sync/wallets', { method: 'POST' }));
  },

  async triggerAllExchanges() {
    return handleResponse(await apiFetch('/br/sync/exchanges', { method: 'POST' }));
  },

  async triggerPrices() {
    return handleResponse(await apiFetch('/br/sync/prices', { method: 'POST' }));
  }
};

export const analysis = {
  async upload(file: File, params: any): Promise<AnalyzeResult> {
    const formData = new FormData();
    formData.append('file', file);
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined) formData.append(key, String(params[key]));
    });
    const res = await apiFetch('/analyze-upload', { method: 'POST', body: formData });
    return handleResponse<AnalyzeResult>(res);
  },

  async uploadMulti(files: File[], params: any): Promise<AnalyzeResult> {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined) formData.append(key, String(params[key]));
    });
    const res = await apiFetch('/analyze-upload-multi', { method: 'POST', body: formData });
    return handleResponse<AnalyzeResult>(res);
  },

  async listRuns(): Promise<{ runs?: RunHistoryItem[] }> {
    const res = await apiFetch('/br/runs');
    return handleResponse<{ runs?: RunHistoryItem[] }>(res);
  },

  async deleteRun(runId: number): Promise<{ status: string; run_id: number }> {
    const res = await apiFetch(`/br/runs/${runId}`, { method: 'DELETE' });
    return handleResponse(res);
  },

  async analyzeSources(params: {
    source_ids: string[];
    accounting_method: string;
    country: string;
    use_ptax?: boolean;
    auto_classify?: boolean;
  }): Promise<AnalyzeResult> {
    const res = await apiFetch('/br/analysis/from-sources', {
      method: 'POST',
      body: JSON.stringify(params),
      useAuth: true,
    });
    return handleResponse<AnalyzeResult>(res);
  },

  async getTaxAnalysis(params?: any): Promise<any> {
    const qs = params ? `?${new URLSearchParams(params)}` : '';
    const res = await apiFetch(`/br/analysis/latest${qs}`, { useAuth: true });
    return handleResponse(res);
  }
};

export const reconciliation = {
  async listIssues(runId: number, resolved?: boolean) {
    const res = await apiFetch(`/reconciliation/issues/${runId}${resolved !== undefined ? `?resolved=${resolved}` : ''}`);
    return handleResponse(res);
  },

  async resolve(issueId: number, resolution: string, costBasis?: number) {
    const res = await apiFetch('/reconciliation/resolve', {
      method: 'POST',
      body: JSON.stringify({ issue_id: issueId, resolution, cost_basis_override: costBasis }),
    });
    return handleResponse(res);
  },

  async bulkResolve(data: { issue_ids: number[], resolution: string, cost_basis_override?: number }) {
    const res = await apiFetch('/reconciliation/bulk-resolve', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  }
};

export interface JurisdictionDetectResult {
  jurisdiction_code: string;
  jurisdiction_name: string;
  base_currency: string;
  applied_now: boolean;
  geo_jurisdiction_applied: boolean;
  country_locked: boolean;
  source?: string | null;
  cf_country?: string | null;
}

export const tax = {
  async getJurisdictions() {
    return handleResponse(await apiFetch('/tax/jurisdictions', { useAuth: false }));
  },

  async autoDetectJurisdiction(): Promise<JurisdictionDetectResult> {
    const res = await apiFetch('/tax/jurisdiction/auto-detect', { method: 'POST' });
    return handleResponse<JurisdictionDetectResult>(res);
  },

  async setJurisdiction(jurisdictionCode: string): Promise<JurisdictionDetectResult> {
    const res = await apiFetch('/tax/jurisdiction', {
      method: 'PUT',
      body: JSON.stringify({ jurisdiction_code: jurisdictionCode }),
    });
    return handleResponse<JurisdictionDetectResult>(res);
  },

  async exportReport(runId: number, format: 'br' | 'gcap' | 'decripto' | 'dirpf' | 'audit') {
    const res = await apiFetch(`/exports/${format}/${runId}`);
    if (!res.ok) throw new Error(`Export ${format} failed`);
    return res.blob();
  }
};

export const plugins = {
  async list(): Promise<{ plugins: PluginInfo[]; count: number }> {
    const res = await apiFetch('/plugins', { useAuth: false });
    return handleResponse<{ plugins: PluginInfo[]; count: number }>(res);
  },

  async reload(): Promise<{ status: string; message?: string }> {
    const res = await apiFetch('/plugins/reload', { method: 'POST' });
    return handleResponse<{ status: string; message?: string }>(res);
  },
};

export const billing = {
  async getStatus() {
    return handleResponse(await apiFetch('/billing/status'));
  },

  async createCheckout(plan: string, successUrl: string, cancelUrl: string) {
    const res = await apiFetch('/billing/checkout', {
      method: 'POST',
      body: JSON.stringify({ plan, success_url: successUrl, cancel_url: cancelUrl }),
    });
    return handleResponse<{ url: string }>(res);
  }
};

export const twoFactor = {
  async status(): Promise<{ enabled: boolean; pending_setup: boolean }> {
    return handleResponse(await apiFetch('/auth/2fa/status'));
  },

  async setupBegin(): Promise<{ otpauth_uri: string; issuer: string }> {
    const res = await apiFetch('/auth/2fa/setup/begin', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    return handleResponse(res);
  },

  async setupConfirm(code: string): Promise<void> {
    const res = await apiFetch('/auth/2fa/setup/confirm', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
    if (!res.ok) await handleResponse(res);
  },

  async setupCancel(): Promise<void> {
    const res = await apiFetch('/auth/2fa/setup/cancel', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    if (!res.ok) await handleResponse(res);
  },

  async disable(password: string, code: string): Promise<void> {
    const res = await apiFetch('/auth/2fa/disable', {
      method: 'POST',
      body: JSON.stringify({ password, code }),
    });
    if (!res.ok) await handleResponse(res);
  },
};

export const supportStaff = {
  async impersonationStart(payload: { user_id?: number; email?: string; reason: string }) {
    const res = await apiFetch('/support/staff/impersonation/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return handleResponse<{
      access_token: string;
      expires_in: number;
      token_type: string;
      subject: { id: number; email: string };
    }>(res);
  },

  async impersonationEnd(): Promise<{ status: string; message?: string }> {
    const res = await apiFetch('/support/staff/impersonation/end', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    return handleResponse(res);
  },

  async impersonationStatus(): Promise<{
    active: boolean;
    actor_email?: string;
    subject_email?: string;
    log_id?: number;
  }> {
    return handleResponse(await apiFetch('/support/staff/impersonation/status'));
  },
};

export const reportsExport = {
  async generate(format: 'csv' | 'pdf', runId: number): Promise<{ task_id: string; status: 'completed' | 'processing' | 'failed'; row_count?: number }> {
    const res = await apiFetch('/exports/generate', {
      method: 'POST',
      body: JSON.stringify({ format, run_id: runId }),
    });
    return handleResponse(res);
  },

  async checkStatus(taskId: string): Promise<{ task_id: string; status: 'completed' | 'processing' | 'failed'; progress: number; message: string; error: string | null }> {
    const res = await apiFetch(`/exports/status/${taskId}`);
    return handleResponse(res);
  },

  async download(taskId: string): Promise<Blob> {
    const res = await apiFetch(`/exports/download/${taskId}`);
    if (!res.ok) throw new Error(`Download of export task ${taskId} failed`);
    return res.blob();
  },

  async planCheck(): Promise<{ can_export: boolean; plan: string; upgrade_required: boolean }> {
    const res = await apiFetch('/exports/plan-check');
    return handleResponse(res);
  },
};

export default {
  auth,
  portfolio,
  wallet,
  exchange,
  sync,
  analysis,
  reconciliation,
  tax,
  billing,
  twoFactor,
  supportStaff,
  plugins,
  exports: reportsExport,
  // Utils
  getApiUrl,
  getToken,
  setToken,
  clearToken,
};
