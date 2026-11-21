import React from 'react';
import { formatINR, formatINRCompact } from '../../lib/format';
import { motion } from 'framer-motion';
import { ResponsiveContainer, ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

/**
 * Revenue forecast: 6-month historical (solid area) + 3-month projected (dashed line).
 *
 * @param {{ all: Array<{month:string, revenue_inr:number, type:'actual'|'forecast'}> }} props
 */
export default function RevenueForecast({ all = [] }) {
    if (!all.length) {
        return (
            <div className="h-[320px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No forecast data</p>
            </div>
        );
    }

    // Split into actual vs forecast for separate series
    const data = all.map((d) => ({
        month: d.month,
        actual: d.type === 'actual' ? d.revenue_inr : null,
        forecast: d.type === 'forecast' ? d.revenue_inr : null,
        // Connect the junction point
        ...(d.type === 'forecast' ? {} : {}),
    }));

    // Add bridge: last actual point also appears as first forecast so line connects
    const lastActualIdx = data.findLastIndex((d) => d.actual !== null);
    if (lastActualIdx >= 0 && lastActualIdx < data.length - 1) {
        data[lastActualIdx].forecast = data[lastActualIdx].actual;
    }

    const fmt = (v) => formatINRCompact(v);
    const dividerMonth = all.find((d) => d.type === 'forecast')?.month;

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-1">
                Revenue Forecast
            </h3>
            <p className="text-[10px] text-gray-400 mb-4">Historical (solid) + 3-month projection (dashed)</p>
            <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={data}>
                    <defs>
                        <linearGradient id="gradActual" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                            <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                    <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={fmt} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => formatINR(v)} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    {dividerMonth && (
                        <ReferenceLine x={dividerMonth} stroke="#9ca3af" strokeDasharray="4 4" label={{ value: 'Forecast →', position: 'top', fill: '#9ca3af', fontSize: 10 }} />
                    )}
                    <Area type="monotone" dataKey="actual" name="Actual" stroke="#6366f1" strokeWidth={2} fill="url(#gradActual)" connectNulls={false} />
                    <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#caff42" strokeWidth={2.5} strokeDasharray="6 3" dot={{ r: 4, fill: '#caff42' }} connectNulls />
                </ComposedChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
