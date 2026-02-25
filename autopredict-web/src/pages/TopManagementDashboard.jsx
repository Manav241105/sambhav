import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import {
  DollarSign,
  Activity,
  ShieldAlert,
  Brain,
  TrendingUp,
  AlertTriangle,
  ChevronDown,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  BarChart,
  Bar,
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

/* ── Pie colours ─────────────────────────────────── */
const HEALTH_COLORS = ['#22c55e', '#fbbf24', '#ef4444']; // Normal, Warning, Critical
const REVENUE_COLORS = ['#6366f1', '#38bdf8', '#a78bfa', '#fb923c', '#34d399', '#f472b6'];
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
const HOURS = ['8am', '9am', '10am', '11am', '12pm', '1pm', '2pm', '3pm', '4pm', '5pm'];

/* Seed heatmap data deterministically */
const HEATMAP_DATA = DAYS.flatMap((day) =>
  HOURS.map((hour, hi) => {
    const rng = new Intl.Collator().compare(day + hour, 'z');
    const base = [3, 8, 10, 9, 11, 12, 9, 8, 6, 4][hi];
    const val = Math.max(0, base + (day === 'Mon' || day === 'Fri' ? -2 : 1) + (hi < 2 || hi > 7 ? -2 : 0));
    return { day, hour, value: val };
  })
);

/* ── Avg repair cost (used for cost avoidance calc) ─ */
const AVG_REPAIR_COST = 2800;

/* ════════════════════════════════════════════════════
   EXECUTIVE DASHBOARD
   ════════════════════════════════════════════════════ */
export default function TopManagementDashboard() {
  /* ── State ─────────────────────────────────────── */
  const [summary, setSummary] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [mfgSummary, setMfgSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  /* ── Fetch ─────────────────────────────────────── */
  const fetchAll = useCallback(async () => {
    try {
      const [sRes, vRes, mRes, mfgRes] = await Promise.all([
        axios.get(`${API}/api/dashboard/summary`),
        axios.get(`${API}/api/vehicles`),
        axios.get(`${API}/api/analytics/monthly`),
        axios.get(`${API}/api/manufacturing/summary`),
      ]);
      setSummary(sRes.data);
      setVehicles(Array.isArray(vRes.data) ? vRes.data : Object.values(vRes.data));
      setMonthly(mRes.data?.months || []);
      setMfgSummary(mfgRes.data);
    } catch (err) {
      console.error('Executive fetch error:', err);
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

  // Cost avoidance
  const costAvoidance = useMemo(() => {
    if (!vehicles.length) return 0;
    return vehicles.reduce((sum, v) => sum + (v.failure_probability || 0) * AVG_REPAIR_COST, 0);
  }, [vehicles]);

  // Fleet health pie
  const healthPie = useMemo(() => {
    if (!summary) return [];
    const critical = summary.critical_vehicles || 0;
    const total = summary.total_vehicles || 10;
    // We don't get a "warning" count directly from summary, derive from vehicles
    const warningCount = vehicles.filter((v) => v.scenario === 'warning' || v.priority === 'P2').length;
    const normalCount = Math.max(0, total - critical - warningCount);
    return [
      { name: 'Normal', value: normalCount },
      { name: 'Warning', value: warningCount },
      { name: 'Critical', value: critical },
    ];
  }, [summary, vehicles]);

  // Top 5 at-risk vehicles
  const topAtRisk = useMemo(() => {
    return [...vehicles]
      .sort((a, b) => (b.failure_probability || 0) - (a.failure_probability || 0))
      .slice(0, 5);
  }, [vehicles]);

  // Monthly trend for line + bar charts
  const monthlyTrend = useMemo(() => {
    return monthly.map((m) => ({
      ...m,
      acceptance_pct: Math.round((m.acceptance_rate || 0) * 100),
      conversion_pct: Math.round((m.conversion_rate || 0) * 100),
      escalation_pct: Math.round((m.escalation_rate || 0) * 100),
    }));
  }, [monthly]);

  // Revenue by component (derived from vehicles)
  const revenuePie = useMemo(() => {
    const components = {};
    vehicles.forEach((v) => {
      const comp = v.diagnosis?.predicted_component?.replace(/_/g, ' ') || 'General';
      components[comp] = (components[comp] || 0) + Math.round((v.failure_probability || 0.1) * 3200);
    });
    return Object.entries(components).map(([name, value]) => ({ name, value })).slice(0, 6);
  }, [vehicles]);

  /* ── Big metric cards ──────────────────────────── */
  const bigMetrics = [
    {
      label: 'Cost Avoidance',
      value: loading ? '—' : `$${Math.round(costAvoidance).toLocaleString()}`,
      sub: 'estimated savings this cycle',
      icon: DollarSign,
      color: 'text-emerald-400',
    },
    {
      label: 'AI Accuracy',
      value: loading ? '—' : `${Math.round((summary?.ai_accuracy || 0) * 100)}%`,
      sub: `${Math.round((summary?.fallback_rate || 0) * 100)}% fallback rate`,
      icon: Brain,
      color: 'text-[#6366f1]',
    },
    {
      label: 'Open Recalls',
      value: loading ? '—' : (mfgSummary?.total_open_recalls ?? 0),
      sub: `across ${mfgSummary?.vehicles_with_recalls?.length ?? 0} vehicles`,
      icon: ShieldAlert,
      color: 'text-orange-400',
    },
    {
      label: 'Fleet Health',
      value: loading ? '—' : `${summary?.total_vehicles ?? 0} vehicles`,
      sub: `${summary?.critical_vehicles ?? 0} critical`,
      icon: Activity,
      color: 'text-blue-400',
    },
  ];

  /* ════════════════════════════════════════════════
     RENDER
     ════════════════════════════════════════════════ */
  return (
    <DashboardLayout title="Executive Dashboard">
      {/* ── Live WebSocket Toast ─────────────────── */}
      <LiveToast onEvent={() => fetchAll()} />

      {/* ── Big Metric Cards ────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {bigMetrics.map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.label}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ ...spring, delay: i * 0.08 }}
              className="group relative p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl overflow-hidden"
            >
              {/* Glow */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-[#6366f1] to-transparent opacity-0 group-hover:opacity-[0.06] blur-xl transition-opacity pointer-events-none" />
              <div className={`p-3 rounded-2xl bg-gray-100 dark:bg-white/5 ${card.color} w-fit mb-3`}>
                <Icon size={22} />
              </div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{card.label}</p>
              <p className="text-2xl font-extrabold text-gray-900 dark:text-white tracking-tight">{card.value}</p>
              <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">{card.sub}</p>
            </motion.div>
          );
        })}
      </div>

      {/* ── Charts Row ──────────────────────────── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
        {/* Fleet Health Ring */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.35 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Fleet Health Distribution
          </h2>

          {healthPie.length > 0 && healthPie.some((d) => d.value > 0) ? (
            <div className="flex items-center gap-8">
              <ResponsiveContainer width="55%" height={240}>
                <PieChart>
                  <Pie
                    data={healthPie}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                    animationDuration={1200}
                    animationEasing="ease-out"
                    stroke="none"
                  >
                    {healthPie.map((_, idx) => (
                      <Cell key={idx} fill={HEALTH_COLORS[idx]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>

              {/* Legend */}
              <div className="space-y-3">
                {healthPie.map((entry, idx) => (
                  <div key={entry.name} className="flex items-center gap-3">
                    <span
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{ backgroundColor: HEALTH_COLORS[idx] }}
                    />
                    <div>
                      <p className="text-xs font-bold text-gray-900 dark:text-white">{entry.value}</p>
                      <p className="text-[10px] text-gray-400 dark:text-gray-500">{entry.name}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-[240px] flex items-center justify-center">
              <p className="text-xs text-gray-400 dark:text-gray-500">Loading fleet data…</p>
            </div>
          )}
        </motion.div>

        {/* Month-over-Month Acceptance Rate */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.45 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Booking Acceptance Rate
          </h2>

          {monthlyTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={monthlyTrend}>
                <defs>
                  <linearGradient id="gradLine" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.15)" />
                <XAxis
                  dataKey="month"
                  tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={[50, 100]}
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(val) => [`${val}%`, 'Acceptance']}
                />
                <Line
                  type="monotone"
                  dataKey="acceptance_pct"
                  name="Acceptance %"
                  stroke="#6366f1"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#6366f1', stroke: '#0b0f19', strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: '#6366f1' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[240px] flex items-center justify-center">
              <p className="text-xs text-gray-400 dark:text-gray-500">Loading trends…</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* ── Cost Avoidance Bar Chart ─────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...spring, delay: 0.55 }}
        className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl mb-6"
      >
        <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
          Cost Avoidance Trend (6 months)
        </h2>
        {monthlyTrend.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={monthlyTrend} barSize={28}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.12)" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`$${v.toLocaleString()}`, 'Cost Avoided']} />
              <Bar dataKey="cost_avoidance_usd" name="Cost Avoided" fill="#6366f1" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[220px] flex items-center justify-center"><p className="text-xs text-gray-400">Loading…</p></div>
        )}
      </motion.div>

      {/* ── AI Performance + Revenue Pie ─────────── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-6">
        {/* AI Agent Performance */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.62 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            AI Agent Performance
          </h2>
          {monthlyTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={monthlyTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.12)" />
                <XAxis dataKey="month" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <Tooltip contentStyle={tooltipStyle} formatter={(v, n) => [`${v}%`, n]} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="acceptance_pct" name="Acceptance" stroke="#6366f1" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="conversion_pct" name="Conversion" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="escalation_pct" name="Escalation" stroke="#f87171" strokeWidth={2} strokeDasharray="4 3" dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center"><p className="text-xs text-gray-400">Loading…</p></div>
          )}
        </motion.div>

        {/* Revenue by Component Pie */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.70 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Revenue by Service Type
          </h2>
          {revenuePie.length > 0 ? (
            <div className="flex items-center gap-6">
              <ResponsiveContainer width="55%" height={220}>
                <PieChart>
                  <Pie data={revenuePie} cx="50%" cy="50%" innerRadius={52} outerRadius={82} paddingAngle={4} dataKey="value" stroke="none" animationDuration={1200}>
                    {revenuePie.map((_, idx) => <Cell key={idx} fill={REVENUE_COLORS[idx % REVENUE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`$${v.toLocaleString()}`, 'Revenue']} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2">
                {revenuePie.map((entry, idx) => (
                  <div key={entry.name} className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: REVENUE_COLORS[idx % REVENUE_COLORS.length] }} />
                    <p className="text-[10px] text-gray-500 dark:text-gray-400 capitalize truncate max-w-[120px]">{entry.name}</p>
                    <p className="text-[10px] font-bold text-gray-900 dark:text-white ml-auto">${(entry.value / 1000).toFixed(1)}k</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-[220px] flex items-center justify-center"><p className="text-xs text-gray-400">Loading…</p></div>
          )}
        </motion.div>
      </div>

      {/* ── Booking Heatmap ──────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...spring, delay: 0.75 }}
        className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl mb-6"
      >
        <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
          Booking Heatmap — Day × Hour
        </h2>
        <div className="overflow-x-auto">
          <div className="flex gap-1 mb-2 ml-10">
            {HOURS.map((h) => <span key={h} className="w-9 text-center text-[9px] font-medium text-gray-400 shrink-0">{h}</span>)}
          </div>
          {DAYS.map((day) => (
            <div key={day} className="flex items-center gap-1 mb-1">
              <span className="w-10 text-[10px] text-gray-400 font-medium shrink-0">{day}</span>
              {HOURS.map((hour) => {
                const cell = HEATMAP_DATA.find((d) => d.day === day && d.hour === hour);
                const v = cell ? cell.value : 0;
                const opacity = Math.max(0.08, v / 14);
                return (
                  <div
                    key={hour}
                    title={`${day} ${hour}: ${v} bookings`}
                    className="w-9 h-9 rounded-lg cursor-default transition-all hover:scale-110 shrink-0"
                    style={{ backgroundColor: `rgba(202,255,66,${opacity})`, border: `1px solid rgba(202,255,66,${Math.min(opacity * 1.5, 0.3)})` }}
                  >
                    <span className="flex items-center justify-center h-full text-[9px] font-bold" style={{ color: v > 8 ? '#0b0f19' : '#6b7280' }}>
                      {v > 0 ? v : ''}
                    </span>
                  </div>
                );
              })}
            </div>
          ))}
          <div className="flex items-center gap-2 mt-3 ml-10">
            <span className="text-[9px] text-gray-400">Low</span>
            {[0.08, 0.2, 0.4, 0.6, 0.8, 1.0].map((o) => <div key={o} className="w-5 h-3 rounded" style={{ backgroundColor: `rgba(202,255,66,${o})` }} />)}
            <span className="text-[9px] text-gray-400">High</span>
          </div>
        </div>
      </motion.div>

      {/* ── Top 5 At-Risk Vehicles ──────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ ...spring, delay: 0.55 }}
        className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
      >
        <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-5">
          Top 5 At-Risk Vehicles
        </h2>

        {/* Table header */}
        <div className="grid grid-cols-12 gap-3 px-4 pb-3 border-b border-gray-200 dark:border-gray-700">
          <span className="col-span-1 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">#</span>
          <span className="col-span-2 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">Vehicle</span>
          <span className="col-span-2 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">Make / Model</span>
          <span className="col-span-2 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">Priority</span>
          <span className="col-span-2 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">Failure Prob.</span>
          <span className="col-span-2 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">Component</span>
          <span className="col-span-1 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">RUL</span>
        </div>

        {/* Table rows */}
        <div className="divide-y divide-gray-100 dark:divide-white/5">
          {topAtRisk.length === 0 ? (
            <p className="text-xs text-gray-400 dark:text-gray-500 text-center py-8">Loading vehicles…</p>
          ) : (
            topAtRisk.map((v, i) => {
              const failPct = Math.round((v.failure_probability || 0) * 100);
              const comp = v.diagnosis?.predicted_component?.replace(/_/g, ' ') || '—';
              const rul = v.diagnosis?.rul_days;
              const priConfig = {
                P0: 'bg-red-500/15 text-red-500',
                P1: 'bg-orange-500/15 text-orange-500',
                P2: 'bg-amber-500/15 text-amber-500',
                P3: 'bg-emerald-500/15 text-emerald-500',
              };

              return (
                <motion.div
                  key={v.vehicle_id}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ ...spring, delay: 0.6 + i * 0.06 }}
                  className="grid grid-cols-12 gap-3 px-4 py-3.5 items-center hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors rounded-xl"
                >
                  <span className="col-span-1 text-xs font-extrabold text-gray-400 dark:text-gray-500">
                    {i + 1}
                  </span>
                  <span className="col-span-2 text-xs font-bold text-gray-900 dark:text-white">
                    {v.vehicle_id}
                  </span>
                  <span className="col-span-2 text-xs text-gray-600 dark:text-gray-300">
                    {v.make} {v.model}
                  </span>
                  <span className="col-span-2">
                    <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${priConfig[v.priority] || priConfig.P3}`}>
                      {v.priority}
                    </span>
                  </span>
                  <span className="col-span-2 flex items-center gap-2">
                    {/* Mini bar */}
                    <div className="flex-1 h-2 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${failPct >= 70 ? 'bg-red-500' :
                            failPct >= 40 ? 'bg-amber-400' :
                              'bg-emerald-500'
                          }`}
                        initial={{ width: 0 }}
                        animate={{ width: `${failPct}%` }}
                        transition={{ duration: 1, ease: 'easeOut' }}
                      />
                    </div>
                    <span className="text-xs font-bold text-gray-900 dark:text-white w-8 text-right">{failPct}%</span>
                  </span>
                  <span className="col-span-2 text-xs text-gray-600 dark:text-gray-300 capitalize truncate">
                    {comp}
                  </span>
                  <span className="col-span-1 text-xs font-medium text-gray-500 dark:text-gray-400">
                    {rul != null ? `${rul}d` : '—'}
                  </span>
                </motion.div>
              );
            })
          )}
        </div>
      </motion.div>
    </DashboardLayout>
  );
}
