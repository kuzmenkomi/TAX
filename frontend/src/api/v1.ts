/**
 * Declairo API v1 Client
 * FastAPI REST API for authentication, portfolio, wallets, exchanges, and sync
 * 
 * Base URL: http://localhost:8000 (dev) / https://api.declairo.com (prod)
 * All endpoints use /v1 prefix (not /api/v1)
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const API_PREFIX = '/api/v1';

// ============================================================
// TYPES & INTERFACES
// ============================================================

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    created_at: string;
  };
}

export interface CurrentUser {
  id: string;
  email: string;
  created_at: string;
  is_active: boolean;
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

export interface PortfolioSummary {
  total_value_usd: number;
  total_value_brl: number;
  unrealized_pnl: {
    amount_usd: number;
    amount_brl: number;
    percentage: number;
  };
  by_blockchain: Record<string, number>;
  by_exchange: Record<string, number>;
  by_asset: Record<string, { value_usd: number; percentage: number }>;
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
  from_address: string;
  to_address: string;
  hash: string;
  blockchain: string;
  token: string;
  amount: number;
  value_usd: number;
  value_brl: number;
  timestamp: string;
  type: 'send' | 'receive' | 'swap' | 'contract' | 'nft' | 'bridge';
  status: 'pending' | 'completed' | 'failed';
}

export interface ExchangeConnection {
  id: string;
  user_id: string;
  exchange: string;
  api_key_encrypted: boolean;
  is_active: boolean;
  last_sync_at: string | null;
  created_at: string;
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

export interface SyncEnqueueResponse {
  job_id: string;
  status: string;
}

export interface HealthStatus {
  status: 'ok';
  timestamp: string;
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

export function getApiUrl(path: string): string {
  return `${BASE_URL}${API_PREFIX}${path.startsWith('/') ? path : `/${path}`}`;
}

const TOKEN_KEY = 'tax_auth_token_v1';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

interface FetchOptions extends RequestInit {
  useAuth?: boolean;
}

export async function apiFetch(
  path: string,
  options: FetchOptions = {},
): Promise<Response> {
  const { useAuth = true, ...fetchOptions } = options;
  
  const headers = new Headers(fetchOptions.headers);
  headers.set('Content-Type', 'application/json');
  
  if (useAuth) {
    const token = getToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  const response = await fetch(getApiUrl(path), {
    ...fetchOptions,
    headers,
  });

  // Handle 401 Unauthorized - clear token and redirect to login
  if (response.status === 401) {
    clearToken();
    window.location.href = '/login';
  }

  return response;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    
    // Handle different error formats
    let errorMessage = 'API Error';
    
    if (errorData.detail) {
      if (Array.isArray(errorData.detail)) {
        // Handle FastAPI validation error array
        errorMessage = errorData.detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
      } else {
        errorMessage = String(errorData.detail);
      }
    } else if (errorData.error) {
      // Handle Rate Limiter and other simple error objects
      errorMessage = String(errorData.error);
    } else if (errorData.message) {
      errorMessage = String(errorData.message);
    }
    
    throw new Error(errorMessage);
  }
  return response.json();
}

// ============================================================
// AUTHENTICATION API
// ============================================================

export const auth = {
  /**
   * Register new user
   */
  async register(email: string, password: string): Promise<AuthTokenResponse> {
    const response = await apiFetch('/auth/register', {
      method: 'POST',
      useAuth: false,
      body: JSON.stringify({ email, password }),
    });
    const data = await handleResponse<AuthTokenResponse>(response);
    setToken(data.access_token);
    return data;
  },

  /**
   * Login user
   */
  async login(email: string, password: string): Promise<AuthTokenResponse> {
    const response = await apiFetch('/auth/login', {
      method: 'POST',
      useAuth: false,
      body: JSON.stringify({ email, password }),
    });
    const data = await handleResponse<AuthTokenResponse>(response);
    setToken(data.access_token);
    return data;
  },

  /**
   * Get current user
   */
  async me(): Promise<CurrentUser> {
    const response = await apiFetch('/auth/me');
    return handleResponse<CurrentUser>(response);
  },

  /**
   * Logout (client-side only, clears token)
   */
  logout(): void {
    clearToken();
    window.location.href = '/login';
  },

  /**
   * Health check
   */
  async health(): Promise<HealthStatus> {
    const response = await apiFetch('/auth/health', { useAuth: false });
    return handleResponse<HealthStatus>(response);
  },
};

// ============================================================
// PORTFOLIO API
// ============================================================

export const portfolio = {
  /**
   * Get user portfolio summary
   */
  async getSummary(): Promise<PortfolioSummary> {
    const response = await apiFetch('/portfolio/summary');
    return handleResponse<PortfolioSummary>(response);
  },

  /**
   * Get full portfolio data
   */
  async get(): Promise<Portfolio> {
    const response = await apiFetch('/portfolio');
    return handleResponse<Portfolio>(response);
  },

  /**
   * Get unrealized P&L
   */
  async getUnrealizedPnL(): Promise<{
    amount_usd: number;
    amount_brl: number;
    percentage: number;
  }> {
    const response = await apiFetch('/portfolio/unrealized-pnl');
    return handleResponse(response);
  },
};

// ============================================================
// BLOCKCHAIN WALLET API
// ============================================================

export const wallet = {
  /**
   * Import blockchain wallet by address
   * 
   * @param blockchain - Blockchain network (ethereum, polygon, bsc, solana, etc)
   * @param address - Wallet address to import
   */
  async importBlockchain(
    blockchain: string,
    address: string,
  ): Promise<BlockchainWallet> {
    const response = await apiFetch('/wallet/import-blockchain', {
      method: 'POST',
      body: JSON.stringify({ blockchain, address }),
    });
    return handleResponse<BlockchainWallet>(response);
  },

  /**
   * Get wallet transactions
   */
  async getTransactions(
    walletId?: string,
    limit: number = 100,
    offset: number = 0,
  ): Promise<Transaction[]> {
    const params = new URLSearchParams();
    if (walletId) params.append('wallet_id', walletId);
    params.append('limit', String(limit));
    params.append('offset', String(offset));

    const response = await apiFetch(`/wallet/transactions?${params}`);
    return handleResponse<Transaction[]>(response);
  },

  /**
   * Get wallet holdings
   */
  async getHoldings(walletId?: string): Promise<Record<string, any>[]> {
    const params = new URLSearchParams();
    if (walletId) params.append('wallet_id', walletId);

    const response = await apiFetch(`/wallet/holdings?${params}`);
    return handleResponse(response);
  },
};

// ============================================================
// EXCHANGE API
// ============================================================

export const exchange = {
  /**
   * Connect exchange (add API keys)
   */
  async connect(
    exchange: string,
    apiKey: string,
    apiSecret: string,
  ): Promise<ExchangeConnection> {
    const response = await apiFetch('/exchange/connect', {
      method: 'POST',
      body: JSON.stringify({
        exchange,
        api_key: apiKey,
        api_secret: apiSecret,
      }),
    });
    return handleResponse<ExchangeConnection>(response);
  },

  /**
   * List connected exchanges
   */
  async listConnections(): Promise<ExchangeConnection[]> {
    const response = await apiFetch('/exchange/list');
    return handleResponse<ExchangeConnection[]>(response);
  },

  /**
   * Get exchange trades
   */
  async getTrades(
    exchange?: string,
    limit: number = 100,
    offset: number = 0,
  ): Promise<Transaction[]> {
    const params = new URLSearchParams();
    if (exchange) params.append('exchange', exchange);
    params.append('limit', String(limit));
    params.append('offset', String(offset));

    const response = await apiFetch(`/exchange/trades?${params}`);
    return handleResponse<Transaction[]>(response);
  },

  /**
   * Disconnect exchange
   */
  async disconnect(exchangeId: string): Promise<{ status: string }> {
    const response = await apiFetch(`/exchange/${exchangeId}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

// ============================================================
// SYNC & SCHEDULER API
// ============================================================

export const sync = {
  /**
   * Enqueue sync job
   */
  async enqueueJob(jobType: 'wallet_sync' | 'exchange_sync' | 'price_update'): Promise<SyncEnqueueResponse> {
    const response = await apiFetch('/sync/enqueue-job', {
      method: 'POST',
      body: JSON.stringify({ job_type: jobType }),
    });
    return handleResponse<SyncEnqueueResponse>(response);
  },

  /**
   * Get sync status and job history
   */
  async getStatus(): Promise<SyncStatus> {
    const response = await apiFetch('/sync/status');
    return handleResponse<SyncStatus>(response);
  },

  /**
   * Get sync settings (webhook to this function to adjust sync schedule)
   */
  async getSettings(): Promise<{
    wallet_sync_interval_hours: number;
    exchange_sync_interval_hours: number;
    price_update_interval_hours: number;
  }> {
    const response = await apiFetch('/sync/settings');
    return handleResponse(response);
  },
};

// ============================================================
// TAX EXPORTS API (Future)
// ============================================================

export const exports = {
  /**
   * Export GCAP (Brazilian tax form)
   */
  async gcap(): Promise<Blob> {
    const response = await apiFetch('/exports/gcap');
    if (!response.ok) throw new Error('GCAP export failed');
    return response.blob();
  },

  /**
   * Export DIRPF (Brazilian tax form)
   */
  async dirpf(): Promise<Blob> {
    const response = await apiFetch('/exports/dirpf');
    if (!response.ok) throw new Error('DIRPF export failed');
    return response.blob();
  },

  /**
   * Export IRPF XML
   */
  async irpfXml(): Promise<Blob> {
    const response = await apiFetch('/exports/irpf-xml');
    if (!response.ok) throw new Error('IRPF XML export failed');
    return response.blob();
  },
};

// ============================================================
// DEFI API (Future)
// ============================================================

export const defi = {
  /**
   * Get DeFi events
   */
  async getEvents(): Promise<Record<string, any>[]> {
    const response = await apiFetch('/defi/events');
    return handleResponse(response);
  },

  /**
   * Get DeFi protocol holdings
   */
  async getHoldings(): Promise<Record<string, any>[]> {
    const response = await apiFetch('/defi/holdings');
    return handleResponse(response);
  },
};

// ============================================================
// TAX & JURISDICTION API
// ============================================================

export const tax = {
  /**
   * Get all supported jurisdictions metadata
   */
  async getJurisdictions(): Promise<any[]> {
    const response = await apiFetch('/tax/jurisdictions', { useAuth: false });
    return handleResponse<any[]>(response);
  },

  /**
   * Get metadata for a specific jurisdiction
   */
  async getJurisdiction(code: string): Promise<any> {
    const response = await apiFetch(`/tax/jurisdiction/${code}`, { useAuth: false });
    return handleResponse<any>(response);
  },

  /**
   * Export tax report (PDF/XML)
   */
  async exportReport(code: string, year: number, format: 'pdf' | 'xml' = 'pdf'): Promise<Blob> {
    const response = await apiFetch(`/tax/export/${code}/${year}?format=${format}`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error(`Export failed: ${response.statusText}`);
    return response.blob();
  }
};

// ============================================================
// ANALYSIS API (Future)
// ============================================================

export const analysis = {
  /**
   * Get tax analysis (P&L, tax breakdown, etc)
   */
  async getTaxAnalysis(): Promise<Record<string, any>> {
    const response = await apiFetch('/analysis/tax');
    return handleResponse(response);
  },

  /**
   * Get portfolio analysis (allocation, performance, etc)
   */
  async getPortfolioAnalysis(): Promise<Record<string, any>> {
    const response = await apiFetch('/analysis/portfolio');
    return handleResponse(response);
  },
};

// ============================================================
// PLUGINS API
// ============================================================

export const plugins = {
  /**
   * List all DeFi plugins
   */
  async list(): Promise<{ status: string; count: number; plugins: any[] }> {
    const response = await apiFetch('/plugins', { useAuth: true });
    return handleResponse(response);
  },

  /**
   * Reload plugins
   */
  async reload(): Promise<{ status: string; message: string }> {
    const response = await apiFetch('/plugins/reload', {
      method: 'POST',
      useAuth: true,
    });
    return handleResponse(response);
  },
};

// ============================================================
// DEFAULT EXPORTS
// ============================================================

export default {
  auth,
  portfolio,
  wallet,
  exchange,
  sync,
  exports,
  defi,
  analysis,
  tax,
  plugins,
  // Utils
  getToken,
  setToken,
  clearToken,
};
