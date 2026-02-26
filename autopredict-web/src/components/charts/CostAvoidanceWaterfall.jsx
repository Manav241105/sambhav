import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/**
 * Cumulative cost-avoidance waterfall chart — each vehicle adds a segment.
 *
 * @param {{ breakdown: Array<{vehicle_id:string, component:string, cost_avoided_usd:number, cumulative_usd:number}>, total: number }} props
 */
export default function CostAvoidanceWaterfall({ breakdown = [], total = 0 }) {
    if (!breakdown.length) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={spring}
                className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
            >
                <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                    Cost Avoidance Waterfall
                </h3>
                <div className="h-[260px] flex items-center justify-center">
                    <p className="text-xs text-gray-400">No cost avoidance data yet</p>
                </div>
            </motion.div>
        );
    }

    const maxVal = Math.max(...breakdown.map((b) => b.cumulative_usd), total, 1);
    const fmt = (v) => `$${(v / 1000).toFixed(1)}k`;

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <div className="flex items-baseline justify-between mb-4">
                <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider">
                    Cost Avoidance Waterfall
                </h3>
                <span className="text-lg font-extrabold text-emerald-500">{fmt(total)}</span>
            </div>

            <div className="flex items-end gap-2 h-[240px]">
                {breakdown.map((b, i) => {
                    const segmentH = (b.cost_avoided_usd / maxVal) * 100;
                    const offsetH = ((b.cumulative_usd - b.cost_avoided_usd) / maxVal) * 100;

                    return (
                        <div key={b.vehicle_id} className="flex-1 flex flex-col items-center justify-end h-full" title={`${b.vehicle_id}: +$${b.cost_avoided_usd.toLocaleString()}`}>
                            <div className="w-full flex flex-col items-center justify-end" style={{ height: '100%' }}>
                                <span className="text-[9px] font-bold text-emerald-500 mb-1">
                                    +{fmt(b.cost_avoided_usd)}
                                </span>
                                <div className="w-full relative" style={{ marginBottom: `${offsetH}%` }}>
                                    <motion.div
                                        initial={{ height: 0 }}
                                        animate={{ height: `${segmentH}%` }}
                                        transition={{ ...spring, delay: i * 0.08 }}
                                        className="w-full bg-emerald-500 rounded-t-lg"
                                        style={{ minHeight: 8, height: `${Math.max(segmentH, 4)}%` }}
                                    />
                                </div>
                            </div>
                            <p className="text-[9px] font-semibold text-gray-400 mt-1 truncate w-full text-center">
                                {b.vehicle_id}
                            </p>
                        </div>
                    );
                })}
                {/* Total bar */}
                <div className="flex-1 flex flex-col items-center justify-end h-full">
                    <span className="text-[9px] font-bold text-[#6366f1] mb-1">{fmt(total)}</span>
                    <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${(total / maxVal) * 100}%` }}
                        transition={{ ...spring, delay: breakdown.length * 0.08 }}
                        className="w-full bg-[#6366f1] rounded-t-lg"
                        style={{ minHeight: 8 }}
                    />
                    <p className="text-[9px] font-extrabold text-gray-600 dark:text-gray-300 mt-1">Total</p>
                </div>
            </div>
        </motion.div>
    );
}
