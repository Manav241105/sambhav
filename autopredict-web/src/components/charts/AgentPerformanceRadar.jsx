import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip, Legend } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };
const COLORS = ['#6366f1', '#3b82f6', '#22c55e', '#f59e0b'];

/**
 * Radar chart showing per-agent performance across 5 dimensions:
 * conversion, escalation, booking velocity, sentiment, response time.
 *
 * @param {{ agents: Array<{agent:string, conversion:number, escalation:number, booking_velocity:number, sentiment:number, response_time:number}> }} props
 */
export default function AgentPerformanceRadar({ agents = [] }) {
    if (!agents.length) {
        return (
            <div className="h-[320px] flex items-center justify-center">
                <p className="text-xs text-gray-400">No agent data available</p>
            </div>
        );
    }

    // Reshape data for recharts Radar: one entry per metric, with each agent as a key
    const metrics = ['conversion', 'escalation', 'booking_velocity', 'sentiment', 'response_time'];
    const labels = { conversion: 'Conversion', escalation: 'Low Escalation', booking_velocity: 'Booking Speed', sentiment: 'Sentiment', response_time: 'Response Time' };

    const data = metrics.map((m) => {
        const row = { metric: labels[m] || m };
        agents.forEach((a) => {
            // For escalation, invert so lower is better on the radar
            row[a.agent] = m === 'escalation' ? 100 - (a[m] || 0) : (a[m] || 0);
        });
        return row;
    });

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={spring}
            className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Agent Performance
            </h3>
            <ResponsiveContainer width="100%" height={320}>
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
                    <PolarGrid stroke="rgba(156,163,175,0.2)" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: '#9ca3af', fontSize: 10, fontWeight: 600 }} />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
                    {agents.map((a, i) => (
                        <Radar
                            key={a.agent}
                            name={a.agent}
                            dataKey={a.agent}
                            stroke={COLORS[i % COLORS.length]}
                            fill={COLORS[i % COLORS.length]}
                            fillOpacity={0.12}
                            strokeWidth={2}
                        />
                    ))}
                    <Tooltip contentStyle={tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                </RadarChart>
            </ResponsiveContainer>
        </motion.div>
    );
}
