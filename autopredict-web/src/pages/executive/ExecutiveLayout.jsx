import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Outlet } from 'react-router-dom';
import api from '../../lib/api';
import { formatINR } from '../../lib/format';
import { DollarSign, Activity, ShieldAlert, Brain } from 'lucide-react';
import DashboardLayout from '../../components/DashboardLayout';
import LiveEventBus from '../../components/LiveEventBus';

const HEALTH_COLORS = ['#22c55e', '#fbbf24', '#ef4444'];

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
    const [costAvoidance, setCostAvoidance] = useState({ breakdown: [], total: 0 });

    const fetchAll = useCallback(async () => {
        try {
            const [sRes, vRes, mRes, mfgRes, cfRes, afRes, cmRes, kpiRes, roiRes, rdRes, rhRes, caRes] = await Promise.all([
                api.get(`/api/dashboard/summary`),
                api.get(`/api/vehicles`),
                api.get(`/api/analytics/monthly`),
                api.get(`/api/manufacturing/summary`),
                api.get(`/api/analytics/component-failure-rate`).catch(() => ({ data: [] })),
                api.get(`/api/analytics/alert-funnel`).catch(() => ({ data: [] })),
                api.get(`/api/analytics/conversion-by-make`).catch(() => ({ data: [] })),
                api.get(`/api/analytics/kpi-trends`).catch(() => ({ data: [] })),
                api.get(`/api/analytics/roi`).catch(() => ({ data: [] })),
                api.get(`/api/analytics/recall-details`).catch(() => ({ data: {} })),
                api.get(`/api/analytics/recall-heatmap`).catch(() => ({ data: [] })),
                api.get(`/api/analytics/cost-avoidance`).catch(() => ({ data: {} })),
            ]);
            setSummary(sRes.data);
            setVehicles(Array.isArray(vRes.data) ? vRes.data : Object.values(vRes.data));
            setMonthly(mRes.data?.months || []);
            setMfgSummary(mfgRes.data);
            setComponentFailures(cfRes.data?.components || []);
            setAlertFunnel(afRes.data?.funnel || []);
            setConversionByMake(cmRes.data?.makes || []);
            setKpiTrends(kpiRes.data?.kpis || []);
            setRoiData((roiRes.data?.months || []).map((r) => ({
                month: r.month, cost_avoidance: r.cost_avoided_inr,
                operating_cost: r.operating_cost_inr, net: r.net_roi_inr,
            })));
            setRecallDetails(rdRes.data || {});
            setRecallHeatmap(rhRes.data?.heatmap || []);
            setCostAvoidance({ breakdown: caRes.data?.breakdown || [], total: caRes.data?.total_cost_avoided_inr || 0 });
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

    const bigMetrics = [
        { label: 'Cost Avoidance', value: loading ? '—' : formatINR(costAvoidance.total), sub: 'expected, confirmed by workshop findings (6 months)', icon: DollarSign, color: 'text-emerald-400' },
        { label: 'AI Accuracy', value: loading ? '—' : (summary?.ai_accuracy != null ? `${Math.round(summary.ai_accuracy * 100)}%` : '—'), sub: `${summary?.ai_accuracy_sample ?? 0} workshop-verified jobs`, icon: Brain, color: 'text-[#6366f1]' },
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
        return { remedied: recallDetails?.remedied || 0, open: recallDetails?.open || 0, in_progress: 0 };
    }, [recallDetails]);

    const recallTimeline = useMemo(() => {
        const byCampaign = {};
        (recallDetails?.timeline || []).forEach((r) => {
            const c = (byCampaign[r.campaign] ||= { campaign: r.campaign, discovered: r.discovery_date, remedied_date: null, days: [], affected: 0 });
            c.affected += 1;
            if (r.discovery_date < c.discovered) c.discovered = r.discovery_date;
            if (r.remedy_date) {
                if (!c.remedied_date || r.remedy_date > c.remedied_date) c.remedied_date = r.remedy_date;
                c.days.push((new Date(r.remedy_date) - new Date(r.discovery_date)) / 86400000);
            }
        });
        return Object.values(byCampaign).map(({ days, ...c }) => ({
            ...c, days_to_remedy: days.length ? Math.round(days.reduce((a, b) => a + b, 0) / days.length) : null,
        }));
    }, [recallDetails]);

    const ctx = {
        summary, vehicles, monthly, mfgSummary, loading,
        healthPie, topAtRisk, monthlyTrend, bigMetrics,
        HEALTH_COLORS,
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
