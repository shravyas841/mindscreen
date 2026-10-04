import { describe, expect, it } from 'vitest';

import { clearAuthTokens, handleResponseError, storeRefreshedTokens } from './client';


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
  return {
    values,
    getItem(key: string) { return values[key] ?? null; },
    setItem(key: string, value: string) { values[key] = value; },
    removeItem(key: string) { delete values[key]; },
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

    expect(storage.values).toEqual({});
    expect(redirected).toBe(true);
  });

  it('does not call refresh without a refresh token or retry a request twice', async () => {
    const storage = memoryStorage({ unrelated: 'preserved' });
    let postCount = 0;
    const error = { response: { status: 401 }, config: { headers: {} } };

    await expect(handleResponseError(error, {
      storage,
      post: (async () => { postCount += 1; }) as any,
      retry: async () => { throw new Error('should not retry'); },
      redirectToLogin: () => undefined,
    })).rejects.toBe(error);
    expect(postCount).toBe(0);
    expect(storage.values).toEqual({ unrelated: 'preserved' });

    const retriedError = { response: { status: 401 }, config: { _retry: true } };
    await expect(handleResponseError(retriedError, {
      storage,
      post: (async () => { postCount += 1; }) as any,
    })).rejects.toBe(retriedError);
    expect(postCount).toBe(0);
  });

  it('uses one refresh request for concurrent 401 responses', async () => {
    const storage = memoryStorage({ access_token: 'old-access', refresh_token: 'old-refresh' });
    let postCount = 0;
    let finishRefresh: ((value: any) => void) | undefined;
    const post = (() => {
      postCount += 1;
      return new Promise((resolve) => { finishRefresh = resolve; });
    }) as any;
    let retryCount = 0;
    const retry = async (config: any) => {
      retryCount += 1;
      return config.headers.Authorization;
    };

    const first = handleResponseError(
      { response: { status: 401 }, config: { headers: {} } },
      { storage, post, retry, redirectToLogin: () => undefined },
    );
    const second = handleResponseError(
      { response: { status: 401 }, config: { headers: {} } },
      { storage, post, retry, redirectToLogin: () => undefined },
    );

    expect(postCount).toBe(1);
    finishRefresh?.({ data: { access_token: 'new-access', refresh_token: 'new-refresh' } });
    await expect(Promise.all([first, second])).resolves.toEqual([
      'Bearer new-access',
      'Bearer new-access',
    ]);
    expect(retryCount).toBe(2);
    expect(storage.values.refresh_token).toBe('new-refresh');
  });
});

describe('clearAuthTokens', () => {
  it('clears only authentication credentials during logout', () => {
    const storage = memoryStorage({
      access_token: 'access',
      refresh_token: 'refresh',
      assessment_draft: 'keep-me',
    });

    clearAuthTokens(storage);

    expect(storage.values).toEqual({ assessment_draft: 'keep-me' });
  });
});
