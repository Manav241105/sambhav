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
  Legend,
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

const BAR_COLORS = ['#6366f1', '#38bdf8', '#fb923c', '#a78bfa', '#34d399'];

/**
 * TechnicianWorkload — stacked / grouped bar chart of technician hours + utilisation.
 *
 * Props:
 *   technicians — array from GET /api/analytics/workload → technicians
 *   bays        — array from GET /api/analytics/workload → bays
 */
export default function TechnicianWorkload({ technicians = [], bays = [] }) {
  const data = technicians.map((t) => ({
    name: t.name?.split(' ')[0] || t.name,        // first name for label brevity
    hours: t.hours_booked,
    utilisation: +(t.utilisation * 100).toFixed(0), // 0-100 %
  }));

  if (data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center">
        <p className="text-xs text-gray-400 dark:text-gray-500">No workload data</p>
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
        <BarChart data={data} barCategoryGap="20%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.12)" />
          <XAxis
            dataKey="name"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            domain={[0, 10]}
            label={{ value: 'Hours', angle: -90, position: 'insideLeft', fill: '#9ca3af', fontSize: 10 }}
          />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Bar
            dataKey="hours"
            name="Hours Booked"
            radius={[8, 8, 0, 0]}
            animationDuration={1000}
          >
            {data.map((_, idx) => (
              <Cell key={idx} fill={BAR_COLORS[idx % BAR_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Bay utilisation pills */}
      {bays.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {bays.map((b) => (
            <span
              key={b.bay}
              className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-300"
            >
              {b.bay}: {b.hours_booked}h ({(b.utilisation * 100).toFixed(0)}%)
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}
