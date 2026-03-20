import React, { createContext, useState, useRef, useCallback, useEffect, useContext } from 'react';
import { WS_BASE } from '../config';

const WS_URL = `${WS_BASE}/ws/dashboard`;
const MAX_RETRIES = 10;
const BASE_DELAY = 1000;

const WebSocketContext = createContext({
    lastEvent: null,
    connected: false,
    subscribe: () => () => {},
});

export function WebSocketProvider({ children }) {
    const [connected, setConnected] = useState(false);
    const [lastEvent, setLastEvent] = useState(null);
    const wsRef = useRef(null);
    const retriesRef = useRef(0);
    const timerRef = useRef(null);

    /**
     * Subscriber registry: Map<eventType, Set<callback>>
     * Callbacks receive the full event object.
     */
    const subscribersRef = useRef(new Map());

    /** Dispatch an event to type-specific subscribers + wildcard '*' */
    const dispatch = useCallback((event) => {
        const type = event?.type;
        // Notify type-specific subscribers
        if (type) {
            const set = subscribersRef.current.get(type);
            if (set) set.forEach((cb) => { try { cb(event); } catch (_) { /* noop */ } });
        }
        // Notify wildcard subscribers
        const wildcard = subscribersRef.current.get('*');
        if (wildcard) wildcard.forEach((cb) => { try { cb(event); } catch (_) { /* noop */ } });
    }, []);

    /** Subscribe to a specific event type (or '*' for all). Returns unsubscribe fn. */
    const subscribe = useCallback((eventType, callback) => {
        if (!subscribersRef.current.has(eventType)) {
            subscribersRef.current.set(eventType, new Set());
        }
        subscribersRef.current.get(eventType).add(callback);

        return () => {
            const set = subscribersRef.current.get(eventType);
            if (set) {
                set.delete(callback);
                if (set.size === 0) subscribersRef.current.delete(eventType);
            }
        };
    }, []);

    /** Connect / reconnect with exponential back-off */
    const connect = useCallback(() => {
        if (wsRef.current) {
            try { wsRef.current.close(); } catch (_) { /* noop */ }
        }
        try {
            const ws = new WebSocket(WS_URL);
            wsRef.current = ws;

            ws.onopen = () => {
                setConnected(true);
                retriesRef.current = 0;
            };

            ws.onmessage = (msg) => {
                try {
                    const data = JSON.parse(msg.data);
                    setLastEvent(data);
                    dispatch(data);
                } catch {
                    // Non-JSON — ignore
                }
            };

            ws.onerror = () => {};

            ws.onclose = () => {
                setConnected(false);
                wsRef.current = null;
                if (retriesRef.current < MAX_RETRIES) {
                    const delay = BASE_DELAY * Math.pow(2, retriesRef.current);
                    retriesRef.current += 1;
                    timerRef.current = setTimeout(connect, delay);
                }
            };
        } catch {
            setConnected(false);
        }
    }, [dispatch]);

    useEffect(() => {
        connect();
        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
            if (wsRef.current) {
                try { wsRef.current.close(); } catch (_) { /* noop */ }
            }
        };
    }, [connect]);

    return (
        <WebSocketContext.Provider value={{ lastEvent, connected, subscribe }}>
            {children}
        </WebSocketContext.Provider>
    );
}

/** Raw access — same API as the old useWebSocket hook */
export function useWebSocketContext() {
    return useContext(WebSocketContext);
}

export default WebSocketContext;
