import React, { useState, useCallback, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import axios from 'axios';
import { AlertTriangle, ShieldCheck, Users, Wrench } from 'lucide-react';
import DashboardLayout from '../../components/DashboardLayout';
import LiveEventBus from '../../components/LiveEventBus';

import { API_BASE } from '../../config';

const API = API_BASE;
export const tooltipStyle = { backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px', fontSize: 12, color: '#fff' };

export default function ManagerLayout() {
    const [summary, setSummary] = useState(null);
    const [bookings, setBookings] = useState([]);
    const [allBookings, setAllBookings] = useState([]);
    const [conversations, setConversations] = useState([]);
    const [mfgSummary, setMfgSummary] = useState(null);
    const [loading, setLoading] = useState(true);

    // Phase 3 analytics state
    const [agentPerformance, setAgentPerformance] = useState([]);
    const [conversationVolume, setConversationVolume] = useState([]);
    const [bookingFunnel, setBookingFunnel] = useState([]);
    const [escalationHeatmapData, setEscalationHeatmapData] = useState({ heatmap: [], days: [], hours: [] });
    const [escalationAnalytics, setEscalationAnalytics] = useState({ reasons_breakdown: [], sla_breach_risk: [], sla_breach_count: 0 });
    const [escalationTrend, setEscalationTrend] = useState([]);
    const [revenueAnalytics, setRevenueAnalytics] = useState([]);
    const [revenueByComponent, setRevenueByComponent] = useState([]);
    const [revenueForecastData, setRevenueForecastData] = useState([]);
    const [bayOccupancy, setBayOccupancy] = useState({ slots: [], bays: [] });
    const [serviceDuration, setServiceDuration] = useState([]);
    const [bookingVelocity, setBookingVelocity] = useState(null);

    const fetchAll = useCallback(async () => {
        try {
            const [sRes, bTodayRes, bAllRes, cRes, mRes,
                   agentRes, convoVolRes, funnelRes, escHeatRes, escAnalRes, escTrendRes,
                   revRes, revCompRes, revForecastRes, bayRes, svcDurRes, velRes] = await Promise.all([
                // Original fetches
                axios.get(`${API}/api/dashboard/summary`),
                axios.get(`${API}/api/bookings/today`),
                axios.get(`${API}/api/bookings`),
                axios.get(`${API}/api/conversations`),
                axios.get(`${API}/api/manufacturing/summary`),
                // Phase 3 fetches
                axios.get(`${API}/api/analytics/agent-performance`).catch(() => ({ data: { agents: [] } })),
                axios.get(`${API}/api/analytics/conversation-volume`).catch(() => ({ data: { days: [] } })),
                axios.get(`${API}/api/analytics/booking-funnel`).catch(() => ({ data: { funnel: [] } })),
                axios.get(`${API}/api/analytics/escalation-heatmap`).catch(() => ({ data: { heatmap: [], days: [], hours: [] } })),
                axios.get(`${API}/api/analytics/escalations`).catch(() => ({ data: { reasons_breakdown: [], sla_breach_risk: [], sla_breach_count: 0 } })),
                axios.get(`${API}/api/analytics/escalation-trend`).catch(() => ({ data: { weeks: [] } })),
                axios.get(`${API}/api/analytics/revenue`).catch(() => ({ data: { months: [] } })),
                axios.get(`${API}/api/analytics/revenue-by-component`).catch(() => ({ data: { components: [] } })),
                axios.get(`${API}/api/analytics/revenue-forecast`).catch(() => ({ data: { all: [] } })),
                axios.get(`${API}/api/analytics/bay-occupancy`).catch(() => ({ data: { slots: [], bays: [] } })),
                axios.get(`${API}/api/analytics/service-duration`).catch(() => ({ data: { components: [] } })),
                axios.get(`${API}/api/analytics/booking-velocity`).catch(() => ({ data: null })),
            ]);

            // Original state
            setSummary(sRes.data);
            setBookings(Array.isArray(bTodayRes.data) ? bTodayRes.data : []);
            setAllBookings(Array.isArray(bAllRes.data) ? bAllRes.data : []);
            setConversations(Array.isArray(cRes.data) ? cRes.data : []);
            setMfgSummary(mRes.data);

            // Phase 3 state
            setAgentPerformance(agentRes.data?.agents || []);
            setConversationVolume(convoVolRes.data?.days || []);
            setBookingFunnel(funnelRes.data?.funnel || []);
            setEscalationHeatmapData(escHeatRes.data || { heatmap: [], days: [], hours: [] });
            setEscalationAnalytics(escAnalRes.data || { reasons_breakdown: [], sla_breach_risk: [], sla_breach_count: 0 });
            setEscalationTrend(escTrendRes.data?.weeks || []);
            setRevenueAnalytics(revRes.data?.months || []);
            setRevenueByComponent(revCompRes.data?.components || []);
            setRevenueForecastData(revForecastRes.data?.all || []);
            setBayOccupancy(bayRes.data || { slots: [], bays: [] });
            setServiceDuration(svcDurRes.data?.components || []);
            setBookingVelocity(velRes.data);
        } catch (err) {
            console.error('Manager fetch error:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAll();
        const id = setInterval(fetchAll, 30_000);
        return () => clearInterval(id);
    }, [fetchAll]);

    /* ── Derived ──────────────────────────────────────── */
    const slaViolations = summary?.active_alerts ?? 0;

    const escalationQueue = React.useMemo(() => {
        const grouped = {};
        conversations.forEach((t) => {
            if (t.status === 'OPEN') {
                if (!grouped[t.vehicle_id]) grouped[t.vehicle_id] = { vehicle_id: t.vehicle_id, customer_name: t.customer_name || 'Unknown', channel: t.channel, turns: [] };
                grouped[t.vehicle_id].turns.push(t);
            }
        });
        return Object.values(grouped);
    }, [conversations]);

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
            const key = (b.slot_time_iso || b.created_at || '').slice(0, 7);
            if (!months[key]) months[key] = { month: key, confirmed: 0, pending: 0 };
            if (b.status === 'CONFIRMED') months[key].confirmed += 1;
            else months[key].pending += 1;
        });
        const live = Object.values(months);
        return live.length > 1 ? live : STABLE;
    }, [allBookings]);

    const sentimentData = React.useMemo(() => [
        { week: 'W1', positive: 68, neutral: 22, negative: 10 },
        { week: 'W2', positive: 72, neutral: 18, negative: 10 },
        { week: 'W3', positive: 65, neutral: 24, negative: 11 },
        { week: 'W4', positive: 79, neutral: 15, negative: 6 },
        { week: 'W5', positive: 74, neutral: 19, negative: 7 },
        { week: 'W6', positive: 81, neutral: 13, negative: 6 },
    ], []);

    const slaCompliance = React.useMemo(() => {
        const total = summary?.total_vehicles || 10;
        const critical = summary?.critical_vehicles || 0;
        const pct = Math.round(Math.max(0, ((total - critical) / total) * 100));
        return [{ name: 'SLA', value: pct, fill: pct >= 80 ? '#22c55e' : pct >= 60 ? '#fbbf24' : '#ef4444' }];
    }, [summary]);

    const timeline = React.useMemo(() =>
        [...bookings]
            .sort((a, b) => (a.slot_time_iso || '').localeCompare(b.slot_time_iso || ''))
            .map((b) => ({
                ...b,
                displayTime: b.slot_time_iso ? new Date(b.slot_time_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—',
            })),
        [bookings]);

    const statCards = [
        { label: 'SLA Violations', value: loading ? '—' : slaViolations, icon: AlertTriangle, color: 'text-red-400', sub: 'P0 alerts active' },
        { label: 'Active Escalations', value: loading ? '—' : escalationQueue.length, icon: ShieldCheck, color: 'text-orange-400', sub: 'open conversations' },
        { label: 'Manufacturing Defects', value: loading ? '—' : (mfgSummary?.total_dtc_codes ?? 0), icon: Wrench, color: 'text-amber-400', sub: `${mfgSummary?.total_open_recalls ?? 0} recalls open` },
        { label: 'Technicians Active', value: loading ? '—' : techWorkload.length, icon: Users, color: 'text-blue-400', sub: `${bookings.length} jobs today` },
    ];

    const ctx = {
        summary, bookings, allBookings, conversations, mfgSummary, loading,
        slaViolations, escalationQueue, techWorkload, revenuePipeline, sentimentData, slaCompliance, timeline, statCards,
        // Phase 3 analytics
        agentPerformance, conversationVolume, bookingFunnel,
        escalationHeatmapData, escalationAnalytics, escalationTrend,
        revenueAnalytics, revenueByComponent, revenueForecastData,
        bayOccupancy, serviceDuration, bookingVelocity,
    };

    return (
        <DashboardLayout title="Manager Dashboard">
            <LiveEventBus
                onBookingCreated={fetchAll}
                onConversationTurn={fetchAll}
                onAlertFired={fetchAll}
                onAnyEvent={fetchAll}
            />
            <Outlet context={ctx} />
        </DashboardLayout>
    );
}
