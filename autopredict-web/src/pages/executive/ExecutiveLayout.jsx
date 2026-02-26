import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Outlet } from 'react-router-dom';
import axios from 'axios';
import { DollarSign, Activity, ShieldAlert, Brain } from 'lucide-react';
import DashboardLayout from '../../components/DashboardLayout';
import LiveEventBus from '../../components/LiveEventBus';

const API = 'http://localhost:8000';
const HEALTH_COLORS = ['#22c55e', '#fbbf24', '#ef4444'];
const REVENUE_COLORS = ['#6366f1', '#38bdf8', '#a78bfa', '#fb923c', '#34d399', '#f472b6'];
const AVG_REPAIR_COST = 2800;

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
const HOURS = ['8am', '9am', '10am', '11am', '12pm', '1pm', '2pm', '3pm', '4pm', '5pm'];
const HEATMAP_DATA = DAYS.flatMap((day) =>
    HOURS.map((hour, hi) => {
        const base = [3, 8, 10, 9, 11, 12, 9, 8, 6, 4][hi];
        const val = Math.max(0, base + (day === 'Mon' || day === 'Fri' ? -2 : 1) + (hi < 2 || hi > 7 ? -2 : 0));
        return { day, hour, value: val };
    })
);

export default function ExecutiveLayout() {
    const [summary, setSummary] = useState(null);
    const [vehicles, setVehicles] = useState([]);
    const [monthly, setMonthly] = useState([]);
    const [mfgSummary, setMfgSummary] = useState(null);
    const [loading, setLoading] = useState(true);

    /* Phase 4 state */
    const [componentFailures, setComponentFailures] = useState([]);
    const [alertFunnel, setAlertFunnel] = useState([]);
    const [conversionByMake, setConversionByMake] = useState([]);
    const [kpiTrends, setKpiTrends] = useState([]);
    const [roiData, setRoiData] = useState([]);
    const [recallDetails, setRecallDetails] = useState({});
    const [recallHeatmap, setRecallHeatmap] = useState([]);

    const fetchAll = useCallback(async () => {
        try {
            const [sRes, vRes, mRes, mfgRes, cfRes, afRes, cmRes, kpiRes, roiRes, rdRes, rhRes] = await Promise.all([
                axios.get(`${API}/api/dashboard/summary`),
                axios.get(`${API}/api/vehicles`),
                axios.get(`${API}/api/analytics/monthly`),
                axios.get(`${API}/api/manufacturing/summary`),
                axios.get(`${API}/api/analytics/component-failure-rate`).catch(() => ({ data: [] })),
                axios.get(`${API}/api/analytics/alert-funnel`).catch(() => ({ data: [] })),
                axios.get(`${API}/api/analytics/conversion-by-make`).catch(() => ({ data: [] })),
                axios.get(`${API}/api/analytics/kpi-trends`).catch(() => ({ data: [] })),
                axios.get(`${API}/api/analytics/roi`).catch(() => ({ data: [] })),
                axios.get(`${API}/api/analytics/recall-details`).catch(() => ({ data: {} })),
                axios.get(`${API}/api/analytics/recall-heatmap`).catch(() => ({ data: [] })),
            ]);
            setSummary(sRes.data);
            setVehicles(Array.isArray(vRes.data) ? vRes.data : Object.values(vRes.data));
            setMonthly(mRes.data?.months || []);
            setMfgSummary(mfgRes.data);
            setComponentFailures(Array.isArray(cfRes.data) ? cfRes.data : []);
            setAlertFunnel(Array.isArray(afRes.data) ? afRes.data : []);
            setConversionByMake(Array.isArray(cmRes.data) ? cmRes.data : []);
            setKpiTrends(Array.isArray(kpiRes.data) ? kpiRes.data : []);
            setRoiData(Array.isArray(roiRes.data) ? roiRes.data : []);
            setRecallDetails(rdRes.data || {});
            setRecallHeatmap(Array.isArray(rhRes.data) ? rhRes.data : []);
        } catch (err) {
            console.error('Executive fetch error:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchAll();
        const id = setInterval(fetchAll, 30_000);
        return () => clearInterval(id);
    }, [fetchAll]);

    /* ── Derived data ─────────────────────────────────── */
    const costAvoidance = useMemo(() =>
        vehicles.reduce((s, v) => s + (v.failure_probability || 0) * AVG_REPAIR_COST, 0),
        [vehicles]);

    const healthPie = useMemo(() => {
        if (!summary) return [];
        const critical = summary.critical_vehicles || 0;
        const total = summary.total_vehicles || 10;
        const warning = vehicles.filter((v) => v.scenario === 'warning' || v.priority === 'P2').length;
        const normal = Math.max(0, total - critical - warning);
        return [{ name: 'Normal', value: normal }, { name: 'Warning', value: warning }, { name: 'Critical', value: critical }];
    }, [summary, vehicles]);

    const topAtRisk = useMemo(() =>
        [...vehicles].sort((a, b) => (b.failure_probability || 0) - (a.failure_probability || 0)).slice(0, 5),
        [vehicles]);

    const monthlyTrend = useMemo(() =>
        monthly.map((m) => ({
            ...m,
            acceptance_pct: Math.round((m.acceptance_rate || 0) * 100),
            conversion_pct: Math.round((m.conversion_rate || 0) * 100),
            escalation_pct: Math.round((m.escalation_rate || 0) * 100),
        })),
        [monthly]);

    const revenuePie = useMemo(() => {
        const components = {};
        vehicles.forEach((v) => {
            const comp = v.diagnosis?.predicted_component?.replace(/_/g, ' ') || 'General';
            components[comp] = (components[comp] || 0) + Math.round((v.failure_probability || 0.1) * 3200);
        });
        return Object.entries(components).map(([name, value]) => ({ name, value })).slice(0, 6);
    }, [vehicles]);

    const bigMetrics = [
        { label: 'Cost Avoidance', value: loading ? '—' : `$${Math.round(costAvoidance).toLocaleString()}`, sub: 'estimated savings this cycle', icon: DollarSign, color: 'text-emerald-400' },
        { label: 'AI Accuracy', value: loading ? '—' : `${Math.round((summary?.ai_accuracy || 0) * 100)}%`, sub: `${Math.round((summary?.fallback_rate || 0) * 100)}% fallback rate`, icon: Brain, color: 'text-[#6366f1]' },
        { label: 'Open Recalls', value: loading ? '—' : (mfgSummary?.total_open_recalls ?? 0), sub: `across ${mfgSummary?.vehicles_with_recalls?.length ?? 0} vehicles`, icon: ShieldAlert, color: 'text-orange-400' },
        { label: 'Fleet Health', value: loading ? '—' : `${summary?.total_vehicles ?? 0} vehicles`, sub: `${summary?.critical_vehicles ?? 0} critical`, icon: Activity, color: 'text-blue-400' },
    ];

    /* ── Derived Phase 4 data ────────────────────────── */
    const fleetHealthScore = useMemo(() => {
        if (!vehicles.length) return 0;
        const avg = vehicles.reduce((s, v) => s + (v.health_score ?? (1 - (v.failure_probability || 0))), 0) / vehicles.length;
        return Math.round(avg * 100);
    }, [vehicles]);

    const recallCompletion = useMemo(() => {
        return recallDetails?.completion || { remedied: 0, open: 0, in_progress: 0 };
    }, [recallDetails]);

    const recallTimeline = useMemo(() => {
        return recallDetails?.timeline || [];
    }, [recallDetails]);

    const ctx = {
        summary, vehicles, monthly, mfgSummary, loading,
        healthPie, topAtRisk, monthlyTrend, revenuePie, bigMetrics,
        HEALTH_COLORS, REVENUE_COLORS, DAYS, HOURS, HEATMAP_DATA,
        /* Phase 4 */
        fleetHealthScore, costAvoidance,
        componentFailures, alertFunnel, conversionByMake, kpiTrends,
        roiData, recallHeatmap, recallCompletion, recallTimeline,
    };

    return (
        <DashboardLayout title="Executive Dashboard">
            <LiveEventBus
                onDiagnosisUpdated={fetchAll}
                onVehicleUpdated={fetchAll}
                onAnyEvent={fetchAll}
            />
            <Outlet context={ctx} />
        </DashboardLayout>
    );
}
