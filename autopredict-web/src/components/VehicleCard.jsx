import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Gauge, Wrench, Clock, ChevronRight, MessageCircle } from 'lucide-react';
import api from '../lib/api';
import TelematicsSparklines from './charts/TelematicsSparklines';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/* ── Priority colours ─────────────────────────────── */
const PRIORITY_CONFIG = {
  P0: { bg: 'bg-red-500/15', text: 'text-red-500', ring: '#ef4444' },
  P1: { bg: 'bg-orange-500/15', text: 'text-orange-500', ring: '#f97316' },
  P2: { bg: 'bg-amber-500/15', text: 'text-amber-400', ring: '#fbbf24' },
  P3: { bg: 'bg-emerald-500/15', text: 'text-emerald-500', ring: '#22c55e' },
};

/**
 * SVG health ring — a clean circular progress indicator.
 */
function HealthRing({ score = 0, size = 64, strokeWidth = 5, color = '#22c55e' }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score);

  return (
    <svg width={size} height={size} className="shrink-0 -rotate-90">
      {/* Background track */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="currentColor"
        className="text-gray-200 dark:text-white/10"
        strokeWidth={strokeWidth}
      />
      {/* Filled arc */}
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        initial={{ strokeDashoffset: circumference }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
      />
      {/* Centre label */}
      <text
        x={size / 2}
        y={size / 2}
        dominantBaseline="central"
        textAnchor="middle"
        className="fill-gray-900 dark:fill-white text-xs font-bold rotate-90 origin-center"
        transform={`rotate(90 ${size / 2} ${size / 2})`}
      >
        {Math.round(score * 100)}%
      </text>
    </svg>
  );
}

/**
 * VehicleCard — shows vehicle summary, health ring, priority badge.
 *
 * Props:
 *   vehicle   — full vehicle object from API
 *   onClick   — callback when card is clicked
 *   selected  — boolean, highlights the active card
 */
const STAGE_CONFIG = {
  contacted: { bg: 'bg-[#6366f1]/10', text: 'text-[#6366f1]', label: 'Contacted' },
  interested: { bg: 'bg-blue-500/10', text: 'text-blue-500', label: 'Interested' },
  booked: { bg: 'bg-emerald-500/10', text: 'text-emerald-500', label: 'Booked' },
  none: { bg: 'bg-gray-500/10', text: 'text-gray-400', label: 'No Contact' },
};

export default function VehicleCard({ vehicle, onClick, selected = false, conversationStage }) {
  /* ── 7-day sparkline history (hooks run before any early return) ── */
  const vehicleId = vehicle?.vehicle_id;
  const [sparkData, setSparkData] = useState([]);
  useEffect(() => {
    if (!vehicleId) return undefined;
    let cancelled = false;
    api
      .get(`/api/vehicles/${vehicleId}/history?days=7`)
      .then((r) => { if (!cancelled) setSparkData(r.data?.history || []); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [vehicleId]);

  if (!vehicle) return null;

  const pri = PRIORITY_CONFIG[vehicle.priority] || PRIORITY_CONFIG.P3;
  const healthScore = vehicle.health_score ?? 0;
  const diagnosis = vehicle.diagnosis || {};
  const component = diagnosis.predicted_component?.replace(/_/g, ' ') || 'Healthy';
  const rulDays = diagnosis.rul_days;
  const severity = diagnosis.severity || 'normal';
  const stage = STAGE_CONFIG[conversationStage] || STAGE_CONFIG.none;

  /* ── Dynamic ring colour based on actual health score ── */
  const ringColor =
    healthScore >= 0.75 ? '#22c55e' :
    healthScore >= 0.5  ? '#fbbf24' :
    healthScore >= 0.3  ? '#f97316' : '#ef4444';

  /* ── Last contact timestamp ── */
  const lastContact = vehicle.updated_at || vehicle.telematics?.timestamp;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={spring}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onClick?.(vehicle)}
      className={`
        relative group p-5 rounded-3xl border cursor-pointer transition-colors
        ${selected
          ? 'border-[#6366f1] bg-[#6366f1]/5 dark:bg-[#6366f1]/5 shadow-lg shadow-[#6366f1]/10'
          : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-white/5 hover:border-gray-300 dark:hover:border-gray-600'}
      `}
    >
      {/* Glow on hover */}
      <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-[#6366f1] to-transparent opacity-0 group-hover:opacity-[0.06] blur-xl transition-opacity pointer-events-none" />

      {/* Header: ID + priority badge */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">{vehicle.vehicle_id}</p>
          <h3 className="text-sm font-extrabold text-gray-900 dark:text-white">
            {vehicle.make} {vehicle.model}
          </h3>
          <p className="text-[11px] text-gray-400 dark:text-gray-500">{vehicle.year}</p>
        </div>

        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${pri.bg} ${pri.text}`}>
          {vehicle.priority}
        </span>
      </div>

      {/* Health ring + details */}
      <div className="flex items-center gap-4">
        <HealthRing score={healthScore} color={ringColor} />

        <div className="flex-1 space-y-2 min-w-0">
          {/* Predicted component */}
          <div className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-300">
            <Wrench size={12} className="shrink-0 text-gray-400" />
            <span className="capitalize truncate">{component}</span>
          </div>

          {/* RUL */}
          {rulDays != null && (
            <div className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-300">
              <Clock size={12} className="shrink-0 text-gray-400" />
              <span>{rulDays} days RUL</span>
            </div>
          )}

          {/* Severity */}
          <div className="flex items-center gap-1.5 text-xs">
            <Gauge size={12} className="shrink-0 text-gray-400" />
            <span className={`capitalize font-medium ${
              severity === 'critical' ? 'text-red-500' :
              severity === 'warning' ? 'text-amber-500' :
              'text-emerald-500'
            }`}>
              {severity}
            </span>
          </div>
        </div>
      </div>

      {/* 7-day battery sparkline */}
      {sparkData.length > 0 && (
        <div className="mt-3 px-1">
          <p className="text-[9px] text-gray-400 dark:text-gray-500 mb-0.5 uppercase tracking-wider font-medium">
            Battery 7d
          </p>
          <TelematicsSparklines
            data={sparkData}
            dataKey="battery_voltage_v"
            color={ringColor}
            height={28}
          />
        </div>
      )}

      {/* Last contact badge + conversation stage */}
      <div className="flex items-center gap-2 mt-2">
        {lastContact && (
          <div className="flex items-center gap-1">
            <MessageCircle size={10} className="text-gray-400 dark:text-gray-500" />
            <span className="text-[9px] text-gray-400 dark:text-gray-500">
              {new Date(lastContact).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        )}
        <span className={`px-1.5 py-0.5 rounded-full text-[8px] font-bold uppercase tracking-wider ${stage.bg} ${stage.text}`}>
          {stage.label}
        </span>
      </div>

      {/* Tap indicator */}
      <div className="absolute bottom-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
        <ChevronRight size={14} className="text-gray-400" />
      </div>
    </motion.div>
  );
}
