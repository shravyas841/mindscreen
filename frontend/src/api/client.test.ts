import { describe, expect, it } from 'vitest';

import { handleResponseError, storeRefreshedTokens } from './client';


describe('storeRefreshedTokens', () => {
  it('stores both tokens returned by refresh-token rotation', () => {
    const stored: Record<string, string> = {};
    const storage = {
      setItem(key: string, value: string) {
        stored[key] = value;
      },
    };

    storeRefreshedTokens(
      { access_token: 'new-access', refresh_token: 'new-refresh' },
      storage,
    );

    expect(stored).toEqual({
      access_token: 'new-access',
      refresh_token: 'new-refresh',
    });
  });
});

function memoryStorage(initial: Record<string, string> = {}) {
  const values = { ...initial };
  let cleared = false;
  return {
    values,
    get cleared() { return cleared; },
    getItem(key: string) { return values[key] ?? null; },
    setItem(key: string, value: string) { values[key] = value; },
    clear() {
      cleared = true;
      Object.keys(values).forEach((key) => delete values[key]);
    },
  };
}

describe('refresh response interceptor', () => {
  it('refreshes on 401, replaces both tokens, and retries with the new access token', async () => {
    const storage = memoryStorage({ access_token: 'old-access', refresh_token: 'old-refresh' });
    const refreshBodies: any[] = [];
    const retriedConfigs: any[] = [];
    const error = { response: { status: 401 }, config: { headers: {} } };

    const result = await handleResponseError(error, {
      storage,
      post: (async (_url: string, body: any) => {
        refreshBodies.push(body);
        return { data: { access_token: 'new-access', refresh_token: 'new-refresh' } };
      }) as any,
      retry: async (config) => {
        retriedConfigs.push(config);
        return { data: 'retried' };
      },
      redirectToLogin: () => { throw new Error('should not redirect'); },
    });

    expect(refreshBodies).toEqual([{ refresh_token: 'old-refresh' }]);
    expect(storage.values.access_token).toBe('new-access');
    expect(storage.values.refresh_token).toBe('new-refresh');
    expect(retriedConfigs[0].headers.Authorization).toBe('Bearer new-access');
    expect(result).toEqual({ data: 'retried' });

    await handleResponseError(
      { response: { status: 401 }, config: { headers: {} } },
      {
        storage,
        post: (async (_url: string, body: any) => {
          refreshBodies.push(body);
          return { data: { access_token: 'newer-access', refresh_token: 'newer-refresh' } };
        }) as any,
        retry: async (config) => config,
        redirectToLogin: () => { throw new Error('should not redirect'); },
      },
    );
    expect(refreshBodies[1]).toEqual({ refresh_token: 'new-refresh' });
  });

  it('clears tokens, redirects, and rejects when refresh fails', async () => {
    const storage = memoryStorage({ access_token: 'old-access', refresh_token: 'old-refresh' });
    let redirected = false;
    const error = { response: { status: 401 }, config: { headers: {} } };

    await expect(handleResponseError(error, {
      storage,
      post: (async () => { throw new Error('refresh failed'); }) as any,
      retry: async () => { throw new Error('should not retry'); },
      redirectToLogin: () => { redirected = true; },
    })).rejects.toBe(error);

    expect(storage.cleared).toBe(true);
    expect(redirected).toBe(true);
  });
});
