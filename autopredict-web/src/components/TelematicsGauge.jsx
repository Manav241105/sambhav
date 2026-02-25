import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/* ── Colour mapping for each metric ───────────────── */
const METRIC_COLORS = {
  default:               { track: '#e5e7eb', fill: '#caff42' },
  battery_voltage:       { track: '#e5e7eb', fill: '#22c55e' },
  brake_pad_thickness:   { track: '#e5e7eb', fill: '#ef4444' },
  coolant_temp:          { track: '#e5e7eb', fill: '#3b82f6' },
  tire_pressure:         { track: '#e5e7eb', fill: '#f59e0b' },
  engine_rpm:            { track: '#e5e7eb', fill: '#8b5cf6' },
  oil_pressure:          { track: '#e5e7eb', fill: '#14b8a6' },
  transmission_temp:     { track: '#e5e7eb', fill: '#f97316' },
};

/**
 * Animated arc gauge — shows a single telemetry value as a half-circle.
 *
 * Props:
 *   label     — human-readable metric name (e.g. "Battery Voltage")
 *   value     — current value (e.g. 12.4)
 *   max       — maximum of the range (e.g. 14)
 *   unit      — unit string (e.g. "V")
 *   metricKey — key into METRIC_COLORS (e.g. "battery_voltage")
 *   size      — SVG viewBox width/height (default 140)
 */
export default function TelematicsGauge({
  label = 'Metric',
  value = 0,
  max = 100,
  unit = '',
  metricKey = 'default',
  size = 140,
}) {
  const colors = METRIC_COLORS[metricKey] || METRIC_COLORS.default;
  const pct = Math.min(Math.max(value / max, 0), 1);

  // Arc geometry — 180° half-circle at top
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2 - 4;
  const cx = size / 2;
  const cy = size / 2 + 10; // shift arc up slightly

  // Arc path (semi-circle from left to right)
  const startAngle = Math.PI;
  const endAngle = 0;
  const arcLength = Math.PI * radius; // half circumference

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={spring}
      className="flex flex-col items-center gap-1"
    >
      <svg width={size} height={size * 0.65} viewBox={`0 0 ${size} ${size * 0.65}`} className="overflow-visible">
        {/* Track */}
        <path
          d={describeArc(cx, cy, radius, startAngle, endAngle)}
          fill="none"
          stroke="currentColor"
          className="text-gray-200 dark:text-white/10"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Filled arc */}
        <motion.path
          d={describeArc(cx, cy, radius, startAngle, endAngle)}
          fill="none"
          stroke={colors.fill}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={arcLength}
          initial={{ strokeDashoffset: arcLength }}
          animate={{ strokeDashoffset: arcLength * (1 - pct) }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />

        {/* Value text in centre */}
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          dominantBaseline="central"
          className="fill-gray-900 dark:fill-white text-lg font-extrabold"
        >
          {typeof value === 'number' ? value.toFixed(1) : value}
        </text>
        <text
          x={cx}
          y={cy + 14}
          textAnchor="middle"
          dominantBaseline="central"
          className="fill-gray-400 dark:fill-gray-500 text-[10px] font-medium"
        >
          {unit}
        </text>
      </svg>

      <span className="text-[11px] font-medium text-gray-500 dark:text-gray-400 text-center leading-tight">
        {label}
      </span>
    </motion.div>
  );
}

/* ── Helper: SVG arc path ─────────────────────────── */
function describeArc(cx, cy, r, startAngle, endAngle) {
  const x1 = cx + r * Math.cos(startAngle);
  const y1 = cy - r * Math.sin(startAngle);
  const x2 = cx + r * Math.cos(endAngle);
  const y2 = cy - r * Math.sin(endAngle);
  const largeArc = Math.abs(endAngle - startAngle) > Math.PI ? 1 : 0;
  return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`;
}
