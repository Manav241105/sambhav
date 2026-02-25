import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/* ── Thresholds per metric:  [goodMax, warnMax]
   • value <= goodMax  → green  (healthy)
   • value <= warnMax  → yellow (warning)
   • value >  warnMax  → red    (critical)
   For metrics where HIGH is bad (coolant, temp, etc.) this is the correct direction.
   For metrics where LOW is bad (battery, brake pad, oil) we invert via `invertedRisk`. ── */
const THRESHOLDS = {
  battery_voltage: { low: 12.0, mid: 12.6, invertedRisk: true }, // low = bad
  brake_pad_thickness: { low: 4.0, mid: 7.0, invertedRisk: true }, // low = bad
  coolant_temp: { low: 95, mid: 105, invertedRisk: false }, // high = bad
  tire_pressure: { low: 28, mid: 32, invertedRisk: true }, // low = bad
  oil_pressure: { low: 30, mid: 45, invertedRisk: true }, // low = bad
  transmission_temp: { low: 90, mid: 110, invertedRisk: false }, // high = bad
  engine_rpm: { low: 3500, mid: 5000, invertedRisk: false }, // high = bad
};

const GREEN = '#22c55e';
const YELLOW = '#f59e0b';
const RED = '#ef4444';

function gaugeColor(metricKey, value) {
  const t = THRESHOLDS[metricKey];
  if (!t) return '#6366f1'; // fallback indigo
  if (t.invertedRisk) {
    // Low values are dangerous
    if (value <= t.low) return RED;
    if (value <= t.mid) return YELLOW;
    return GREEN;
  } else {
    // High values are dangerous
    if (value >= t.mid) return RED;
    if (value >= t.low) return YELLOW;
    return GREEN;
  }
}

/**
 * Animated arc gauge.
 * Props: label, value, max, unit, metricKey, size
 */
export default function TelematicsGauge({
  label = 'Metric',
  value = 0,
  max = 100,
  unit = '',
  metricKey = 'default',
  size = 140,
}) {
  const fillColor = gaugeColor(metricKey, value);
  const pct = Math.min(Math.max(value / max, 0), 1);

  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2 - 4;
  const cx = size / 2;
  const cy = size / 2 + 10;
  const startAngle = Math.PI;
  const endAngle = 0;
  const arcLength = Math.PI * radius;

  // Dot indicator at tip of arc
  const tipAngle = Math.PI - pct * Math.PI;
  const dotX = cx + radius * Math.cos(tipAngle);
  const dotY = cy - radius * Math.sin(tipAngle);

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

        {/* Coloured arc */}
        <motion.path
          d={describeArc(cx, cy, radius, startAngle, endAngle)}
          fill="none"
          stroke={fillColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={arcLength}
          initial={{ strokeDashoffset: arcLength }}
          animate={{ strokeDashoffset: arcLength * (1 - pct) }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />

        {/* Glowing tip dot */}
        <motion.circle
          cx={dotX}
          cy={dotY}
          r={5}
          fill={fillColor}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.3 }}
          style={{ filter: `drop-shadow(0 0 4px ${fillColor})` }}
        />

        {/* Value label */}
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          dominantBaseline="central"
          fill={fillColor}
          fontSize="15"
          fontWeight="800"
        >
          {typeof value === 'number' ? value.toFixed(1) : value}
        </text>

        {/* Unit label */}
        <text
          x={cx}
          y={cy + 14}
          textAnchor="middle"
          dominantBaseline="central"
          className="fill-gray-400 dark:fill-gray-500"
          fontSize="9"
          fontWeight="500"
        >
          {unit}
        </text>
      </svg>

      {/* Status pill */}
      <span
        className="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
        style={{
          color: fillColor,
          backgroundColor: fillColor + '20',
        }}
      >
        {fillColor === RED ? 'Critical' : fillColor === YELLOW ? 'Warning' : 'Good'}
      </span>

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
