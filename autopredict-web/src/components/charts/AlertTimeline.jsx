import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, AlertOctagon, ShieldAlert, Info } from 'lucide-react';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

const PRI_CONFIG = {
  P0: { icon: AlertOctagon, bg: 'bg-red-500/15', text: 'text-red-500', dot: '#ef4444', label: 'CRITICAL' },
  P1: { icon: AlertTriangle, bg: 'bg-orange-500/15', text: 'text-orange-500', dot: '#f97316', label: 'HIGH' },
  P2: { icon: ShieldAlert, bg: 'bg-amber-500/15', text: 'text-amber-400', dot: '#fbbf24', label: 'MEDIUM' },
  P3: { icon: Info, bg: 'bg-blue-500/15', text: 'text-blue-400', dot: '#3b82f6', label: 'LOW' },
};

/**
 * AlertTimeline — horizontal timeline showing P0→P3 alerts over the last 24h.
 *
 * Props:
 *   alerts — array of { priority, vehicle_id, message, fired_at }
 */
export default function AlertTimeline({ alerts = [] }) {
  const [nowRef] = useState(() => Date.now());
  if (!alerts || alerts.length === 0) {
    return (
      <div className="h-32 flex items-center justify-center">
        <p className="text-xs text-gray-400 dark:text-gray-500">No alerts in the last 24 hours</p>
      </div>
    );
  }

  /* Filter to last 24h and sort by time */
  const now = nowRef;
  const h24 = 24 * 60 * 60 * 1000;
  const recent = alerts
    .filter((a) => {
      const ts = a.fired_at ? new Date(a.fired_at).getTime() : now;
      return now - ts < h24;
    })
    .sort((a, b) => new Date(a.fired_at || 0) - new Date(b.fired_at || 0));

  const items = recent.length > 0 ? recent : alerts.slice(0, 8);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={spring}
      className="relative"
    >
      {/* Horizontal timeline line */}
      <div className="absolute top-5 left-4 right-4 h-px bg-gray-200 dark:bg-white/10" />

      <div className="flex gap-0 overflow-x-auto pb-2 scrollbar-thin">
        {items.map((alert, i) => {
          const pri = PRI_CONFIG[alert.priority] || PRI_CONFIG.P3;
          const Icon = pri.icon;
          const time = alert.fired_at
            ? new Date(alert.fired_at).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
            : '—';

          return (
            <motion.div
              key={`${alert.vehicle_id}-${i}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...spring, delay: i * 0.05 }}
              className="flex flex-col items-center min-w-[72px] px-1"
            >
              {/* Dot */}
              <div
                className="w-2.5 h-2.5 rounded-full border-2 border-white dark:border-[#0b0f19] z-10 shrink-0"
                style={{ backgroundColor: pri.dot }}
              />

              {/* Card */}
              <div className={`mt-2 p-2 rounded-xl ${pri.bg} text-center w-full`}>
                <Icon size={12} className={`mx-auto ${pri.text} mb-1`} />
                <p className={`text-[8px] font-bold uppercase tracking-wider ${pri.text}`}>
                  {pri.label}
                </p>
                <p className="text-[8px] text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                  {alert.vehicle_id}
                </p>
              </div>

              {/* Time */}
              <p className="text-[8px] text-gray-400 dark:text-gray-500 mt-1">{time}</p>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
