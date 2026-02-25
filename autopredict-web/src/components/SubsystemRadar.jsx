import React from 'react';
import { motion } from 'framer-motion';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/**
 * 8-axis subsystem radar chart — powered by Recharts.
 * Shows the health state of the main vehicle subsystems.
 *
 * Props:
 *   telematics — the raw telematics object from the API (latest snapshot)
 *   diagnosis  — the diagnosis object (severity, predicted_component, etc.)
 */

/* ── Default 8-axis labels + extract helpers ─────── */
const AXES = [
  { key: 'brake',        label: 'Brakes',       extract: (t) => normalise(t?.brake_pad_thickness, 0, 12) },
  { key: 'battery',      label: 'Battery',      extract: (t) => normalise(t?.battery_voltage, 10, 14.5) },
  { key: 'coolant',      label: 'Coolant',      extract: (t) => 1 - normalise(t?.coolant_temp, 70, 120) },  // inverted — lower is healthier
  { key: 'tires',        label: 'Tires',        extract: (t) => normalise(t?.tire_pressure_fl, 28, 35) },
  { key: 'engine',       label: 'Engine',       extract: (t) => normalise(t?.engine_rpm, 600, 6000) },
  { key: 'oil',          label: 'Oil',          extract: (t) => normalise(t?.oil_pressure, 20, 65) },
  { key: 'transmission', label: 'Transmission', extract: (t) => 1 - normalise(t?.transmission_temp, 60, 120) },
  { key: 'fuel',         label: 'Fuel System',  extract: (t) => normalise(t?.fuel_level, 0, 100) },
];

function normalise(val, min, max) {
  if (val == null) return 0.7; // default to "decent" if missing
  return Math.min(Math.max((val - min) / (max - min), 0), 1);
}

function extractLatest(telematics) {
  if (!telematics) return null;
  // telematics can be an array of snapshots or a single object
  if (Array.isArray(telematics)) return telematics[telematics.length - 1] || null;
  return telematics;
}

export default function SubsystemRadar({ telematics, diagnosis }) {
  const latest = extractLatest(telematics);

  const data = AXES.map((axis) => ({
    subject: axis.label,
    health: Math.round(axis.extract(latest) * 100),
    fullMark: 100,
  }));

  const severityColor =
    diagnosis?.severity === 'critical' ? '#ef4444' :
    diagnosis?.severity === 'warning'  ? '#fbbf24' :
    '#caff42';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.92 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={spring}
      className="w-full"
    >
      <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-2">
        Subsystem Health
      </h4>

      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid
            stroke="currentColor"
            className="text-gray-200 dark:text-white/10"
          />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: '#9ca3af', fontSize: 10, fontWeight: 500 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={false}
            axisLine={false}
          />
          <Radar
            name="Health"
            dataKey="health"
            stroke={severityColor}
            fill={severityColor}
            fillOpacity={0.18}
            strokeWidth={2}
            dot={{ r: 3, fill: severityColor }}
            animationDuration={1200}
            animationEasing="ease-out"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '12px',
              fontSize: 12,
              color: '#fff',
            }}
            formatter={(val) => [`${val}%`, 'Health']}
          />
        </RadarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
