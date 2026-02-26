import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

const PRIORITY_COLORS = {
    P0: { bar: 'bg-red-500', text: 'text-white' },
    P1: { bar: 'bg-orange-400', text: 'text-white' },
    P2: { bar: 'bg-amber-400', text: 'text-gray-900' },
    P3: { bar: 'bg-indigo-500', text: 'text-white' },
};

/**
 * Gantt chart for bay occupancy — horizontal bars showing time slots per bay.
 *
 * @param {{ slots: Array<{bay:string, vehicle_id:string, technician:string, start_hour:number, end_hour:number, duration_hours:number, priority:string, component:string}>, bays: string[] }} props
 */
export default function BayOccupancyGantt({ slots = [], bays = [] }) {
    const START_HOUR = 8;
    const END_HOUR = 18;
    const SPAN = END_HOUR - START_HOUR;

    if (!slots.length) {
        return (
            <div className="h-[240px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No bay occupancy data</p>
            </div>
        );
    }

    const hours = Array.from({ length: SPAN + 1 }, (_, i) => START_HOUR + i);

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Bay Occupancy — Today
            </h3>

            <div className="overflow-x-auto">
                {/* Time axis */}
                <div className="flex items-end mb-1 ml-20">
                    {hours.map((h) => (
                        <div key={h} className="text-[10px] font-medium text-gray-400" style={{ width: `${100 / SPAN}%`, minWidth: 40 }}>
                            {h}:00
                        </div>
                    ))}
                </div>

                {/* Bays */}
                <div className="space-y-2">
                    {bays.map((bay, bi) => {
                        const baySlots = slots.filter((s) => s.bay === bay);
                        return (
                            <div key={bay} className="flex items-center gap-2">
                                <span className="text-[10px] font-bold text-gray-600 dark:text-gray-300 w-18 shrink-0 text-right">
                                    {bay}
                                </span>
                                <div className="flex-1 relative h-8 bg-gray-50 dark:bg-white/[0.02] rounded-lg overflow-hidden">
                                    {baySlots.map((slot, si) => {
                                        const leftPct = Math.max(0, ((slot.start_hour - START_HOUR) / SPAN) * 100);
                                        const widthPct = Math.min(100 - leftPct, (slot.duration_hours / SPAN) * 100);
                                        const colors = PRIORITY_COLORS[slot.priority] || PRIORITY_COLORS.P3;

                                        return (
                                            <motion.div
                                                key={si}
                                                initial={{ width: 0, opacity: 0 }}
                                                animate={{ width: `${widthPct}%`, opacity: 1 }}
                                                transition={{ ...spring, delay: bi * 0.1 + si * 0.05 }}
                                                className={`absolute top-0.5 bottom-0.5 rounded-md ${colors.bar} flex items-center px-2 overflow-hidden`}
                                                style={{ left: `${leftPct}%` }}
                                                title={`${slot.vehicle_id} — ${slot.component} (${slot.technician}) ${slot.start_hour}:00–${slot.end_hour.toFixed(0)}:00`}
                                            >
                                                <span className={`text-[9px] font-bold truncate ${colors.text}`}>
                                                    {slot.vehicle_id}
                                                </span>
                                            </motion.div>
                                        );
                                    })}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Priority legend */}
            <div className="flex items-center gap-4 mt-4">
                {Object.entries(PRIORITY_COLORS).map(([p, c]) => (
                    <div key={p} className="flex items-center gap-1.5">
                        <div className={`w-3 h-3 rounded ${c.bar}`} />
                        <span className="text-[10px] font-semibold text-gray-500">{p}</span>
                    </div>
                ))}
            </div>
        </motion.div>
    );
}
