import React, { useState, useEffect, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import api from '../../lib/api';
import { Truck, CalendarDays, MessageSquare, AlertTriangle } from 'lucide-react';
import DashboardLayout from '../../components/DashboardLayout';

import AlertBanner from '../../components/AlertBanner';
import LiveEventBus from '../../components/LiveEventBus';



export default function OperationsLayout() {
    const [vehicles, setVehicles] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [bookings, setBookings] = useState([]);
    const [conversations, setConversations] = useState([]);
    const [summary, setSummary] = useState(null);
    const [selectedVehicle, setSelectedVehicle] = useState(null);
    const [manufacturing, setManufacturing] = useState(null);
    const [mfgLoading, setMfgLoading] = useState(false);
    const [loading, setLoading] = useState(true);

    /* ── Phase 2 state ──────────────────────────────── */
    const [vehicleHistory, setVehicleHistory] = useState([]);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [serviceHistory, setServiceHistory] = useState([]);
    const [workloadData, setWorkloadData] = useState(null);
    const [fleetAnalytics, setFleetAnalytics] = useState(null);
    const [diagnosing, setDiagnosing] = useState(false);

    const fetchAll = useCallback(async () => {
        try {
            const [vRes, aRes, bRes, cRes, sRes, wRes, fRes] = await Promise.all([
                api.get(`/api/vehicles`),
                api.get(`/api/dashboard/alerts`),
                api.get(`/api/bookings/today`),
                api.get(`/api/conversations`),
                api.get(`/api/dashboard/summary`),
                api.get(`/api/analytics/workload`).catch(() => ({ data: null })),
                api.get(`/api/analytics/fleet`).catch(() => ({ data: null })),
            ]);
            setVehicles(Array.isArray(vRes.data) ? vRes.data : Object.values(vRes.data));
            setAlerts(Array.isArray(aRes.data) ? aRes.data : []);
            setBookings(Array.isArray(bRes.data) ? bRes.data : []);
            setConversations(Array.isArray(cRes.data) ? cRes.data : []);
            setSummary(sRes.data);
            if (wRes.data) setWorkloadData(wRes.data);
            if (fRes.data) setFleetAnalytics(fRes.data);
        } catch (err) {
            console.error('Ops fetch error:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAll();
        const id = setInterval(fetchAll, 30_000);
        return () => clearInterval(id);
    }, [fetchAll]);

    // Fetch manufacturing when vehicle is selected
    useEffect(() => {
        if (!selectedVehicle) { setManufacturing(null); return; }
        let cancelled = false;
        setMfgLoading(true);
        api.get(`/api/vehicles/${selectedVehicle.vehicle_id}/manufacturing`)
            .then((r) => { if (!cancelled) setManufacturing(r.data); })
            .catch(() => { if (!cancelled) setManufacturing(null); })
            .finally(() => { if (!cancelled) setMfgLoading(false); });
        return () => { cancelled = true; };
    }, [selectedVehicle]);

    /* ── Fetch vehicle history when a vehicle is selected ── */
    useEffect(() => {
        if (!selectedVehicle) { setVehicleHistory([]); return; }
        let cancelled = false;
        setHistoryLoading(true);
        api.get(`/api/vehicles/${selectedVehicle.vehicle_id}/history?days=7`)
            .then((r) => { if (!cancelled) setVehicleHistory(r.data?.history || []); })
            .catch(() => { if (!cancelled) setVehicleHistory([]); })
            .finally(() => { if (!cancelled) setHistoryLoading(false); });
        return () => { cancelled = true; };
    }, [selectedVehicle]);

    /* ── Workshop service history for the selected vehicle ── */
    useEffect(() => {
        if (!selectedVehicle) { setServiceHistory([]); return; }
        let cancelled = false;
        api.get(`/api/vehicles/${selectedVehicle.vehicle_id}/service-history?limit=10`)
            .then((r) => { if (!cancelled) setServiceHistory(r.data?.records || []); })
            .catch(() => { if (!cancelled) setServiceHistory([]); });
        return () => { cancelled = true; };
    }, [selectedVehicle]);

    /* ── Trigger AI diagnosis for a vehicle ──────────── */
    const triggerDiagnosis = useCallback(async (vehicleId) => {
        setDiagnosing(true);
        try {
            await api.post(`/api/vehicles/${vehicleId}/diagnose`);
            await fetchAll();
            const { data: refreshed } = await api.get(`/api/vehicles/${vehicleId}`);
            setSelectedVehicle(refreshed);
        } catch (err) {
            console.error('Diagnosis error:', err);
        } finally {
            setDiagnosing(false);
        }
    }, [fetchAll]);

    // Acknowledge on the server so the alert stays dismissed for everyone.
    const dismissAlert = async (alert) => {
        if (!alert?.id) return;
        try {
            await api.post(`/api/dashboard/alerts/${alert.id}/ack`);
            setAlerts((prev) => prev.filter((a) => a.id !== alert.id));
        } catch (err) {
            console.error('Acknowledge failed:', err);
        }
    };
    const selectFromAlert = (alert) => {
        const v = vehicles.find((v) => v.vehicle_id === alert.vehicle_id);
        if (v) setSelectedVehicle(v);
    };

    const statCards = [
        { label: 'Active Vehicles', value: summary?.total_vehicles ?? vehicles.length, icon: Truck, color: 'text-[#6366f1]' },
        { label: "Today's Bookings", value: summary?.total_bookings ?? bookings.length, icon: CalendarDays, color: 'text-blue-400' },
        { label: 'Open Conversations', value: summary?.total_conversations ?? conversations.length, icon: MessageSquare, color: 'text-purple-400' },
        { label: 'P0 Alerts', value: alerts.filter((a) => a.priority === 'P0').length, icon: AlertTriangle, color: 'text-red-400' },
    ];

    /* ── Derived chart data ─────────────────────────── */
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

    const telematicsTrend = React.useMemo(() => {
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        return days.map((d, i) => ({
            day: d,
            battery: +(12.2 + Math.sin(i * 0.8) * 0.3).toFixed(2),
            coolant: Math.round(88 + Math.sin(i * 0.5) * 4),
            oil: Math.round(44 + Math.cos(i * 0.7) * 3),
        }));
    }, []);

    const ctx = {
        vehicles, alerts, bookings, conversations, summary, loading,
        selectedVehicle, setSelectedVehicle, manufacturing, mfgLoading,
        dismissAlert, selectFromAlert, statCards, fleetHealthPie, telematicsTrend,
        /* Phase 2 */
        vehicleHistory, historyLoading, serviceHistory, workloadData, fleetAnalytics,
        diagnosing, triggerDiagnosis, fetchAll,
    };

    return (
        <DashboardLayout title="Operations Dashboard">
            <LiveEventBus
                onDiagnosisUpdated={fetchAll}
                onBookingCreated={fetchAll}
                onAlertFired={fetchAll}
                onVehicleUpdated={fetchAll}
                onConversationTurn={fetchAll}
            />
            <Outlet context={ctx} />
        </DashboardLayout>
    );
}
