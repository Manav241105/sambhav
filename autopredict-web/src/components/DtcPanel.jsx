import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertOctagon, ShieldAlert, Info, ChevronDown, ChevronUp } from 'lucide-react';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/* ── Severity badge config ────────────────────────── */
const SEVERITY_MAP = {
  CRITICAL: { icon: AlertOctagon, bg: 'bg-red-500/15', text: 'text-red-500' },
  HIGH:     { icon: AlertOctagon, bg: 'bg-red-500/15', text: 'text-red-500' },
  MODERATE: { icon: ShieldAlert,  bg: 'bg-amber-500/15', text: 'text-amber-500' },
  LOW:      { icon: Info,         bg: 'bg-blue-500/15', text: 'text-blue-400' },
};

/**
 * DTC codes list + recall warning badge.
 *
 * Props:
 *   dtcCodes  — array of { code, description, severity, system }
 *   recalls   — array of { campaign_number, component, description, remedy, risk_level }
 *   loading   — boolean, show skeleton
 */
export default function DtcPanel({ dtcCodes = [], recalls = [], loading = false }) {
  const [expanded, setExpanded] = React.useState(true);

  if (loading) {
    return (
      <div className="space-y-3 animate-pulse">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-14 rounded-2xl bg-gray-200 dark:bg-white/5" />
        ))}
      </div>
    );
  }

  const hasRecalls = recalls.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={spring}
      className="w-full"
    >
      {/* Section header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full mb-3"
      >
        <div className="flex items-center gap-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
            Diagnostic Trouble Codes
          </h4>
          {dtcCodes.length > 0 && (
            <span className="text-[10px] font-bold bg-gray-200 dark:bg-white/10 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded-full">
              {dtcCodes.length}
            </span>
          )}
        </div>
        {expanded ? <ChevronUp size={14} className="text-gray-400" /> : <ChevronDown size={14} className="text-gray-400" />}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            {/* Recall badge */}
            {hasRecalls && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={spring}
                className="flex items-center gap-3 p-3.5 mb-3 rounded-2xl border border-red-400/30 bg-red-500/10 dark:bg-red-500/10"
              >
                <div className="p-2 rounded-xl bg-red-500/20">
                  <ShieldAlert size={16} className="text-red-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-bold text-red-500">
                    {recalls.length} Open Recall{recalls.length > 1 ? 's' : ''}
                  </p>
                  {recalls.map((r, i) => (
                    <p key={i} className="text-[11px] text-gray-600 dark:text-gray-300 truncate">
                      <span className="font-semibold">{r.campaign_number}</span> — {r.component}: {r.description}
                    </p>
                  ))}
                </div>
              </motion.div>
            )}

            {/* DTC list */}
            {dtcCodes.length === 0 && !hasRecalls ? (
              <p className="text-xs text-gray-400 dark:text-gray-500 text-center py-4">
                No active trouble codes
              </p>
            ) : (
              <div className="space-y-2">
                {dtcCodes.map((dtc, i) => {
                  const sev = SEVERITY_MAP[dtc.severity] || SEVERITY_MAP.LOW;
                  const SevIcon = sev.icon;

                  return (
                    <motion.div
                      key={dtc.code + i}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ ...spring, delay: i * 0.04 }}
                      className="flex items-start gap-3 p-3 rounded-2xl bg-gray-50 dark:bg-white/[0.03] border border-gray-100 dark:border-white/5"
                    >
                      <div className={`p-1.5 mt-0.5 rounded-lg ${sev.bg}`}>
                        <SevIcon size={13} className={sev.text} />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-xs font-bold text-gray-900 dark:text-white font-mono">
                            {dtc.code}
                          </span>
                          <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded-full ${sev.bg} ${sev.text}`}>
                            {dtc.severity}
                          </span>
                        </div>
                        <p className="text-[11px] text-gray-600 dark:text-gray-400 leading-relaxed">
                          {dtc.description}
                        </p>
                        {dtc.system && (
                          <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">
                            System: {dtc.system}
                          </p>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
