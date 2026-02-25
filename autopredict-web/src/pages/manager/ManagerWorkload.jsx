import React from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

export default function ManagerWorkload() {
    const { techWorkload, timeline } = useOutletContext();

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={spring} className="space-y-8">
            <div>
                <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-2">
                    Technician Workload &amp; Today's Schedule
                </h2>
                <p className="text-sm text-gray-400 dark:text-gray-500 mb-6 max-w-2xl leading-relaxed">
                    Measures bay utilisation and individual technician load for the current day.
                    Use this view to balance assignments if specific bays or staff are over-indexed while others remain idle.
                    Technicians with &gt;8 hours are approaching capacity.
                </p>
            </div>

            {/* Technician Workload Chart */}
            <div className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Technician Workload</h3>
                {techWorkload.length > 0 ? (
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={techWorkload} barCategoryGap="25%">
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                            <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(202,255,66,0.06)' }} />
                            <Bar dataKey="jobs" name="Jobs" fill="#6366f1" radius={[8, 8, 0, 0]} />
                            <Bar dataKey="hours" name="Hours" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="h-[280px] flex items-center justify-center">
                        <p className="text-xs text-gray-400">No bookings today</p>
                    </div>
                )}
            </div>

            {/* Today's Appointments Timeline */}
            <div className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl max-h-[480px] flex flex-col">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Today's Appointments</h3>
                <div className="flex-1 overflow-y-auto space-y-0 pr-1">
                    {timeline.length === 0 ? (
                        <p className="text-xs text-gray-400 text-center py-12">No appointments today</p>
                    ) : (
                        timeline.map((appt, i) => {
                            const priorityColor = appt.priority === 'P0' ? 'bg-red-500' : appt.priority === 'P1' ? 'bg-orange-500' : appt.priority === 'P2' ? 'bg-amber-400' : 'bg-[#6366f1]';
                            return (
                                <motion.div
                                    key={appt.booking_id}
                                    initial={{ opacity: 0, x: -12 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ ...spring, delay: i * 0.04 }}
                                    className="flex gap-4 relative"
                                >
                                    <div className="flex flex-col items-center w-5 shrink-0">
                                        <div className={`w-3 h-3 rounded-full ${priorityColor} mt-1.5 shrink-0 z-10`} />
                                        {i < timeline.length - 1 && <div className="w-px flex-1 bg-gray-200 dark:bg-white/10" />}
                                    </div>
                                    <div className="pb-5 flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-xs font-bold text-gray-900 dark:text-white">{appt.displayTime}</span>
                                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300">{appt.bay}</span>
                                            <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${appt.priority === 'P0' ? 'bg-red-500/15 text-red-500' : appt.priority === 'P1' ? 'bg-orange-500/15 text-orange-500' : appt.priority === 'P2' ? 'bg-amber-500/15 text-amber-500' : 'bg-[#6366f1]/15 text-[#6366f1]'}`}>
                                                {appt.priority}
                                            </span>
                                        </div>
                                        <p className="text-[11px] text-gray-700 dark:text-gray-300 font-medium truncate">{appt.vehicle_id} — {(appt.service_component || '').replace(/_/g, ' ')}</p>
                                        <p className="text-[10px] text-gray-400 truncate">{appt.technician_name} · {appt.customer_name} · {appt.service_duration_hours}h</p>
                                    </div>
                                </motion.div>
                            );
                        })
                    )}
                </div>
            </div>
        </motion.div>
    );
}
