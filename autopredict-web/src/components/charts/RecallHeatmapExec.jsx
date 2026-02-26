import React from 'react';
import { motion } from 'framer-motion';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/**
 * Heatmap matrix: Make × Recall Campaign.
 * Cells show affected vehicle count; colour intensity = severity.
 *
 * @param {{ heatmap: Array<{make:string, campaign:string, count:number}>, makes?: string[], campaigns?: string[] }} props
 */
export default function RecallHeatmapExec({ heatmap = [] }) {
    if (!heatmap.length) {
        return (
            <div className="h-[300px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No recall heatmap data</p>
            </div>
        );
    }

    // Derive unique makes and campaigns
    const makesSet = new Set();
    const campaignsSet = new Set();
    const lookup = {};
    let maxCount = 1;

    heatmap.forEach((h) => {
        makesSet.add(h.make);
        campaignsSet.add(h.campaign);
        const key = `${h.make}__${h.campaign}`;
        lookup[key] = h.count;
        if (h.count > maxCount) maxCount = h.count;
    });

    const makes = [...makesSet];
    const campaigns = [...campaignsSet];

    const colourForCount = (count) => {
        if (!count) return 'rgba(156,163,175,0.07)';
        const ratio = count / maxCount;
        if (ratio > 0.75) return '#ef4444';
        if (ratio > 0.5) return '#f97316';
        if (ratio > 0.25) return '#facc15';
        return '#86efac';
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl overflow-x-auto"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Recall Heatmap — Make × Campaign
            </h3>
            <table className="w-full text-[11px]">
                <thead>
                    <tr>
                        <th className="text-left text-gray-500 py-1 pr-3">Make</th>
                        {campaigns.map((c) => (
                            <th key={c} className="text-center text-gray-500 py-1 px-2 max-w-[90px] truncate">{c}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {makes.map((m) => (
                        <tr key={m}>
                            <td className="font-semibold text-gray-700 dark:text-gray-300 py-1 pr-3 whitespace-nowrap">{m}</td>
                            {campaigns.map((c) => {
                                const count = lookup[`${m}__${c}`] || 0;
                                return (
                                    <td key={c} className="text-center py-1 px-2">
                                        <div
                                            className="mx-auto w-10 h-8 flex items-center justify-center rounded-lg text-[10px] font-bold"
                                            style={{
                                                backgroundColor: colourForCount(count),
                                                color: count && count / maxCount > 0.5 ? '#fff' : '#374151',
                                            }}
                                        >
                                            {count || '—'}
                                        </div>
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>

            {/* Legend */}
            <div className="flex items-center gap-3 mt-4">
                <span className="text-[10px] text-gray-500">Low</span>
                {['#86efac', '#facc15', '#f97316', '#ef4444'].map((c) => (
                    <div key={c} className="w-5 h-3 rounded" style={{ backgroundColor: c }} />
                ))}
                <span className="text-[10px] text-gray-500">High</span>
            </div>
        </motion.div>
    );
}
