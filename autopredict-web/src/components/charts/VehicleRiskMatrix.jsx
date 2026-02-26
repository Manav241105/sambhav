import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ZAxis } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
        <div style={tooltipStyle} className="p-2">
            <p className="font-bold">{d.vehicle_id}</p>
            <p>Health: {(d.health_score * 100).toFixed(0)}%</p>
            <p>Failure: {(d.failure_probability * 100).toFixed(0)}%</p>
            <p className="capitalize">{d.priority}</p>
        </div>
    );
};

/**
 * Scatter plot: health score (X) vs failure probability (Y) with 4 quadrants.
 *
 * @param {{ vehicles: Array<{vehicle_id:string, health_score:number, failure_probability:number, priority:string}> }} props
 */
export default function VehicleRiskMatrix({ vehicles = [] }) {
    if (!vehicles.length) {
        return (
            <div className="h-[360px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No vehicle data</p>
            </div>
        );
    }

    const data = vehicles.map((v) => ({
        vehicle_id: v.vehicle_id,
        health_score: v.health_score || 0.5,
        failure_probability: v.failure_probability || 0,
        priority: v.priority || 'P3',
        fill: v.priority === 'P0' ? '#ef4444' : v.priority === 'P1' ? '#f97316' : v.priority === 'P2' ? '#fbbf24' : '#22c55e',
    }));

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-1">
                Vehicle Risk Matrix
            </h3>
            <p className="text-[10px] text-gray-400 mb-4">Health score vs failure probability — 4 quadrants</p>
            <ResponsiveContainer width="100%" height={360}>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                    <XAxis
                        type="number" dataKey="health_score" name="Health"
                        domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                        tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false}
                        label={{ value: 'Health Score →', position: 'insideBottomRight', fill: '#9ca3af', fontSize: 10, offset: -5 }}
                    />
                    <YAxis
                        type="number" dataKey="failure_probability" name="Failure Prob"
                        domain={[0, 1]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                        tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false}
                        label={{ value: 'Failure Probability →', angle: -90, position: 'insideLeft', fill: '#9ca3af', fontSize: 10, offset: 10 }}
                    />
                    <ZAxis range={[80, 200]} />
                    <Tooltip content={<CustomTooltip />} />
                    {/* Quadrant dividers at 50% */}
                    <ReferenceLine x={0.5} stroke="#9ca3af" strokeDasharray="4 4" strokeOpacity={0.4} />
                    <ReferenceLine y={0.5} stroke="#9ca3af" strokeDasharray="4 4" strokeOpacity={0.4} />
                    <Scatter data={data} shape="circle">
                        {data.map((d, i) => (
                            <circle key={i} fill={d.fill} />
                        ))}
                    </Scatter>
                </ScatterChart>
            </ResponsiveContainer>
            {/* Quadrant labels */}
            <div className="grid grid-cols-2 gap-2 mt-2 text-[9px] font-bold text-gray-400 text-center">
                <span>High Health, High Risk</span>
                <span className="text-red-400">Low Health, High Risk</span>
                <span className="text-emerald-400">High Health, Low Risk</span>
                <span>Low Health, Low Risk</span>
            </div>
        </motion.div>
    );
}
