import React from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import RecallHeatmapExec from '../../components/charts/RecallHeatmapExec';
import RecallCompletionDonut from '../../components/charts/RecallCompletionDonut';
import RecallTimelineBar from '../../components/charts/RecallTimelineBar';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

const PRI = {
    P0: 'bg-red-500/15 text-red-500',
    P1: 'bg-orange-500/15 text-orange-500',
    P2: 'bg-amber-500/15 text-amber-500',
    P3: 'bg-emerald-500/15 text-emerald-500',
};

export default function ExecRecalls() {
    const { topAtRisk, loading, recallHeatmap, recallCompletion, recallTimeline } = useOutletContext();

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={spring}>
            <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-2">
                Top 5 At-Risk Vehicles
            </h2>
            <p className="text-sm text-gray-400 dark:text-gray-500 mb-6 max-w-2xl leading-relaxed">
                Prioritises vehicles based on AI-calculated failure probability and remaining useful life (RUL).
                Vehicles flagged as <strong className="text-red-400">P0/P1</strong> require immediate manual intervention or priority scheduling.
                RUL below 7 days signals an urgent service window.
            </p>

            {/* Existing top-at-risk table */}
            <div className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl mb-8">
                <div className="grid grid-cols-12 gap-3 px-4 pb-3 border-b border-gray-200 dark:border-gray-700">
                    {['#', 'Vehicle', 'Make / Model', 'Priority', 'Failure Prob.', 'Component', 'RUL'].map((h, i) => (
                        <span key={h} className={`col-span-${[1, 2, 2, 2, 2, 2, 1][i]} text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase`}>{h}</span>
                    ))}
                </div>

                <div className="divide-y divide-gray-100 dark:divide-white/5">
                    {loading ? (
                        <p className="text-xs text-gray-400 text-center py-8">Loading…</p>
                    ) : topAtRisk.length === 0 ? (
                        <p className="text-xs text-gray-400 text-center py-8">No vehicle data available</p>
                    ) : (
                        topAtRisk.map((v, i) => {
                            const failPct = Math.round((v.failure_probability || 0) * 100);
                            const comp = v.diagnosis?.predicted_component?.replace(/_/g, ' ') || '—';
                            const rul = v.diagnosis?.rul_days;

                            return (
                                <motion.div
                                    key={v.vehicle_id}
                                    initial={{ opacity: 0, x: -12 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ ...spring, delay: i * 0.06 }}
                                    className="grid grid-cols-12 gap-3 px-4 py-3.5 items-center hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors rounded-xl"
                                >
                                    <span className="col-span-1 text-xs font-extrabold text-gray-400">{i + 1}</span>
                                    <span className="col-span-2 text-xs font-bold text-gray-900 dark:text-white">{v.vehicle_id}</span>
                                    <span className="col-span-2 text-xs text-gray-600 dark:text-gray-300">{v.make} {v.model}</span>
                                    <span className="col-span-2">
                                        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${PRI[v.priority] || PRI.P3}`}>{v.priority}</span>
                                    </span>
                                    <span className="col-span-2 flex items-center gap-2">
                                        <div className="flex-1 h-2 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden">
                                            <motion.div
                                                className={`h-full rounded-full ${failPct >= 70 ? 'bg-red-500' : failPct >= 40 ? 'bg-amber-400' : 'bg-emerald-500'}`}
                                                initial={{ width: 0 }}
                                                animate={{ width: `${failPct}%` }}
                                                transition={{ duration: 1, ease: 'easeOut' }}
                                            />
                                        </div>
                                        <span className="text-xs font-bold text-gray-900 dark:text-white w-8 text-right">{failPct}%</span>
                                    </span>
                                    <span className="col-span-2 text-xs text-gray-600 dark:text-gray-300 capitalize truncate">{comp}</span>
                                    <span className="col-span-1 text-xs font-medium text-gray-500 dark:text-gray-400">{rul != null ? `${rul}d` : '—'}</span>
                                </motion.div>
                            );
                        })
                    )}
                </div>
            </div>

            {/* Phase 4 recalls charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <RecallCompletionDonut completion={recallCompletion} />
                <RecallTimelineBar timeline={recallTimeline} />
            </div>

            <RecallHeatmapExec heatmap={recallHeatmap} />
        </motion.div>
    );
}
