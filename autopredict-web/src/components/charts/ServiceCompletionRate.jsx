import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/**
 * ServiceCompletionRate — animated radial progress ring.
 *
 * Props:
 *   total      — total bookings
 *   completed  — completed bookings
 *   pending    — pending / confirmed bookings
 *   size       — ring diameter (default 160)
 */
export default function ServiceCompletionRate({
  total = 0,
  completed = 0,
  pending = 0,
  size = 160,
}) {
  const rate = total > 0 ? completed / total : 0;
  const strokeWidth = 14;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - rate);

  const completedColor = '#22c55e';
  const pendingColor = '#6366f1';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={spring}
      className="flex flex-col items-center"
    >
      <svg width={size} height={size} className="-rotate-90">
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          className="text-gray-200 dark:text-white/10"
          strokeWidth={strokeWidth}
        />
        {/* Completed arc */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={completedColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.4, ease: 'easeOut' }}
        />
        {/* Centre text */}
        <text
          x={size / 2}
          y={size / 2}
          dominantBaseline="central"
          textAnchor="middle"
          className="fill-gray-900 dark:fill-white text-2xl font-extrabold"
          transform={`rotate(90 ${size / 2} ${size / 2})`}
        >
          {Math.round(rate * 100)}%
        </text>
      </svg>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-3">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: completedColor }} />
          <span className="text-[10px] font-medium text-gray-500 dark:text-gray-400">
            Completed ({completed})
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: pendingColor }} />
          <span className="text-[10px] font-medium text-gray-500 dark:text-gray-400">
            Pending ({pending})
          </span>
        </div>
      </div>
    </motion.div>
  );
}
