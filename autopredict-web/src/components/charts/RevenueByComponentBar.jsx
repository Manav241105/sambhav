import React from 'react';
import { formatINR, formatINRCompact } from '../../lib/format';
import { motion } from 'framer-motion';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

/**
 * Horizontal bar chart — revenue breakdown by service component.
 *
 * @param {{ components: Array<{component:string, revenue_inr:number}> }} props
 */
export default function RevenueByComponentBar({ components = [] }) {
    if (!components.length) {
        return (
            <div className="h-[300px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No component revenue data</p>
            </div>
        );
    }

    const fmt = (v) => formatINRCompact(v);

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Revenue by Service Component
            </h3>
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={components} layout="vertical" barCategoryGap="20%">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" horizontal={false} />
                    <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={fmt} />
                    <YAxis type="category" dataKey="component" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} width={110} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => formatINR(v)} />
                    <Bar dataKey="revenue_inr" name="Revenue" fill="#6366f1" radius={[0, 8, 8, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
