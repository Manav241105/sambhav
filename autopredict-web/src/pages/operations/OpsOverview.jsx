import React from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

export default function OpsOverview() {
    const { statCards, loading } = useOutletContext();

    return (
        <div>
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-6">
                Live operations pulse. Use the tabs above to drill into the fleet, bay schedule, or live conversations.
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
                            <div className={`p-3 rounded-2xl bg-gray-100 dark:bg-white/5 ${card.color} w-fit mb-3`}>
                                <Icon size={22} />
                            </div>
                            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{card.label}</p>
                            <p className="text-2xl font-extrabold text-gray-900 dark:text-white tracking-tight">{card.value}</p>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
}
