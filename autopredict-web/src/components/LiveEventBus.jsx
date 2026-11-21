import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wifi, WifiOff, X, Zap, AlertTriangle, Car, CalendarDays, MessageSquare, Brain } from 'lucide-react';
import { useWebSocketContext } from '../contexts/useWebSocketContext';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const TOAST_DURATION = 5000;
const ALERT_DURATION = 8000;

/**
 * LiveEventBus — upgraded replacement for LiveToast.
 *
 * Renders:
 *   • Connection indicator pill (bottom-left)
 *   • Toast stack (bottom-right) for all event types
 *   • Alert banner (top) for ALERT_FIRED events
 *
 * Dispatches to per-type callbacks so layouts can trigger
 * targeted refreshes instead of full re-fetches.
 *
 * Props:
 *   onDiagnosisUpdated(event) — called on DIAGNOSIS_UPDATED
 *   onBookingCreated(event)   — called on BOOKING_CREATED
 *   onAlertFired(event)       — called on ALERT_FIRED
 *   onConversationTurn(event) — called on CONVERSATION_TURN
 *   onVehicleUpdated(event)   — called on VEHICLE_UPDATED
 *   onAnyEvent(event)         — called on every WS event (fallback)
 */
export default function LiveEventBus({
    onDiagnosisUpdated,
    onBookingCreated,
    onAlertFired,
    onConversationTurn,
    onVehicleUpdated,
    onAnyEvent,
}) {
    const { connected, subscribe } = useWebSocketContext();

    // Toast stack
    const [toasts, setToasts] = useState([]);
    // Alert banner
    const [alertBanner, setAlertBanner] = useState(null);

    // ── Push toast helper ────────────────────────────────────
    const pushToast = useCallback((event) => {
        if (!event) return;
        const id = Date.now() + Math.random();
        const label = formatEvent(event);
        const icon = iconForType(event.type);
        const color = colorForType(event.type);

        setToasts((prev) => [...prev.slice(-4), { id, label, icon, color, event }]);
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, TOAST_DURATION);
    }, []);

    // Latest callbacks, so subscriptions don't need to be recreated when props change.
    const handlers = useRef({});
    useEffect(() => {
        handlers.current = { onDiagnosisUpdated, onBookingCreated, onAlertFired, onConversationTurn, onVehicleUpdated, onAnyEvent };
    });

    const bannerTimer = useRef(null);
    useEffect(() => {
        const perType = {
            DIAGNOSIS_UPDATED: 'onDiagnosisUpdated',
            BOOKING_CREATED: 'onBookingCreated',
            ALERT_FIRED: 'onAlertFired',
            CONVERSATION_TURN: 'onConversationTurn',
            VEHICLE_UPDATED: 'onVehicleUpdated',
            WORKFLOW_COMPLETED: null,
        };
        const unsubs = Object.entries(perType).map(([type, cbName]) =>
            subscribe(type, (event) => {
                pushToast(event);
                if (cbName) handlers.current[cbName]?.(event);
                handlers.current.onAnyEvent?.(event);
                if (type === 'ALERT_FIRED') {
                    setAlertBanner(event);
                    clearTimeout(bannerTimer.current);
                    bannerTimer.current = setTimeout(() => setAlertBanner(null), ALERT_DURATION);
                }
            }),
        );
        return () => {
            unsubs.forEach((u) => u());
            clearTimeout(bannerTimer.current);
        };
    }, [subscribe, pushToast]);

    const dismiss = (id) => setToasts((prev) => prev.filter((t) => t.id !== id));

    return (
        <>
            {/* ── Alert banner — fixed top ────────────────── */}
            <AnimatePresence>
                {alertBanner && (
                    <motion.div
                        key="alert-banner"
                        initial={{ opacity: 0, y: -40 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -40 }}
                        transition={spring}
                        className="fixed top-0 inset-x-0 z-[60] flex items-center justify-center gap-3 px-6 py-3 bg-red-500/95 text-white text-sm font-bold backdrop-blur-md"
                    >
                        <AlertTriangle size={16} />
                        <span>
                            {alertBanner.payload?.priority || 'ALERT'} — {alertBanner.payload?.vehicle_id || 'Unknown'}: {alertBanner.payload?.message || 'New alert fired'}
                        </span>
                        <button
                            onClick={() => setAlertBanner(null)}
                            className="ml-4 p-1 rounded-lg hover:bg-white/20"
                        >
                            <X size={14} />
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* ── Connection pill — fixed bottom-left ─────── */}
            <div className="fixed bottom-4 left-4 z-50">
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold tracking-wide backdrop-blur-md border ${
                        connected
                            ? 'bg-[#6366f1]/10 border-[#6366f1]/20 text-[#6366f1]'
                            : 'bg-red-500/10 border-red-500/20 text-red-400'
                    }`}
                >
                    {connected ? <Wifi size={10} /> : <WifiOff size={10} />}
                    {connected ? 'LIVE' : 'OFFLINE'}
                </motion.div>
            </div>

            {/* ── Toast stack — fixed bottom-right ────────── */}
            <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 items-end max-w-sm">
                <AnimatePresence mode="popLayout">
                    {toasts.map((t) => {
                        const Icon = t.icon;
                        return (
                            <motion.div
                                key={t.id}
                                layout
                                initial={{ opacity: 0, x: 40, scale: 0.95 }}
                                animate={{ opacity: 1, x: 0, scale: 1 }}
                                exit={{ opacity: 0, x: 40, scale: 0.95 }}
                                transition={spring}
                                className="flex items-center gap-3 px-4 py-3 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white/90 dark:bg-[#0b0f19]/90 backdrop-blur-md shadow-lg"
                            >
                                <div className={`p-1.5 rounded-lg ${t.color}`}>
                                    <Icon size={12} />
                                </div>
                                <p className="text-xs font-medium text-gray-700 dark:text-gray-300 flex-1 min-w-0 truncate">
                                    {t.label}
                                </p>
                                <button
                                    onClick={() => dismiss(t.id)}
                                    className="p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 shrink-0"
                                >
                                    <X size={10} className="text-gray-400" />
                                </button>
                            </motion.div>
                        );
                    })}
                </AnimatePresence>
            </div>
        </>
    );
}

/* ── Helpers ─────────────────────────────────────────── */

function iconForType(type) {
    switch (type) {
        case 'DIAGNOSIS_UPDATED':  return Brain;
        case 'BOOKING_CREATED':
        case 'BOOKING_CANCELLED':  return CalendarDays;
        case 'ALERT_FIRED':        return AlertTriangle;
        case 'CONVERSATION_TURN':  return MessageSquare;
        case 'VEHICLE_UPDATED':    return Car;
        default:                   return Zap;
    }
}

function colorForType(type) {
    switch (type) {
        case 'DIAGNOSIS_UPDATED':  return 'bg-[#caff42]/15 text-[#caff42]';
        case 'BOOKING_CREATED':    return 'bg-blue-500/15 text-blue-400';
        case 'BOOKING_CANCELLED':  return 'bg-orange-500/15 text-orange-400';
        case 'ALERT_FIRED':        return 'bg-red-500/15 text-red-400';
        case 'CONVERSATION_TURN':  return 'bg-purple-500/15 text-purple-400';
        case 'VEHICLE_UPDATED':    return 'bg-emerald-500/15 text-emerald-400';
        default:                   return 'bg-[#6366f1]/15 text-[#6366f1]';
    }
}

function formatEvent(evt) {
    const type = evt?.type || 'update';
    const vid = evt?.payload?.vehicle_id || '';
    const msg = evt?.payload?.message || '';

    switch (type) {
        case 'VEHICLE_UPDATED':    return `Vehicle ${vid} data updated`;
        case 'DIAGNOSIS_UPDATED':  return `AI diagnosis refreshed — ${vid}`;
        case 'BOOKING_CREATED':    return `New booking created for ${vid}`;
        case 'BOOKING_CANCELLED':  return `Booking cancelled — ${vid}`;
        case 'ALERT_FIRED':        return `${evt?.payload?.priority || 'ALERT'} — ${vid}: ${msg}`;
        case 'CONVERSATION_TURN':  return `New message — ${vid}`;
        case 'WORKFLOW_COMPLETED': return `Workflow completed — ${vid}`;
        default:                   return msg || `${type}: ${vid}`;
    }
}
