import React from 'react';
import { motion } from 'framer-motion';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
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
 * HealthScoreTimeline — area chart showing vehicle health score over time.
 *
 * Props:
 *   data   — array from GET /api/vehicles/{id}/history  → history[]
 *            each item must have { day_label, health_score }
 *   height — chart height in px (default 180)
 */
export default function HealthScoreTimeline({ data = [], height = 180 }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-36 flex items-center justify-center">
        <p className="text-xs text-gray-400 dark:text-gray-500">No history data</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={spring}
    >
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="healthGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.12)" />
          <XAxis
            dataKey="day_label"
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 1]}
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={(v) => [`${(v * 100).toFixed(1)}%`, 'Health']}
          />
          <Area
            type="monotone"
            dataKey="health_score"
            stroke="#6366f1"
            strokeWidth={2}
            fill="url(#healthGrad)"
            dot={{ r: 3, fill: '#6366f1', stroke: '#fff', strokeWidth: 1.5 }}
            activeDot={{ r: 5 }}
            animationDuration={1000}
          />
        </AreaChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
