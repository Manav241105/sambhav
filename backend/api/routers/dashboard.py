"""Dashboard summary, alerts and the manufacturing roll-up (staff only)."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from api import serializers
from api.deps import DB, Staff
from api.events import DashboardEvent, hub
from db import models as m
from db.base import app_tz, iso_local, utcnow
from manufacturing_agent import ManufacturingAgent
from services import audit

router = APIRouter(prefix="/api", tags=["dashboard"])
_mfg = ManufacturingAgent()


async def prediction_accuracy(db: DB, since: datetime | None = None) -> tuple[float | None, int]:
    """
    Share of agent-initiated, completed bookings where the workshop found the
    predicted part worn or failed. Returns (accuracy, sample size).
    """
    q = (
        select(m.Prediction.component, m.ServiceItem.part, m.ServiceItem.finding, m.Booking.id)
        .join(m.Booking, m.Booking.prediction_id == m.Prediction.id)
        .join(m.ServiceRecord, m.ServiceRecord.booking_id == m.Booking.id)
        .join(m.ServiceItem, m.ServiceItem.record_id == m.ServiceRecord.id)
        .where(m.Booking.status == "COMPLETED", m.Prediction.component.is_not(None))
    )
    if since is not None:
        q = q.where(m.Booking.completed_at >= since)
    confirmed: dict[int, bool] = {}
    for component, part, finding, booking_id in (await db.execute(q)).all():
        hit = part == component and finding in ("worn", "failed")
        confirmed[booking_id] = confirmed.get(booking_id, False) or hit
    if not confirmed:
        return None, 0
    return round(sum(confirmed.values()) / len(confirmed), 3), len(confirmed)


@router.get("/dashboard/summary")
async def summary(current: Staff, db: DB) -> dict:
    tz = app_tz()
    today = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    total = await db.scalar(select(func.count()).select_from(m.Vehicle))
    by_priority = dict(
        (
            await db.execute(
                select(m.Prediction.priority, func.count()).where(m.Prediction.is_current.is_(True)).group_by(m.Prediction.priority)
            )
        ).all()
    )
    critical = by_priority.get("P0", 0) + by_priority.get("P1", 0)
    bookings_total = await db.scalar(select(func.count()).select_from(m.Booking).where(m.Booking.status != "CANCELLED"))
    todays = await db.scalar(
        select(func.count())
        .select_from(m.Booking)
        .where(m.Booking.status != "CANCELLED", m.Booking.slot_start >= today, m.Booking.slot_start < today + timedelta(days=1))
    )
    open_convs = await db.scalar(select(func.count()).select_from(m.Conversation).where(m.Conversation.status.in_(("OPEN", "ESCALATED"))))
    active_alerts = await db.scalar(select(func.count()).select_from(m.Alert).where(m.Alert.acknowledged_at.is_(None)))

    accuracy, sample = await prediction_accuracy(db)
    llm_total = await db.scalar(select(func.count()).select_from(m.Prediction).where(m.Prediction.model_version.like("llm-%")))
    llm_fallback = await db.scalar(select(func.count()).select_from(m.Prediction).where(m.Prediction.model_version.like("llm-%+fallback")))
    return {
        "total_vehicles": total,
        "critical_vehicles": critical,
        "warning_vehicles": by_priority.get("P2", 0),
        "normal_vehicles": total - critical - by_priority.get("P2", 0),
        "priority_breakdown": {p: by_priority.get(p, 0) for p in ("P0", "P1", "P2", "P3")},
        "total_bookings": bookings_total,
        "todays_bookings": todays,
        "open_conversations": open_convs,
        "active_alerts": active_alerts,
        # Measured, not assumed: workshop findings vs. predictions.
        "ai_accuracy": accuracy,
        "ai_accuracy_sample": sample,
        # Share of LLM diagnosis runs that fell back to rules (None until the LLM has run).
        "fallback_rate": round(llm_fallback / llm_total, 3) if llm_total else None,
        "llm_diagnosis_runs": llm_total,
        "updated_at": iso_local(utcnow()),
    }


@router.get("/dashboard/alerts")
async def alerts(current: Staff, db: DB, include_acknowledged: bool = False, limit: int = Query(200, ge=1, le=1000)) -> list[dict]:
    q = select(m.Alert, m.Vehicle.code).join(m.Vehicle, m.Alert.vehicle_id == m.Vehicle.id).order_by(m.Alert.fired_at.desc()).limit(limit)
    if not include_acknowledged:
        q = q.where(m.Alert.acknowledged_at.is_(None))
    return [serializers.alert_dict(a, code) for a, code in (await db.execute(q)).all()]


@router.post("/dashboard/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: int, current: Staff, db: DB) -> dict:
    row = (
        await db.execute(select(m.Alert, m.Vehicle.code).join(m.Vehicle, m.Alert.vehicle_id == m.Vehicle.id).where(m.Alert.id == alert_id))
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    alert, code = row
    if alert.acknowledged_at is None:
        alert.acknowledged_at, alert.acknowledged_by_user_id = utcnow(), current.id
        audit.record(db, current.id, "acknowledge", "alert", str(alert.id))
        await db.commit()
        await hub.publish(DashboardEvent.ALERT_ACKNOWLEDGED, {"alert_id": alert.id, "vehicle_id": code})
    return serializers.alert_dict(alert, code)


@router.get("/manufacturing/summary")
async def manufacturing_summary(current: Staff, db: DB) -> dict:
    codes = (await db.scalars(select(m.Vehicle.code))).all()
    recalls = (
        await db.execute(
            select(m.VehicleRecall, m.Vehicle.code)
            .join(m.Vehicle, m.VehicleRecall.vehicle_id == m.Vehicle.id)
            .where(m.VehicleRecall.status == "OPEN")
        )
    ).all()
    per_vehicle: dict[str, list] = {}
    for r, code in recalls:
        per_vehicle.setdefault(code, []).append(serializers.recall_dict(r))
    return {
        "total_vehicles_checked": len(codes),
        "total_dtc_codes": sum(len(_mfg.get_dtc_codes(c)) for c in codes),
        "dtc_source": "simulated",
        "total_open_recalls": len(recalls),
        "vehicles_with_recalls": [{"vehicle_id": c, "recall_count": len(r), "recalls": r} for c, r in sorted(per_vehicle.items())],
    }
