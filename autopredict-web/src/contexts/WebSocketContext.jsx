import React, { useState, useEffect, useRef, useCallback } from 'react';
import { WebSocketContext } from './webSocketContextObject';
import { WS_BASE } from '../config';
import api from '../lib/api';
import { SESSION_EVENT, clearSession, getAccessToken, hasSession } from '../lib/auth';

/**
 * WebSocketProvider — singleton React context that manages a single
 * WS connection to /ws/dashboard and dispatches events to type-specific
 * subscribers.  Wrap your <App /> (or router) with this provider once;
 * then use `useWebSocketContext()` and its `subscribe(type, callback)`
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

const MAX_RETRIES = 10;
const BASE_DELAY = 1000;


export function WebSocketProvider({ children }) {
    const [connected, setConnected] = useState(false);
    const wsRef = useRef(null);
    const retriesRef = useRef(0);
    const timerRef = useRef(null);
    const connectRef = useRef(() => {});

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
        if (timerRef.current) clearTimeout(timerRef.current);
        if (!hasSession()) {
            // Not signed in, or a leftover token from the old mock login: drop it, don't connect.
            if (getAccessToken()) clearSession();
            return;
        }
        const token = getAccessToken();
        try {
            // Browsers can't send headers on WebSockets, so the token goes in the query string.
            const ws = new WebSocket(`${WS_BASE}/ws/dashboard?token=${encodeURIComponent(token)}`);
            wsRef.current = ws;

            ws.onopen = () => {
                setConnected(true);
                retriesRef.current = 0;
            };

            ws.onmessage = (msg) => {
                try {
                    const data = JSON.parse(msg.data);
                    dispatch(data);
                } catch {
                    // Non-JSON — ignore
                }
            };

            ws.onerror = () => {};

            ws.onclose = (event) => {
                setConnected(false);
                wsRef.current = null;
                if (event.code === 4403) return; // signed in, but not a staff account
                if (retriesRef.current < MAX_RETRIES) {
                    const delay = BASE_DELAY * Math.pow(2, retriesRef.current);
                    retriesRef.current += 1;
                    // 4401 = token expired: any API call renews it via the shared client.
                    const renew = event.code === 4401 ? api.get('/api/auth/me').catch(() => null) : Promise.resolve();
                    renew.then(() => { timerRef.current = setTimeout(() => connectRef.current(), delay); });
                }
            };
        } catch (err) {
            console.warn('WebSocket connect failed:', err);
        }
    }, [dispatch]);

    useEffect(() => {
        connectRef.current = connect;
    }, [connect]);

    useEffect(() => {
        connect();
        // Reconnect on sign-in / sign-out (saveSession and clearSession fire this event).
        const onSession = () => { retriesRef.current = 0; connect(); };
        window.addEventListener(SESSION_EVENT, onSession);
        return () => {
            window.removeEventListener(SESSION_EVENT, onSession);
            if (timerRef.current) clearTimeout(timerRef.current);
            if (wsRef.current) {
                try { wsRef.current.close(); } catch (_) { /* noop */ }
            }
        };
    }, [connect]);

    return (
        <WebSocketContext.Provider value={{ connected, subscribe }}>
            {children}
        </WebSocketContext.Provider>
    );
}

