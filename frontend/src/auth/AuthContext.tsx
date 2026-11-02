import { createContext, useContext, useEffect, useMemo, useState, useCallback, ReactNode } from 'react';
import { auth, type CurrentUser } from '../api/v1';

const STORAGE_KEY = 'tax_auth_user_v1';

export type AuthUser = {
  id: string;
  email: string;
  created_at: string;
  is_active?: boolean;
  role?: string;
  two_factor_enabled?: boolean;
  jurisdiction_code?: string;
  jurisdiction_name?: string;
  impersonation?: CurrentUser['impersonation'];
};

function meToAuthUser(me: CurrentUser): AuthUser {
  return {
    id: String(me.id),
    email: me.email,
    created_at: me.created_at ?? '',
    is_active: me.is_active,
    role: me.role,
    two_factor_enabled: me.two_factor_enabled,
    jurisdiction_code: me.jurisdiction_code,
    jurisdiction_name: me.jurisdiction_name,
    impersonation: me.impersonation,
  };
}

export class TwoFactorRequiredError extends Error {
  readonly twoFactorToken: string;
  constructor(twoFactorToken: string) {
    super('Two-factor authentication required');
    this.name = 'TwoFactorRequiredError';
    this.twoFactorToken = twoFactorToken;
  }
}

type AuthState = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
  registerWithPassword: (email: string, password: string) => Promise<void>;
  loginWithPassword: (email: string, password: string) => Promise<void>;
  completeTwoFactorLogin: (twoFactorToken: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  error: string | null;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await auth.health().catch(() => undefined);
        const me = await auth.me().catch(() => null);
        if (cancelled) return;
        if (me) {
          const userData = meToAuthUser(me);
          setUser(userData);
          try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
          } catch {
            /* ignore */
          }
        } else {
          setUser(null);
          localStorage.removeItem(STORAGE_KEY);
        }
      } catch (err) {
        console.error('Failed to restore session:', err);
        setUser(null);
        localStorage.removeItem(STORAGE_KEY);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshUser = useCallback(async () => {
    const me = await auth.me();
    const userData = meToAuthUser(me);
    setUser(userData);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo<AuthState>(() => {
    return {
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      token: null,
      error,
      refreshUser,

      registerWithPassword: async (email: string, password: string) => {
        try {
          setError(null);
          const result = await auth.register(email, password);
          if (!result.user) throw new Error('Registration failed');
          const userData: AuthUser = {
            id: String(result.user.id),
            email: result.user.email,
            created_at: result.user.created_at,
          };
          setUser(userData);
          try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
          } catch {
            /* ignore */
          }
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : 'Registration failed';
          setError(errorMsg);
          throw err;
        }
      },

      loginWithPassword: async (email: string, password: string) => {
        try {
          setError(null);
          const result = await auth.login(email, password);
          if (result.requires_two_factor && result.two_factor_token) {
            throw new TwoFactorRequiredError(result.two_factor_token);
          }
          if (!result.user) throw new Error('Login failed');
          const userData: AuthUser = {
            id: String(result.user.id),
            email: result.user.email,
            created_at: result.user.created_at,
          };
          setUser(userData);
          try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
          } catch {
            /* ignore */
          }
          const me = await auth.me().catch(() => null);
          if (me) {
            const full = meToAuthUser(me);
            setUser(full);
            try {
              localStorage.setItem(STORAGE_KEY, JSON.stringify(full));
            } catch {
              /* ignore */
            }
          }
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : 'Login failed';
          setError(errorMsg);
          throw err;
        }
      },

      completeTwoFactorLogin: async (twoFactorToken: string, code: string) => {
        try {
          setError(null);
          const result = await auth.completeLoginTwoFactor(twoFactorToken, code);
          if (!result.user) throw new Error('2FA verification failed');
          const userData: AuthUser = {
            id: String(result.user.id),
            email: result.user.email,
            created_at: result.user.created_at,
          };
          setUser(userData);
          try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
          } catch {
            /* ignore */
          }
          const me = await auth.me().catch(() => null);
          if (me) {
            const full = meToAuthUser(me);
            setUser(full);
            try {
              localStorage.setItem(STORAGE_KEY, JSON.stringify(full));
            } catch {
              /* ignore */
            }
          }
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : '2FA failed';
          setError(errorMsg);
          throw err;
        }
      },

      logout: async () => {
        try {
          await auth.logout();
        } catch {
          /* ignore */
        }
        setUser(null);
        setError(null);
        localStorage.removeItem(STORAGE_KEY);
      },
    };
  }, [user, isLoading, error, refreshUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
