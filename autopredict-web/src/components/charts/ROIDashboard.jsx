import React from 'react';
import { formatINR, formatINRCompact } from '../../lib/format';
import { motion } from 'framer-motion';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

/**
 * ROI Dashboard — cost avoidance vs system operating cost over 6 months.
 *
 * @param {{ roi: Array<{month:string, cost_avoidance:number, operating_cost:number, net:number}> }} props
 */
export default function ROIDashboard({ roi = [] }) {
    if (!roi.length) {
        return (
            <div className="h-[300px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No ROI data</p>
            </div>
        );
    }

    const totalAvoidance = roi.reduce((s, r) => s + r.cost_avoidance, 0);
    const totalOperating = roi.reduce((s, r) => s + r.operating_cost, 0);
    const netROI = totalAvoidance - totalOperating;

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider">
                    ROI Dashboard
                </h3>
                <div className="flex items-center gap-4">
                    <div className="text-center">
                        <p className="text-[10px] text-gray-500 uppercase tracking-wider">Cost Avoided</p>
                        <p className="text-sm font-extrabold text-green-500">${(totalAvoidance / 1000).toFixed(0)}k</p>
                    </div>
                    <div className="text-center">
                        <p className="text-[10px] text-gray-500 uppercase tracking-wider">Opex</p>
                        <p className="text-sm font-extrabold text-red-400">${(totalOperating / 1000).toFixed(0)}k</p>
                    </div>
                    <div className="text-center">
                        <p className="text-[10px] text-gray-500 uppercase tracking-wider">Net ROI</p>
                        <p className={`text-sm font-extrabold ${netROI >= 0 ? 'text-[#caff42]' : 'text-red-500'}`}>
                            ${(netROI / 1000).toFixed(0)}k
                        </p>
                    </div>
                </div>
            </div>

            <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={roi}>
                    <defs>
                        <linearGradient id="gradCostAv" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#22c55e" stopOpacity={0.25} />
                            <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="gradOpex" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.2} />
                            <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                    <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => formatINRCompact(v)} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => formatINR(v)} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Area type="monotone" dataKey="cost_avoidance" name="Cost Avoided" stroke="#22c55e" strokeWidth={2.5} fill="url(#gradCostAv)" dot={{ r: 3, fill: '#22c55e' }} />
                    <Area type="monotone" dataKey="operating_cost" name="Operating Cost" stroke="#ef4444" strokeWidth={2} fill="url(#gradOpex)" dot={{ r: 3, fill: '#ef4444' }} />
                </AreaChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
