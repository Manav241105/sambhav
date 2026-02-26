import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

/**
 * Horizontal bar chart showing which components fail most.
 *
 * @param {{ components: Array<{component:string, failures:number}> }} props
 */
export default function ComponentFailureRate({ components = [] }) {
    if (!components.length) {
        return (
            <div className="h-[280px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No failure data</p>
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
                Component Failure Rate
            </h3>
            <ResponsiveContainer width="100%" height={280}>
                <BarChart data={components} layout="vertical" barCategoryGap="25%">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" horizontal={false} />
                    <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="component" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} width={110} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="failures" name="Failures" fill="#ef4444" radius={[0, 8, 8, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
