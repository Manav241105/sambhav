"""Reusable read queries shared by several routers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db import models as m


def vehicle_query() -> Select:
    return select(m.Vehicle).options(selectinload(m.Vehicle.owner), selectinload(m.Vehicle.vehicle_model))


def booking_query() -> Select:
    return select(m.Booking).options(
        selectinload(m.Booking.vehicle).selectinload(m.Vehicle.owner),
        selectinload(m.Booking.technician),
        selectinload(m.Booking.bay),
    )


async def current_predictions(session: AsyncSession, vehicle_ids: list[int] | None = None) -> dict[int, m.Prediction]:
    q = select(m.Prediction).where(m.Prediction.is_current.is_(True))
    if vehicle_ids is not None:
        q = q.where(m.Prediction.vehicle_id.in_(vehicle_ids))
    return {p.vehicle_id: p for p in (await session.scalars(q)).all()}


async def latest_telemetry(session: AsyncSession, vehicle_ids: list[int] | None = None) -> dict[int, m.TelemetrySnapshot]:
    latest = select(m.TelemetrySnapshot.vehicle_id, func.max(m.TelemetrySnapshot.recorded_at).label("at")).group_by(
        m.TelemetrySnapshot.vehicle_id
    )
    if vehicle_ids is not None:
        latest = latest.where(m.TelemetrySnapshot.vehicle_id.in_(vehicle_ids))
    latest = latest.subquery()
    q = select(m.TelemetrySnapshot).join(
        latest,
        (m.TelemetrySnapshot.vehicle_id == latest.c.vehicle_id) & (m.TelemetrySnapshot.recorded_at == latest.c.at),
    )
    return {t.vehicle_id: t for t in (await session.scalars(q)).all()}


async def last_service_dates(session: AsyncSession, vehicle_ids: list[int] | None = None) -> dict[int, datetime]:
    q = select(m.ServiceRecord.vehicle_id, func.max(m.ServiceRecord.service_date)).group_by(m.ServiceRecord.vehicle_id)
    if vehicle_ids is not None:
        q = q.where(m.ServiceRecord.vehicle_id.in_(vehicle_ids))
    return dict((await session.execute(q)).all())
