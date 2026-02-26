import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };
const COLORS = ['#22c55e', '#ef4444', '#f59e0b'];

/**
 * Donut chart: Recall completion — remedied vs open (vs in-progress).
 *
 * @param {{ completion: { remedied: number, open: number, in_progress?: number } }} props
 */
export default function RecallCompletionDonut({ completion = {} }) {
    const { remedied = 0, open = 0, in_progress = 0 } = completion;
    const total = remedied + open + in_progress;

    if (!total) {
        return (
            <div className="h-[280px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No recall completion data</p>
            </div>
        );
    }

    const data = [
        { name: 'Remedied', value: remedied },
        { name: 'Open', value: open },
    ];
    if (in_progress > 0) data.push({ name: 'In Progress', value: in_progress });

    const pct = Math.round((remedied / total) * 100);

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Recall Completion
            </h3>
            <div className="relative">
                <ResponsiveContainer width="100%" height={260}>
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={70}
                            outerRadius={100}
                            paddingAngle={3}
                            dataKey="value"
                            strokeWidth={0}
                        >
                            {data.map((_, i) => (
                                <Cell key={i} fill={COLORS[i]} />
                            ))}
                        </Pie>
                        <Tooltip contentStyle={tooltipStyle} />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                    </PieChart>
                </ResponsiveContainer>
                {/* Centre label */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="text-center">
                        <p className="text-2xl font-extrabold text-gray-900 dark:text-white">{pct}%</p>
                        <p className="text-[10px] text-gray-500 uppercase tracking-wider">Remedied</p>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
