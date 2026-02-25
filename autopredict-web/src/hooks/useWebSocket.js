import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * useWebSocket — connects to the dashboard WebSocket and exposes
 * the latest event so any dashboard can display live toast notifications.
 *
 * Usage:
 *   const { lastEvent, connected } = useWebSocket();
 *
 *   useEffect(() => {
 *     if (lastEvent) toast(`${lastEvent.type}: ${lastEvent.vehicle_id}`);
 *   }, [lastEvent]);
 *
 * The hook auto-reconnects on disconnect with exponential back-off.
 */

const WS_URL = 'ws://localhost:8000/ws/dashboard';
const MAX_RETRIES = 10;
const BASE_DELAY = 1000; // 1 s

export default function useWebSocket() {
  const [lastEvent, setLastEvent] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const retriesRef = useRef(0);
  const timerRef = useRef(null);

  const connect = useCallback(() => {
    // Cleanup any existing connection
    if (wsRef.current) {
      try { wsRef.current.close(); } catch (_) { /* noop */ }
    }

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retriesRef.current = 0; // reset back-off on success
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastEvent(data);
        } catch {
          // Non-JSON message — ignore
        }
      };

      ws.onerror = () => {
        // Error will trigger onclose
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;

        // Reconnect with exponential back-off
        if (retriesRef.current < MAX_RETRIES) {
          const delay = BASE_DELAY * Math.pow(2, retriesRef.current);
          retriesRef.current += 1;
          timerRef.current = setTimeout(connect, delay);
        }
      };
    } catch {
      // WebSocket constructor can throw if URL is malformed
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      // Cleanup on unmount
      if (timerRef.current) clearTimeout(timerRef.current);
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (_) { /* noop */ }
      }
    };
  }, [connect]);

  return { lastEvent, connected };
}
