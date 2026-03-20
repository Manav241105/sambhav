import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import {
    RotateCcw, AlertTriangle, CheckCircle, Clock, ChevronRight,
    Search, Filter, X, Truck, Calendar, AlertOctagon, ShieldCheck,
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import LiveEventBus from '../components/LiveEventBus';

import { API_BASE } from '../config';

const API = API_BASE;
const spring = { type: 'spring', stiffness: 100, damping: 10 };

const STATUS_CONFIG = {
    open: { label: 'Open', color: 'text-red-500', bg: 'bg-red-500/15', dot: 'bg-red-500' },
    notified: { label: 'Notified', color: 'text-orange-500', bg: 'bg-orange-500/15', dot: 'bg-orange-500' },
    scheduled: { label: 'Scheduled', color: 'text-blue-400', bg: 'bg-blue-400/15', dot: 'bg-blue-400' },
    closed: { label: 'Closed', color: 'text-emerald-500', bg: 'bg-emerald-500/15', dot: 'bg-emerald-500' },
};

export default function RecallsPage() {
    const [vehicles, setVehicles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQ, setSearchQ] = useState('');
    const [filterStatus, setFilterStatus] = useState('ALL');
    const [recallStatuses, setRecallStatuses] = useState({});

    /* Build fleet-wide recall list from manufacturing data */
    const fetchAll = useCallback(async () => {
        try {
            const [vRes, mRes] = await Promise.all([
                axios.get(`${API}/api/vehicles`),
                axios.get(`${API}/api/manufacturing/summary`),
            ]);
            const vs = Array.isArray(vRes.data) ? vRes.data : Object.values(vRes.data);
            setVehicles(vs);

            // Seed default statuses
            const defaults = {};
            (mRes.data.vehicles_with_recalls || []).forEach((v) => {
                v.recalls.forEach((_, idx) => {
                    const key = `${v.vehicle_id}-${idx}`;
                    if (!defaults[key]) defaults[key] = 'open';
                });
            });
            setRecallStatuses((prev) => ({ ...defaults, ...prev }));
        } catch (err) {
            console.error('Recalls fetch error:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAll();
    }, [fetchAll]);

    /* Build flat recall list */
    const recallList = useMemo(() => {
        const list = [];
        vehicles.forEach((v) => {
            const recalls = v.diagnosis?.predicted_component ? [{
                title: `${(v.diagnosis.predicted_component || '').replace(/_/g, ' ')} Recall`,
                description: `Potential ${v.diagnosis.severity} ${(v.diagnosis.predicted_component || '').replace(/_/g, ' ')} failure detected. RUL: ${v.diagnosis.rul_days ?? '?'} days.`,
                severity: v.diagnosis.severity,
                campaign: `RC-${v.vehicle_id}-${(v.diagnosis.predicted_component || 'UNK').slice(0, 3).toUpperCase()}`,
                reported_date: '2025-12-01',
            }] : [];

            recalls.forEach((recall, idx) => {
                const key = `${v.vehicle_id}-${idx}`;
                list.push({
                    key,
                    vehicle_id: v.vehicle_id,
                    make: v.make,
                    model: v.model,
                    year: v.year,
                    customer_name: v.customer?.name || 'Unknown',
                    priority: v.priority,
                    recall,
                    status: recallStatuses[key] || 'open',
                });
            });
        });
        return list;
    }, [vehicles, recallStatuses]);

    const filtered = recallList.filter((r) => {
        const matchQ = !searchQ || r.vehicle_id.toLowerCase().includes(searchQ.toLowerCase()) || r.customer_name.toLowerCase().includes(searchQ.toLowerCase()) || r.recall.title.toLowerCase().includes(searchQ.toLowerCase());
        const matchS = filterStatus === 'ALL' || r.status === filterStatus.toLowerCase();
        return matchQ && matchS;
    });

    const stats = {
        total: recallList.length,
        open: recallList.filter((r) => r.status === 'open').length,
        scheduled: recallList.filter((r) => r.status === 'scheduled').length,
        closed: recallList.filter((r) => r.status === 'closed').length,
    };

    const cycleStatus = (key) => {
        const order = ['open', 'notified', 'scheduled', 'closed'];
        setRecallStatuses((prev) => {
            const cur = prev[key] || 'open';
            const next = order[(order.indexOf(cur) + 1) % order.length];
            return { ...prev, [key]: next };
        });
    };

    return (
        <DashboardLayout title="Recall Management">
            <LiveEventBus onAnyEvent={fetchAll} />

            {/* Stat cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
                {[
                    { label: 'Total Recalls', value: stats.total, icon: RotateCcw, color: 'text-gray-400' },
                    { label: 'Open', value: stats.open, icon: AlertTriangle, color: 'text-red-500' },
                    { label: 'Scheduled', value: stats.scheduled, icon: Calendar, color: 'text-blue-400' },
                    { label: 'Resolved', value: stats.closed, icon: CheckCircle, color: 'text-emerald-500' },
                ].map((card, i) => {
                    const Icon = card.icon;
                    return (
                        <motion.div
                            key={card.label}
                            initial={{ opacity: 0, y: 24 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ ...spring, delay: i * 0.08 }}
                            className="p-5 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl flex items-center gap-4"
                        >
                            <div className={`p-3 rounded-2xl bg-gray-100 dark:bg-white/5 ${card.color}`}>
                                <Icon size={22} />
                            </div>
                            <div>
                                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">{card.label}</p>
                                <p className="text-2xl font-extrabold text-gray-900 dark:text-white">{loading ? '—' : card.value}</p>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {/* Search + filter */}
            <div className="flex items-center gap-3 mb-6">
                <div className="flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-white/5 border border-gray-200 dark:border-gray-700 rounded-xl flex-1 max-w-sm">
                    <Search size={14} className="text-gray-400 shrink-0" />
                    <input
                        value={searchQ}
                        onChange={(e) => setSearchQ(e.target.value)}
                        placeholder="Search vehicle, customer, recall..."
                        className="flex-1 bg-transparent text-sm text-gray-900 dark:text-white placeholder-gray-400 outline-none"
                    />
                </div>
                <div className="flex gap-2">
                    {['ALL', 'OPEN', 'NOTIFIED', 'SCHEDULED', 'CLOSED'].map((s) => (
                        <button
                            key={s}
                            onClick={() => setFilterStatus(s)}
                            className={`px-3 py-2 text-[10px] font-bold rounded-xl transition-colors ${filterStatus === s ? 'bg-[#6366f1]/15 text-[#6366f1]' : 'bg-white dark:bg-white/5 border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400'}`}
                        >
                            {s}
                        </button>
                    ))}
                </div>
            </div>

            {/* Recall table */}
            <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...spring, delay: 0.4 }}
                className="border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl overflow-hidden"
            >
                <div className="grid grid-cols-12 gap-3 px-6 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-white/[0.02]">
                    <span className="col-span-2 text-[10px] font-bold text-gray-400 uppercase">Vehicle</span>
                    <span className="col-span-2 text-[10px] font-bold text-gray-400 uppercase">Customer</span>
                    <span className="col-span-3 text-[10px] font-bold text-gray-400 uppercase">Recall Title</span>
                    <span className="col-span-2 text-[10px] font-bold text-gray-400 uppercase">Campaign</span>
                    <span className="col-span-1 text-[10px] font-bold text-gray-400 uppercase">Priority</span>
                    <span className="col-span-2 text-[10px] font-bold text-gray-400 uppercase">Status</span>
                </div>
                <div className="divide-y divide-gray-100 dark:divide-white/5">
                    {loading ? (
                        [...Array(5)].map((_, i) => (
                            <div key={i} className="px-6 py-4 animate-pulse grid grid-cols-12 gap-3">
                                {[2, 2, 3, 2, 1, 2].map((span, j) => (
                                    <div key={j} className={`col-span-${span} h-4 bg-gray-200 dark:bg-white/10 rounded`} />
                                ))}
                            </div>
                        ))
                    ) : filtered.length === 0 ? (
                        <div className="py-16 text-center">
                            <ShieldCheck size={40} className="text-emerald-500 mx-auto mb-3" />
                            <p className="text-sm font-bold text-gray-900 dark:text-white">No recalls found</p>
                            <p className="text-xs text-gray-400 mt-1">All vehicles are clear</p>
                        </div>
                    ) : (
                        filtered.map((row, i) => {
                            const sc = STATUS_CONFIG[row.status];
                            const priColors = { P0: 'text-red-500 bg-red-500/15', P1: 'text-orange-500 bg-orange-500/15', P2: 'text-amber-500 bg-amber-500/15', P3: 'text-emerald-500 bg-emerald-500/15' };
                            return (
                                <motion.div
                                    key={row.key}
                                    initial={{ opacity: 0, x: -8 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ ...spring, delay: i * 0.04 }}
                                    className="grid grid-cols-12 gap-3 px-6 py-4 items-center hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors"
                                >
                                    <div className="col-span-2">
                                        <p className="text-xs font-bold text-gray-900 dark:text-white">{row.vehicle_id}</p>
                                        <p className="text-[10px] text-gray-400">{row.make} {row.model}</p>
                                    </div>
                                    <span className="col-span-2 text-xs text-gray-600 dark:text-gray-300 truncate">{row.customer_name}</span>
                                    <div className="col-span-3">
                                        <p className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">{row.recall.title}</p>
                                        <p className="text-[10px] text-gray-400 truncate">{row.recall.description?.slice(0, 60)}</p>
                                    </div>
                                    <span className="col-span-2 text-[10px] font-mono text-gray-500 dark:text-gray-400">{row.recall.campaign}</span>
                                    <span className="col-span-1">
                                        <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${priColors[row.priority] || priColors.P3}`}>{row.priority}</span>
                                    </span>
                                    <div className="col-span-2">
                                        <button
                                            onClick={() => cycleStatus(row.key)}
                                            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[9px] font-bold transition-all hover:opacity-80 ${sc.bg} ${sc.color}`}
                                        >
                                            <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
                                            {sc.label}
                                            <ChevronRight size={8} />
                                        </button>
                                    </div>
                                </motion.div>
                            );
                        })
                    )}
                </div>
            </motion.div>
        </DashboardLayout>
    );
}
