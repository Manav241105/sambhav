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

  // Monthly trend for line chart
  const monthlyTrend = useMemo(() => {
    return monthly.map((m) => ({
      ...m,
      acceptance_pct: Math.round((m.acceptance_rate || 0) * 100),
    }));
  }, [monthly]);

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
      color: 'text-[#caff42]',
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
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-[#caff42] to-transparent opacity-0 group-hover:opacity-[0.06] blur-xl transition-opacity pointer-events-none" />
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
                    <stop offset="0%" stopColor="#caff42" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#caff42" stopOpacity={0} />
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
                  stroke="#caff42"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#caff42', stroke: '#0b0f19', strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: '#caff42' }}
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
                        className={`h-full rounded-full ${
                          failPct >= 70 ? 'bg-red-500' :
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
