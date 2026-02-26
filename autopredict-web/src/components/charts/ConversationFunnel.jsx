import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

const STAGES = [
  { key: 'contacted', label: 'Contacted', color: '#6366f1' },
  { key: 'interested', label: 'Interested', color: '#38bdf8' },
  { key: 'booked', label: 'Booked', color: '#22c55e' },
];

/**
 * ConversationFunnel — visual funnel: Contacted → Interested → Booked.
 *
 * Props:
 *   conversations — array of conversation turn objects from the API
 *                   Each has { vehicle_id, turn_number, direction, status }
 *
 * Funnel logic:
 *   • Contacted = unique vehicles with at least 1 OUTBOUND turn
 *   • Interested = unique vehicles with at least 1 INBOUND reply
 *   • Booked = unique vehicles with 5+ turns (completed flow) or status "BOOKED"
 */
export default function ConversationFunnel({ conversations = [] }) {
  /* Group by vehicle_id */
  const byVehicle = {};
  conversations.forEach((c) => {
    const vid = c.vehicle_id;
    if (!vid) return;
    if (!byVehicle[vid]) byVehicle[vid] = { outbound: 0, inbound: 0, turns: 0, booked: false };
    byVehicle[vid].turns += 1;
    if (c.direction === 'OUTBOUND') byVehicle[vid].outbound += 1;
    if (c.direction === 'INBOUND') byVehicle[vid].inbound += 1;
    if (c.status === 'BOOKED' || c.status === 'COMPLETED') byVehicle[vid].booked = true;
  });

  const vehicles = Object.values(byVehicle);
  const contacted = vehicles.filter((v) => v.outbound > 0).length;
  const interested = vehicles.filter((v) => v.inbound > 0).length;
  const booked = vehicles.filter((v) => v.booked || v.turns >= 5).length;

  const values = { contacted, interested, booked };
  const maxVal = Math.max(contacted, 1);

  if (contacted === 0) {
    return (
      <div className="h-48 flex items-center justify-center">
        <p className="text-xs text-gray-400 dark:text-gray-500">No conversation data</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={spring}
      className="space-y-3"
    >
      {STAGES.map((stage, i) => {
        const count = values[stage.key];
        const pct = maxVal > 0 ? (count / maxVal) * 100 : 0;
        const convRate = i > 0 ? (count / Math.max(values[STAGES[i - 1].key], 1) * 100).toFixed(0) : null;

        return (
          <motion.div
            key={stage.key}
            initial={{ opacity: 0, x: -16 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ ...spring, delay: i * 0.1 }}
          >
            {/* Label row */}
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: stage.color }} />
                <span className="text-xs font-bold text-gray-900 dark:text-white">{stage.label}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-extrabold text-gray-900 dark:text-white">{count}</span>
                {convRate && (
                  <span className="text-[9px] font-medium text-gray-400 dark:text-gray-500">
                    ({convRate}% conv.)
                  </span>
                )}
              </div>
            </div>

            {/* Bar */}
            <div className="h-6 rounded-xl bg-gray-100 dark:bg-white/5 overflow-hidden">
              <motion.div
                className="h-full rounded-xl"
                style={{ backgroundColor: stage.color }}
                initial={{ width: 0 }}
                animate={{ width: `${Math.max(pct, 4)}%` }}
                transition={{ duration: 1, ease: 'easeOut', delay: i * 0.15 }}
              />
            </div>
          </motion.div>
        );
      })}

      {/* Overall conversion */}
      <div className="pt-2 border-t border-gray-100 dark:border-white/5">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider">
            Overall Conversion
          </span>
          <span className="text-sm font-extrabold text-[#6366f1]">
            {contacted > 0 ? ((booked / contacted) * 100).toFixed(0) : 0}%
          </span>
        </div>
      </div>
    </motion.div>
  );
}
