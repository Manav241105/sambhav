import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

/**
 * 30-day daily conversation volume area chart (inbound vs outbound).
 *
 * @param {{ days: Array<{date:string, inbound:number, outbound:number, total:number}> }} props
 */
export default function ConversationVolumeArea({ days = [] }) {
    if (!days.length) {
        return (
            <div className="h-[280px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No conversation data</p>
            </div>
        );
    }

    // Abbreviate dates for x-axis
    const data = days.map((d) => ({
        ...d,
        label: d.date?.slice(5) || d.date,  // MM-DD
    }));

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Conversation Volume — 30 Days
            </h3>
            <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="gradInbound" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#6366f1" stopOpacity={0.35} />
                            <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="gradOutbound" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#caff42" stopOpacity={0.3} />
                            <stop offset="100%" stopColor="#caff42" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                    <XAxis dataKey="label" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} interval={4} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Area type="monotone" dataKey="inbound" name="Inbound" stroke="#6366f1" strokeWidth={2} fill="url(#gradInbound)" />
                    <Area type="monotone" dataKey="outbound" name="Outbound" stroke="#caff42" strokeWidth={2} fill="url(#gradOutbound)" />
                </AreaChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
