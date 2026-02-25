import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X, ChevronRight } from 'lucide-react';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/**
 * Sticky P0 alert banner — sits at the top of the Operations Dashboard.
 * Cycles through critical alerts with a dismiss action.
 *
 * Props:
 *   alerts  — array of { vehicle_id, priority, message, component, timestamp }
 *   onDismiss(index)  — callback to remove an alert
 *   onClickAlert(alert) — callback when user clicks to view vehicle
 */
export default function AlertBanner({ alerts = [], onDismiss, onClickAlert }) {
  if (!alerts.length) return null;

  return (
    <div className="sticky top-0 z-50 flex flex-col gap-2 mb-6">
      <AnimatePresence mode="popLayout">
        {alerts.map((alert, i) => {
          const isP0 = alert.priority === 'P0';
          return (
            <motion.div
              key={alert.vehicle_id + '-' + i}
              layout
              initial={{ opacity: 0, y: -20, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 80, scale: 0.95 }}
              transition={spring}
              className={`
                relative flex items-center gap-4 px-5 py-3.5 rounded-2xl border backdrop-blur-md cursor-pointer
                ${isP0
                  ? 'bg-red-500/10 dark:bg-red-500/10 border-red-400/30 dark:border-red-500/30'
                  : 'bg-amber-500/10 dark:bg-amber-500/10 border-amber-400/30 dark:border-amber-500/30'}
              `}
              onClick={() => onClickAlert?.(alert)}
            >
              {/* Pulse indicator */}
              <span className="relative flex h-3 w-3 shrink-0">
                <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${isP0 ? 'bg-red-400' : 'bg-amber-400'}`} />
                <span className={`relative inline-flex rounded-full h-3 w-3 ${isP0 ? 'bg-red-500' : 'bg-amber-500'}`} />
              </span>

              {/* Icon */}
              <div className={`p-2 rounded-xl ${isP0 ? 'bg-red-500/15 text-red-500' : 'bg-amber-500/15 text-amber-500'}`}>
                <AlertTriangle size={18} />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${isP0 ? 'bg-red-500/20 text-red-500' : 'bg-amber-500/20 text-amber-500'}`}>
                    {alert.priority}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {alert.vehicle_id}
                  </span>
                </div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                  {alert.message}
                </p>
              </div>

              {/* View action */}
              <ChevronRight size={16} className="text-gray-400 shrink-0" />

              {/* Dismiss */}
              <button
                onClick={(e) => { e.stopPropagation(); onDismiss?.(i); }}
                className="p-1.5 rounded-xl hover:bg-black/5 dark:hover:bg-white/5 transition-colors shrink-0"
              >
                <X size={14} className="text-gray-400" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
