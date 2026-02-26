import React from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import VehicleRiskMatrix from '../../components/charts/VehicleRiskMatrix';
import ComponentFailureRate from '../../components/charts/ComponentFailureRate';
import PredictiveAlertFunnel from '../../components/charts/PredictiveAlertFunnel';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

export default function ExecFleetHealth() {
    const { healthPie, HEALTH_COLORS, vehicles, componentFailures, alertFunnel } = useOutletContext();

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={spring}>
            <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-2">
                Fleet Health Distribution
            </h2>
            <p className="text-sm text-gray-400 dark:text-gray-500 mb-6 max-w-2xl leading-relaxed">
                This chart displays the current ratio of healthy vehicles versus those in warning or critical states.
                A healthy fleet should maintain <strong className="text-gray-300">&gt;80%</strong> in the green.
                Expanding 'Warning' segments indicate a growing maintenance backlog requiring proactive scheduling.
            </p>

            {/* Existing health pie */}
            <div className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl mb-8">
                {healthPie.length > 0 && healthPie.some((d) => d.value > 0) ? (
                    <div className="flex items-center gap-12">
                        <ResponsiveContainer width="40%" height={280}>
                            <PieChart>
                                <Pie
                                    data={healthPie}
                                    cx="50%" cy="50%"
                                    innerRadius={65} outerRadius={105}
                                    paddingAngle={4} dataKey="value"
                                    animationDuration={1400} animationEasing="ease-out" stroke="none"
                                >
                                    {healthPie.map((_, idx) => <Cell key={idx} fill={HEALTH_COLORS[idx]} />)}
                                </Pie>
                                <Tooltip contentStyle={tooltipStyle} />
                            </PieChart>
                        </ResponsiveContainer>

                        <div className="space-y-5">
                            {healthPie.map((entry, idx) => (
                                <div key={entry.name} className="flex items-center gap-4">
                                    <span className="w-4 h-4 rounded-full shrink-0" style={{ backgroundColor: HEALTH_COLORS[idx] }} />
                                    <div>
                                        <p className="text-2xl font-black text-gray-900 dark:text-white">{entry.value}</p>
                                        <p className="text-xs text-gray-400">{entry.name} vehicles</p>
                                    </div>
                                    <div className="ml-4 flex-1 h-2 rounded-full bg-gray-100 dark:bg-white/10 min-w-[120px]">
                                        <motion.div
                                            className="h-full rounded-full"
                                            style={{ backgroundColor: HEALTH_COLORS[idx] }}
                                            initial={{ width: 0 }}
                                            animate={{ width: `${healthPie.reduce((s, d) => s + d.value, 0) ? (entry.value / healthPie.reduce((s, d) => s + d.value, 0)) * 100 : 0}%` }}
                                            transition={{ duration: 1, ease: 'easeOut' }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="h-[280px] flex items-center justify-center">
                        <p className="text-sm text-gray-400">Loading fleet data…</p>
                    </div>
                )}
            </div>

            {/* Phase 4 charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <VehicleRiskMatrix vehicles={vehicles} />
                <PredictiveAlertFunnel stages={alertFunnel} />
            </div>

            <ComponentFailureRate components={componentFailures} />
        </motion.div>
    );
}
