// Backend location. Set VITE_API_URL in `.env.local` (dev) or at build time (prod).
export const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8001').replace(/\/$/, '');

// ws:// or wss:// matching the API scheme.
export const WS_BASE = API_BASE.replace(/^http/, 'ws');
