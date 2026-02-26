import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const COLORS = ['#6366f1', '#3b82f6', '#caff42', '#22c55e'];

/**
 * Booking funnel: Prospects → Contacted → Booked → Serviced.
 * Rendered as horizontal bars with conversion rates between stages.
 *
 * @param {{ funnel: Array<{stage:string, count:number}> }} props
 */
export default function BookingFunnelSankey({ funnel = [] }) {
    if (!funnel.length) {
        return (
            <div className="h-[200px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No funnel data</p>
            </div>
        );
    }

    const maxVal = Math.max(...funnel.map((f) => f.count), 1);

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Booking Funnel
            </h3>
            <div className="space-y-3">
                {funnel.map((stage, i) => {
                    const pct = Math.round((stage.count / maxVal) * 100);
                    const convRate = i > 0 && funnel[i - 1].count > 0
                        ? Math.round((stage.count / funnel[i - 1].count) * 100)
                        : null;

                    return (
                        <div key={stage.stage}>
                            {convRate !== null && (
                                <div className="flex items-center gap-2 mb-1 ml-2">
                                    <div className="w-4 h-px bg-gray-300 dark:bg-gray-600" />
                                    <span className="text-[10px] font-bold text-gray-400 dark:text-gray-500">
                                        {convRate}% conversion
                                    </span>
                                </div>
                            )}
                            <div className="flex items-center gap-3">
                                <span className="text-xs font-semibold text-gray-600 dark:text-gray-300 w-20 shrink-0 text-right">
                                    {stage.stage}
                                </span>
                                <div className="flex-1 relative h-8">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${pct}%` }}
                                        transition={{ ...spring, delay: i * 0.1 }}
                                        className="h-full rounded-xl flex items-center px-3"
                                        style={{ backgroundColor: COLORS[i % COLORS.length], minWidth: 40 }}
                                    >
                                        <span className="text-xs font-extrabold text-gray-900">{stage.count}</span>
                                    </motion.div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </motion.div>
    );
}
