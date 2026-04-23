import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from 'react';
import { auth, setToken, clearToken } from '../api/v1';

const STORAGE_KEY = 'tax_auth_user_v1';
const TOKEN_KEY = 'tax_auth_token_v1';

export type AuthUser = {
  id: string;
  email: string;
  created_at: string;
  is_active?: boolean;
};

type AuthState = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
  registerWithPassword: (email: string, password: string) => Promise<void>;
  loginWithPassword: (email: string, password: string) => Promise<void>;
  logout: () => void;
  error: string | null;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load user from localStorage on mount
  useEffect(() => {
    try {
      const rawUser = localStorage.getItem(STORAGE_KEY);
      const rawToken = localStorage.getItem(TOKEN_KEY);
      
      if (rawUser && rawToken) {
        const parsed = JSON.parse(rawUser) as AuthUser;
        setUser(parsed);
        setTokenState(rawToken);
        // Also set it in the API client
        setToken(rawToken);
      }
    } catch (err) {
      console.error('Failed to load auth from storage:', err);
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(TOKEN_KEY);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const persistSession = (userData: AuthUser, accessToken: string) => {
    setUser(userData);
    setTokenState(accessToken);
    setToken(accessToken);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
    localStorage.setItem(TOKEN_KEY, accessToken);
    setError(null);
  };

  const value = useMemo<AuthState>(() => {
    return {
      user,
      isAuthenticated: Boolean(user && token),
      isLoading,
      token,
      error,

      registerWithPassword: async (email: string, password: string) => {
        try {
          setError(null);
          const result = await auth.register(email, password);
          const userData: AuthUser = {
            id: String(result.user.id),
            email: result.user.email,
            created_at: result.user.created_at,
          };
          persistSession(userData, result.access_token);
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
          const userData: AuthUser = {
            id: String(result.user.id),
            email: result.user.email,
            created_at: result.user.created_at,
          };
          persistSession(userData, result.access_token);
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : 'Login failed';
          setError(errorMsg);
          throw err;
        }
      },

      logout: () => {
        setUser(null);
        setTokenState(null);
        setError(null);
        clearToken();
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(TOKEN_KEY);
      },
    };
  }, [user, token, isLoading, error]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

