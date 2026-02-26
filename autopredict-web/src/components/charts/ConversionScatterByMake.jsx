import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ZAxis } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

const COLORS = ['#6366f1', '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div style={tooltipStyle} className="p-2">
            <p className="font-bold">{d.make}</p>
            <p>{d.total_vehicles} vehicles</p>
            <p>Conversion: {d.conversion_pct}%</p>
            <p>Booked: {d.booked}</p>
        </div>
    );
};

/**
 * Scatter chart: vehicle makes plotted by total vehicles (X) vs conversion % (Y),
 * bubble size = booked count.
 *
 * @param {{ makes: Array<{make:string, total_vehicles:number, contacted:number, booked:number, conversion_pct:number}> }} props
 */
export default function ConversionScatterByMake({ makes = [] }) {
    if (!makes.length) {
        return (
            <div className="h-[300px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No conversion data by make</p>
            </div>
        );
    }

    const data = makes.map((m, i) => ({
        ...m,
        fill: COLORS[i % COLORS.length],
    }));

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Conversion by Vehicle Make
            </h3>
            <ResponsiveContainer width="100%" height={300}>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                    <XAxis
                        type="number" dataKey="total_vehicles" name="Vehicles"
                        tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false}
                        label={{ value: 'Fleet Size →', position: 'insideBottomRight', fill: '#9ca3af', fontSize: 10, offset: -5 }}
                    />
                    <YAxis
                        type="number" dataKey="conversion_pct" name="Conversion %"
                        domain={[0, 100]}
                        tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false}
                        tickFormatter={(v) => `${v}%`}
                        label={{ value: 'Conversion % →', angle: -90, position: 'insideLeft', fill: '#9ca3af', fontSize: 10, offset: 10 }}
                    />
                    <ZAxis type="number" dataKey="booked" range={[60, 300]} />
                    <Tooltip content={<CustomTooltip />} />
                    <Scatter data={data} shape="circle">
                        {data.map((d, i) => (
                            <circle key={i} fill={d.fill} />
                        ))}
                    </Scatter>
                </ScatterChart>
            </ResponsiveContainer>
            {/* Legend */}
            <div className="flex flex-wrap gap-3 mt-3">
                {data.map((d) => (
                    <div key={d.make} className="flex items-center gap-1.5">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: d.fill }} />
                        <span className="text-[10px] font-semibold text-gray-500">{d.make}</span>
                    </div>
                ))}
            </div>
        </motion.div>
    );
}
