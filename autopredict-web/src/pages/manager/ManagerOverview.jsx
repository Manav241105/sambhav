import React from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

export default function ManagerOverview() {
    const { statCards, loading } = useOutletContext();

    return (
        <div>
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-6">
                At-a-glance summary of team performance. Select a tab above to drill into specific metrics.
            </p>
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
        </div>
    );
}
