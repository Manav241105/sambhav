import React from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import { TrendingUp, TrendingDown, Zap } from 'lucide-react';
import AgentPerformanceRadar from '../../components/charts/AgentPerformanceRadar';
import ConversationVolumeArea from '../../components/charts/ConversationVolumeArea';
import BookingFunnelSankey from '../../components/charts/BookingFunnelSankey';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

export default function ManagerOverview() {
    const { statCards, agentPerformance, conversationVolume, bookingFunnel, bookingVelocity, sentimentData } = useOutletContext();

    return (
        <div className="space-y-8">
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-2">
                At-a-glance summary of team performance. Select a tab above to drill into specific metrics.
            </p>

            {/* Stat Cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {statCards.map((card, i) => {
                    const Icon = card.icon;
                    return (
                        <motion.div
                            key={card.label}
                            initial={{ opacity: 0, y: 24 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ ...spring, delay: i * 0.08 }}
                            className="group relative p-5 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl overflow-hidden"
                        >
                            <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-[#6366f1] to-transparent opacity-0 group-hover:opacity-[0.06] blur-xl transition-opacity pointer-events-none" />
                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-2xl bg-gray-100 dark:bg-white/5 ${card.color}`}>
                                    <Icon size={22} />
                                </div>
                                <div>
                                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400">{card.label}</p>
                                    <p className="text-xl font-extrabold text-gray-900 dark:text-white">{card.value}</p>
                                    <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{card.sub}</p>
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {/* Booking Velocity Widget */}
            {bookingVelocity && (
                <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={spring}
                    className="p-5 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl flex items-center gap-6"
                >
                    <div className="p-3 rounded-2xl bg-[#caff42]/15">
                        <Zap size={22} className="text-[#caff42]" />
                    </div>
                    <div className="flex-1">
                        <p className="text-xs font-extrabold text-gray-900 dark:text-white uppercase tracking-wider">Booking Velocity</p>
                        <div className="flex items-baseline gap-3 mt-1">
                            <span className="text-2xl font-extrabold text-gray-900 dark:text-white">
                                {bookingVelocity.velocity_per_hour_today}/hr
                            </span>
                            <span className="text-xs text-gray-400">today ({bookingVelocity.today_total} total)</span>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className={`flex items-center gap-1 ${bookingVelocity.delta_pct >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                            {bookingVelocity.delta_pct >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                            <span className="text-sm font-bold">{bookingVelocity.delta_pct > 0 ? '+' : ''}{bookingVelocity.delta_pct}%</span>
                        </div>
                        <p className="text-[10px] text-gray-400">vs last week ({bookingVelocity.velocity_per_hour_last_week}/hr)</p>
                    </div>
                </motion.div>
            )}

            {/* Charts Grid: Agent Radar + Booking Funnel */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <AgentPerformanceRadar agents={agentPerformance} />
                <BookingFunnelSankey funnel={bookingFunnel} />
            </div>

            {/* Conversation Volume Area Chart */}
            <ConversationVolumeArea days={conversationVolume} />

            {/* Sentiment Stacked Bar — uses existing sentimentData from Layout */}
            {sentimentData && sentimentData.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={spring}
                    className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
                >
                    <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                        Conversation Sentiment — Weekly
                    </h3>
                    <ResponsiveContainer width="100%" height={240}>
                        <BarChart data={sentimentData} barCategoryGap="20%">
                            <XAxis dataKey="week" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={tooltipStyle} />
                            <Legend wrapperStyle={{ fontSize: 11 }} />
                            <Bar dataKey="positive" name="Positive" stackId="s" fill="#22c55e" radius={[0, 0, 0, 0]} />
                            <Bar dataKey="neutral" name="Neutral" stackId="s" fill="#6366f1" radius={[0, 0, 0, 0]} />
                            <Bar dataKey="negative" name="Negative" stackId="s" fill="#ef4444" radius={[8, 8, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </motion.div>
            )}
        </div>
    );
}
