import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import { X, Car, Gauge, Activity, Calendar } from 'lucide-react';
import VehicleCard from '../../components/VehicleCard';
import TelematicsGauge from '../../components/TelematicsGauge';
import SubsystemRadar from '../../components/SubsystemRadar';
import DtcPanel from '../../components/DtcPanel';
import {
    ResponsiveContainer, PieChart, Pie, Cell, Tooltip,
    LineChart, Line, XAxis, YAxis, CartesianGrid, Legend,
} from 'recharts';

const spring = { type: 'spring', stiffness: 100, damping: 10 };
const tooltipStyle = {
    backgroundColor: '#1f2937',
    border: '1px solid #374151',
    borderRadius: '12px',
    fontSize: 12,
    color: '#fff',
};

/* ── Extract latest telematics snapshot ─────────────── */
function latestTelem(telematics) {
    if (!telematics) return {};
    if (Array.isArray(telematics)) return telematics[telematics.length - 1] || {};
    return telematics;
}

/* ── Build gauge configs using REAL backend field names ─
   Backend: brake_pad_mm, battery_voltage_v, coolant_temp_c,
            oil_pressure_bar, tire_pressure_psi.fl, engine_rpm ── */
function buildGauges(vehicle) {
    const t = latestTelem(vehicle?.telematics);
    return [
        {
            label: 'Battery',
            value: t.battery_voltage_v ?? t.battery_voltage ?? 12.6,
            max: 14.5, unit: 'V', metricKey: 'battery_voltage',
        },
        {
            label: 'Brake Pad',
            value: t.brake_pad_mm ?? t.brake_pad_thickness ?? 8.0,
            max: 12, unit: 'mm', metricKey: 'brake_pad_thickness',
        },
        {
            label: 'Coolant',
            value: t.coolant_temp_c ?? t.coolant_temp ?? 90,
            max: 120, unit: '°C', metricKey: 'coolant_temp',
        },
        {
            label: 'Tire PSI',
            value: (t.tire_pressure_psi?.fl ?? t.tire_pressure_fl ?? 32),
            max: 38, unit: 'psi', metricKey: 'tire_pressure',
        },
        {
            label: 'Oil Pressure',
            // backend sends bars — multiply to match gauge max if needed
            value: t.oil_pressure_bar != null ? t.oil_pressure_bar * 14.5 : (t.oil_pressure ?? 45),
            max: 65, unit: 'psi', metricKey: 'oil_pressure',
        },
        {
            label: 'Engine RPM',
            value: t.engine_rpm ?? 900,
            max: 6000, unit: 'rpm', metricKey: 'engine_rpm',
        },
    ];
}

/* ── Priority badge helper ─────────────────────────── */
const PRI = {
    P0: { text: 'text-red-500', bg: 'bg-red-500/10', label: 'CRITICAL' },
    P1: { text: 'text-orange-500', bg: 'bg-orange-500/10', label: 'HIGH' },
    P2: { text: 'text-amber-500', bg: 'bg-amber-500/10', label: 'MEDIUM' },
    P3: { text: 'text-emerald-500', bg: 'bg-emerald-500/10', label: 'NORMAL' },
};

export default function OpsFleet() {
    const {
        vehicles, selectedVehicle, setSelectedVehicle,
        manufacturing, mfgLoading, fleetHealthPie, telematicsTrend,
    } = useOutletContext();

    const hasSelection = Boolean(selectedVehicle);
    const pri = selectedVehicle ? (PRI[selectedVehicle.priority] || PRI.P3) : null;
    const diag = selectedVehicle?.diagnosis || {};
    const telem = latestTelem(selectedVehicle?.telematics);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={spring}
            className="space-y-6"
        >
            {/* Header */}
            <div>
                <h2 className="text-sm font-extrabold text-gray-900 dark:text-white uppercase tracking-wider mb-1">
                    Fleet Overview
                </h2>
                <p className="text-sm text-gray-400 dark:text-gray-500 max-w-2xl leading-relaxed">
                    Live telematics for all connected vehicles. Click a card to see its full diagnostic breakdown.
                </p>
            </div>

            {/* Charts row */}
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                {/* Fleet Health Donut */}
                <div className="p-5 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl">
                    <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
                        Fleet Health Distribution
                    </h3>
                    {fleetHealthPie.length > 0 ? (
                        <div className="flex items-center gap-6">
                            <ResponsiveContainer width="50%" height={180}>
                                <PieChart>
                                    <Pie data={fleetHealthPie} cx="50%" cy="50%" innerRadius={46} outerRadius={72}
                                        paddingAngle={4} dataKey="value" stroke="none" animationDuration={1200}>
                                        {fleetHealthPie.map((d, i) => <Cell key={i} fill={d.fill} />)}
                                    </Pie>
                                    <Tooltip contentStyle={tooltipStyle} />
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="space-y-2.5">
                                {fleetHealthPie.map((d) => (
                                    <div key={d.name} className="flex items-center gap-3">
                                        <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: d.fill }} />
                                        <span className="text-xs font-bold text-gray-900 dark:text-white">{d.value}</span>
                                        <span className="text-[10px] text-gray-400">{d.name}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="h-[180px] flex items-center justify-center">
                            <p className="text-xs text-gray-400">Loading…</p>
                        </div>
                    )}
                </div>

                {/* Telematics Trend */}
                <div className="p-5 border bg-white dark:bg-white/5 border-gray-200 dark:border-gray-700 rounded-3xl">
                    <h3 className="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">
                        Telematics Trends (7-day)
                    </h3>
                    <ResponsiveContainer width="100%" height={180}>
                        <LineChart data={telematicsTrend}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(156,163,175,0.12)" />
                            <XAxis dataKey="day" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={tooltipStyle} />
                            <Legend wrapperStyle={{ fontSize: 10 }} />
                            <Line type="monotone" dataKey="battery" name="Battery (V)" stroke="#22c55e" strokeWidth={2} dot={{ r: 2 }} />
                            <Line type="monotone" dataKey="coolant" name="Coolant (°C)" stroke="#ef4444" strokeWidth={2} dot={{ r: 2 }} />
                            <Line type="monotone" dataKey="oil" name="Oil (psi)" stroke="#f59e0b" strokeWidth={2} dot={{ r: 2 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* ── Split layout: card grid | side detail panel ── */}
            <div className="flex gap-5 items-start">

                {/* Vehicle Cards — narrows when panel is open */}
                <div className={`grid gap-4 transition-all duration-300 ${hasSelection
                        ? 'grid-cols-1 sm:grid-cols-2 min-w-0 flex-[1.1]'
                        : 'grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 flex-1'
                    }`}>
                    {vehicles.map((v, i) => (
                        <motion.div
                            key={v.vehicle_id}
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ ...spring, delay: i * 0.04 }}
                        >
                            <VehicleCard
                                vehicle={v}
                                selected={selectedVehicle?.vehicle_id === v.vehicle_id}
                                onClick={(clicked) =>
                                    setSelectedVehicle(
                                        selectedVehicle?.vehicle_id === clicked.vehicle_id ? null : clicked
                                    )
                                }
                            />
                        </motion.div>
                    ))}
                </div>

                {/* ── Side Detail Panel ── */}
                <AnimatePresence>
                    {selectedVehicle && (
                        <motion.div
                            key="detail-panel"
                            initial={{ opacity: 0, x: 32 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 32 }}
                            transition={{ type: 'spring', stiffness: 300, damping: 28 }}
                            style={{ width: '46%', minWidth: 320 }}
                            className="shrink-0 self-start sticky top-4"
                        >
                            <div className="border bg-white dark:bg-[#0d1117] border-gray-200 dark:border-gray-700 rounded-3xl overflow-hidden">

                                {/* ─ Header ─ */}
                                <div className="px-5 pt-5 pb-4 border-b border-gray-100 dark:border-gray-800">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-2xl bg-[#6366f1]/10 flex items-center justify-center shrink-0">
                                                <Car size={18} className="text-[#6366f1]" />
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2 mb-0.5">
                                                    <p className="text-[10px] font-mono font-semibold text-gray-400 uppercase tracking-wider">
                                                        {selectedVehicle.vehicle_id}
                                                    </p>
                                                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${pri.bg} ${pri.text}`}>
                                                        {pri.label}
                                                    </span>
                                                </div>
                                                <h3 className="text-base font-extrabold text-gray-900 dark:text-white leading-tight">
                                                    {selectedVehicle.year} {selectedVehicle.make} {selectedVehicle.model}
                                                </h3>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => setSelectedVehicle(null)}
                                            className="p-1.5 rounded-xl hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                                        >
                                            <X size={14} className="text-gray-400" />
                                        </button>
                                    </div>

                                    {/* Quick stats row */}
                                    <div className="grid grid-cols-3 gap-3 mt-4">
                                        <div className="p-2.5 rounded-2xl bg-gray-50 dark:bg-white/5">
                                            <p className="text-[9px] text-gray-400 uppercase tracking-wider mb-0.5">Health Score</p>
                                            <p className="text-sm font-extrabold text-gray-900 dark:text-white">
                                                {Math.round((selectedVehicle.health_score ?? 0) * 100)}%
                                            </p>
                                        </div>
                                        <div className="p-2.5 rounded-2xl bg-gray-50 dark:bg-white/5">
                                            <p className="text-[9px] text-gray-400 uppercase tracking-wider mb-0.5">Odometer</p>
                                            <p className="text-sm font-extrabold text-gray-900 dark:text-white">
                                                {telem.odo_km != null ? `${telem.odo_km.toLocaleString()} km` : '—'}
                                            </p>
                                        </div>
                                        <div className="p-2.5 rounded-2xl bg-gray-50 dark:bg-white/5">
                                            <p className="text-[9px] text-gray-400 uppercase tracking-wider mb-0.5">RUL</p>
                                            <p className="text-sm font-extrabold text-gray-900 dark:text-white">
                                                {diag.rul_days != null ? `${diag.rul_days}d` : '—'}
                                            </p>
                                        </div>
                                    </div>

                                    {diag.predicted_component && (
                                        <div className="mt-3 flex items-center gap-2 px-3 py-2 rounded-2xl bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20">
                                            <Activity size={13} className="text-red-500 shrink-0" />
                                            <p className="text-xs text-red-600 dark:text-red-400 font-medium capitalize">
                                                Predicted failure: <span className="font-bold">{diag.predicted_component.replace(/_/g, ' ')}</span>
                                                {diag.confidence ? ` (${Math.round(diag.confidence * 100)}% confidence)` : ''}
                                            </p>
                                        </div>
                                    )}
                                </div>

                                {/* Scrollable content */}
                                <div className="overflow-y-auto max-h-[55vh] space-y-0">

                                    {/* ─ Live Gauges ─ */}
                                    <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-800">
                                        <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-3 flex items-center gap-1.5">
                                            <Gauge size={11} /> Live Telematics
                                        </p>
                                        <div className="grid grid-cols-3 gap-2">
                                            {buildGauges(selectedVehicle).map((g) => (
                                                <TelematicsGauge key={g.label} {...g} size={100} />
                                            ))}
                                        </div>
                                    </div>

                                    {/* ─ Subsystem Radar ─ */}
                                    <div className="px-5 py-4 border-b border-gray-100 dark:border-gray-800">
                                        <SubsystemRadar
                                            telematics={selectedVehicle.telematics}
                                            diagnosis={selectedVehicle.diagnosis}
                                        />
                                    </div>

                                    {/* ─ DTC / Manufacturing ─ */}
                                    <div className="px-5 py-4">
                                        <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-3 flex items-center gap-1.5">
                                            <Calendar size={11} /> Manufacturing & DTCs
                                        </p>
                                        {mfgLoading ? (
                                            <div className="h-20 flex items-center justify-center">
                                                <p className="text-xs text-gray-400">Loading…</p>
                                            </div>
                                        ) : manufacturing ? (
                                            <DtcPanel manufacturing={manufacturing} />
                                        ) : (
                                            <p className="text-xs text-gray-400">No manufacturing data available.</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}
