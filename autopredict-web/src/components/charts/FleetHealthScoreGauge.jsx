import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/**
 * Large radial gauge showing overall fleet health score (0–100 %).
 *
 * @param {{ score: number, total: number, critical: number, warning: number }} props
 */
export default function FleetHealthScoreGauge({ score = 0, total = 0, critical = 0, warning = 0 }) {
    const pct = Math.min(Math.max(score, 0), 100);
    const R = 80;
    const STROKE = 14;
    const C = 2 * Math.PI * R;
    const arcLen = C * 0.75; // 270° arc
    const fill = arcLen * (pct / 100);

    const color = pct >= 80 ? '#22c55e' : pct >= 60 ? '#fbbf24' : '#ef4444';

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl flex flex-col items-center"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4 self-start">
                Fleet Health Score
            </h3>

            <svg width={200} height={180} viewBox="0 0 200 200">
                {/* Background arc */}
                <circle
                    cx={100} cy={100} r={R}
                    fill="none"
                    stroke="rgba(156,163,175,0.12)"
                    strokeWidth={STROKE}
                    strokeDasharray={`${arcLen} ${C}`}
                    strokeDashoffset={0}
                    strokeLinecap="round"
                    transform="rotate(135 100 100)"
                />
                {/* Filled arc */}
                <motion.circle
                    cx={100} cy={100} r={R}
                    fill="none"
                    stroke={color}
                    strokeWidth={STROKE}
                    strokeDasharray={`${arcLen} ${C}`}
                    strokeLinecap="round"
                    transform="rotate(135 100 100)"
                    initial={{ strokeDashoffset: arcLen }}
                    animate={{ strokeDashoffset: arcLen - fill }}
                    transition={{ duration: 1.5, ease: 'easeOut' }}
                />
                {/* Score text */}
                <text x={100} y={92} textAnchor="middle" dominantBaseline="middle"
                    style={{ fontSize: 36, fontWeight: 900, fill: 'currentColor' }} className="text-gray-900 dark:text-white">
                    {pct}%
                </text>
                <text x={100} y={115} textAnchor="middle" style={{ fontSize: 11, fill: '#9ca3af' }}>
                    fleet health
                </text>
            </svg>

            <div className="flex gap-6 mt-2">
                {[
                    { label: 'Total', value: total, cls: 'text-gray-500' },
                    { label: 'Critical', value: critical, cls: 'text-red-500' },
                    { label: 'Warning', value: warning, cls: 'text-amber-500' },
                ].map(({ label, value, cls }) => (
                    <div key={label} className="text-center">
                        <p className={`text-lg font-extrabold ${cls}`}>{value}</p>
                        <p className="text-[10px] text-gray-400">{label}</p>
                    </div>
                ))}
            </div>
        </motion.div>
    );
}
