import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';

/**
 * WebSocketProvider — singleton React context that manages a single
 * WS connection to /ws/dashboard and dispatches events to type-specific
 * subscribers.  Wrap your <App /> (or router) with this provider once;
 * then use `useWebSocket()` for raw access or `useWebSocketData(type)`
 * for targeted subscriptions.
 *
 * Event types dispatched by the backend:
 *   VEHICLE_UPDATED   → vehicle card + side panel refresh
 *   BOOKING_CREATED   → bay calendar + KPI cards refresh
 *   BOOKING_CANCELLED → bay calendar refresh
 *   ALERT_FIRED       → flash alert banner + RUL histogram
 *   CONVERSATION_TURN → funnel chart + conversation log
 *   DIAGNOSIS_UPDATED → vehicle card + side panel + fleet health
 *   WORKFLOW_COMPLETED→ general refresh
 */

const WS_URL = 'ws://localhost:8001/ws/dashboard';
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
