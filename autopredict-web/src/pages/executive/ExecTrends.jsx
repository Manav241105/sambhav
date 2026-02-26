import React from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import SixMonthComparison from '../../components/charts/SixMonthComparison';
import AcceptanceRateLine from '../../components/charts/AcceptanceRateLine';
import ConversionScatterByMake from '../../components/charts/ConversionScatterByMake';
import WhatIfSimulator from '../../components/charts/WhatIfSimulator';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

export default function ExecTrends() {
    const { monthlyTrend, monthly, conversionByMake } = useOutletContext();

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={spring}>
            <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-2">
                Booking Acceptance Rate
            </h2>
            <p className="text-sm text-gray-400 dark:text-gray-500 mb-6 max-w-2xl leading-relaxed">
                Tracks the success rate of AI outreach converting into actual service centre bookings.
                A downward trend may indicate ineffective customer engagement or a lack of available scheduling slots.
                Escalation rate rising alongside conversion rate drop is a flag for agent retraining.
            </p>

            {/* Existing line chart */}
            <div className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl mb-8">
                {monthlyTrend.length > 0 ? (
                    <ResponsiveContainer width="100%" height={320}>
                        <LineChart data={monthlyTrend}>
                            <defs>
                                <linearGradient id="gradLine" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.2} />
                                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                            <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} />
                            <YAxis domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                            <Tooltip contentStyle={tooltipStyle} formatter={(val, name) => [`${val}%`, name]} />
                            <Legend wrapperStyle={{ fontSize: 11 }} />
                            <Line type="monotone" dataKey="acceptance_pct" name="Acceptance %" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 4, fill: '#6366f1', stroke: '#0b0f19', strokeWidth: 2 }} />
                            <Line type="monotone" dataKey="conversion_pct" name="Conversion %" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} />
                            <Line type="monotone" dataKey="escalation_pct" name="Escalation %" stroke="#f87171" strokeWidth={2} strokeDasharray="4 3" dot={{ r: 3 }} />
                        </LineChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-[320px] flex items-center justify-center">
                        <p className="text-sm text-gray-400">Loading trends…</p>
                    </div>
                )}
            </div>

            {/* Phase 4 charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <SixMonthComparison months={monthlyTrend} />
                <AcceptanceRateLine months={monthlyTrend} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ConversionScatterByMake makes={conversionByMake} />
                <WhatIfSimulator />
            </div>
        </motion.div>
    );
}
