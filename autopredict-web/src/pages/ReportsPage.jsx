import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import {
    FileText, Download, BarChart3, Truck, MessageSquare,
    Calendar, DollarSign, RefreshCw, CheckCircle, AlertTriangle,
} from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';

const API = 'http://localhost:8000';
const spring = { type: 'spring', stiffness: 100, damping: 10 };

const REPORT_TYPES = [
    {
        id: 'fleet-health',
        title: 'Fleet Health Report',
        description: 'Current health scores, priority levels, and RUL days for all vehicles.',
        icon: Truck,
        color: 'text-[#6366f1]',
        bg: 'bg-[#6366f1]/15',
        format: 'CSV',
        size: '~14 KB',
    },
    {
        id: 'monthly-bookings',
        title: 'Monthly Bookings Summary',
        description: '6-month booking history with acceptance rates and conversion data.',
        icon: Calendar,
        color: 'text-blue-400',
        bg: 'bg-blue-400/15',
        format: 'CSV',
        size: '~8 KB',
    },
    {
        id: 'revenue-pipeline',
        title: 'Revenue Pipeline',
        description: 'Projected revenue, cost avoidance estimates, and service breakdown.',
        icon: DollarSign,
        color: 'text-emerald-500',
        bg: 'bg-emerald-500/15',
        format: 'CSV',
        size: '~6 KB',
    },
    {
        id: 'conversation-transcripts',
        title: 'Conversation Transcripts',
        description: 'Full AI agent conversation logs per vehicle with turn-by-turn detail.',
        icon: MessageSquare,
        color: 'text-purple-400',
        bg: 'bg-purple-400/15',
        format: 'CSV',
        size: '~32 KB',
    },
    {
        id: 'analytics-summary',
        title: 'Analytics Summary',
        description: 'Acceptance rate, escalation rate, and AI performance metrics.',
        icon: BarChart3,
        color: 'text-orange-400',
        bg: 'bg-orange-400/15',
        format: 'CSV',
        size: '~5 KB',
    },
];

function toCsv(rows) {
    if (!rows.length) return '';
    const headers = Object.keys(rows[0]).join(',');
    const lines = rows.map((r) =>
        Object.values(r).map((v) => (typeof v === 'string' && v.includes(',') ? `"${v}"` : v)).join(',')
    );
    return [headers, ...lines].join('\n');
}

function downloadCsv(filename, content) {
    const blob = new Blob([content], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

export default function ReportsPage() {
    const [data, setData] = useState({ vehicles: [], analytics: [], conversations: [] });
    const [loading, setLoading] = useState(true);
    const [downloading, setDownloading] = useState(null);
    const [downloaded, setDownloaded] = useState([]);

    const fetchAll = useCallback(async () => {
        try {
            const [vRes, aRes, cRes] = await Promise.all([
                axios.get(`${API}/api/vehicles`),
                axios.get(`${API}/api/analytics/monthly`),
                axios.get(`${API}/api/conversations`),
            ]);
            setData({
                vehicles: Array.isArray(vRes.data) ? vRes.data : Object.values(vRes.data),
                analytics: aRes.data.months || [],
                conversations: Array.isArray(cRes.data) ? cRes.data : [],
            });
        } catch (err) {
            console.error('Reports fetch error:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchAll(); }, [fetchAll]);

    const handleDownload = async (reportId) => {
        setDownloading(reportId);
        await new Promise((r) => setTimeout(r, 600)); // simulate generation

        let content = '';
        const ts = new Date().toISOString().slice(0, 10);

        if (reportId === 'fleet-health') {
            const rows = data.vehicles.map((v) => ({
                vehicle_id: v.vehicle_id,
                make: v.make,
                model: v.model,
                year: v.year,
                priority: v.priority,
                health_score: v.health_score,
                severity: v.diagnosis?.severity || 'normal',
                predicted_component: v.diagnosis?.predicted_component || '',
                rul_days: v.diagnosis?.rul_days || '',
            }));
            content = toCsv(rows);
            downloadCsv(`fleet-health-${ts}.csv`, content);
        } else if (reportId === 'monthly-bookings') {
            content = toCsv(data.analytics);
            downloadCsv(`bookings-${ts}.csv`, content);
        } else if (reportId === 'revenue-pipeline') {
            const rows = data.analytics.map((m) => ({
                month: m.month,
                bookings: m.bookings,
                cost_avoidance_usd: m.cost_avoidance_usd,
                vehicles_serviced: m.vehicles_serviced,
                acceptance_rate: m.acceptance_rate,
                conversion_rate: m.conversion_rate,
            }));
            content = toCsv(rows);
            downloadCsv(`revenue-pipeline-${ts}.csv`, content);
        } else if (reportId === 'conversation-transcripts') {
            const rows = data.conversations.map((c) => ({
                vehicle_id: c.vehicle_id,
                customer_name: c.customer_name || '',
                direction: c.direction,
                channel: c.channel,
                turn_number: c.turn_number,
                status: c.status,
                message: c.message?.replace(/,/g, ';') || '',
            }));
            content = toCsv(rows);
            downloadCsv(`conversations-${ts}.csv`, content);
        } else if (reportId === 'analytics-summary') {
            content = toCsv(data.analytics);
            downloadCsv(`analytics-${ts}.csv`, content);
        }

        setDownloading(null);
        setDownloaded((prev) => [...new Set([...prev, reportId])]);
    };

    return (
        <DashboardLayout title="Reports & Export">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={spring}
                className="mb-8 flex items-start justify-between"
            >
                <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Download fleet data, analytics, and conversation logs as CSV files.
                    </p>
                </div>
                <button
                    onClick={fetchAll}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white bg-white dark:bg-white/5 border border-gray-200 dark:border-gray-700 rounded-xl transition-colors"
                >
                    <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                    Refresh data
                </button>
            </motion.div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-8">
                {[
                    { label: 'Vehicles tracked', value: data.vehicles.length, icon: Truck },
                    { label: 'Analytics months', value: data.analytics.length, icon: BarChart3 },
                    { label: 'Conversations logged', value: data.conversations.length, icon: MessageSquare },
                ].map((s, i) => {
                    const Icon = s.icon;
                    return (
                        <motion.div
                            key={s.label}
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ ...spring, delay: i * 0.06 }}
                            className="flex items-center gap-4 p-5 bg-white dark:bg-white/5 border border-gray-200 dark:border-gray-700 rounded-3xl"
                        >
                            <div className="p-3 rounded-2xl bg-gray-100 dark:bg-white/5 text-[#6366f1]">
                                <Icon size={20} />
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 dark:text-gray-400">{s.label}</p>
                                <p className="text-2xl font-extrabold text-gray-900 dark:text-white">{loading ? '—' : s.value}</p>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {/* Report cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {REPORT_TYPES.map((report, i) => {
                    const Icon = report.icon;
                    const isDl = downloading === report.id;
                    const wasDownloaded = downloaded.includes(report.id);
                    return (
                        <motion.div
                            key={report.id}
                            initial={{ opacity: 0, y: 24 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ ...spring, delay: i * 0.1 }}
                            className="relative group p-6 bg-white dark:bg-white/5 border border-gray-200 dark:border-gray-700 rounded-3xl hover:border-[#6366f1]/30 dark:hover:border-[#6366f1]/30 transition-all"
                        >
                            {wasDownloaded && (
                                <div className="absolute top-4 right-4">
                                    <CheckCircle size={14} className="text-emerald-500" />
                                </div>
                            )}
                            <div className={`w-12 h-12 rounded-2xl ${report.bg} ${report.color} flex items-center justify-center mb-5`}>
                                <Icon size={24} />
                            </div>
                            <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-1">{report.title}</h3>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 leading-relaxed">{report.description}</p>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="text-[10px] bg-gray-100 dark:bg-white/10 text-gray-400 px-2 py-0.5 rounded-md font-mono font-bold">{report.format}</span>
                                    <span className="text-[10px] text-gray-400">{report.size}</span>
                                </div>
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={() => handleDownload(report.id)}
                                    disabled={loading || isDl}
                                    className="flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-xl bg-[#6366f1] text-gray-900 hover:bg-[#d4ff5c] transition-colors disabled:opacity-50 disabled:cursor-wait"
                                >
                                    {isDl ? (
                                        <RefreshCw size={12} className="animate-spin" />
                                    ) : (
                                        <Download size={12} />
                                    )}
                                    {isDl ? 'Generating…' : 'Download'}
                                </motion.button>
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </DashboardLayout>
    );
}
