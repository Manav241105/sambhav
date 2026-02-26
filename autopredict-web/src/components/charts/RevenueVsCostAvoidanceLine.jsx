import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

/**
 * Dual-axis chart: Revenue (bar) + Cost Avoidance (line).
 *
 * @param {{ months: Array<{month:string, revenue_usd:number, cost_avoidance_usd:number, net_value:number}> }} props
 */
export default function RevenueVsCostAvoidanceLine({ months = [] }) {
    if (!months.length) {
        return (
            <div className="h-[320px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No revenue data</p>
            </div>
        );
    }

    const fmt = (v) => `$${(v / 1000).toFixed(1)}k`;

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Revenue vs Cost Avoidance
            </h3>
            <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={months}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                    <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} />
                    <YAxis yAxisId="left" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={fmt} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={fmt} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => `$${v.toLocaleString()}`} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar yAxisId="left" dataKey="revenue_usd" name="Revenue" fill="#6366f1" radius={[8, 8, 0, 0]} barSize={32} />
                    <Line yAxisId="right" type="monotone" dataKey="cost_avoidance_usd" name="Cost Avoidance" stroke="#caff42" strokeWidth={2.5} dot={{ r: 4, fill: '#caff42', stroke: '#caff42' }} />
                </ComposedChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
