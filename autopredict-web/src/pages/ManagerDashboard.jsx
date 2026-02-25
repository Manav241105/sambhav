import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import {
  AlertTriangle,
  ShieldCheck,
  BarChart3,
  Users,
  Clock,
  MessageSquare,
  ChevronRight,
  X,
  Wrench,
  AlertOctagon,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  RadialBarChart,
  RadialBar,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

import DashboardLayout from '../components/DashboardLayout';
import LiveToast from '../components/LiveToast';

const API = 'http://localhost:8000';
const spring = { type: 'spring', stiffness: 100, damping: 10 };

/* ── Chart tooltip style ─────────────────────────── */
const tooltipStyle = {
  backgroundColor: '#1f2937',
  border: '1px solid #374151',
  borderRadius: '12px',
  fontSize: 12,
  color: '#fff',
};

/* ════════════════════════════════════════════════════
   MANAGER DASHBOARD
   ════════════════════════════════════════════════════ */
export default function ManagerDashboard() {
  /* ── State ─────────────────────────────────────── */
  const [summary, setSummary] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [allBookings, setAllBookings] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [mfgSummary, setMfgSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedConvo, setSelectedConvo] = useState(null);

  /* ── Fetch ─────────────────────────────────────── */
  const fetchAll = useCallback(async () => {
    try {
      const [sRes, bTodayRes, bAllRes, cRes, mRes] = await Promise.all([
        axios.get(`${API}/api/dashboard/summary`),
        axios.get(`${API}/api/bookings/today`),
        axios.get(`${API}/api/bookings`),
        axios.get(`${API}/api/conversations`),
        axios.get(`${API}/api/manufacturing/summary`),
      ]);
      setSummary(sRes.data);
      setBookings(Array.isArray(bTodayRes.data) ? bTodayRes.data : []);
      setAllBookings(Array.isArray(bAllRes.data) ? bAllRes.data : []);
      setConversations(Array.isArray(cRes.data) ? cRes.data : []);
      setMfgSummary(mRes.data);
    } catch (err) {
      console.error('Manager fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30_000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  /* ── Derived data ──────────────────────────────── */

  // SLA violations: active alerts that represent unresolved P0
  const slaViolations = summary?.active_alerts ?? 0;

  // Escalation candidates: conversations with OPEN status grouped by vehicle
  const escalationQueue = React.useMemo(() => {
    const grouped = {};
    conversations.forEach((t) => {
      if (t.status === 'OPEN') {
        if (!grouped[t.vehicle_id]) {
          grouped[t.vehicle_id] = {
            vehicle_id: t.vehicle_id,
            customer_name: t.customer_name || 'Unknown',
            channel: t.channel,
            turns: [],
          };
        }
        grouped[t.vehicle_id].turns.push(t);
      }
    });
    return Object.values(grouped);
  }, [conversations]);

  // Technician workload from today's bookings
  const techWorkload = React.useMemo(() => {
    const map = {};
    bookings.forEach((b) => {
      const name = b.technician_name || 'Unassigned';
      if (!map[name]) map[name] = { name, jobs: 0, hours: 0 };
      map[name].jobs += 1;
      map[name].hours += b.service_duration_hours || 1.5;
    });
    return Object.values(map).map((t) => ({ ...t, hours: +t.hours.toFixed(1) }));
  }, [bookings]);

  // Revenue pipeline: stable seed-based data
  const revenuePipeline = React.useMemo(() => {
    const STABLE = [
      { month: 'Oct', confirmed: 38, pending: 12 },
      { month: 'Nov', confirmed: 52, pending: 18 },
      { month: 'Dec', confirmed: 61, pending: 15 },
      { month: 'Jan', confirmed: 57, pending: 21 },
      { month: 'Feb', confirmed: 74, pending: 14 },
      { month: 'Mar', confirmed: 68, pending: 19 },
    ];
    const months = {};
    allBookings.forEach((b) => {
      const iso = b.slot_time_iso || b.created_at || '';
      const monthKey = iso.slice(0, 7);
      if (!months[monthKey]) months[monthKey] = { month: monthKey, confirmed: 0, pending: 0 };
      if (b.status === 'CONFIRMED') months[monthKey].confirmed += 1;
      else months[monthKey].pending += 1;
    });
    const live = Object.values(months);
    return live.length > 1 ? live : STABLE;
  }, [allBookings]);

  // Sentiment breakdown per week (stable mock)
  const sentimentData = React.useMemo(() => [
    { week: 'W1', positive: 68, neutral: 22, negative: 10 },
    { week: 'W2', positive: 72, neutral: 18, negative: 10 },
    { week: 'W3', positive: 65, neutral: 24, negative: 11 },
    { week: 'W4', positive: 79, neutral: 15, negative: 6 },
    { week: 'W5', positive: 74, neutral: 19, negative: 7 },
    { week: 'W6', positive: 81, neutral: 13, negative: 6 },
  ], []);

  // SLA compliance (% of P0 resolved within 48h)
  const slaCompliance = React.useMemo(() => {
    const total = (summary?.total_vehicles || 10);
    const critical = summary?.critical_vehicles || 0;
    const pct = Math.round(Math.max(0, ((total - critical) / total) * 100));
    return [{ name: 'SLA', value: pct, fill: pct >= 80 ? '#22c55e' : pct >= 60 ? '#fbbf24' : '#ef4444' }];
  }, [summary]);

  // Appointments timeline
  const timeline = React.useMemo(() => {
    return [...bookings]
      .sort((a, b) => (a.slot_time_iso || '').localeCompare(b.slot_time_iso || ''))
      .map((b) => {
        const time = b.slot_time_iso ? new Date(b.slot_time_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—';
        return { ...b, displayTime: time };
      });
  }, [bookings]);

  /* ── Stat cards ────────────────────────────────── */
  const statCards = [
    {
      label: 'SLA Violations',
      value: loading ? '—' : slaViolations,
      icon: AlertTriangle,
      color: 'text-red-400',
      sub: 'P0 alerts active',
    },
    {
      label: 'Active Escalations',
      value: loading ? '—' : escalationQueue.length,
      icon: ShieldCheck,
      color: 'text-orange-400',
      sub: 'open conversations',
    },
    {
      label: 'Manufacturing Defects',
      value: loading ? '—' : (mfgSummary?.total_dtc_codes ?? 0),
      icon: Wrench,
      color: 'text-amber-400',
      sub: `${mfgSummary?.total_open_recalls ?? 0} recalls open`,
    },
    {
      label: 'Technicians Active',
      value: loading ? '—' : techWorkload.length,
      icon: Users,
      color: 'text-blue-400',
      sub: `${bookings.length} jobs today`,
    },
  ];

  /* ════════════════════════════════════════════════
     RENDER
     ════════════════════════════════════════════════ */
  return (
    <DashboardLayout title="Manager Dashboard">
      {/* ── Live WebSocket Toast ─────────────────── */}
      <LiveToast onEvent={() => fetchAll()} />

      {/* ── Stat Cards ──────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
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
              {/* Glow */}
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

      {/* ── Charts Row ──────────────────────────── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
        {/* Technician Workload */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.35 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Technician Workload
          </h2>
          {techWorkload.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={techWorkload} barCategoryGap="25%">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(202,255,66,0.06)' }} />
                <Bar dataKey="jobs" name="Jobs" fill="#6366f1" radius={[8, 8, 0, 0]} />
                <Bar dataKey="hours" name="Hours" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[260px] flex items-center justify-center">
              <p className="text-xs text-gray-400 dark:text-gray-500">No bookings today</p>
            </div>
          )}
        </motion.div>

        {/* Revenue Pipeline */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.45 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Revenue Pipeline
          </h2>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={revenuePipeline}>
              <defs>
                <linearGradient id="gradConfirmed" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.35} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradPending" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
              <XAxis
                dataKey="month"
                tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area
                type="monotone"
                dataKey="confirmed"
                name="Confirmed"
                stroke="#6366f1"
                strokeWidth={2}
                fill="url(#gradConfirmed)"
              />
              <Area
                type="monotone"
                dataKey="pending"
                name="Pending"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#gradPending)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* ── SLA + Sentiment Row ─────────────────── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
        {/* SLA Compliance Radial Gauge */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.50 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl flex flex-col"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            SLA Compliance — P0 Resolution
          </h2>
          <div className="flex items-center gap-8 flex-1">
            <ResponsiveContainer width={180} height={180}>
              <RadialBarChart cx="50%" cy="50%" innerRadius={50} outerRadius={80} startAngle={90} endAngle={-270} data={slaCompliance}>
                <RadialBar dataKey="value" cornerRadius={8} background={{ fill: 'rgba(156,163,175,0.1)' }} />
                <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="fill-gray-900 dark:fill-white" style={{ fontSize: 28, fontWeight: 900 }}>
                  {slaCompliance[0]?.value}%
                </text>
                <text x="50%" y="62%" textAnchor="middle" dominantBaseline="middle" className="fill-gray-400" style={{ fontSize: 10 }}>
                  compliance
                </text>
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="space-y-3">
              {[['Target', '≥ 80%', 'text-emerald-500'], ['Current', `${slaCompliance[0]?.value}%`, slaCompliance[0]?.value >= 80 ? 'text-emerald-500' : 'text-red-500'], ['Critical Open', `${summary?.critical_vehicles ?? 0}`, 'text-red-400'], ['Total Fleet', `${summary?.total_vehicles ?? 0}`, 'text-gray-400']].map(([label, val, color]) => (
                <div key={label}>
                  <p className="text-[10px] text-gray-400 uppercase tracking-wider">{label}</p>
                  <p className={`text-xl font-extrabold ${color}`}>{val}</p>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Conversation Sentiment Stacked Bar */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.58 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Conversation Sentiment (Weekly)
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={sentimentData} barSize={22}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.12)" vertical={false} />
              <XAxis dataKey="week" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v, n) => [`${v}%`, n]} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="positive" name="Positive" fill="#22c55e" radius={[4, 4, 0, 0]} stackId="sent" />
              <Bar dataKey="neutral" name="Neutral" fill="#9ca3af" stackId="sent" />
              <Bar dataKey="negative" name="Negative" fill="#f87171" radius={[0, 0, 4, 4]} stackId="sent" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* ── Bottom Row: Escalation + Timeline ──── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Escalation Queue */}
        <motion.div
          id="escalations"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.55 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl flex flex-col max-h-[480px]"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Escalation Queue
          </h2>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {escalationQueue.length === 0 ? (
              <p className="text-xs text-gray-400 dark:text-gray-500 text-center py-12">
                No open escalations
              </p>
            ) : (
              escalationQueue.map((esc, i) => (
                <motion.button
                  key={esc.vehicle_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ ...spring, delay: i * 0.04 }}
                  onClick={() => setSelectedConvo(selectedConvo?.vehicle_id === esc.vehicle_id ? null : esc)}
                  className={`w-full text-left flex items-center gap-3 p-4 rounded-2xl border transition-colors ${selectedConvo?.vehicle_id === esc.vehicle_id
                      ? 'border-[#6366f1] bg-[#6366f1]/5 dark:bg-[#6366f1]/5'
                      : 'border-gray-100 dark:border-white/5 bg-gray-50 dark:bg-white/[0.03] hover:border-gray-200 dark:hover:border-white/10'
                    }`}
                >
                  <div className="p-2 rounded-xl bg-orange-500/15">
                    <AlertOctagon size={14} className="text-orange-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-gray-900 dark:text-white">{esc.vehicle_id}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-orange-500/15 text-orange-500">
                        {esc.turns.length} turns
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate">
                      {esc.customer_name} · {esc.channel}
                    </p>
                  </div>
                  <ChevronRight size={14} className="text-gray-400 shrink-0" />
                </motion.button>
              ))
            )}
          </div>

          {/* Chat history modal */}
          <AnimatePresence>
            {selectedConvo && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.25 }}
                className="mt-4 overflow-hidden"
              >
                <div className="p-4 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-white/[0.02]">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-bold text-gray-900 dark:text-white">
                      Chat History — {selectedConvo.vehicle_id}
                    </h4>
                    <button onClick={() => setSelectedConvo(null)} className="p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/5">
                      <X size={12} className="text-gray-400" />
                    </button>
                  </div>
                  <div className="space-y-2 max-h-[180px] overflow-y-auto">
                    {[...selectedConvo.turns]
                      .sort((a, b) => a.turn_number - b.turn_number)
                      .map((t, j) => (
                        <div
                          key={j}
                          className={`flex gap-2 ${t.direction === 'OUTBOUND' ? '' : 'flex-row-reverse'}`}
                        >
                          <div className={`px-3 py-2 rounded-xl text-[11px] max-w-[85%] ${t.direction === 'OUTBOUND'
                              ? 'bg-white dark:bg-white/5 text-gray-700 dark:text-gray-300'
                              : 'bg-blue-50 dark:bg-blue-500/10 text-gray-700 dark:text-gray-300'
                            }`}>
                            {t.message}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Today's Appointments Timeline */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.65 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl flex flex-col max-h-[480px]"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Today's Appointments
          </h2>

          <div className="flex-1 overflow-y-auto space-y-0 pr-1">
            {timeline.length === 0 ? (
              <p className="text-xs text-gray-400 dark:text-gray-500 text-center py-12">
                No appointments today
              </p>
            ) : (
              timeline.map((appt, i) => {
                const priorityColor =
                  appt.priority === 'P0' ? 'bg-red-500' :
                    appt.priority === 'P1' ? 'bg-orange-500' :
                      appt.priority === 'P2' ? 'bg-amber-400' :
                        'bg-[#6366f1]';

                return (
                  <motion.div
                    key={appt.booking_id}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ ...spring, delay: i * 0.05 }}
                    className="flex gap-4 relative"
                  >
                    {/* Timeline line + dot */}
                    <div className="flex flex-col items-center w-5 shrink-0">
                      <div className={`w-3 h-3 rounded-full ${priorityColor} mt-1.5 shrink-0 z-10`} />
                      {i < timeline.length - 1 && (
                        <div className="w-px flex-1 bg-gray-200 dark:bg-white/10" />
                      )}
                    </div>

                    {/* Content */}
                    <div className="pb-5 flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold text-gray-900 dark:text-white">{appt.displayTime}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300">
                          {appt.bay}
                        </span>
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${appt.priority === 'P0' ? 'bg-red-500/15 text-red-500' :
                            appt.priority === 'P1' ? 'bg-orange-500/15 text-orange-500' :
                              appt.priority === 'P2' ? 'bg-amber-500/15 text-amber-500' :
                                'bg-[#6366f1]/15 text-[#6366f1]'
                          }`}>
                          {appt.priority}
                        </span>
                      </div>
                      <p className="text-[11px] text-gray-700 dark:text-gray-300 font-medium truncate">
                        {appt.vehicle_id} — {(appt.service_component || '').replace(/_/g, ' ')}
                      </p>
                      <p className="text-[10px] text-gray-400 dark:text-gray-500 truncate">
                        {appt.technician_name} · {appt.customer_name} · {appt.service_duration_hours}h
                      </p>
                    </div>
                  </motion.div>
                );
              })
            )}
          </div>
        </motion.div>
      </div>
    </DashboardLayout>
  );
}
