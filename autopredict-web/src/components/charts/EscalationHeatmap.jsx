import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/**
 * Escalation heatmap — day-of-week × hour grid showing escalation counts.
 *
 * @param {{ heatmap: Array<{day:string, hour:number, count:number}>, days: string[], hours: number[] }} props
 */
export default function EscalationHeatmap({ heatmap = [], days = [], hours = [] }) {
    if (!heatmap.length) {
        return (
            <div className="h-[280px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No escalation data</p>
            </div>
        );
    }

    // Build lookup map
    const lookup = {};
    let maxCount = 1;
    heatmap.forEach((cell) => {
        const key = `${cell.day}-${cell.hour}`;
        lookup[key] = cell.count;
        if (cell.count > maxCount) maxCount = cell.count;
    });

    const getColor = (count) => {
        const intensity = count / maxCount;
        if (intensity === 0) return 'bg-gray-50 dark:bg-white/[0.02]';
        if (intensity < 0.25) return 'bg-indigo-100 dark:bg-indigo-500/10';
        if (intensity < 0.5) return 'bg-indigo-200 dark:bg-indigo-500/20';
        if (intensity < 0.75) return 'bg-indigo-400 dark:bg-indigo-500/40';
        return 'bg-indigo-600 dark:bg-indigo-500/70';
    };

    const getTextColor = (count) => {
        const intensity = count / maxCount;
        if (intensity >= 0.5) return 'text-white';
        return 'text-gray-600 dark:text-gray-400';
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Escalation Heatmap — Day × Hour
            </h3>
            <div className="overflow-x-auto">
                <table className="w-full border-separate" style={{ borderSpacing: 2 }}>
                    <thead>
                        <tr>
                            <th className="w-10" />
                            {hours.map((h) => (
                                <th key={h} className="text-[10px] font-medium text-gray-400 pb-1 text-center">
                                    {h}:00
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {days.map((day, di) => (
                            <tr key={day}>
                                <td className="text-[10px] font-semibold text-gray-500 dark:text-gray-400 pr-2 text-right">
                                    {day}
                                </td>
                                {hours.map((h) => {
                                    const count = lookup[`${day}-${h}`] || 0;
                                    return (
                                        <motion.td
                                            key={h}
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: di * 0.03 + (h - hours[0]) * 0.01 }}
                                            className={`w-8 h-8 text-center rounded-lg cursor-default ${getColor(count)}`}
                                            title={`${day} ${h}:00 — ${count} escalations`}
                                        >
                                            <span className={`text-[9px] font-bold ${getTextColor(count)}`}>
                                                {count || ''}
                                            </span>
                                        </motion.td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {/* Legend */}
            <div className="flex items-center gap-3 mt-4">
                <span className="text-[10px] text-gray-400">Low</span>
                {['bg-gray-50 dark:bg-white/[0.02]', 'bg-indigo-100 dark:bg-indigo-500/10', 'bg-indigo-200 dark:bg-indigo-500/20', 'bg-indigo-400 dark:bg-indigo-500/40', 'bg-indigo-600 dark:bg-indigo-500/70'].map((cls, i) => (
                    <div key={i} className={`w-5 h-3 rounded ${cls}`} />
                ))}
                <span className="text-[10px] text-gray-400">High</span>
            </div>
        </motion.div>
    );
}
