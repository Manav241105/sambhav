import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import { AlertOctagon, ChevronRight, X } from 'lucide-react';
import { ResponsiveContainer, RadialBarChart, RadialBar } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

export default function ManagerEscalations() {
    const { escalationQueue, slaCompliance, summary } = useOutletContext();
    const [selectedConvo, setSelectedConvo] = useState(null);

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={spring}>
            <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-2">
                Escalation Queue &amp; SLA Compliance
            </h2>
            <p className="text-sm text-gray-400 dark:text-gray-500 mb-6 max-w-2xl leading-relaxed">
                Monitors active conversations where the AI has handed off to a human advisor.
                Unresolved escalations older than 2 hours risk SLA violations.
                The compliance gauge measures the % of P0 critical vehicles resolved within the 48-hour window.
            </p>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                {/* Escalation Queue */}
                <div className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl flex flex-col max-h-[480px]">
                    <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                        Open Escalations
                    </h3>
                    <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                        {escalationQueue.length === 0 ? (
                            <p className="text-xs text-gray-400 dark:text-gray-500 text-center py-12">No open escalations ✓</p>
                        ) : (
                            escalationQueue.map((esc, i) => (
                                <motion.button
                                    key={esc.vehicle_id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ ...spring, delay: i * 0.05 }}
                                    onClick={() => setSelectedConvo(selectedConvo?.vehicle_id === esc.vehicle_id ? null : esc)}
                                    className={`w-full text-left flex items-center gap-3 p-4 rounded-2xl border transition-colors ${selectedConvo?.vehicle_id === esc.vehicle_id
                                            ? 'border-[#6366f1] bg-[#6366f1]/5'
                                            : 'border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/[0.03] hover:border-gray-200 dark:hover:border-white/10'
                                        }`}
                                >
                                    <div className="p-2 rounded-xl bg-orange-500/15">
                                        <AlertOctagon size={14} className="text-orange-500" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs font-bold text-gray-900 dark:text-white">{esc.vehicle_id}</span>
                                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-orange-500/15 text-orange-500">{esc.turns.length} turns</span>
                                        </div>
                                        <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate">{esc.customer_name} · {esc.channel}</p>
                                    </div>
                                    <ChevronRight size={14} className="text-gray-400 shrink-0" />
                                </motion.button>
                            ))
                        )}
                    </div>

                    <AnimatePresence>
                        {selectedConvo && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className="mt-4 overflow-hidden"
                            >
                                <div className="p-4 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-white/[0.02]">
                                    <div className="flex items-center justify-between mb-3">
                                        <h4 className="text-xs font-bold text-gray-900 dark:text-white">Chat — {selectedConvo.vehicle_id}</h4>
                                        <button onClick={() => setSelectedConvo(null)} className="p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/5">
                                            <X size={12} className="text-gray-400" />
                                        </button>
                                    </div>
                                    <div className="space-y-2 max-h-[180px] overflow-y-auto">
                                        {[...selectedConvo.turns]
                                            .sort((a, b) => a.turn_number - b.turn_number)
                                            .map((t, j) => (
                                                <div key={j} className={`flex gap-2 ${t.direction === 'OUTBOUND' ? '' : 'flex-row-reverse'}`}>
                                                    <div className={`px-3 py-2 rounded-xl text-[11px] max-w-[85%] ${t.direction === 'OUTBOUND'
                                                            ? 'bg-white dark:bg-white/5 text-gray-700 dark:text-gray-300'
                                                            : 'bg-blue-50 dark:bg-blue-500/10 text-gray-700 dark:text-gray-300'
                                                        }`}>{t.message}</div>
                                                </div>
                                            ))}
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* SLA Compliance Gauge */}
                <div className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl flex flex-col">
                    <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                        SLA Compliance — P0 Resolution
                    </h3>
                    <div className="flex items-center gap-8 flex-1">
                        <ResponsiveContainer width={180} height={180}>
                            <RadialBarChart cx="50%" cy="50%" innerRadius={50} outerRadius={80} startAngle={90} endAngle={-270} data={slaCompliance}>
                                <RadialBar dataKey="value" cornerRadius={8} background={{ fill: 'rgba(156,163,175,0.1)' }} />
                                <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 28, fontWeight: 900, fill: 'currentColor' }}>
                                    {slaCompliance[0]?.value}%
                                </text>
                                <text x="50%" y="62%" textAnchor="middle" dominantBaseline="middle" style={{ fontSize: 10, fill: '#9ca3af' }}>
                                    compliance
                                </text>
                            </RadialBarChart>
                        </ResponsiveContainer>

                        <div className="space-y-3">
                            {[
                                ['Target', '≥ 80%', 'text-emerald-500'],
                                ['Current', `${slaCompliance[0]?.value}%`, slaCompliance[0]?.value >= 80 ? 'text-emerald-500' : 'text-red-500'],
                                ['Critical Open', `${summary?.critical_vehicles ?? 0}`, 'text-red-400'],
                                ['Total Fleet', `${summary?.total_vehicles ?? 0}`, 'text-gray-400'],
                            ].map(([label, val, color]) => (
                                <div key={label}>
                                    <p className="text-[10px] text-gray-400 uppercase tracking-wider">{label}</p>
                                    <p className={`text-xl font-extrabold ${color}`}>{val}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
