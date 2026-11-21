import axios from 'axios';
import { API_BASE } from '../config';
import { clearSession, getAccessToken, getRefreshToken, saveSession } from './auth';

// One HTTP client for the whole dashboard: base URL, auth header, token refresh.
const api = axios.create({ baseURL: API_BASE, timeout: 20000 });

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing = null; // share one refresh between parallel 401s

async function refreshTokens() {
  const refresh_token = getRefreshToken();
  if (!refresh_token) throw new Error('No session');
  const { data } = await axios.post(`${API_BASE}/api/auth/refresh`, { refresh_token });
  saveSession(data);
  return data.access_token;
}

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const isAuthCall = original?.url?.includes('/api/auth/');
    if (error.response?.status === 401 && original && !original._retried && !isAuthCall) {
      original._retried = true;
      try {
        refreshing = refreshing || refreshTokens();
        const token = await refreshing;
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      } catch {
        clearSession();
        if (!window.location.pathname.startsWith('/login')) window.location.assign('/login');
      } finally {
        refreshing = null;
      }
    }
    return Promise.reject(error);
  },
);

export async function logout() {
  const refresh_token = getRefreshToken();
  if (refresh_token) {
    try {
      await axios.post(`${API_BASE}/api/auth/logout`, { refresh_token });
    } catch {
      /* already invalid: nothing to revoke */
    }
  }
  clearSession();
}

// Human-readable message from an API error.
export function errorMessage(err, fallback = 'Something went wrong') {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return fallback;
}

export default api;
