"""Vehicles: list/detail, readings history, service history, manufacturing data, diagnosis."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api import queries, serializers
from api.deps import DB, Auth, Staff, get_vehicle_for
from db import models as m
from db.base import iso_local, utcnow
from manufacturing_agent import ManufacturingAgent

router = APIRouter(prefix="/api", tags=["vehicles"])
_mfg = ManufacturingAgent()


@router.get("/vehicles")
async def list_vehicles(
    current: Auth,
    db: DB,
    priority: str | None = Query(None, pattern=r"^P[0-3]$"),
    limit: int = Query(1000, ge=1, le=2000),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """Staff see every vehicle; owners see their own."""
    q = queries.vehicle_query().order_by(m.Vehicle.code)
    if not current.is_staff:
        if current.owner is None:
            return []
        q = q.where(m.Vehicle.owner_id == current.owner.id)
    if priority:
        q = q.join(m.Prediction, (m.Prediction.vehicle_id == m.Vehicle.id) & m.Prediction.is_current.is_(True)).where(
            m.Prediction.priority == priority
        )
    vehicles = (await db.scalars(q.limit(limit).offset(offset))).all()
    ids = [v.id for v in vehicles]
    preds = await queries.current_predictions(db, ids)
    tele = await queries.latest_telemetry(db, ids)
    services = await queries.last_service_dates(db, ids)
    return [serializers.vehicle_dict(v, preds.get(v.id), tele.get(v.id), services.get(v.id)) for v in vehicles]


@router.get("/me/vehicles")
async def my_vehicles(current: Auth, db: DB) -> list[dict]:
    """The signed-in owner's cars (same shape as /vehicles)."""
    if current.owner is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only owner accounts have vehicles")
    return await list_vehicles(current, db, None, 100, 0)


@router.get("/vehicles/{code}")
async def get_vehicle(code: str, current: Auth, db: DB) -> dict:
    v = await get_vehicle_for(db, current, code)
    v = await db.scalar(queries.vehicle_query().where(m.Vehicle.id == v.id))
    preds = await queries.current_predictions(db, [v.id])
    tele = await queries.latest_telemetry(db, [v.id])
    services = await queries.last_service_dates(db, [v.id])
    return serializers.vehicle_dict(v, preds.get(v.id), tele.get(v.id), services.get(v.id), include_parts=True)


@router.get("/vehicles/{code}/history")
async def vehicle_history(code: str, current: Auth, db: DB, days: int = Query(7, ge=1, le=30)) -> dict:
    """Daily readings for trend charts (empty for cars without a reading source)."""
    v = await get_vehicle_for(db, current, code)
    since = utcnow() - timedelta(days=days)
    rows = (
        await db.scalars(
            select(m.TelemetrySnapshot)
            .where(m.TelemetrySnapshot.vehicle_id == v.id, m.TelemetrySnapshot.recorded_at >= since)
            .order_by(m.TelemetrySnapshot.recorded_at)
        )
    ).all()
    history = []
    for t in rows:
        d = serializers.telemetry_dict(t, code)
        d["day"] = t.recorded_at.strftime("%a")
        history.append(d)
    return {"vehicle_id": code, "days": days, "history": history, "has_readings": bool(history)}


@router.get("/vehicles/{code}/service-history")
async def service_history(code: str, current: Auth, db: DB, limit: int = Query(50, ge=1, le=200)) -> dict:
    v = await get_vehicle_for(db, current, code)
    records = (
        await db.scalars(
            select(m.ServiceRecord)
            .options(selectinload(m.ServiceRecord.items))
            .where(m.ServiceRecord.vehicle_id == v.id)
            .order_by(m.ServiceRecord.service_date.desc())
            .limit(limit)
        )
    ).all()
    return {
        "vehicle_id": code,
        "records": [
            {
                "id": r.id,
                "service_date": iso_local(r.service_date),
                "odometer_km": r.odometer_km,
                "service_type": r.service_type,
                "total_cost_inr": r.total_cost_inr,
                "at_partner_workshop": r.workshop_id is not None,
                "source": r.extracted_by,
                "notes": r.notes,
                "items": [{"part": i.part, "action": i.action, "finding": i.finding, "cost_inr": i.cost_inr} for i in r.items],
            }
            for r in records
        ],
    }


@router.get("/vehicles/{code}/manufacturing")
async def vehicle_manufacturing(code: str, current: Auth, db: DB) -> dict:
    """DTCs are simulated (no OBD reader yet); recalls come from the recall table."""
    v = await get_vehicle_for(db, current, code)
    recalls = (
        await db.scalars(select(m.VehicleRecall).where(m.VehicleRecall.vehicle_id == v.id).order_by(m.VehicleRecall.notified_at))
    ).all()
    dtcs = _mfg.get_dtc_codes(code)
    open_recalls = [r for r in recalls if r.status == "OPEN"]
    return {
        "vehicle_id": code,
        "checked_at": iso_local(utcnow()),
        "dtc_codes": dtcs,
        "dtc_count": len(dtcs),
        "dtc_source": "simulated",
        "recalls": [serializers.recall_dict(r) for r in recalls],
        "recall_count": len(open_recalls),
        "has_critical_issue": any(d["severity"] == "critical" for d in dtcs) or bool(open_recalls),
    }


@router.post("/vehicles/{code}/diagnose")
async def diagnose(code: str, current: Staff, db: DB) -> dict:
    """Run the LLM diagnosis pipeline for one vehicle now (staff only)."""
    from services.diagnosis import load_vehicle, run_llm_diagnosis

    vehicle = await load_vehicle(db, code)
    if vehicle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Vehicle {code} not found")
    try:
        pred = await run_llm_diagnosis(db, vehicle)
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Diagnosis failed: {exc}") from exc
    return {"vehicle_id": code, "diagnosis": serializers.diagnosis_dict(pred, include_parts=True), "priority": pred.priority}
