import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/**
 * Month-over-month KPI delta chips for 6 metrics.
 *
 * @param {{ kpis: Array<{kpi:string, current:number, previous:number, delta:number, delta_pct:number, unit:string, is_positive:boolean}> }} props
 */
export default function KPITrendCards({ kpis = [] }) {
    if (!kpis.length) {
        return (
            <div className="h-[120px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No KPI data</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {kpis.map((kpi, i) => {
                const colorCls = kpi.is_positive ? 'text-emerald-500' : kpi.delta === 0 ? 'text-gray-400' : 'text-red-500';
                const bgCls = kpi.is_positive ? 'bg-emerald-500/10' : kpi.delta === 0 ? 'bg-gray-100 dark:bg-white/5' : 'bg-red-500/10';
                const Icon = kpi.delta > 0 ? TrendingUp : kpi.delta < 0 ? TrendingDown : Minus;

                return (
                    <motion.div
                        key={kpi.kpi}
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ ...spring, delay: i * 0.06 }}
                        className="p-4 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-2xl"
                    >
                        <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1 truncate">{kpi.kpi}</p>
                        <p className="text-lg font-extrabold text-gray-900 dark:text-white">
                            {kpi.current}{kpi.unit}
                        </p>
                        <div className={`inline-flex items-center gap-1 mt-1.5 px-2 py-0.5 rounded-full ${bgCls}`}>
                            <Icon size={11} className={colorCls} />
                            <span className={`text-[10px] font-bold ${colorCls}`}>
                                {kpi.delta_pct > 0 ? '+' : ''}{kpi.delta_pct}%
                            </span>
                        </div>
                    </motion.div>
                );
            })}
        </div>
    );
}
