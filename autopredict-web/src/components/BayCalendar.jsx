import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';

const spring = { type: 'spring', stiffness: 100, damping: 10 };

/* ── Priority → event colour ─────────────────────── */
const PRIORITY_COLORS = {
  P0: { bg: '#ef4444', border: '#dc2626', text: '#fff' },
  P1: { bg: '#f97316', border: '#ea580c', text: '#fff' },
  P2: { bg: '#fbbf24', border: '#f59e0b', text: '#1f2937' },
  P3: { bg: '#caff42', border: '#a3e635', text: '#1f2937' },
};

/**
 * Bay Calendar — weekly view of service bay bookings using FullCalendar.
 *
 * Props:
 *   bookings — array of booking objects from GET /api/bookings/today
 *              { booking_id, vehicle_id, customer_name, slot_time_iso,
 *                technician_name, bay, service_component, service_duration_hours, priority, status }
 *   onEventClick(booking) — optional callback when a booking is clicked
 */
export default function BayCalendar({ bookings = [], onEventClick }) {
  const events = useMemo(() =>
    bookings.map((b) => {
      const colors = PRIORITY_COLORS[b.priority] || PRIORITY_COLORS.P3;
      const start = b.slot_time_iso ? new Date(b.slot_time_iso) : new Date();
      const durationMs = (b.service_duration_hours || 1.5) * 60 * 60 * 1000;
      const end = new Date(start.getTime() + durationMs);

      return {
        id: b.booking_id,
        title: `${b.bay || 'BAY'} · ${b.vehicle_id} — ${(b.service_component || '').replace(/_/g, ' ')}`,
        start,
        end,
        backgroundColor: colors.bg,
        borderColor: colors.border,
        textColor: colors.text,
        extendedProps: b,
      };
    }),
    [bookings]
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={spring}
      className="bay-calendar-wrapper"
    >
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin]}
        initialView="timeGridWeek"
        headerToolbar={{
          left: 'title',
          center: '',
          right: 'timeGridDay,timeGridWeek',
        }}
        slotMinTime="07:00:00"
        slotMaxTime="19:00:00"
        allDaySlot={false}
        height="auto"
        contentHeight={420}
        nowIndicator
        events={events}
        eventClick={(info) => {
          if (onEventClick) onEventClick(info.event.extendedProps);
        }}
        eventContent={(arg) => (
          <div className="px-1.5 py-0.5 text-[10px] leading-tight font-medium truncate">
            <span className="font-bold">{arg.event.extendedProps.bay}</span>
            {' · '}
            {arg.event.extendedProps.vehicle_id}
            <br />
            <span className="opacity-80">
              {(arg.event.extendedProps.service_component || '').replace(/_/g, ' ')}
            </span>
          </div>
        )}
      />
    </motion.div>
  );
}
