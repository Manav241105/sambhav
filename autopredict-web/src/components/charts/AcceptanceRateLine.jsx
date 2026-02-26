import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

/**
 * 6-month acceptance rate area chart.
 *
 * @param {{ months: Array<{month:string, acceptance_pct:number}> }} props
 */
export default function AcceptanceRateLine({ months = [] }) {
    if (!months.length) {
        return (
            <div className="h-[280px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No acceptance data</p>
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
                Acceptance Rate — 6 Month Trend
            </h3>
            <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={months}>
                    <defs>
                        <linearGradient id="gradAcceptance" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                            <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                    <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => `${v}%`} />
                    <Area type="monotone" dataKey="acceptance_pct" name="Acceptance %" stroke="#6366f1" strokeWidth={2.5} fill="url(#gradAcceptance)" dot={{ r: 4, fill: '#6366f1' }} />
                </AreaChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
