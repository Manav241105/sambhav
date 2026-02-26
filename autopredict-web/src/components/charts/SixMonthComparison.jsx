import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

/**
 * Grouped bar chart: bookings vs acceptance vs serviced each month over 6 months.
 *
 * @param {{ months: Array<{month:string, bookings:number, acceptance_rate:number, vehicles_serviced:number}> }} props
 */
export default function SixMonthComparison({ months = [] }) {
    if (!months.length) {
        return (
            <div className="h-[320px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No monthly data</p>
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
                6-Month Comparison
            </h3>
            <ResponsiveContainer width="100%" height={320}>
                <BarChart data={months} barCategoryGap="20%">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                    <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="bookings" name="Bookings" fill="#6366f1" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="vehicles_serviced" name="Serviced" fill="#22c55e" radius={[6, 6, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
