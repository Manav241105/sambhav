import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/**
 * Technician utilisation heatmap — tech × hour-of-day grid.
 * Colour intensity = proportion of max utilisation.
 *
 * @param {{ technicians: Array<{name:string, hours_booked:number, utilisation:number}>, bookings: Array }} props
 */
export default function TechnicianUtilisation({ technicians = [], bookings = [] }) {
    // Build a per-tech × hour grid from bookings with slot times
    const HOURS = Array.from({ length: 10 }, (_, i) => i + 8); // 8 AM – 5 PM
    const techs = technicians.map((t) => t.name);

    if (!techs.length) {
        return (
            <div className="h-[240px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No technician data</p>
            </div>
        );
    }

    // Populate grid from bookings
    const grid = {};
    let maxCount = 1;

    techs.forEach((t) => {
        HOURS.forEach((h) => {
            grid[`${t}-${h}`] = 0;
        });
    });

    bookings.forEach((b) => {
        const tech = b.technician_name || 'Unassigned';
        const iso = b.slot_time_iso;
        if (!iso || !techs.includes(tech)) return;
        try {
            const dt = new Date(iso);
            const startH = dt.getHours();
            const dur = b.service_duration_hours || 2;
            for (let h = startH; h < startH + Math.ceil(dur) && h <= 17; h++) {
                const key = `${tech}-${h}`;
                if (key in grid) {
                    grid[key] += 1;
                    if (grid[key] > maxCount) maxCount = grid[key];
                }
            }
        } catch { /* ignore parse errors */ }
    });

    const getColor = (count) => {
        if (count === 0) return 'bg-gray-50 dark:bg-white/[0.02]';
        const intensity = count / maxCount;
        if (intensity < 0.33) return 'bg-emerald-200 dark:bg-emerald-500/20';
        if (intensity < 0.66) return 'bg-amber-300 dark:bg-amber-500/30';
        return 'bg-red-400 dark:bg-red-500/40';
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Technician Utilisation — Hour Grid
            </h3>
            <div className="overflow-x-auto">
                <table className="w-full border-separate" style={{ borderSpacing: 3 }}>
                    <thead>
                        <tr>
                            <th className="w-28" />
                            {HOURS.map((h) => (
                                <th key={h} className="text-[10px] font-medium text-gray-400 pb-1 text-center">
                                    {h}:00
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {techs.map((tech, ti) => (
                            <tr key={tech}>
                                <td className="text-[10px] font-semibold text-gray-600 dark:text-gray-300 pr-2 text-right truncate max-w-[120px]">
                                    {tech}
                                </td>
                                {HOURS.map((h) => {
                                    const count = grid[`${tech}-${h}`] || 0;
                                    return (
                                        <motion.td
                                            key={h}
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: ti * 0.04 + (h - 8) * 0.02 }}
                                            className={`w-8 h-8 text-center rounded-lg ${getColor(count)}`}
                                            title={`${tech} at ${h}:00 — ${count} job(s)`}
                                        >
                                            <span className="text-[9px] font-bold text-gray-600 dark:text-gray-300">
                                                {count || ''}
                                            </span>
                                        </motion.td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {/* Legend */}
            <div className="flex items-center gap-3 mt-4">
                <span className="text-[10px] text-gray-400">Free</span>
                {['bg-gray-50 dark:bg-white/[0.02]', 'bg-emerald-200 dark:bg-emerald-500/20', 'bg-amber-300 dark:bg-amber-500/30', 'bg-red-400 dark:bg-red-500/40'].map((cls, i) => (
                    <div key={i} className={`w-5 h-3 rounded ${cls}`} />
                ))}
                <span className="text-[10px] text-gray-400">Overloaded</span>
            </div>
        </motion.div>
    );
}
