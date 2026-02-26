import React from 'react';
import { motion } from 'framer-motion';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  ReferenceLine,
} from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = {
  backgroundColor: '#1f2937',
  border: '1px solid #374151',
  borderRadius: '12px',
  fontSize: 12,
  color: '#fff',
};

/**
 * RULDistribution — histogram showing distribution of Remaining Useful Life (days)
 * across the fleet. Buckets: 0-7, 7-14, 14-30, 30-60, 60-90, >90.
 *
 * Props:
 *   vehicles — array of vehicle objects with diagnosis.rul_days
 */
export default function RULDistribution({ vehicles = [] }) {
  const buckets = [
    { range: '0-7d', min: 0, max: 7, fill: '#ef4444' },
    { range: '7-14d', min: 7, max: 14, fill: '#f97316' },
    { range: '14-30d', min: 14, max: 30, fill: '#fbbf24' },
    { range: '30-60d', min: 30, max: 60, fill: '#6366f1' },
    { range: '60-90d', min: 60, max: 90, fill: '#38bdf8' },
    { range: '>90d', min: 90, max: Infinity, fill: '#22c55e' },
  ];

  const data = buckets.map((b) => ({
    range: b.range,
    count: vehicles.filter((v) => {
      const rul = v.diagnosis?.rul_days;
      if (rul == null) return b.min === 90; // unknown RUL → >90d bucket
      return rul >= b.min && rul < b.max;
    }).length,
    fill: b.fill,
  }));

  const totalVehicles = vehicles.length;
  if (totalVehicles === 0) {
    return (
      <div className="h-48 flex items-center justify-center">
        <p className="text-xs text-gray-400 dark:text-gray-500">No vehicle data</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={spring}
    >
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} barCategoryGap="15%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.12)" />
          <XAxis
            dataKey="range"
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
            label={{ value: 'Vehicles', angle: -90, position: 'insideLeft', fill: '#9ca3af', fontSize: 10 }}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={(value) => [`${value} vehicle${value !== 1 ? 's' : ''}`, 'Count']}
          />
          <ReferenceLine y={0} stroke="rgba(156,163,175,0.2)" />
          <Bar dataKey="count" name="Vehicles" radius={[8, 8, 0, 0]} animationDuration={1000}>
            {data.map((entry, idx) => (
              <Cell key={idx} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Urgent callout */}
      {data[0].count > 0 && (
        <div className="mt-2 px-3 py-2 rounded-xl bg-red-500/10 border border-red-500/20">
          <p className="text-[10px] font-bold text-red-500">
            ⚠ {data[0].count} vehicle{data[0].count !== 1 ? 's' : ''} with RUL &lt; 7 days — immediate attention needed
          </p>
        </div>
      )}
    </motion.div>
  );
}
