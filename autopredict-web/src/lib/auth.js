// Session storage for the dashboard (access token, refresh token, role).
// The access token is short-lived; the refresh token renews it.

const KEYS = { access: 'ap_token', refresh: 'ap_refresh', role: 'ap_role', email: 'ap_email' };

// Fired on sign-in / sign-out so long-lived connections (WebSocket) can follow.
export const SESSION_EVENT = 'ap:session-changed';
const announce = () => window.dispatchEvent(new Event(SESSION_EVENT));

export const ROLE_HOME = {
  ops: '/dashboard/operations',
  manager: '/dashboard/manager',
  executive: '/dashboard/executive',
  admin: '/dashboard/operations',
};

export function saveSession(tokens) {
  try {
    localStorage.setItem(KEYS.access, tokens.access_token);
    localStorage.setItem(KEYS.refresh, tokens.refresh_token);
    localStorage.setItem(KEYS.role, tokens.role);
    if (tokens.email) localStorage.setItem(KEYS.email, tokens.email);
  } catch {
    /* storage blocked: the session lasts for this page only */
  }
  announce();
}

export function clearSession() {
  try {
    Object.values(KEYS).forEach((k) => localStorage.removeItem(k));
  } catch {
    /* ignore */
  }
  announce();
}

const read = (key) => {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
};

export const getAccessToken = () => read(KEYS.access);
export const getRefreshToken = () => read(KEYS.refresh);
export const getRole = () => read(KEYS.role);
export const getEmail = () => read(KEYS.email);

// Reads the JWT payload for display/routing only. The server verifies every request.
export function tokenPayload(token = getAccessToken()) {
  if (!token) return null;
  try {
    const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(part.padEnd(part.length + ((4 - (part.length % 4)) % 4), '=')));
  } catch {
    return null;
  }
}

export function hasSession() {
  // An expired access token is fine while a refresh token exists; the API client renews it.
  return Boolean(getAccessToken() && getRefreshToken() && tokenPayload());
}
