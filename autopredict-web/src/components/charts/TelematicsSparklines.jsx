import React from 'react';
import { ResponsiveContainer, LineChart, Line } from 'recharts';

/**
 * TelematicsSparklines — a tiny 7-day trend line with no axes.
 *
 * Props:
 *   data      — array of { day_label, battery_voltage_v, brake_pad_mm, … }
 *   dataKey   — which field to plot (default: "battery_voltage_v")
 *   color     — stroke colour (default: brand indigo)
 *   height    — pixel height (default: 32)
 */
export default function TelematicsSparklines({
  data = [],
  dataKey = 'battery_voltage_v',
  color = '#6366f1',
  height = 32,
}) {
  if (!data || data.length === 0) return null;

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={true}
            animationDuration={800}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
