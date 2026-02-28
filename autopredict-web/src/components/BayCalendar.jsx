import React, { useMemo, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import axios from 'axios';
import {
  X, CheckCircle2, Clock, Wrench, Trash2,
  AlertTriangle, Save, LayoutGrid, Activity
} from 'lucide-react';

const API = 'http://localhost:8000';
const spring = { type: 'spring', stiffness: 220, damping: 20 };

/* ── 10 Bays ─────────────────────────────────────────── */
const ALL_BAYS = [
  { id: 'BAY-1', label: 'Bay 1', spec: 'General Service' },
  { id: 'BAY-2', label: 'Bay 2', spec: 'Engine & Cooling' },
  { id: 'BAY-3', label: 'Bay 3', spec: 'Brakes & Tires' },
  { id: 'BAY-4', label: 'Bay 4', spec: 'Electrical / Battery' },
  { id: 'BAY-5', label: 'Bay 5', spec: 'Transmission' },
  { id: 'BAY-6', label: 'Bay 6', spec: 'Body & Detailing' },
  { id: 'BAY-7', label: 'Bay 7', spec: 'Express Service' },
  { id: 'BAY-8', label: 'Bay 8', spec: 'Diagnostics' },
  { id: 'BAY-9', label: 'Bay 9', spec: 'Alignment & Tyres' },
  { id: 'BAY-10', label: 'Bay 10', spec: 'Heavy Repairs' },
];

const TECHNICIANS = [
  { id: 'T001', name: 'Rajesh Kumar', spec: 'Brake / Tires' },
  { id: 'T002', name: 'Amit Sharma', spec: 'Battery / Electrical' },
  { id: 'T003', name: 'Priya Nair', spec: 'Cooling / Engine' },
  { id: 'T004', name: 'Suresh Patel', spec: 'Transmission / Full' },
  { id: 'T005', name: 'Deepak Mehta', spec: 'Brake / Battery' },
  { id: 'T006', name: 'Kavya Rao', spec: 'Diagnostics' },
  { id: 'T007', name: 'Arjun Singh', spec: 'Body & Detailing' },
  { id: 'T008', name: 'Meena Iyer', spec: 'Alignment / Tyres' },
];

const SERVICE_TYPES = [
  'Brake Pads', 'Battery', 'Cooling System', 'Engine',
  'Transmission', 'Tires', 'Oil Change', 'Full Service',
  'Diagnostics', 'Alignment', 'Body Work', 'Express Check',
];

const PRIORITIES = ['P0', 'P1', 'P2', 'P3'];
const STATUS_STEPS = ['CONFIRMED', 'IN_PROGRESS', 'COMPLETED'];

/* ── Priority → color ────────────────────────────────── */
const PRIORITY_COLORS = {
  P0: { bg: '#ef4444', border: '#dc2626', text: '#fff' },
  P1: { bg: '#f97316', border: '#ea580c', text: '#fff' },
  P2: { bg: '#fbbf24', border: '#d97706', text: '#1f2937' },
  P3: { bg: '#6366f1', border: '#4f46e5', text: '#fff' },
};

/* Bay accent colors for the "all bays" status row */
const BAY_COLORS = [
  '#6366f1', '#f97316', '#22c55e', '#ef4444', '#38bdf8',
  '#a78bfa', '#fbbf24', '#f472b6', '#34d399', '#fb923c',
];

const selectCls = 'w-full rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#6366f1]/50';
const labelCls = 'block text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1';

/* ─────────────────────────────────────────────────────────
   Bay Status Bar — quick glance at utilisation per bay
────────────────────────────────────────────────────────── */
function BayStatusBar({ bookings, selectedBay, onSelectBay }) {
  const today = new Date().toISOString().slice(0, 10);

  return (
    <div className="grid grid-cols-5 gap-2 mb-4 lg:grid-cols-10">
      {ALL_BAYS.map((bay, i) => {
        const bayBookings = bookings.filter(b => b.bay === bay.id && (b.slot_time_iso || '').startsWith(today));
        const count = bayBookings.length;
        const hasP0 = bayBookings.some(b => b.priority === 'P0');
        const hasP1 = bayBookings.some(b => b.priority === 'P1');
        const isSelected = selectedBay === bay.id;
        const statusColor = hasP0 ? '#ef4444' : hasP1 ? '#f97316' : count > 0 ? '#22c55e' : '#6b7280';

        return (
          <button
            key={bay.id}
            onClick={() => onSelectBay(isSelected ? null : bay.id)}
            className={`relative flex flex-col items-center p-2.5 rounded-2xl border-2 transition-all text-center
              ${isSelected
                ? 'border-[#6366f1] bg-[#6366f1]/10'
                : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-white/5 hover:border-gray-300 dark:hover:border-gray-600'}`}
          >
            {/* Colored top bar */}
            <span className="absolute top-0 left-4 right-4 h-0.5 rounded-full" style={{ background: BAY_COLORS[i] }} />

            <span className="text-[11px] font-extrabold text-gray-800 dark:text-white mt-1">{bay.label}</span>
            <span className="text-[9px] text-gray-400 truncate w-full">{bay.spec}</span>

            {/* Today's booking count */}
            <span
              className="mt-1.5 text-[10px] font-bold px-1.5 py-0.5 rounded-full"
              style={{ background: statusColor + '22', color: statusColor }}
            >
              {count} today
            </span>
          </button>
        );
      })}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   New Booking Modal
────────────────────────────────────────────────────────── */
function BookingModal({ slotInfo, vehicles = [], defaultBay = null, onClose, onCreated }) {
  const [form, setForm] = useState({
    vehicle_id: '',
    service_component: 'Oil Change',
    technician_name: TECHNICIANS[0].name,
    bay: defaultBay || ALL_BAYS[0].id,
    priority: 'P3',
    service_duration_hours: 1.5,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.vehicle_id) { setError('Please select a vehicle'); return; }
    setSaving(true); setError('');
    try {
      await axios.post(`${API}/api/bookings`, {
        ...form,
        slot_time_iso: slotInfo.startStr,
        status: 'CONFIRMED',
      });
      onCreated?.();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || `Error: ${err.message}`);
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={e => e.target === e.currentTarget && onClose()}>
      <motion.div
        initial={{ opacity: 0, scale: 0.93, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.93, y: 16 }}
        transition={spring}
        className="bg-white dark:bg-gray-900 rounded-3xl shadow-2xl w-full max-w-md p-6 border border-gray-100 dark:border-gray-700"
      >
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-base font-extrabold text-gray-900 dark:text-white">New Booking</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              {new Date(slotInfo.startStr).toLocaleString([], { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-white/5 transition-colors">
            <X size={16} className="text-gray-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className={labelCls}>Vehicle</label>
            <select className={selectCls} value={form.vehicle_id} onChange={e => set('vehicle_id', e.target.value)}>
              <option value="">Select vehicle…</option>
              {vehicles.map(v => (
                <option key={v.vehicle_id} value={v.vehicle_id}>
                  {v.vehicle_id} — {v.make} {v.model} ({v.year})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className={labelCls}>Service Type</label>
            <select className={selectCls} value={form.service_component} onChange={e => set('service_component', e.target.value)}>
              {SERVICE_TYPES.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Technician</label>
              <select className={selectCls} value={form.technician_name} onChange={e => set('technician_name', e.target.value)}>
                {TECHNICIANS.map(t => <option key={t.id} value={t.name}>{t.name}</option>)}
              </select>
            </div>
            <div>
              <label className={labelCls}>Bay</label>
              <select className={selectCls} value={form.bay} onChange={e => set('bay', e.target.value)}>
                {ALL_BAYS.map(b => <option key={b.id} value={b.id}>{b.label} — {b.spec}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Priority</label>
              <div className="flex gap-1.5 flex-wrap">
                {PRIORITIES.map(p => {
                  const c = PRIORITY_COLORS[p];
                  return (
                    <button key={p} type="button" onClick={() => set('priority', p)}
                      className="px-2.5 py-1 rounded-lg text-xs font-bold border-2 transition-all"
                      style={form.priority === p
                        ? { background: c.bg, borderColor: c.border, color: c.text }
                        : { borderColor: '#e5e7eb', color: '#6b7280', background: 'transparent' }}>
                      {p}
                    </button>
                  );
                })}
              </div>
            </div>
            <div>
              <label className={labelCls}>Duration (hrs)</label>
              <input type="number" min={0.5} max={8} step={0.5}
                className={selectCls}
                value={form.service_duration_hours}
                onChange={e => set('service_duration_hours', parseFloat(e.target.value))} />
            </div>
          </div>

          {error && <p className="text-xs text-red-500 bg-red-50 dark:bg-red-900/20 rounded-xl px-3 py-2">{error}</p>}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 rounded-xl border border-gray-200 dark:border-gray-600 text-sm font-semibold text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={saving}
              className="flex-1 py-2.5 rounded-xl bg-[#6366f1] text-white text-sm font-bold hover:bg-[#4f46e5] transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
              {saving ? <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" /> : <Save size={14} />}
              {saving ? 'Saving…' : 'Create Booking'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────
   Event Drawer — full edit
────────────────────────────────────────────────────────── */
function EventDrawer({ booking, onClose, onRefresh }) {
  const [form, setForm] = useState({
    service_component: booking.service_component || 'General',
    technician_name: booking.technician_name || TECHNICIANS[0].name,
    bay: booking.bay || ALL_BAYS[0].id,
    priority: booking.priority || 'P3',
    status: booking.status || 'CONFIRMED',
    service_duration_hours: booking.service_duration_hours || 1.5,
    slot_time_iso: booking.slot_time_iso
      ? booking.slot_time_iso.slice(0, 16)
      : new Date().toISOString().slice(0, 16),
  });
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const c = PRIORITY_COLORS[form.priority] || PRIORITY_COLORS.P3;

  async function saveChanges() {
    setSaving(true); setError('');
    try {
      await axios.patch(`${API}/api/bookings/${booking.booking_id}`, {
        ...form,
        service_duration_hours: parseFloat(form.service_duration_hours),
        slot_time_iso: form.slot_time_iso + ':00',
      });
      onRefresh?.();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || `Error: ${err.message}`);
    } finally { setSaving(false); }
  }

  async function deleteBooking() {
    if (!window.confirm('Cancel this booking?')) return;
    setDeleting(true);
    try {
      await axios.delete(`${API}/api/bookings/${booking.booking_id}`);
      onRefresh?.();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || `Error: ${err.message}`);
    } finally { setDeleting(false); }
  }

  return (
    <motion.div
      initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }} transition={spring}
      className="fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-700 shadow-2xl z-50 flex flex-col"
    >
      <div className="px-5 pt-5 pb-4 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-start justify-between">
          <div>
            <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold mb-2"
              style={{ background: c.bg, color: c.text }}>{form.priority}</span>
            <h3 className="text-sm font-extrabold text-gray-900 dark:text-white">{booking.vehicle_id || '—'}</h3>
            <p className="text-xs text-gray-400 font-mono">{booking.booking_id}</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5">
            <X size={15} className="text-gray-400" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        <div>
          <label className={labelCls}>Date &amp; Time</label>
          <input type="datetime-local" className={selectCls}
            value={form.slot_time_iso} onChange={e => set('slot_time_iso', e.target.value)} />
        </div>

        <div>
          <label className={labelCls}>Service Type</label>
          <select className={selectCls} value={form.service_component} onChange={e => set('service_component', e.target.value)}>
            {SERVICE_TYPES.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>

        <div>
          <label className={labelCls}>Technician</label>
          <select className={selectCls} value={form.technician_name} onChange={e => set('technician_name', e.target.value)}>
            {TECHNICIANS.map(t => <option key={t.id} value={t.name}>{t.name} — {t.spec}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelCls}>Bay</label>
            <select className={selectCls} value={form.bay} onChange={e => set('bay', e.target.value)}>
              {ALL_BAYS.map(b => <option key={b.id} value={b.id}>{b.label}</option>)}
            </select>
          </div>
          <div>
            <label className={labelCls}>Duration (hrs)</label>
            <input type="number" min={0.5} max={8} step={0.5}
              className={selectCls}
              value={form.service_duration_hours}
              onChange={e => set('service_duration_hours', e.target.value)} />
          </div>
        </div>

        <div>
          <label className={labelCls}>Priority</label>
          <div className="flex gap-2">
            {PRIORITIES.map(p => {
              const pc = PRIORITY_COLORS[p];
              return (
                <button key={p} type="button" onClick={() => set('priority', p)}
                  className="flex-1 py-2 rounded-xl text-xs font-bold border-2 transition-all"
                  style={form.priority === p
                    ? { background: pc.bg, borderColor: pc.border, color: pc.text }
                    : { borderColor: '#e5e7eb', color: '#6b7280', background: 'transparent' }}>
                  {p}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <label className={labelCls}>Status</label>
          <div className="flex flex-col gap-1.5">
            {STATUS_STEPS.map(s => (
              <button key={s} onClick={() => set('status', s)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold border transition-all ${form.status === s
                    ? 'bg-[#6366f1]/10 border-[#6366f1] text-[#6366f1]'
                    : 'border-gray-200 dark:border-gray-600 text-gray-500 hover:border-gray-300'
                  }`}>
                {s === 'CONFIRMED' && <Clock size={12} />}
                {s === 'IN_PROGRESS' && <Wrench size={12} />}
                {s === 'COMPLETED' && <CheckCircle2 size={12} />}
                {s.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-xs text-red-500 bg-red-50 dark:bg-red-900/20 rounded-xl px-3 py-2">{error}</p>}
      </div>

      <div className="px-5 pb-5 pt-3 border-t border-gray-100 dark:border-gray-700 space-y-2">
        <button onClick={saveChanges} disabled={saving}
          className="w-full py-2.5 rounded-xl bg-[#6366f1] text-white text-sm font-bold hover:bg-[#4f46e5] transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
          {saving ? <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" /> : <Save size={14} />}
          Save Changes
        </button>
        <button onClick={deleteBooking} disabled={deleting}
          className="w-full py-2.5 rounded-xl border border-red-200 dark:border-red-900 text-red-500 text-sm font-semibold hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors flex items-center justify-center gap-2">
          {deleting ? <span className="animate-spin h-4 w-4 border-2 border-red-400 border-t-transparent rounded-full" /> : <Trash2 size={14} />}
          Cancel Booking
        </button>
      </div>
    </motion.div>
  );
}

/* ─────────────────────────────────────────────────────────
   Main BayCalendar — bay-filtered view
────────────────────────────────────────────────────────── */
export default function BayCalendar({ bookings = [], vehicles = [], onRefresh }) {
  const calRef = useRef(null);
  const [selectedBay, setSelectedBay] = useState('BAY-1');  // default first bay
  const [modalSlot, setModalSlot] = useState(null);
  const [drawerBooking, setDrawerBooking] = useState(null);

  /* Filter bookings to the selected bay (or all if null) */
  const filteredBookings = useMemo(() =>
    selectedBay
      ? bookings.filter(b => b.bay === selectedBay)
      : bookings,
    [bookings, selectedBay]
  );

  const events = useMemo(() =>
    filteredBookings.map(b => {
      const colors = PRIORITY_COLORS[b.priority] || PRIORITY_COLORS.P3;
      const start = b.slot_time_iso ? new Date(b.slot_time_iso) : new Date();
      const durMs = (b.service_duration_hours || 1.5) * 3_600_000;
      return {
        id: b.booking_id,
        title: `${b.vehicle_id} · ${(b.service_component || '').replace(/_/g, ' ')}`,
        start,
        end: new Date(start.getTime() + durMs),
        backgroundColor: colors.bg,
        borderColor: colors.border,
        textColor: colors.text,
        extendedProps: b,
      };
    }),
    [filteredBookings]
  );

  const handleEventDrop = useCallback(async (info) => {
    try {
      await axios.patch(`${API}/api/bookings/${info.event.id}`, { slot_time_iso: info.event.startStr });
      onRefresh?.();
    } catch { info.revert(); }
  }, [onRefresh]);

  const handleEventResize = useCallback(async (info) => {
    const dur = (info.event.end - info.event.start) / 3_600_000;
    try {
      await axios.patch(`${API}/api/bookings/${info.event.id}`, { service_duration_hours: dur });
      onRefresh?.();
    } catch { info.revert(); }
  }, [onRefresh]);

  const activeBayInfo = ALL_BAYS.find(b => b.id === selectedBay);
  const activeBayIdx = ALL_BAYS.findIndex(b => b.id === selectedBay);

  return (
    <>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={spring} className="space-y-5">

        {/* ── Bay status grid ── */}
        <BayStatusBar
          bookings={bookings}
          selectedBay={selectedBay}
          onSelectBay={bay => setSelectedBay(bay || 'BAY-1')}
        />

        {/* ── Active bay header ── */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Color bar matching bay grid */}
            <span className="inline-block w-3 h-3 rounded-full"
              style={{ background: BAY_COLORS[activeBayIdx] ?? '#6366f1' }} />
            <div>
              <h3 className="text-sm font-extrabold text-gray-900 dark:text-white">
                {activeBayInfo?.label ?? 'All Bays'}
              </h3>
              <p className="text-xs text-gray-400">{activeBayInfo?.spec}</p>
            </div>
            <span className="ml-2 text-xs font-semibold text-gray-400 bg-gray-100 dark:bg-white/5 px-2 py-0.5 rounded-full">
              {filteredBookings.length} booking{filteredBookings.length !== 1 ? 's' : ''}
            </span>
          </div>

          {/* Priority legend */}
          <div className="flex gap-3 items-center">
            {Object.entries(PRIORITY_COLORS).map(([p, c]) => (
              <span key={p} className="flex items-center gap-1 text-xs font-semibold text-gray-500">
                <span className="w-2 h-2 rounded-full" style={{ background: c.bg }} />{p}
              </span>
            ))}
            <span className="text-[11px] text-gray-400 flex items-center gap-1 ml-2">
              <AlertTriangle size={11} /> Drag to reschedule · Click slot to add
            </span>
          </div>
        </div>

        {/* ── Calendar ── */}
        <FullCalendar
          ref={calRef}
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'timeGridDay,timeGridWeek,dayGridMonth',
          }}
          slotMinTime="07:00:00"
          slotMaxTime="19:00:00"
          allDaySlot={false}
          height="auto"
          contentHeight={540}
          nowIndicator
          editable
          selectable
          selectMirror
          dayMaxEvents={6}
          events={events}
          eventDrop={handleEventDrop}
          eventResize={handleEventResize}
          select={info => setModalSlot(info)}
          eventClick={info => setDrawerBooking(info.event.extendedProps)}
          eventContent={arg => (
            <div className="px-1.5 py-0.5 text-[10px] leading-tight font-medium overflow-hidden h-full">
              <span className="font-bold block truncate">{arg.event.extendedProps.vehicle_id}</span>
              <span className="opacity-80 truncate block">
                {(arg.event.extendedProps.service_component || '').replace(/_/g, ' ')}
              </span>
              <span className="opacity-60">{arg.event.extendedProps.technician_name?.split(' ')[0]}</span>
            </div>
          )}
        />
      </motion.div>

      {/* ── Modals ── */}
      <AnimatePresence>
        {modalSlot && (
          <BookingModal key="modal" slotInfo={modalSlot} vehicles={vehicles}
            defaultBay={selectedBay}
            onClose={() => setModalSlot(null)}
            onCreated={() => { onRefresh?.(); setModalSlot(null); }} />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {drawerBooking && (
          <EventDrawer key="drawer" booking={drawerBooking}
            onClose={() => setDrawerBooking(null)}
            onRefresh={onRefresh} />
        )}
      </AnimatePresence>
    </>
  );
}
