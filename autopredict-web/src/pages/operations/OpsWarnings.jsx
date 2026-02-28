import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import {
    AlertTriangle, ShieldAlert, Info, CheckCircle2,
    ChevronRight, X, Clock, Truck, Wrench, ArrowRight
} from 'lucide-react';

const spring = { type: 'spring', stiffness: 120, damping: 14 };

/* ── Priority config ─────────────────────────────────── */
const PRI = {
    P0: { bg: 'bg-red-500/10', border: 'border-red-400/40', text: 'text-red-500', dot: 'bg-red-500', icon: ShieldAlert, label: 'Critical' },
    P1: { bg: 'bg-orange-500/10', border: 'border-orange-400/40', text: 'text-orange-500', dot: 'bg-orange-500', icon: AlertTriangle, label: 'High' },
    P2: { bg: 'bg-amber-400/10', border: 'border-amber-400/40', text: 'text-amber-500', dot: 'bg-amber-400', icon: Info, label: 'Warning' },
    P3: { bg: 'bg-sky-500/10', border: 'border-sky-400/40', text: 'text-sky-500', dot: 'bg-sky-400', icon: Info, label: 'Info' },
};

/* ── Filter tabs ─────────────────────────────────────── */
const FILTERS = ['All', 'P0', 'P1', 'P2'];

function AlertRow({ alert, onDismiss, onSelect, index }) {
    const cfg = PRI[alert.priority] || PRI.P2;
    const Icon = cfg.icon;
    const [dismissed, setDismissed] = useState(false);

    if (dismissed) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -20, height: 0, marginBottom: 0 }}
            transition={{ ...spring, delay: index * 0.04 }}
            className={`relative flex items-start gap-4 p-5 rounded-2xl border ${cfg.bg} ${cfg.border} group`}
        >
            {/* Priority dot */}
            <span className={`mt-0.5 w-2 h-2 rounded-full shrink-0 ${cfg.dot} shadow-sm shadow-current`} />

            {/* Icon */}
            <div className={`shrink-0 p-2 rounded-xl bg-white/30 dark:bg-white/5 ${cfg.text}`}>
                <Icon size={16} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/40 dark:bg-white/10 ${cfg.text}`}>
                        {alert.priority} · {cfg.label}
                    </span>
                    <span className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1">
                        <Truck size={11} className="text-gray-400" />
                        {alert.vehicle_id || '—'}
                    </span>
                    {alert.fired_at && (
                        <span className="text-[10px] text-gray-400 flex items-center gap-1 ml-auto">
                            <Clock size={10} />
                            {new Date(alert.fired_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    )}
                </div>
                <p className="text-sm font-medium text-gray-900 dark:text-white leading-snug">{alert.message || '—'}</p>
                {alert.component && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-1">
                        <Wrench size={10} />
                        {alert.component.replace(/_/g, ' ')}
                    </p>
                )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1 shrink-0">
                {onSelect && (
                    <button
                        onClick={() => onSelect(alert)}
                        className="p-1.5 rounded-lg hover:bg-white/40 dark:hover:bg-white/10 transition-colors"
                        title="View vehicle"
                    >
                        <ArrowRight size={14} className={cfg.text} />
                    </button>
                )}
                <button
                    onClick={() => { setDismissed(true); onDismiss?.(alert); }}
                    className="p-1.5 rounded-lg hover:bg-white/40 dark:hover:bg-white/10 transition-colors opacity-0 group-hover:opacity-100"
                    title="Dismiss"
                >
                    <X size={13} className="text-gray-400" />
                </button>
            </div>
        </motion.div>
    );
}

export default function OpsWarnings() {
    const { alerts = [], dismissAlert, selectFromAlert } = useOutletContext();
    const [filter, setFilter] = useState('All');
    const [dismissed, setDismissed] = useState(new Set());

    const visible = alerts.filter(a =>
        !dismissed.has(a.vehicle_id + a.message) &&
        (filter === 'All' || a.priority === filter)
    );

    const counts = FILTERS.reduce((acc, f) => {
        acc[f] = f === 'All'
            ? alerts.filter(a => !dismissed.has(a.vehicle_id + a.message)).length
            : alerts.filter(a => a.priority === f && !dismissed.has(a.vehicle_id + a.message)).length;
        return acc;
    }, {});

    function handleDismiss(alert) {
        setDismissed(prev => new Set([...prev, alert.vehicle_id + alert.message]));
    }

    function dismissAll() {
        const keys = new Set(alerts.map(a => a.vehicle_id + a.message));
        setDismissed(keys);
    }

    return (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={spring}>
            {/* Header */}
            <div className="flex items-start justify-between mb-6">
                <div>
                    <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-1">
                        Warnings & Alerts
                    </h2>
                    <p className="text-sm text-gray-400 dark:text-gray-500 max-w-xl leading-relaxed">
                        All active P0–P2 alerts from the AI diagnosis pipeline. Click the arrow to jump to the vehicle in Fleet view.
                    </p>
                </div>
                {visible.length > 0 && (
                    <button onClick={dismissAll}
                        className="text-xs font-semibold text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 flex items-center gap-1.5 transition-colors mt-1 shrink-0">
                        <CheckCircle2 size={13} />
                        Dismiss all
                    </button>
                )}
            </div>

            {/* Filter chips */}
            <div className="flex gap-2 mb-6 flex-wrap">
                {FILTERS.map(f => {
                    const cfg = f === 'All' ? null : PRI[f];
                    const active = filter === f;
                    return (
                        <button key={f} onClick={() => setFilter(f)}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold border-2 transition-all ${active
                                    ? 'border-[#6366f1] bg-[#6366f1]/10 text-[#6366f1]'
                                    : 'border-gray-200 dark:border-gray-700 text-gray-500 hover:border-gray-300 dark:hover:border-gray-600'
                                }`}
                        >
                            {f}
                            {counts[f] > 0 && (
                                <span className={`ml-1.5 inline-block px-1.5 py-0.5 rounded-full text-[9px] font-black ${active ? 'bg-[#6366f1] text-white' : (cfg ? `${cfg.dot.replace('bg-', 'bg-')} text-white` : 'bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-white')
                                    }`}>
                                    {counts[f]}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Alert list */}
            {visible.length === 0 ? (
                <motion.div
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className="flex flex-col items-center justify-center py-20 text-center"
                >
                    <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center mb-4">
                        <CheckCircle2 size={28} className="text-emerald-500" />
                    </div>
                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">All clear</p>
                    <p className="text-xs text-gray-400 mt-1">No active warnings matching this filter</p>
                </motion.div>
            ) : (
                <div className="space-y-3">
                    <AnimatePresence>
                        {visible.map((alert, i) => (
                            <AlertRow
                                key={`${alert.vehicle_id}-${alert.message}-${i}`}
                                alert={alert}
                                index={i}
                                onDismiss={handleDismiss}
                                onSelect={selectFromAlert}
                            />
                        ))}
                    </AnimatePresence>
                </div>
            )}
        </motion.div>
    );
}
