import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export function storeRefreshedTokens(
  data: { access_token: string; refresh_token?: string },
  storage: Pick<Storage, 'setItem'> = localStorage,
) {
  storage.setItem('access_token', data.access_token);
  if (data.refresh_token) {
    storage.setItem('refresh_token', data.refresh_token);
  }
}

interface RefreshHandlerDependencies {
  storage?: Pick<Storage, 'getItem' | 'setItem' | 'clear'>;
  post?: typeof axios.post;
  retry?: (config: any) => Promise<any>;
  redirectToLogin?: () => void;
}

export async function handleResponseError(error: any, dependencies: RefreshHandlerDependencies = {}) {
  const original = error.config;
  const storage = dependencies.storage ?? localStorage;
  const post = dependencies.post ?? axios.post;
  const retry = dependencies.retry ?? ((config) => apiClient(config));
  const redirectToLogin = dependencies.redirectToLogin ?? (() => {
    window.location.href = '/login';
  });

  if (error.response?.status === 401 && original && !original._retry) {
    original._retry = true;
    try {
      const refresh = storage.getItem('refresh_token');
      const { data } = await post(`${API_BASE}/api/auth/refresh`, {
        refresh_token: refresh,
      });
      storeRefreshedTokens(data, storage);
      original.headers = original.headers ?? {};
      original.headers.Authorization = `Bearer ${data.access_token}`;
      return retry(original);
    } catch {
      storage.clear();
      redirectToLogin();
    }
  }
  return Promise.reject(error);
}

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  handleResponseError,
);
