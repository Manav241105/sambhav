import React, { useState, useEffect, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import axios from 'axios';
import { Truck, CalendarDays, MessageSquare, AlertTriangle } from 'lucide-react';
import DashboardLayout from '../../components/DashboardLayout';

import AlertBanner from '../../components/AlertBanner';
import LiveToast from '../../components/LiveToast';

const API = 'http://localhost:8000';
const spring = { type: 'spring', stiffness: 100, damping: 10 };
export { spring };

function latestTelem(telematics) {
    if (!telematics) return {};
    if (Array.isArray(telematics)) return telematics[telematics.length - 1] || {};
    return telematics;
}
export { latestTelem };

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
        axios.get(`${API}/api/vehicles/${selectedVehicle.vehicle_id}/manufacturing`)
            .then((r) => { if (!cancelled) setManufacturing(r.data); })
            .catch(() => { if (!cancelled) setManufacturing(null); })
            .finally(() => { if (!cancelled) setMfgLoading(false); });
        return () => { cancelled = true; };
    }, [selectedVehicle]);

    const dismissAlert = (i) => setAlerts((prev) => prev.filter((_, idx) => idx !== i));
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
    };

    return (
        <DashboardLayout title="Operations Dashboard">
            <LiveToast onEvent={fetchAll} />
            <AlertBanner alerts={alerts} onDismiss={dismissAlert} onClickAlert={selectFromAlert} />
            <Outlet context={ctx} />
        </DashboardLayout>
    );
}
