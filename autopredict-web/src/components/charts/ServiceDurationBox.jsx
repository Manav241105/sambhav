import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const ACCENT = '#6366f1';

/**
 * Box-and-whisker plot for service durations grouped by component.
 * Pure SVG — no charting library dependency.
 *
 * @param {{ components: Array<{component:string, min:number, q1:number, median:number, q3:number, max:number}> }} props
 */
export default function ServiceDurationBox({ components = [] }) {
    if (!components.length) {
        return (
            <div className="h-[280px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No service duration data</p>
            </div>
        );
    }

    const globalMax = Math.max(...components.map((c) => c.max), 1);
    const W = 600;
    const ROW_H = 44;
    const PAD_LEFT = 130;
    const PAD_RIGHT = 20;
    const chartW = W - PAD_LEFT - PAD_RIGHT;

    const scale = (v) => PAD_LEFT + (v / globalMax) * chartW;

    const COLORS = ['#6366f1', '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Service Duration Distribution
            </h3>
            <svg viewBox={`0 0 ${W} ${components.length * ROW_H + 30}`} className="w-full" style={{ maxHeight: 360 }}>
                {/* X-axis ticks */}
                {[0, 1, 2, 3, 4, 5, 6].filter((v) => v <= globalMax).map((v) => (
                    <g key={v}>
                        <line x1={scale(v)} y1={8} x2={scale(v)} y2={components.length * ROW_H + 10} stroke="rgba(156,163,175,0.15)" />
                        <text x={scale(v)} y={components.length * ROW_H + 24} textAnchor="middle" fill="#9ca3af" fontSize={10}>{v}h</text>
                    </g>
                ))}

                {components.map((c, i) => {
                    const y = i * ROW_H + 20;
                    const color = COLORS[i % COLORS.length];
                    return (
                        <g key={c.component}>
                            {/* Label */}
                            <text x={PAD_LEFT - 8} y={y + 4} textAnchor="end" fill="#9ca3af" fontSize={11} fontWeight={600}>
                                {c.component}
                            </text>
                            {/* Whisker line (min to max) */}
                            <line x1={scale(c.min)} y1={y} x2={scale(c.max)} y2={y} stroke={color} strokeWidth={1.5} />
                            {/* Min cap */}
                            <line x1={scale(c.min)} y1={y - 6} x2={scale(c.min)} y2={y + 6} stroke={color} strokeWidth={1.5} />
                            {/* Max cap */}
                            <line x1={scale(c.max)} y1={y - 6} x2={scale(c.max)} y2={y + 6} stroke={color} strokeWidth={1.5} />
                            {/* Box (Q1 to Q3) */}
                            <rect
                                x={scale(c.q1)}
                                y={y - 10}
                                width={scale(c.q3) - scale(c.q1)}
                                height={20}
                                rx={4}
                                fill={color}
                                fillOpacity={0.2}
                                stroke={color}
                                strokeWidth={1.5}
                            />
                            {/* Median line */}
                            <line x1={scale(c.median)} y1={y - 10} x2={scale(c.median)} y2={y + 10} stroke={color} strokeWidth={2.5} />
                        </g>
                    );
                })}
            </svg>
        </motion.div>
    );
}
