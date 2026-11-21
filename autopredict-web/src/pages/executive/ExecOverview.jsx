import React from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import FleetHealthScoreGauge from '../../components/charts/FleetHealthScoreGauge';
import KPITrendCards from '../../components/charts/KPITrendCards';
import CostAvoidanceWaterfall from '../../components/charts/CostAvoidanceWaterfall';
import AIExecutiveSummary from '../../components/charts/AIExecutiveSummary';
import ROIDashboard from '../../components/charts/ROIDashboard';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

export default function ExecOverview() {
    const { bigMetrics, fleetHealthScore, vehicles, summary, kpiTrends, roiData, costAvoidance } = useOutletContext();

    return (
        <div>
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-6">
                High-level pulse check across the fleet. Click a tab above for deeper analysis.
            </p>

            {/* KPI stat cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
                {bigMetrics.map((card, i) => {
                    const Icon = card.icon;
                    return (
                        <motion.div
                            key={card.label}
                            initial={{ opacity: 0, y: 24 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ ...spring, delay: i * 0.08 }}
                            className="group relative p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl overflow-hidden"
                        >
                            <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-[#6366f1] to-transparent opacity-0 group-hover:opacity-[0.06] blur-xl transition-opacity pointer-events-none" />
                            <div className={`p-3 rounded-2xl bg-gray-100 dark:bg-white/5 ${card.color} w-fit mb-3`}>
                                <Icon size={22} />
                            </div>
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{card.label}</p>
                            <p className="text-2xl font-extrabold text-gray-900 dark:text-white tracking-tight">{card.value}</p>
                            <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">{card.sub}</p>
                        </motion.div>
                    );
                })}
            </div>

            {/* AI Summary + Fleet Health Gauge */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <div className="lg:col-span-2">
                    <AIExecutiveSummary />
                </div>
                <FleetHealthScoreGauge
                    score={fleetHealthScore}
                    total={summary?.total_vehicles ?? 0}
                    critical={summary?.critical_vehicles ?? 0}
                    warning={vehicles.filter((v) => v.scenario === 'warning' || v.priority === 'P2').length}
                />
            </div>

            {/* KPI Trend Cards */}
            <div className="mb-8">
                <KPITrendCards trends={kpiTrends} />
            </div>

            {/* Cost Avoidance Waterfall + ROI Dashboard */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <CostAvoidanceWaterfall breakdown={costAvoidance.breakdown} total={costAvoidance.total} />
                <ROIDashboard roi={roiData} />
            </div>
        </div>
    );
}
