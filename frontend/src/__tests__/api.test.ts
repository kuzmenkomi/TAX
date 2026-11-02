import { describe, it, expect } from 'vitest';
import { getToken, setToken, clearToken, getApiUrl } from '../api/v1';

describe('API client (cookie session)', () => {
  it('getToken is always null (httpOnly cookies)', () => {
    expect(getToken()).toBeNull();
  });

  it('setToken/clearToken are no-ops', () => {
    setToken('x');
    clearToken();
    expect(getToken()).toBeNull();
  });

  it('getApiUrl builds versioned path', () => {
    expect(getApiUrl('/auth/health')).toMatch(/\/api\/v1\/auth\/health$/);
  });
});
