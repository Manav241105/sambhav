import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wifi, WifiOff, X, Zap } from 'lucide-react';
import useWebSocket from '../hooks/useWebSocket';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const TOAST_DURATION = 5000; // auto-dismiss after 5s

/**
 * LiveToast — renders a floating toast in the bottom-right corner
 * whenever a WebSocket event arrives. Also shows a small connection
 * indicator pill.
 *
 * Props:
 *   onEvent(event) — optional callback fired on every WS message
 *                     (use this to trigger a data refresh)
 */
export default function LiveToast({ onEvent }) {
  const { lastEvent, connected } = useWebSocket();
  const [toasts, setToasts] = useState([]);

  /* ── Push new toast when an event arrives ──────── */
  useEffect(() => {
    if (!lastEvent) return;

    const id = Date.now();
    const label = formatEvent(lastEvent);

    setToasts((prev) => [...prev.slice(-4), { id, label, event: lastEvent }]);

    // Auto-dismiss
    const timer = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, TOAST_DURATION);

    // Notify parent
    onEvent?.(lastEvent);

    return () => clearTimeout(timer);
  }, [lastEvent]); // eslint-disable-line react-hooks/exhaustive-deps

  const dismiss = (id) => setToasts((prev) => prev.filter((t) => t.id !== id));

  return (
    <>
      {/* ── Connection pill — fixed bottom-left ──── */}
      <div className="fixed bottom-4 left-4 z-50">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold tracking-wide backdrop-blur-md border ${
            connected
              ? 'bg-[#caff42]/10 border-[#caff42]/20 text-[#caff42]'
              : 'bg-red-500/10 border-red-500/20 text-red-400'
          }`}
        >
          {connected ? <Wifi size={10} /> : <WifiOff size={10} />}
          {connected ? 'LIVE' : 'OFFLINE'}
        </motion.div>
      </div>

      {/* ── Toast stack — fixed bottom-right ─────── */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 items-end max-w-sm">
        <AnimatePresence mode="popLayout">
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, x: 40, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40, scale: 0.95 }}
              transition={spring}
              className="flex items-center gap-3 px-4 py-3 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white/90 dark:bg-[#0b0f19]/90 backdrop-blur-md shadow-lg"
            >
              <div className="p-1.5 rounded-lg bg-[#caff42]/15">
                <Zap size={12} className="text-[#caff42]" />
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
          ))}
        </AnimatePresence>
      </div>
    </>
  );
}

/* ── Format a WS event into a human-readable label ─ */
function formatEvent(evt) {
  const type = evt.type || evt.event_type || 'update';
  const vid = evt.vehicle_id || '';
  const msg = evt.message || '';

  switch (type) {
    case 'vehicle_update':
      return `🚗 ${vid} data updated`;
    case 'alert':
      return `🚨 ${evt.priority || ''} alert — ${vid}: ${msg}`;
    case 'booking':
      return `📅 New booking for ${vid}`;
    case 'conversation':
      return `💬 New message — ${vid}`;
    default:
      return msg || `${type}: ${vid}`;
  }
}
