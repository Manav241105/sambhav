import React from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

export default function ManagerRevenue() {
    const { revenuePipeline } = useOutletContext();

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={spring}>
            <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-2">
                Revenue Pipeline
            </h2>
            <p className="text-sm text-gray-400 dark:text-gray-500 mb-6 max-w-2xl leading-relaxed">
                Visualises projected revenue from upcoming confirmed and pending bookings over a 6-month window.
                Compare confirmed vs pending ratios against historical averages to gauge service centre profitability for the current cycle.
                A widening gap between confirmed and pending indicates strong conversion.
            </p>

            <div className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl">
                <ResponsiveContainer width="100%" height={340}>
                    <AreaChart data={revenuePipeline}>
                        <defs>
                            <linearGradient id="gradConfirmed" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#6366f1" stopOpacity={0.35} />
                                <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="gradPending" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.25} />
                                <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                        <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                        <Tooltip contentStyle={tooltipStyle} />
                        <Area type="monotone" dataKey="confirmed" name="Confirmed" stroke="#6366f1" strokeWidth={2} fill="url(#gradConfirmed)" />
                        <Area type="monotone" dataKey="pending" name="Pending" stroke="#3b82f6" strokeWidth={2} fill="url(#gradPending)" />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </motion.div>
    );
}
