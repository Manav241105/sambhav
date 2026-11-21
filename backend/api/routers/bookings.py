"""Bookings, availability and workshop resources."""

from __future__ import annotations

import secrets
from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from api import queries, serializers
from api.deps import DB, Auth, Staff, get_vehicle_for
from api.events import DashboardEvent, hub
from db import models as m
from db.base import app_tz, utcnow
from domain.parts import JOB_HOURS
from domain.workshop import ACTIVE_BOOKING_STATUSES, ALLOWED_TRANSITIONS, BAY_LABELS
from services import audit
from services import scheduling as sched

router = APIRouter(prefix="/api", tags=["bookings"])

COMPONENTS = tuple(JOB_HOURS)
_ALIASES = {
    "Brake Pad": "Brake Pads",
    "Tyres": "Tires",
    "Coolant System": "Cooling System",
    "General": "Full Service",
    "Engine Oil": "Oil Change",
    "Periodic Service": "Full Service",
}


def normalize_component(value: str) -> str:
    """Accept snake_case / lowercase / common aliases; return the canonical job name."""
    label = value.replace("_", " ").strip().title()
    label = _ALIASES.get(label, label)
    if label not in COMPONENTS:
        raise ValueError(f"service_component must be one of {', '.join(COMPONENTS)}")
    return label


class BookingCreate(BaseModel):
    vehicle_id: str
    service_component: str
    slot_time_iso: datetime
    technician_id: str | None = None  # code, e.g. "T001"
    technician_name: str | None = None  # accepted for older clients
    bay: str | None = None  # code, e.g. "BAY-3"
    priority: str = Field("P3", pattern=r"^P[0-3]$")
    service_duration_hours: float | None = None

    @field_validator("service_component")
    @classmethod
    def _component(cls, v: str) -> str:
        return normalize_component(v)


class BookingUpdate(BaseModel):
    slot_time_iso: datetime | None = None
    status: str | None = None
    service_duration_hours: float | None = None
    technician_id: str | None = None
    technician_name: str | None = None
    bay: str | None = None
    cost_inr: int | None = Field(None, ge=0)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=app_tz())


async def _technician(db: DB, ws: m.Workshop, code: str | None, name: str | None) -> m.Technician | None:
    if not code and not name:
        return None
    q = select(m.Technician).where(m.Technician.workshop_id == ws.id)
    q = q.where(m.Technician.code == code) if code else q.where(m.Technician.name == name)
    tech = await db.scalar(q)
    if tech is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Unknown technician")
    return tech


async def _bay(db: DB, ws: m.Workshop, code: str | None) -> m.Bay | None:
    if not code:
        return None
    bay = await db.scalar(select(m.Bay).where(m.Bay.workshop_id == ws.id, m.Bay.code == code))
    if bay is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Unknown bay")
    return bay


async def _load(db: DB, booking_id: int) -> m.Booking:
    return await db.scalar(queries.booking_query().where(m.Booking.id == booking_id))


async def _find(db: DB, current, code: str) -> m.Booking:
    b = await db.scalar(queries.booking_query().where(m.Booking.code == code))
    if b is None or (not current.is_staff and (current.owner is None or b.vehicle.owner_id != current.owner.id)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Booking {code} not found")
    return b


# ── Reads ─────────────────────────────────────────────────────────────────────


@router.get("/bookings")
async def list_bookings(
    current: Auth,
    db: DB,
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(2000, ge=1, le=5000),
) -> list[dict]:
    q = queries.booking_query().order_by(m.Booking.slot_start.desc())
    if not current.is_staff:
        if current.owner is None:
            return []
        q = q.join(m.Vehicle, m.Booking.vehicle_id == m.Vehicle.id).where(m.Vehicle.owner_id == current.owner.id)
    tz = app_tz()
    if date_from:
        q = q.where(m.Booking.slot_start >= datetime.combine(date_from, datetime.min.time(), tz))
    if date_to:
        q = q.where(m.Booking.slot_start < datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tz))
    if status_filter:
        q = q.where(m.Booking.status == status_filter.upper())
    return [serializers.booking_dict(b) for b in (await db.scalars(q.limit(limit))).all()]


@router.get("/bookings/today")
async def todays_bookings(current: Staff, db: DB) -> list[dict]:
    today = datetime.now(app_tz()).date()
    return await list_bookings(current, db, today, today, None, 500)


@router.get("/availability")
async def get_availability(
    current: Auth,
    db: DB,
    date_: date | None = Query(None, alias="date"),
    component: str = Query("Full Service"),
) -> dict:
    day = date_ or datetime.now(app_tz()).date()
    try:
        label = normalize_component(component)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return {"date": day.isoformat(), "component": label, "slots": await sched.availability(db, day, label)}


@router.get("/resources")
async def resources(current: Auth, db: DB) -> dict:
    ws = await sched.default_workshop(db)
    techs = (await db.scalars(select(m.Technician).where(m.Technician.workshop_id == ws.id).order_by(m.Technician.code))).all()
    bays = (await db.scalars(select(m.Bay).where(m.Bay.workshop_id == ws.id).order_by(m.Bay.id))).all()
    return {
        "workshop": {"id": ws.code, "name": ws.name, "city": ws.city, "open_hour": ws.open_hour, "close_hour": ws.close_hour},
        "technicians": [
            {"id": t.code, "name": t.name, "level": t.level, "skills": t.skills, "spec": ", ".join(t.skills or [])} for t in techs
        ],
        "bays": [
            {
                "id": b.code,
                "label": b.code.replace("BAY-", "Bay "),
                "bay_type": b.bay_type,
                "spec": BAY_LABELS.get(b.bay_type, b.bay_type.title()),
            }
            for b in bays
        ],
        "components": list(COMPONENTS),
    }


# ── Writes ────────────────────────────────────────────────────────────────────


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(body: BookingCreate, current: Auth, db: DB) -> dict:
    vehicle = await get_vehicle_for(db, current, body.vehicle_id)
    ws = await sched.default_workshop(db)
    start = _aware(body.slot_time_iso)
    try:
        hours = sched.job_hours(body.service_component, body.service_duration_hours)
        sched.check_working_hours(ws, start, hours)
    except sched.SchedulingError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    if start < utcnow():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Slot is in the past")

    # Owners can't choose staff or bays; staff may, otherwise auto-assign.
    tech = bay = None
    if current.is_staff:
        tech = await _technician(db, ws, body.technician_id, body.technician_name)
        bay = await _bay(db, ws, body.bay)
    if tech is None or bay is None:
        picked = await sched.pick_resources(db, ws, body.service_component, start, hours)
        if picked:
            tech, bay = tech or picked[0], bay or picked[1]
    if tech is None or bay is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "No technician or bay free at that time")
    problems = await sched.conflicts(db, start, hours, tech.id, bay.id)
    if problems:
        raise HTTPException(status.HTTP_409_CONFLICT, "; ".join(problems).capitalize())

    priority = body.priority
    if not current.is_staff:
        pred = (await queries.current_predictions(db, [vehicle.id])).get(vehicle.id)
        priority = pred.priority if pred else "P3"
    booking = m.Booking(
        code=f"BK{start.astimezone(app_tz()):%y%m%d}-{secrets.token_hex(3).upper()}",
        vehicle_id=vehicle.id,
        workshop_id=ws.id,
        technician_id=tech.id,
        bay_id=bay.id,
        service_component=body.service_component,
        slot_start=start,
        duration_hours=hours,
        priority=priority,
        status="CONFIRMED",
        source="dashboard" if current.is_staff else "app",
        created_by_user_id=current.id,
    )
    db.add(booking)
    await db.flush()
    audit.record(
        db, current.id, "create", "booking", booking.code, after={"slot": start.isoformat(), "technician": tech.code, "bay": bay.code}
    )
    await db.commit()
    booking = await _load(db, booking.id)
    await hub.publish(DashboardEvent.BOOKING_CREATED, {"booking_id": booking.code, "vehicle_id": vehicle.code})
    return serializers.booking_dict(booking)


@router.patch("/bookings/{code}")
async def update_booking(code: str, body: BookingUpdate, current: Staff, db: DB) -> dict:
    b = await _find(db, current, code)
    before = serializers.booking_dict(b)
    ws = await sched.default_workshop(db)
    start = _aware(body.slot_time_iso) if body.slot_time_iso else b.slot_start
    hours = b.duration_hours
    tech = await _technician(db, ws, body.technician_id, body.technician_name) or b.technician
    bay = await _bay(db, ws, body.bay) or b.bay

    try:
        if body.service_duration_hours is not None:
            hours = sched.job_hours(b.service_component, body.service_duration_hours)
        if body.slot_time_iso or body.service_duration_hours is not None:
            sched.check_working_hours(ws, start, hours)
    except sched.SchedulingError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    if body.status:
        new_status = body.status.upper()
        if new_status != b.status and new_status not in ALLOWED_TRANSITIONS.get(b.status, set()):
            raise HTTPException(status.HTTP_409_CONFLICT, f"Cannot change status from {b.status} to {new_status}")
        b.status = new_status
        if new_status == "COMPLETED":
            b.completed_at = utcnow()
            b.actual_duration_hours = round((b.completed_at - b.slot_start).total_seconds() / 3600, 2)
        if new_status == "CANCELLED":
            b.cancelled_at = utcnow()

    if b.status in ACTIVE_BOOKING_STATUSES:
        problems = await sched.conflicts(db, start, hours, tech.id if tech else None, bay.id if bay else None, exclude_id=b.id)
        if problems:
            raise HTTPException(status.HTTP_409_CONFLICT, "; ".join(problems).capitalize())

    b.slot_start, b.duration_hours = start, hours
    b.technician_id, b.bay_id = (tech.id if tech else None), (bay.id if bay else None)
    if body.cost_inr is not None:
        b.cost_inr = body.cost_inr
    await db.flush()
    b = await _load(db, b.id)
    after = serializers.booking_dict(b)
    audit.record(
        db,
        current.id,
        "update",
        "booking",
        b.code,
        before={k: before[k] for k in ("slot_time_iso", "status", "technician_id", "bay", "service_duration_hours")},
        after={k: after[k] for k in ("slot_time_iso", "status", "technician_id", "bay", "service_duration_hours")},
    )
    await db.commit()
    await hub.publish(DashboardEvent.BOOKING_UPDATED, {"booking_id": b.code, "status": b.status})
    return after


@router.delete("/bookings/{code}")
async def cancel_booking(code: str, current: Auth, db: DB) -> dict:
    """Cancel (the row is kept for history and analytics)."""
    b = await _find(db, current, code)
    if b.status not in ("PENDING", "CONFIRMED"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"A {b.status.lower()} booking can't be cancelled")
    b.status, b.cancelled_at = "CANCELLED", utcnow()
    audit.record(db, current.id, "cancel", "booking", b.code)
    await db.commit()
    await hub.publish(DashboardEvent.BOOKING_CANCELLED, {"booking_id": b.code})
    return serializers.booking_dict(await _load(db, b.id))
