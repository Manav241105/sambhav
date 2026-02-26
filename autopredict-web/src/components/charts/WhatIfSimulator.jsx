import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/**
 * What-If Simulator
 *
 * Sliders:
 *   • Extra technicians (+0…+5)
 *   • Extra bays (+0…+3)
 *   • AI coverage increase (+0%…+30%)
 *
 * Shows predicted impact on bookings/week, avg service time, acceptance rate.
 *
 * @param {{ baseline: { bookings_per_week: number, avg_service_hours: number, acceptance_pct: number } }} props
 */
export default function WhatIfSimulator({
    baseline = { bookings_per_week: 48, avg_service_hours: 3.2, acceptance_pct: 68 },
}) {
    const [extraTechs, setExtraTechs] = useState(0);
    const [extraBays, setExtraBays] = useState(0);
    const [aiBoost, setAiBoost] = useState(0);

    const projected = useMemo(() => {
        // Simple deterministic model for a simulator feel
        const bookings = Math.round(
            baseline.bookings_per_week * (1 + extraTechs * 0.08 + extraBays * 0.12 + aiBoost * 0.005)
        );
        const serviceHrs = Math.max(
            1,
            +(baseline.avg_service_hours * (1 - extraTechs * 0.03 - extraBays * 0.04 - aiBoost * 0.002)).toFixed(1)
        );
        const acceptance = Math.min(
            100,
            Math.round(baseline.acceptance_pct + extraTechs * 1.5 + aiBoost * 0.7)
        );
        return { bookings, serviceHrs, acceptance };
    }, [extraTechs, extraBays, aiBoost, baseline]);

    const sliders = [
        { label: 'Extra Technicians', value: extraTechs, set: setExtraTechs, min: 0, max: 5, unit: '' },
        { label: 'Extra Bays', value: extraBays, set: setExtraBays, min: 0, max: 3, unit: '' },
        { label: 'AI Coverage Increase', value: aiBoost, set: setAiBoost, min: 0, max: 30, unit: '%' },
    ];

    const metrics = [
        { label: 'Bookings / Week', base: baseline.bookings_per_week, proj: projected.bookings },
        { label: 'Avg Service (hrs)', base: baseline.avg_service_hours, proj: projected.serviceHrs },
        { label: 'Acceptance Rate', base: `${baseline.acceptance_pct}%`, proj: `${projected.acceptance}%` },
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-5">
                What-If Simulator
            </h3>

            {/* Sliders */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-6">
                {sliders.map((s) => (
                    <div key={s.label}>
                        <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
                            {s.label}
                        </label>
                        <input
                            type="range"
                            min={s.min}
                            max={s.max}
                            value={s.value}
                            onChange={(e) => s.set(Number(e.target.value))}
                            className="w-full accent-[#caff42]"
                        />
                        <p className="text-right text-xs font-bold text-gray-900 dark:text-white mt-0.5">
                            +{s.value}{s.unit}
                        </p>
                    </div>
                ))}
            </div>

            {/* Projected metrics */}
            <div className="grid grid-cols-3 gap-4">
                {metrics.map((m) => {
                    const up = typeof m.proj === 'number' ? m.proj > m.base : parseFloat(m.proj) > parseFloat(m.base);
                    const label = m.label === 'Avg Service (hrs)' ? !up : up; // lower is better for service hours
                    return (
                        <div
                            key={m.label}
                            className="p-4 rounded-2xl bg-gray-50 dark:bg-white/5 text-center"
                        >
                            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1">{m.label}</p>
                            <p className="text-lg font-extrabold text-gray-900 dark:text-white">{m.proj}</p>
                            <p className={`text-[10px] font-bold mt-0.5 ${label ? 'text-green-500' : 'text-red-500'}`}>
                                was {m.base}
                            </p>
                        </div>
                    );
                })}
            </div>
        </motion.div>
    );
}
