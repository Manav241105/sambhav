import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

/**
 * Week-over-week escalation trend line chart.
 *
 * @param {{ weeks: Array<{week:string, escalations:number, resolved:number}> }} props
 */
export default function EscalationTrendLine({ weeks = [] }) {
    if (!weeks.length) {
        return (
            <div className="h-[260px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No trend data</p>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Escalation Trend — Weekly
            </h3>
            <ResponsiveContainer width="100%" height={260}>
                <LineChart data={weeks}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                    <XAxis dataKey="week" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Line type="monotone" dataKey="escalations" name="Escalations" stroke="#ef4444" strokeWidth={2.5} dot={{ r: 4, fill: '#ef4444' }} />
                    <Line type="monotone" dataKey="resolved" name="Resolved" stroke="#22c55e" strokeWidth={2.5} dot={{ r: 4, fill: '#22c55e' }} />
                </LineChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
