import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };
const COLORS = ['#6366f1', '#3b82f6', '#f59e0b', '#22c55e', '#ef4444', '#8b5cf6', '#ec4899'];

/**
 * Pie chart showing breakdown of escalation reasons by component.
 *
 * @param {{ reasons: Array<{reason:string, count:number}> }} props
 */
export default function EscalationReasonBreakdown({ reasons = [] }) {
    if (!reasons.length) {
        return (
            <div className="h-[280px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No escalation reasons</p>
            </div>
        );
    }

    const data = reasons.map((r) => ({
        name: (r.reason || 'Unknown').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
        value: r.count,
    }));

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Escalation Reasons
            </h3>
            <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={90}
                        paddingAngle={3}
                        dataKey="value"
                        stroke="none"
                    >
                        {data.map((_, i) => (
                            <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend
                        wrapperStyle={{ fontSize: 11 }}
                        formatter={(val) => <span className="text-gray-600 dark:text-gray-300">{val}</span>}
                    />
                </PieChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
