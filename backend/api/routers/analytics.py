"""
Analytics — every number is computed from the database.

Definitions worth knowing
- Revenue: invoiced amount (`cost_inr`) of COMPLETED bookings, by completion month.
- Cost avoided (expected): for agent-initiated bookings where the workshop
  confirmed the predicted part was worn/failed,
  (breakdown cost - planned job cost) x chance the part would have failed,
  all from `vehicle_models.part_costs` for that part and model.
- ROI: cost avoided vs. PLATFORM_MONTHLY_COST_INR (configuration, not data).
- Agent performance: per outreach channel, from agent conversations.
Money is in whole rupees (`*_inr`).
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.deps import DB, Staff
from api.routers.dashboard import prediction_accuracy
from core.settings import get_settings
from db import models as m
from db.base import app_tz, iso_local, to_local, utcnow
from domain.parts import display

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

AGENT_CHANNELS = ("WHATSAPP", "SMS", "EMAIL", "VOICE_CALL", "APP")


# ── Time helpers ──────────────────────────────────────────────────────────────


def _now_local() -> datetime:
    return datetime.now(app_tz())


def _month_starts(n: int) -> list[datetime]:
    """Start of the last `n` calendar months (oldest first), app timezone."""
    first = _now_local().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    out = []
    for i in range(n - 1, -1, -1):
        y, mth = first.year, first.month - i
        while mth <= 0:
            mth += 12
            y -= 1
        out.append(first.replace(year=y, month=mth))
    return out


def _month_key(dt: datetime | None) -> str | None:
    return to_local(dt).strftime("%b %Y") if dt else None


def _day_start(d: date) -> datetime:
    return datetime.combine(d, datetime.min.time(), app_tz())


# ── Shared loaders ────────────────────────────────────────────────────────────


async def _completed_bookings(db: DB, since: datetime) -> list[m.Booking]:
    return (
        await db.scalars(
            select(m.Booking)
            .options(selectinload(m.Booking.vehicle).selectinload(m.Vehicle.vehicle_model))
            .where(m.Booking.status == "COMPLETED", m.Booking.completed_at >= since)
        )
    ).all()


async def _cost_avoided_items(db: DB, since: datetime) -> list[dict]:
    """Confirmed catches: agent booking + workshop found the predicted part worn/failed."""
    rows = (
        await db.execute(
            select(m.Booking, m.Prediction, m.ServiceItem)
            .join(m.Prediction, m.Booking.prediction_id == m.Prediction.id)
            .join(m.ServiceRecord, m.ServiceRecord.booking_id == m.Booking.id)
            .join(m.ServiceItem, m.ServiceItem.record_id == m.ServiceRecord.id)
            .options(selectinload(m.Booking.vehicle).selectinload(m.Vehicle.vehicle_model))
            .where(m.Booking.status == "COMPLETED", m.Booking.completed_at >= since, m.ServiceItem.finding.in_(("worn", "failed")))
        )
    ).all()
    items, seen = [], set()
    for booking, pred, item in rows:
        if item.part != pred.component or booking.id in seen:
            continue
        seen.add(booking.id)
        costs = booking.vehicle.vehicle_model.part_costs.get(item.part, {})
        avoided = round(max(0, costs.get("breakdown_inr", 0) - costs.get("service_inr", 0)) * costs.get("failure_probability", 0))
        items.append({"booking": booking, "prediction": pred, "part": item.part, "avoided": avoided})
    items.sort(key=lambda x: x["booking"].completed_at)
    return items


async def _agent_conversations(db: DB, since: datetime) -> list[m.Conversation]:
    return (
        await db.scalars(
            select(m.Conversation)
            .options(selectinload(m.Conversation.messages), selectinload(m.Conversation.vehicle).selectinload(m.Vehicle.vehicle_model))
            .where(m.Conversation.started_at >= since, m.Conversation.outcome.is_not(None))
        )
    ).all()


# ── Fleet & KPIs ──────────────────────────────────────────────────────────────


@router.get("/fleet")
async def fleet(current: Staff, db: DB) -> dict:
    preds = (await db.scalars(select(m.Prediction).where(m.Prediction.is_current.is_(True)))).all()
    total = len(preds)
    if total == 0:
        return {"total_vehicles": 0}
    rul = [p.rul_days for p in preds if p.component and p.rul_days is not None]
    statuses = Counter((await db.scalars(select(m.Booking.status).where(m.Booking.status != "CANCELLED"))).all())
    bookings_total = sum(statuses.values())
    pr = Counter(p.priority for p in preds)
    return {
        "total_vehicles": total,
        "critical": pr["P0"] + pr["P1"],
        "warning": pr["P2"],
        "healthy": pr["P3"],
        "avg_health_score": round(sum(p.health_score for p in preds) / total, 2),
        "avg_rul_days": round(sum(rul) / len(rul), 1) if rul else None,
        "rul_distribution": {
            "under_7": sum(1 for r in rul if r < 7),
            "7_to_30": sum(1 for r in rul if 7 <= r <= 30),
            "over_30": sum(1 for r in rul if r > 30),
        },
        "bookings_total": bookings_total,
        "bookings_completed": statuses["COMPLETED"],
        "bookings_pending": statuses["CONFIRMED"] + statuses["PENDING"],
        "service_completion_rate": round(statuses["COMPLETED"] / bookings_total, 2) if bookings_total else 0,
    }


@router.get("/kpi-trends")
async def kpi_trends(current: Staff, db: DB) -> dict:
    """Last 30 days vs. the 30 days before."""
    now = utcnow()
    cut, prev_cut = now - timedelta(days=30), now - timedelta(days=60)

    preds = (
        await db.execute(
            select(
                m.Prediction.vehicle_id, m.Prediction.created_at, m.Prediction.health_score, m.Prediction.rul_days, m.Prediction.component
            )
        )
    ).all()
    latest_now, latest_prev = {}, {}
    for vid, at, health, rul, comp in sorted(preds, key=lambda r: r[1]):
        latest_now[vid] = (health, rul, comp)
        if at <= cut:
            latest_prev[vid] = (health, rul, comp)

    def avg_health(d):
        return round(sum(h for h, _, _ in d.values()) / len(d), 2) if d else 0

    def avg_rul(d):
        vals = [r for _, r, c in d.values() if c and r is not None]
        return round(sum(vals) / len(vals), 1) if vals else 0

    bookings = (await db.execute(select(m.Booking.slot_start, m.Booking.status, m.Booking.completed_at))).all()

    def completion(lo, hi):
        due = [s for start, s, _ in bookings if lo <= start < hi and s in ("COMPLETED", "NO_SHOW", "CANCELLED")]
        return round(100 * sum(1 for s in due if s == "COMPLETED") / len(due), 1) if due else 0

    def count_completed(lo, hi):
        return sum(1 for _, s, c in bookings if s == "COMPLETED" and c and lo <= c < hi)

    def count_booked(lo, hi):
        return sum(1 for start, s, _ in bookings if s != "CANCELLED" and lo <= start < hi)

    alerts = (await db.scalars(select(m.Alert.fired_at))).all()

    def count_alerts(lo, hi):
        return sum(1 for a in alerts if lo <= a < hi)

    kpis = [
        {
            "kpi": "Avg Health Score",
            "current": avg_health(latest_now),
            "previous": avg_health(latest_prev),
            "unit": "",
            "higher_is_better": True,
        },
        {
            "kpi": "Service Completion",
            "current": completion(cut, now),
            "previous": completion(prev_cut, cut),
            "unit": "%",
            "higher_is_better": True,
        },
        {
            "kpi": "Alerts (30d)",
            "current": count_alerts(cut, now),
            "previous": count_alerts(prev_cut, cut),
            "unit": "",
            "higher_is_better": False,
        },
        {
            "kpi": "Services Completed (30d)",
            "current": count_completed(cut, now),
            "previous": count_completed(prev_cut, cut),
            "unit": "",
            "higher_is_better": True,
        },
        {
            "kpi": "Bookings (30d)",
            "current": count_booked(cut, now),
            "previous": count_booked(prev_cut, cut),
            "unit": "",
            "higher_is_better": True,
        },
        {"kpi": "Avg RUL", "current": avg_rul(latest_now), "previous": avg_rul(latest_prev), "unit": "d", "higher_is_better": True},
    ]
    for k in kpis:
        diff = k["current"] - k["previous"]
        k["delta"] = round(diff, 2)
        k["delta_pct"] = round(diff / abs(k["previous"]) * 100, 1) if k["previous"] else 0
        k["is_positive"] = diff == 0 or (diff > 0) == k["higher_is_better"]
    return {"kpis": kpis, "window_days": 30}


@router.get("/executive-summary")
async def executive_summary(current: Staff, db: DB) -> dict:
    preds = (await db.scalars(select(m.Prediction).options().where(m.Prediction.is_current.is_(True)))).all()
    codes = dict((await db.execute(select(m.Vehicle.id, m.Vehicle.code))).all())
    total = len(preds)
    pr = Counter(p.priority for p in preds)
    critical = [p for p in preds if p.priority in ("P0", "P1")]
    month_start = _month_starts(1)[0]
    done = await _completed_bookings(db, month_start)
    accuracy, sample = await prediction_accuracy(db)
    upcoming = sum(1 for s in (await db.scalars(select(m.Booking.status))).all() if s == "CONFIRMED")
    urgent_rul = sum(1 for p in preds if p.component and p.rul_days is not None and p.rul_days < 7)
    parts = Counter(display(p.component) for p in critical)

    text = (
        f"{total} vehicles monitored: {pr['P0'] + pr['P1']} need attention now, {pr['P2']} soon, {pr['P3']} healthy. "
        f"{len(done)} services completed this month, {upcoming} upcoming. "
    )
    if parts:
        text += "Most urgent parts: " + ", ".join(f"{n} {c.lower()}" for c, n in parts.most_common(3)) + ". "
        text += f"Priority vehicles: {', '.join(codes[p.vehicle_id] for p in critical[:3])}. "
    if urgent_rul:
        text += f"{urgent_rul} vehicle(s) have under 7 days of estimated life left on a part. "
    if accuracy is not None:
        text += f"Workshop findings confirmed {round(accuracy * 100)}% of agent-flagged issues ({sample} jobs)."
    return {"summary": text.strip(), "generated_at": iso_local(utcnow()), "method": "template_over_aggregates"}


# ── Money ─────────────────────────────────────────────────────────────────────


@router.get("/revenue")
async def revenue(current: Staff, db: DB) -> dict:
    months = _month_starts(6)
    done = await _completed_bookings(db, months[0])
    avoided = await _cost_avoided_items(db, months[0])
    rev, av = defaultdict(int), defaultdict(int)
    for b in done:
        rev[_month_key(b.completed_at)] += b.cost_inr or 0
    for x in avoided:
        av[_month_key(x["booking"].completed_at)] += x["avoided"]
    out = []
    for mstart in months:
        k = mstart.strftime("%b %Y")
        out.append({"month": k, "revenue_inr": rev[k], "cost_avoidance_inr": av[k], "net_value_inr": rev[k] + av[k]})
    return {"months": out, "currency": "INR"}


@router.get("/revenue-by-component")
async def revenue_by_component(current: Staff, db: DB, months: int = Query(6, ge=1, le=24)) -> dict:
    done = await _completed_bookings(db, _month_starts(months)[0])
    by = defaultdict(int)
    for b in done:
        by[b.service_component] += b.cost_inr or 0
    return {"components": [{"component": c, "revenue_inr": v} for c, v in sorted(by.items(), key=lambda x: -x[1])], "currency": "INR"}


@router.get("/revenue-forecast")
async def revenue_forecast(current: Staff, db: DB) -> dict:
    """Six months of actuals plus a 3-month least-squares linear trend."""
    months = _month_starts(6)
    rev = (await revenue(current, db))["months"]
    hist = [{"month": r["month"], "revenue_inr": r["revenue_inr"], "type": "actual"} for r in rev]
    # Fit on complete months only (the current month is partial).
    ys = [r["revenue_inr"] for r in hist[:-1]]
    xs = list(range(len(ys)))
    forecast = []
    if len(ys) >= 3:
        slope, intercept = statistics.linear_regression(xs, ys)
        for i in range(1, 4):
            y, mth = months[-1].year, months[-1].month + i
            while mth > 12:
                mth -= 12
                y += 1
            label = months[-1].replace(year=y, month=mth).strftime("%b %Y")
            forecast.append({"month": label, "revenue_inr": max(0, round(intercept + slope * (len(ys) - 1 + i))), "type": "forecast"})
    return {"historical": hist, "forecast": forecast, "all": hist + forecast, "method": "linear_trend", "currency": "INR"}


@router.get("/cost-avoidance")
async def cost_avoidance(current: Staff, db: DB, months: int = Query(6, ge=1, le=24)) -> dict:
    items = await _cost_avoided_items(db, _month_starts(months)[0])
    breakdown, cumulative = [], 0
    for x in items:
        cumulative += x["avoided"]
        breakdown.append(
            {
                "vehicle_id": x["booking"].vehicle.code,
                "component": display(x["part"]),
                "severity": x["prediction"].severity,
                "cost_avoided_inr": x["avoided"],
                "cumulative_inr": cumulative,
                "completed_at": iso_local(x["booking"].completed_at),
            }
        )
    return {
        "total_cost_avoided_inr": cumulative,
        "vehicles_saved": len({b["vehicle_id"] for b in breakdown}),
        "breakdown": breakdown,
        "currency": "INR",
    }


@router.get("/roi")
async def roi(current: Staff, db: DB) -> dict:
    monthly_cost = get_settings().platform_monthly_cost_inr
    months = _month_starts(6)
    av = defaultdict(int)
    for x in await _cost_avoided_items(db, months[0]):
        av[_month_key(x["booking"].completed_at)] += x["avoided"]
    rows = []
    for mstart in months:
        k = mstart.strftime("%b %Y")
        rows.append(
            {
                "month": k,
                "cost_avoided_inr": av[k],
                "operating_cost_inr": monthly_cost,
                "net_roi_inr": av[k] - monthly_cost,
                "roi_ratio": round(av[k] / monthly_cost, 2) if monthly_cost else None,
            }
        )
    saved, cost = sum(r["cost_avoided_inr"] for r in rows), monthly_cost * len(rows)
    return {
        "months": rows,
        "total_cost_avoided_inr": saved,
        "total_operating_cost_inr": cost,
        "net_roi_inr": saved - cost,
        "overall_roi_ratio": round(saved / cost, 2) if cost else None,
        "operating_cost_source": "PLATFORM_MONTHLY_COST_INR",
        "currency": "INR",
    }


@router.get("/monthly")
async def monthly(current: Staff, db: DB) -> dict:
    months = _month_starts(6)
    since = months[0]
    bookings = (
        await db.execute(
            select(m.Booking.slot_start, m.Booking.status, m.Booking.vehicle_id, m.Booking.actual_duration_hours).where(
                m.Booking.slot_start >= since, m.Booking.status != "CANCELLED"
            )
        )
    ).all()
    convs = (
        await db.execute(
            select(m.Conversation.started_at, m.Conversation.outcome).where(
                m.Conversation.started_at >= since, m.Conversation.outcome.is_not(None)
            )
        )
    ).all()
    preds = (
        await db.execute(
            select(m.Prediction.created_at, m.Prediction.rul_days).where(
                m.Prediction.created_at >= since, m.Prediction.component.is_not(None)
            )
        )
    ).all()
    av = defaultdict(int)
    for x in await _cost_avoided_items(db, since):
        av[_month_key(x["booking"].completed_at)] += x["avoided"]

    out = []
    for mstart in months:
        k = mstart.strftime("%b %Y")
        mb = [b for b in bookings if _month_key(b[0]) == k]
        mc = [c for c in convs if _month_key(c[0]) == k]
        mp = [r for at, r in preds if _month_key(at) == k and r is not None]
        out.append(
            {
                "month": k,
                "bookings": len(mb),
                "acceptance_rate": round(sum(1 for _, o in mc if o == "BOOKED") / len(mc), 2) if mc else None,
                "avg_rul_days": round(sum(mp) / len(mp)) if mp else None,
                "cost_avoidance_inr": av[k],
                "vehicles_serviced": len({v for _, s, v, _d in mb if s == "COMPLETED"}),
                "avg_service_hours": round(statistics.mean(d for _, s, _v, d in mb if s == "COMPLETED" and d), 2)
                if any(s == "COMPLETED" and d for _, s, _v, d in mb)
                else None,
                # Booked jobs that were actually carried out, and outreach handed to a human.
                "conversion_rate": round(sum(1 for _, s, _v, _d in mb if s == "COMPLETED") / len(mb), 2) if mb else None,
                "escalation_rate": round(sum(1 for _, o in mc if o == "ESCALATED") / len(mc), 2) if mc else None,
            }
        )
    return {"months": out, "currency": "INR"}


# ── Workshop operations ───────────────────────────────────────────────────────


async def _bookings_on(db: DB, day: date) -> list[m.Booking]:
    return (
        await db.scalars(
            select(m.Booking)
            .options(selectinload(m.Booking.technician), selectinload(m.Booking.bay), selectinload(m.Booking.vehicle))
            .where(
                m.Booking.status != "CANCELLED",
                m.Booking.slot_start >= _day_start(day),
                m.Booking.slot_start < _day_start(day + timedelta(days=1)),
            )
        )
    ).all()


@router.get("/workload")
async def workload(current: Staff, db: DB, day: date | None = Query(None, alias="date")) -> dict:
    day = day or _now_local().date()
    ws = await db.scalar(select(m.Workshop).limit(1))
    day_hours = (ws.close_hour - ws.open_hour) if ws else 10
    tech_h, bay_h = defaultdict(float), defaultdict(float)
    for b in await _bookings_on(db, day):
        hours = b.actual_duration_hours or b.duration_hours
        tech_h[b.technician.name if b.technician else "Unassigned"] += hours
        bay_h[b.bay.code if b.bay else "Unassigned"] += hours
    fmt = lambda d, key: [
        {key: k, "hours_booked": round(h, 1), "utilisation": round(min(h / day_hours, 1.0), 2)}
        for k, h in sorted(d.items(), key=lambda x: -x[1])
    ]
    return {"date": day.isoformat(), "technicians": fmt(tech_h, "name"), "bays": fmt(bay_h, "bay")}


@router.get("/bay-occupancy")
async def bay_occupancy(current: Staff, db: DB, day: date | None = Query(None, alias="date")) -> dict:
    day = day or _now_local().date()
    slots = []
    for b in await _bookings_on(db, day):
        start = to_local(b.slot_start)
        dur = b.actual_duration_hours or b.duration_hours
        slots.append(
            {
                "bay": b.bay.code if b.bay else "Unassigned",
                "vehicle_id": b.vehicle.code,
                "technician": b.technician.name if b.technician else "Unassigned",
                "start_hour": round(start.hour + start.minute / 60, 2),
                "end_hour": round(start.hour + start.minute / 60 + dur, 2),
                "duration_hours": dur,
                "priority": b.priority,
                "component": b.service_component,
                "status": b.status,
            }
        )
    slots.sort(key=lambda s: (s["bay"], s["start_hour"]))
    return {"date": day.isoformat(), "slots": slots, "bays": sorted({s["bay"] for s in slots})}


@router.get("/service-duration")
async def service_duration(current: Staff, db: DB) -> dict:
    done = await _completed_bookings(db, utcnow() - timedelta(days=180))
    by = defaultdict(list)
    for b in done:
        if b.actual_duration_hours:
            by[b.service_component].append(b.actual_duration_hours)
    out = []
    for comp, vals in sorted(by.items()):
        if len(vals) < 3:
            continue
        q = statistics.quantiles(vals, n=4)
        out.append(
            {
                "component": comp,
                "min": round(min(vals), 1),
                "q1": round(q[0], 1),
                "median": round(statistics.median(vals), 1),
                "q3": round(q[2], 1),
                "max": round(max(vals), 1),
                "count": len(vals),
                "values": [round(v, 1) for v in sorted(vals)][:200],
            }
        )
    return {"components": out}


@router.get("/booking-velocity")
async def booking_velocity(current: Staff, db: DB) -> dict:
    """Bookings created so far today vs. the same hours on the same weekday last week."""
    now = _now_local()
    today0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week0 = today0 - timedelta(days=7)
    created = (await db.scalars(select(m.Booking.created_at).where(m.Booking.created_at >= week0))).all()
    elapsed = now - today0
    today_n = sum(1 for c in created if c >= today0)
    last_n = sum(1 for c in created if week0 <= c < week0 + elapsed)
    hours = max(elapsed.total_seconds() / 3600, 1)
    v_today, v_last = round(today_n / hours, 2), round(last_n / hours, 2)
    return {
        "today_total": today_n,
        "same_time_last_week": last_n,
        "velocity_per_hour_today": v_today,
        "velocity_per_hour_last_week": v_last,
        "delta_pct": round((v_today - v_last) / v_last * 100, 1) if v_last else None,
    }


# ── Engagement ────────────────────────────────────────────────────────────────


@router.get("/conversation-volume")
async def conversation_volume(current: Staff, db: DB, days: int = Query(30, ge=7, le=90)) -> dict:
    since = _day_start(_now_local().date() - timedelta(days=days - 1))
    msgs = (await db.execute(select(m.Message.created_at, m.Message.direction).where(m.Message.created_at >= since))).all()
    daily = {(since + timedelta(days=i)).date().isoformat(): {"inbound": 0, "outbound": 0} for i in range(days)}
    for at, direction in msgs:
        key = to_local(at).date().isoformat()
        if key in daily:
            daily[key]["inbound" if direction == "INBOUND" else "outbound"] += 1
    return {"days": [{"date": d, **v, "total": v["inbound"] + v["outbound"]} for d, v in daily.items()]}


@router.get("/agent-performance")
async def agent_performance(current: Staff, db: DB, days: int = Query(90, ge=7, le=365)) -> dict:
    """Per outreach channel, all values 0-100."""
    convs = await _agent_conversations(db, utcnow() - timedelta(days=days))
    by = defaultdict(list)
    for c in convs:
        by[c.channel].append(c)
    out = []
    for channel, cs in sorted(by.items()):
        n = len(cs)
        booked = [c for c in cs if c.outcome == "BOOKED"]
        inbound = [msg for c in cs for msg in c.messages if msg.direction == "INBOUND"]
        fast_booked = sum(1 for c in booked if c.closed_at and c.closed_at - c.started_at <= timedelta(hours=24))
        quick_replies = 0
        for c in cs:
            first_out = next((x for x in c.messages if x.direction == "OUTBOUND"), None)
            first_in = next((x for x in c.messages if x.direction == "INBOUND"), None)
            if first_out and first_in and first_in.created_at - first_out.created_at <= timedelta(hours=4):
                quick_replies += 1
        out.append(
            {
                "agent": channel.replace("_", " ").title(),
                "channel": channel,
                "conversations": n,
                "conversion": round(100 * len(booked) / n),
                "escalation": round(100 * sum(1 for c in cs if c.outcome == "ESCALATED") / n),
                "booking_velocity": round(100 * fast_booked / len(booked)) if booked else 0,
                "sentiment": round(100 * sum(1 for x in inbound if x.sentiment in ("POSITIVE", "NEUTRAL")) / len(inbound))
                if inbound
                else 0,
                "response_time": round(100 * quick_replies / n),
            }
        )
    return {
        "agents": out,
        "window_days": days,
        "definitions": {
            "conversion": "% conversations ending in a booking",
            "escalation": "% handed to a human",
            "booking_velocity": "% of bookings made within 24 h",
            "sentiment": "% customer replies not negative",
            "response_time": "% customers replying within 4 h",
        },
    }


@router.get("/booking-funnel")
async def booking_funnel(current: Staff, db: DB, days: int = Query(90, ge=7, le=365)) -> dict:
    since = utcnow() - timedelta(days=days)
    flagged = set(
        (
            await db.scalars(
                select(m.Prediction.vehicle_id).where(m.Prediction.created_at >= since, m.Prediction.priority.in_(("P0", "P1", "P2")))
            )
        ).all()
    )
    contacted = (
        set(
            (
                await db.scalars(
                    select(m.Conversation.vehicle_id).where(m.Conversation.started_at >= since, m.Conversation.outcome.is_not(None))
                )
            ).all()
        )
        & flagged
    )
    bookings = (
        await db.execute(
            select(m.Booking.vehicle_id, m.Booking.status).where(m.Booking.created_at >= since, m.Booking.status != "CANCELLED")
        )
    ).all()
    booked = {v for v, _ in bookings} & contacted
    serviced = {v for v, s in bookings if s == "COMPLETED"} & booked
    return {
        "funnel": [
            {"stage": "Flagged", "count": len(flagged)},
            {"stage": "Contacted", "count": len(contacted)},
            {"stage": "Booked", "count": len(booked)},
            {"stage": "Serviced", "count": len(serviced)},
        ],
        "window_days": days,
    }


@router.get("/alert-funnel")
async def alert_funnel(current: Staff, db: DB, days: int = Query(90, ge=7, le=365)) -> dict:
    since = utcnow() - timedelta(days=days)
    alerts = (
        await db.execute(select(m.Alert.vehicle_id, m.Alert.acknowledged_at, m.Alert.fired_at).where(m.Alert.fired_at >= since))
    ).all()
    fired = {v for v, _, _ in alerts}
    acked = {v for v, a, _ in alerts if a}
    first_alert = {}
    for v, _, at in alerts:
        first_alert[v] = min(first_alert.get(v, at), at)
    bookings = (
        await db.execute(
            select(m.Booking.vehicle_id, m.Booking.status, m.Booking.created_at).where(
                m.Booking.created_at >= since, m.Booking.status != "CANCELLED"
            )
        )
    ).all()
    booked = {v for v, _, c in bookings if v in first_alert and c >= first_alert[v]}
    serviced = {v for v, s, c in bookings if s == "COMPLETED" and v in booked}
    return {
        "funnel": [
            {"stage": "Alerts Fired", "count": len(fired)},
            {"stage": "Acknowledged", "count": len(acked)},
            {"stage": "Booked", "count": len(booked)},
            {"stage": "Serviced", "count": len(serviced)},
        ],
        "window_days": days,
    }


@router.get("/conversion-by-make")
async def conversion_by_make(current: Staff, db: DB, days: int = Query(180, ge=7, le=365)) -> dict:
    convs = await _agent_conversations(db, utcnow() - timedelta(days=days))
    fleet = Counter((await db.scalars(select(m.VehicleModel.make).join(m.Vehicle, m.Vehicle.model_id == m.VehicleModel.id))).all())
    contacted, booked = defaultdict(set), defaultdict(set)
    for c in convs:
        make = c.vehicle.vehicle_model.make
        contacted[make].add(c.vehicle_id)
        if c.outcome == "BOOKED":
            booked[make].add(c.vehicle_id)
    return {
        "makes": [
            {
                "make": make,
                "total_vehicles": n,
                "contacted": len(contacted[make]),
                "booked": len(booked[make]),
                "conversion_pct": round(100 * len(booked[make]) / len(contacted[make]), 1) if contacted[make] else 0,
            }
            for make, n in sorted(fleet.items())
        ],
        "window_days": days,
    }


@router.get("/escalations")
async def escalations(current: Staff, db: DB, days: int = Query(30, ge=7, le=365)) -> dict:
    since = utcnow() - timedelta(days=days)
    convs = (await db.execute(select(m.Conversation.status, m.Conversation.escalated_at).where(m.Conversation.started_at >= since))).all()
    escalated = sum(1 for _, e in convs if e)
    alerts = (await db.scalars(select(m.Alert).where(m.Alert.acknowledged_at.is_(None)))).all()
    reasons = Counter(display(a.component) for a in alerts)

    active = set(
        (await db.scalars(select(m.Booking.vehicle_id).where(m.Booking.status.in_(("PENDING", "CONFIRMED", "IN_PROGRESS"))))).all()
    )
    risky = (
        await db.execute(
            select(m.Prediction, m.Vehicle.code)
            .join(m.Vehicle, m.Prediction.vehicle_id == m.Vehicle.id)
            .where(m.Prediction.is_current.is_(True), m.Prediction.component.is_not(None), m.Prediction.rul_days < 7)
        )
    ).all()
    sla = [
        {"vehicle_id": code, "rul_days": p.rul_days, "priority": p.priority, "component": p.component}
        for p, code in risky
        if p.vehicle_id not in active
    ]
    return {
        "total_alerts": len(alerts),
        "escalated_conversations": escalated,
        "escalation_rate": round(escalated / len(convs), 2) if convs else 0,
        "reasons_breakdown": [{"reason": r, "count": c} for r, c in reasons.most_common()],
        "sla_breach_risk": sla,
        "sla_breach_count": len(sla),
        "window_days": days,
    }


@router.get("/escalation-heatmap")
async def escalation_heatmap(current: Staff, db: DB, days: int = Query(90, ge=7, le=365)) -> dict:
    days_lbl = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = list(range(8, 22))
    times = (
        await db.scalars(select(m.Conversation.escalated_at).where(m.Conversation.escalated_at >= utcnow() - timedelta(days=days)))
    ).all()
    counts = Counter((to_local(t).weekday(), to_local(t).hour) for t in times)
    cells = [{"day": days_lbl[d], "hour": h, "count": counts[(d, h)]} for d in range(7) for h in hours]
    return {"heatmap": cells, "days": days_lbl, "hours": hours, "window_days": days}


@router.get("/escalation-trend")
async def escalation_trend(current: Staff, db: DB, weeks: int = Query(8, ge=2, le=26)) -> dict:
    start = _day_start(_now_local().date() - timedelta(days=_now_local().weekday() + 7 * (weeks - 1)))
    rows = (
        await db.execute(select(m.Conversation.escalated_at, m.Conversation.resolved_at).where(m.Conversation.escalated_at >= start))
    ).all()
    out = []
    for i in range(weeks):
        lo, hi = start + timedelta(weeks=i), start + timedelta(weeks=i + 1)
        out.append(
            {
                "week": f"W{lo.isocalendar()[1]}",
                "week_start": lo.date().isoformat(),
                "escalations": sum(1 for e, _ in rows if lo <= e < hi),
                "resolved": sum(1 for _, r in rows if r and lo <= r < hi),
            }
        )
    return {"weeks": out}


# ── Components & recalls ──────────────────────────────────────────────────────


@router.get("/component-failure-rate")
async def component_failure_rate(current: Staff, db: DB, months: int = Query(12, ge=1, le=36)) -> dict:
    rows = (
        await db.execute(
            select(m.ServiceItem.part, m.ServiceItem.finding)
            .join(m.ServiceRecord, m.ServiceItem.record_id == m.ServiceRecord.id)
            .where(m.ServiceRecord.service_date >= utcnow() - timedelta(days=30 * months), m.ServiceItem.finding.in_(("worn", "failed")))
        )
    ).all()
    worn, failed = Counter(), Counter()
    for part, finding in rows:
        if part.startswith("recall:"):
            continue
        (failed if finding == "failed" else worn)[part] += 1
    parts = sorted(set(worn) | set(failed), key=lambda p: -(worn[p] + failed[p]))
    return {
        "components": [
            {"component": display(p), "failures": failed[p], "worn_found": worn[p], "total": worn[p] + failed[p]} for p in parts
        ],
        "window_months": months,
    }


@router.get("/recall-heatmap")
async def recall_heatmap(current: Staff, db: DB) -> dict:
    rows = (
        await db.execute(
            select(m.VehicleRecall, m.VehicleModel.make)
            .join(m.Vehicle, m.VehicleRecall.vehicle_id == m.Vehicle.id)
            .join(m.VehicleModel, m.Vehicle.model_id == m.VehicleModel.id)
            .where(m.VehicleRecall.status == "OPEN")
        )
    ).all()
    matrix, campaigns = Counter(), {}
    for r, make in rows:
        matrix[(make, r.campaign, r.component)] += 1
        c = campaigns.setdefault(
            r.campaign,
            {
                "campaign": r.campaign,
                "component": r.component,
                "summary": r.summary,
                "remedy": r.remedy,
                "affected_makes": [],
                "source": r.source,
            },
        )
        if make not in c["affected_makes"]:
            c["affected_makes"].append(make)
    return {
        "heatmap": [{"make": mk, "campaign": cp, "component": comp, "count": n} for (mk, cp, comp), n in sorted(matrix.items())],
        "campaigns": list(campaigns.values()),
        "total_open_recalls": len(rows),
    }


@router.get("/recall-details")
async def recall_details(current: Staff, db: DB) -> dict:
    rows = (
        await db.execute(
            select(m.VehicleRecall, m.Vehicle.code, m.VehicleModel.make)
            .join(m.Vehicle, m.VehicleRecall.vehicle_id == m.Vehicle.id)
            .join(m.VehicleModel, m.Vehicle.model_id == m.VehicleModel.id)
            .order_by(m.VehicleRecall.notified_at.desc())
        )
    ).all()
    open_n = sum(1 for r, _, _ in rows if r.status == "OPEN")
    remedied = len(rows) - open_n
    return {
        "open": open_n,
        "remedied": remedied,
        "total": len(rows),
        "completion_pct": round(100 * remedied / len(rows), 1) if rows else 0,
        "timeline": [
            {
                "vehicle_id": code,
                "make": make,
                "campaign": r.campaign,
                "component": r.component,
                "summary": r.summary,
                "status": r.status.lower(),
                "discovery_date": to_local(r.notified_at).date().isoformat(),
                "remedy_date": to_local(r.remedied_at).date().isoformat() if r.remedied_at else None,
                "source": r.source,
            }
            for r, code, make in rows
        ],
    }
