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
} from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = {
  backgroundColor: '#1f2937',
  border: '1px solid #374151',
  borderRadius: '12px',
  fontSize: 12,
  color: '#fff',
};

const COLORS = ['#ef4444', '#f97316', '#fbbf24', '#6366f1', '#38bdf8', '#22c55e', '#a78bfa', '#fb7185'];

/**
 * DtcFrequencyBar — horizontal bar chart showing the most common DTC codes across the fleet.
 *
 * Props:
 *   vehicles — array of vehicle objects with manufacturing/dtc data
 */
export default function DtcFrequencyBar({ vehicles = [] }) {
  /* Aggregate DTC frequency across all vehicles */
  const dtcMap = {};
  vehicles.forEach((v) => {
    const dtcs = v.manufacturing?.dtc_codes || v.dtc_codes || [];
    dtcs.forEach((dtc) => {
      const code = typeof dtc === 'string' ? dtc : (dtc.code || dtc.dtc_code || 'Unknown');
      dtcMap[code] = (dtcMap[code] || 0) + 1;
    });
  });

  const data = Object.entries(dtcMap)
    .map(([code, count]) => ({ code, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8);

  if (data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center">
        <p className="text-xs text-gray-400 dark:text-gray-500">No DTC data available</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={spring}
    >
      <ResponsiveContainer width="100%" height={Math.max(200, data.length * 36)}>
        <BarChart data={data} layout="vertical" barCategoryGap="18%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.12)" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <YAxis
            type="category"
            dataKey="code"
            tick={{ fill: '#9ca3af', fontSize: 10, fontFamily: 'monospace' }}
            axisLine={false}
            tickLine={false}
            width={70}
          />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey="count" name="Occurrences" radius={[0, 6, 6, 0]} animationDuration={1000}>
            {data.map((_, idx) => (
              <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
