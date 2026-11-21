"""
Database-backed workshop scheduling: conflicts, resource picking, availability.

Overlap is checked in Python over a narrow time window so the same code works
on SQLite and PostgreSQL (no interval arithmetic in SQL).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import models as m
from db.base import app_tz
from domain.parts import JOB_HOURS
from domain.workshop import ACTIVE_BOOKING_STATUSES, BAY_FOR_COMPONENT, GENERALIST_SKILL

MAX_JOB_HOURS = 8


class SchedulingError(ValueError):
    """Raised for requests that can never be booked (outside hours, unknown resource)."""


async def default_workshop(session: AsyncSession) -> m.Workshop:
    ws = await session.scalar(select(m.Workshop).order_by(m.Workshop.id).limit(1))
    if ws is None:
        raise SchedulingError("No workshop configured")
    return ws


def job_hours(component: str, requested: float | None = None) -> float:
    if requested is not None:
        if not 0.25 <= requested <= MAX_JOB_HOURS:
            raise SchedulingError(f"Duration must be between 0.25 and {MAX_JOB_HOURS} hours")
        return requested
    return JOB_HOURS.get(component, 2.0)


def check_working_hours(ws: m.Workshop, start: datetime, hours: float) -> None:
    local = start.astimezone(app_tz())
    end = local + timedelta(hours=hours)
    open_at = local.replace(hour=ws.open_hour, minute=0, second=0, microsecond=0)
    close_at = local.replace(hour=ws.close_hour, minute=0, second=0, microsecond=0)
    if local < open_at or end > close_at or end.date() != local.date():
        raise SchedulingError(f"Slot must be within working hours {ws.open_hour:02d}:00–{ws.close_hour:02d}:00")


async def active_bookings_between(session: AsyncSession, start: datetime, end: datetime, exclude_id: int | None = None) -> list[m.Booking]:
    q = select(m.Booking).where(
        m.Booking.status.in_(ACTIVE_BOOKING_STATUSES),
        m.Booking.slot_start < end,
        m.Booking.slot_start > start - timedelta(hours=MAX_JOB_HOURS),
    )
    if exclude_id is not None:
        q = q.where(m.Booking.id != exclude_id)
    rows = (await session.scalars(q)).all()
    return [b for b in rows if b.slot_start + timedelta(hours=b.duration_hours) > start]


def _busy(bookings: list[m.Booking]) -> tuple[set[int], set[int]]:
    return {b.technician_id for b in bookings if b.technician_id}, {b.bay_id for b in bookings if b.bay_id}


async def conflicts(
    session: AsyncSession, start: datetime, hours: float, technician_id: int | None, bay_id: int | None, exclude_id: int | None = None
) -> list[str]:
    overlapping = await active_bookings_between(session, start, start + timedelta(hours=hours), exclude_id)
    busy_techs, busy_bays = _busy(overlapping)
    problems = []
    if technician_id and technician_id in busy_techs:
        problems.append("technician is already booked at that time")
    if bay_id and bay_id in busy_bays:
        problems.append("bay is already booked at that time")
    return problems


async def pick_resources(
    session: AsyncSession, ws: m.Workshop, component: str, start: datetime, hours: float, exclude_id: int | None = None
) -> tuple[m.Technician, m.Bay] | None:
    """A skilled free technician and a suitable free bay, or None."""
    overlapping = await active_bookings_between(session, start, start + timedelta(hours=hours), exclude_id)
    busy_techs, busy_bays = _busy(overlapping)
    techs = (await session.scalars(select(m.Technician).where(m.Technician.workshop_id == ws.id).order_by(m.Technician.code))).all()
    bays = (await session.scalars(select(m.Bay).where(m.Bay.workshop_id == ws.id).order_by(m.Bay.id))).all()

    skilled = [t for t in techs if component in (t.skills or [])] or [t for t in techs if GENERALIST_SKILL in (t.skills or [])]
    preferred = BAY_FOR_COMPONENT.get(component, ["GENERAL"])
    suitable = sorted((b for b in bays if b.bay_type in preferred), key=lambda b: preferred.index(b.bay_type))
    tech = next((t for t in skilled if t.id not in busy_techs), None)
    bay = next((b for b in suitable if b.id not in busy_bays), None)
    return (tech, bay) if tech and bay else None


async def availability(session: AsyncSession, day: date, component: str) -> list[dict]:
    """Hourly start times on `day` (app timezone) where the job fits."""
    ws = await default_workshop(session)
    hours = job_hours(component)
    tz = app_tz()
    now = datetime.now(tz)
    slots = []
    for hour in range(ws.open_hour, ws.close_hour):
        start = datetime.combine(day, time(hour), tz)
        fits_day = start + timedelta(hours=hours) <= datetime.combine(day, time(ws.close_hour), tz)
        free = fits_day and start > now and await pick_resources(session, ws, component, start, hours) is not None
        slots.append(
            {
                "slot_time": start.strftime("%I:%M %p"),
                "slot_time_iso": start.isoformat(),
                "available": bool(free),
            }
        )
    return slots
