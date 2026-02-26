import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

/**
 * Grouped bar chart showing recall discovery date vs remedy date for each recall campaign.
 *
 * @param {{ timeline: Array<{campaign:string, discovered:string, remedied_date:string, days_to_remedy:number, affected:number}> }} props
 */
export default function RecallTimelineBar({ timeline = [] }) {
    if (!timeline.length) {
        return (
            <div className="h-[300px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No recall timeline data</p>
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
                Recall Timeline — Days to Remedy
            </h3>
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={timeline} layout="vertical" barCategoryGap="25%">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" horizontal={false} />
                    <XAxis
                        type="number"
                        tick={{ fill: '#9ca3af', fontSize: 11 }}
                        axisLine={false} tickLine={false}
                        label={{ value: 'Days →', position: 'insideBottomRight', fill: '#9ca3af', fontSize: 10, offset: -5 }}
                    />
                    <YAxis
                        type="category" dataKey="campaign" width={120}
                        tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false}
                    />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v, name) => [`${v} days`, name]} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="days_to_remedy" name="Days to Remedy" fill="#6366f1" radius={[0, 6, 6, 0]} />
                    <Bar dataKey="affected" name="Affected Vehicles" fill="#f97316" radius={[0, 6, 6, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
