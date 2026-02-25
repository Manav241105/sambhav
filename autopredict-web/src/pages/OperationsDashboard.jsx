import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import {
  Truck,
  CalendarDays,
  MessageSquare,
  AlertTriangle,
  X,
  RefreshCw,
  Send,
  ArrowDownRight,
  ArrowUpRight,
} from 'lucide-react';

import DashboardLayout from '../components/DashboardLayout';
import AlertBanner from '../components/AlertBanner';
import VehicleCard from '../components/VehicleCard';
import TelematicsGauge from '../components/TelematicsGauge';
import SubsystemRadar from '../components/SubsystemRadar';
import DtcPanel from '../components/DtcPanel';
import BayCalendar from '../components/BayCalendar';
import LiveToast from '../components/LiveToast';
import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts';

const API = 'http://localhost:8000';
const spring = { type: 'spring', stiffness: 100, damping: 10 };

/* ── Helpers ──────────────────────────────────────── */
function latestTelem(telematics) {
  if (!telematics) return {};
  if (Array.isArray(telematics)) return telematics[telematics.length - 1] || {};
  return telematics;
}

/* ════════════════════════════════════════════════════
   OPERATIONS DASHBOARD
   ════════════════════════════════════════════════════ */
export default function OperationsDashboard() {
  /* ── State ─────────────────────────────────────── */
  const [vehicles, setVehicles] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [summary, setSummary] = useState(null);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [manufacturing, setManufacturing] = useState(null);
  const [mfgLoading, setMfgLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  /* ── Fetch core data ───────────────────────────── */
  const fetchAll = useCallback(async () => {
    try {
      const [vRes, aRes, bRes, cRes, sRes] = await Promise.all([
        axios.get(`${API}/api/vehicles`),
        axios.get(`${API}/api/dashboard/alerts`),
        axios.get(`${API}/api/bookings/today`),
        axios.get(`${API}/api/conversations`),
        axios.get(`${API}/api/dashboard/summary`),
      ]);
      setVehicles(Array.isArray(vRes.data) ? vRes.data : Object.values(vRes.data));
      setAlerts(Array.isArray(aRes.data) ? aRes.data : []);
      setBookings(Array.isArray(bRes.data) ? bRes.data : []);
      setConversations(Array.isArray(cRes.data) ? cRes.data : []);
      setSummary(sRes.data);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30_000); // poll every 30s
    return () => clearInterval(interval);
  }, [fetchAll]);

  /* ── Fetch manufacturing when a vehicle is selected */
  useEffect(() => {
    if (!selectedVehicle) { setManufacturing(null); return; }
    let cancelled = false;
    setMfgLoading(true);
    axios
      .get(`${API}/api/vehicles/${selectedVehicle.vehicle_id}/manufacturing`)
      .then((r) => { if (!cancelled) setManufacturing(r.data); })
      .catch(() => { if (!cancelled) setManufacturing(null); })
      .finally(() => { if (!cancelled) setMfgLoading(false); });
    return () => { cancelled = true; };
  }, [selectedVehicle]);

  /* ── Derived stats ─────────────────────────────── */
  const statCards = [
    {
      label: 'Active Vehicles',
      value: summary?.total_vehicles ?? vehicles.length,
      icon: Truck,
      color: 'text-[#6366f1]',
    },
    {
      label: "Today's Bookings",
      value: summary?.total_bookings ?? bookings.length,
      icon: CalendarDays,
      color: 'text-blue-400',
    },
    {
      label: 'Open Conversations',
      value: summary?.total_conversations ?? conversations.length,
      icon: MessageSquare,
      color: 'text-purple-400',
    },
    {
      label: 'P0 Alerts',
      value: alerts.filter((a) => a.priority === 'P0').length,
      icon: AlertTriangle,
      color: 'text-red-400',
    },
  ];

  /* ── Dismiss alert ─────────────────────────────── */
  const dismissAlert = (i) => setAlerts((prev) => prev.filter((_, idx) => idx !== i));

  /* ── Select vehicle from alert or card ─────────── */
  const selectFromAlert = (alert) => {
    const v = vehicles.find((v) => v.vehicle_id === alert.vehicle_id);
    if (v) setSelectedVehicle(v);
  };

  /* ── Gauge data extraction from telematics ─────── */
  function buildGauges(vehicle) {
    const t = latestTelem(vehicle?.telematics);
    return [
      { label: 'Battery', value: t.battery_voltage ?? 12.6, max: 14.5, unit: 'V', metricKey: 'battery_voltage' },
      { label: 'Brake Pad', value: t.brake_pad_thickness ?? 8.0, max: 12, unit: 'mm', metricKey: 'brake_pad_thickness' },
      { label: 'Coolant', value: t.coolant_temp ?? 90, max: 120, unit: '°C', metricKey: 'coolant_temp' },
      { label: 'Tire PSI', value: t.tire_pressure_fl ?? 32, max: 38, unit: 'psi', metricKey: 'tire_pressure' },
      { label: 'Oil', value: t.oil_pressure ?? 45, max: 65, unit: 'psi', metricKey: 'oil_pressure' },
      { label: 'Trans Temp', value: t.transmission_temp ?? 80, max: 120, unit: '°C', metricKey: 'transmission_temp' },
    ];
  }
  /* ── Derived chart data ─────────────────────── */

  // Fleet health donut data
  const fleetHealthPie = React.useMemo(() => {
    const critical = vehicles.filter((v) => v.priority === 'P0').length;
    const warning = vehicles.filter((v) => v.priority === 'P1' || v.priority === 'P2').length;
    const normal = Math.max(0, vehicles.length - critical - warning);
    return [
      { name: 'Normal', value: normal, fill: '#22c55e' },
      { name: 'Warning', value: warning, fill: '#fbbf24' },
      { name: 'Critical', value: critical, fill: '#ef4444' },
    ].filter((d) => d.value > 0);
  }, [vehicles]);

  // Telematics trend (last 7 days — stable seed)
  const telematicsTrend = React.useMemo(() => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    return days.map((d, i) => ({
      day: d,
      battery: +(12.2 + Math.sin(i * 0.8) * 0.3).toFixed(2),
      coolant: Math.round(88 + Math.sin(i * 0.5) * 4),
      oil: Math.round(44 + Math.cos(i * 0.7) * 3),
    }));
  }, []);

  const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };


  return (
    <DashboardLayout title="Operations Dashboard">
      {/* ── Live WebSocket Toast ─────────────────── */}
      <LiveToast onEvent={() => fetchAll()} />

      {/* ── P0 Alert Banner ─────────────────────── */}
      <AlertBanner
        alerts={alerts}
        onDismiss={dismissAlert}
        onClickAlert={selectFromAlert}
      />

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
              className="flex items-center gap-4 p-5 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
            >
              <div className={`p-3 rounded-2xl bg-gray-100 dark:bg-white/5 ${card.color}`}>
                <Icon size={22} />
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400">{card.label}</p>
                <p className="text-xl font-extrabold text-gray-900 dark:text-white">
                  {loading ? '—' : card.value}
                </p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* ── Main grid: Fleet + Detail drawer ────── */}
      <div className="flex gap-6 mb-8">
        {/* Fleet grid */}
        <motion.section
          id="fleet"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
          className={`transition-all duration-300 ${selectedVehicle ? 'w-1/2' : 'w-full'}`}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider">
              Fleet Overview
            </h2>
            <button
              onClick={fetchAll}
              className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
              title="Refresh"
            >
              <RefreshCw size={14} className="text-gray-400" />
            </button>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-44 rounded-3xl bg-gray-200 dark:bg-white/5 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className={`grid gap-4 ${selectedVehicle ? 'grid-cols-1 xl:grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 xl:grid-cols-3'}`}>
              <AnimatePresence>
                {vehicles.map((v) => (
                  <VehicleCard
                    key={v.vehicle_id}
                    vehicle={v}
                    selected={selectedVehicle?.vehicle_id === v.vehicle_id}
                    onClick={setSelectedVehicle}
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
        </motion.section>

        {/* ── Detail side-drawer ─────────────────── */}
        <AnimatePresence>
          {selectedVehicle && (
            <motion.aside
              key="detail-drawer"
              initial={{ opacity: 0, x: 60, width: 0 }}
              animate={{ opacity: 1, x: 0, width: '50%' }}
              exit={{ opacity: 0, x: 60, width: 0 }}
              transition={spring}
              className="overflow-hidden"
            >
              <div className="sticky top-0 p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl overflow-y-auto max-h-[calc(100vh-220px)]">
                {/* Drawer header */}
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{selectedVehicle.vehicle_id}</p>
                    <h3 className="text-lg font-extrabold text-gray-900 dark:text-white">
                      {selectedVehicle.make} {selectedVehicle.model}
                    </h3>
                  </div>
                  <button
                    onClick={() => setSelectedVehicle(null)}
                    className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
                  >
                    <X size={16} className="text-gray-400" />
                  </button>
                </div>

                {/* Telemetry gauges */}
                <div className="grid grid-cols-3 gap-2 mb-6">
                  {buildGauges(selectedVehicle).map((g) => (
                    <TelematicsGauge key={g.metricKey} {...g} size={110} />
                  ))}
                </div>

                {/* Subsystem radar */}
                <div className="mb-6">
                  <SubsystemRadar
                    telematics={selectedVehicle.telematics}
                    diagnosis={selectedVehicle.diagnosis}
                  />
                </div>

                {/* DTC + Recalls */}
                <DtcPanel
                  dtcCodes={manufacturing?.dtc_codes || []}
                  recalls={manufacturing?.recalls || []}
                  loading={mfgLoading}
                />
              </div>
            </motion.aside>
          )}
        </AnimatePresence>
      </div>

      {/* ── Bottom: Calendar + Conversations ────── */}
      <div id="calendar" className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Bay Calendar */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.3 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Bay Schedule
          </h2>
          <BayCalendar
            bookings={bookings}
            onEventClick={(b) => {
              const v = vehicles.find((v) => v.vehicle_id === b.vehicle_id);
              if (v) setSelectedVehicle(v);
            }}
          />
        </motion.div>

        {/* Live Conversation Feed */}
        <motion.div
          id="conversations"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.4 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl flex flex-col max-h-[520px]"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Live Conversations
          </h2>

          {/* Chat list */}
          <div className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar">
            {conversations.length === 0 ? (
              <p className="text-xs text-gray-400 dark:text-gray-500 text-center py-12">
                No conversations yet
              </p>
            ) : (
              conversations.map((turn, i) => {
                const outbound = turn.direction === 'OUTBOUND';
                return (
                  <motion.div
                    key={turn.vehicle_id + '-' + turn.turn_number + '-' + i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ ...spring, delay: i * 0.03 }}
                    className={`flex gap-3 ${outbound ? '' : 'flex-row-reverse'}`}
                  >
                    {/* Direction indicator */}
                    <div className={`mt-1 p-1.5 rounded-lg shrink-0 ${outbound ? 'bg-[#6366f1]/15' : 'bg-blue-500/15'}`}>
                      {outbound
                        ? <ArrowUpRight size={12} className="text-[#6366f1]" />
                        : <ArrowDownRight size={12} className="text-blue-400" />}
                    </div>

                    {/* Message bubble */}
                    <div className={`flex-1 min-w-0 p-3 rounded-2xl ${outbound
                        ? 'bg-gray-50 dark:bg-white/[0.03] border border-gray-100 dark:border-white/5'
                        : 'bg-blue-50 dark:bg-blue-500/5 border border-blue-100 dark:border-blue-500/10'
                      }`}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          {outbound ? 'AI Agent' : turn.customer_name || 'Customer'}
                        </span>
                        <span className="text-[9px] text-gray-400 dark:text-gray-600">
                          {turn.vehicle_id}
                        </span>
                        <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold ${turn.status === 'OPEN'
                            ? 'bg-[#6366f1]/15 text-[#6366f1]'
                            : 'bg-gray-200 dark:bg-white/10 text-gray-500 dark:text-gray-400'
                          }`}>
                          {turn.status || 'OPEN'}
                        </span>
                      </div>
                      <p className="text-xs text-gray-700 dark:text-gray-300 leading-relaxed">
                        {turn.message}
                      </p>
                    </div>
                  </motion.div>
                );
              })
            )}
          </div>
        </motion.div>
      </div>

      {/* Fleet Health Donut + Telematics Trend */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mt-8">
        {/* Fleet Health Donut */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.6 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Fleet Health Summary
          </h2>
          {fleetHealthPie.length > 0 ? (
            <div className="flex items-center gap-8">
              <div style={{ width: 200, height: 200 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={fleetHealthPie} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4} dataKey="value" animationDuration={1200} stroke="none">
                      {fleetHealthPie.map((entry, idx) => <Cell key={idx} fill={entry.fill} />)}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-4">
                {fleetHealthPie.map((entry) => (
                  <div key={entry.name} className="flex items-center gap-3">
                    <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: entry.fill }} />
                    <div>
                      <p className="text-xl font-extrabold text-gray-900 dark:text-white">{entry.value}</p>
                      <p className="text-[10px] text-gray-400">{entry.name} vehicles</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-[200px] flex items-center justify-center">
              <p className="text-xs text-gray-400">Loading fleet…</p>
            </div>
          )}
        </motion.div>

        {/* Telematics Trend */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...spring, delay: 0.70 }}
          className="p-6 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl"
        >
          <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
            Telematics Trends (7-day)
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={telematicsTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.12)" />
              <XAxis dataKey="day" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="battery" name="Battery (V)" stroke="#6366f1" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="coolant" name="Coolant (C)" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="oil" name="Oil PSI" stroke="#fb923c" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
    </DashboardLayout>
  );
}

