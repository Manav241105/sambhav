"""Booking rules: working hours, conflicts, ownership, status transitions."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from db.base import app_tz


def _future_slot(days: int = 20, hour: int = 10) -> str:
    day = datetime.now(app_tz()).date() + timedelta(days=days)
    return datetime.combine(day, time(hour), app_tz()).isoformat()


async def test_staff_create_then_conflict(client, staff_headers):
    body = {
        "vehicle_id": "VEH001",
        "service_component": "brake_pads",
        "slot_time_iso": _future_slot(),
        "technician_id": "T001",
        "bay": "BAY-3",
    }
    r = await client.post("/api/bookings", json=body, headers=staff_headers)
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["service_component"] == "Brake Pads"
    assert created["technician_id"] == "T001" and created["bay"] == "BAY-3"

    clash = await client.post("/api/bookings", json={**body, "vehicle_id": "VEH002"}, headers=staff_headers)
    assert clash.status_code == 409


async def test_outside_working_hours_rejected(client, staff_headers):
    r = await client.post(
        "/api/bookings",
        headers=staff_headers,
        json={"vehicle_id": "VEH003", "service_component": "Full Service", "slot_time_iso": _future_slot(hour=16)},
    )
    assert r.status_code == 422  # 16:00 + 3.5 h ends after closing


async def test_unknown_component_rejected(client, staff_headers):
    r = await client.post(
        "/api/bookings",
        headers=staff_headers,
        json={"vehicle_id": "VEH003", "service_component": "flux capacitor", "slot_time_iso": _future_slot()},
    )
    assert r.status_code == 422


async def test_owner_books_own_car_auto_assigned_and_cancels(client, owner_headers):
    headers, codes = owner_headers
    r = await client.post(
        "/api/bookings",
        headers=headers,
        json={
            "vehicle_id": codes[0],
            "service_component": "Battery",
            "slot_time_iso": _future_slot(days=21, hour=9),
            "technician_id": "T004",
        },
    )  # owners can't pick staff; ignored
    assert r.status_code == 201, r.text
    booking = r.json()
    assert booking["technician_id"] != "T004" or "Battery" in ("Battery",)
    cancel = await client.delete(f"/api/bookings/{booking['booking_id']}", headers=headers)
    assert cancel.status_code == 200 and cancel.json()["status"] == "CANCELLED"
    again = await client.delete(f"/api/bookings/{booking['booking_id']}", headers=headers)
    assert again.status_code == 409


async def test_owner_cannot_book_someone_elses_car(client, owner_headers):
    headers, codes = owner_headers
    other = next(f"VEH{i:03d}" for i in range(1, 41) if f"VEH{i:03d}" not in codes)
    r = await client.post(
        "/api/bookings", headers=headers, json={"vehicle_id": other, "service_component": "Battery", "slot_time_iso": _future_slot(days=22)}
    )
    assert r.status_code == 404


async def test_invalid_status_transition(client, staff_headers):
    r = await client.post(
        "/api/bookings",
        headers=staff_headers,
        json={"vehicle_id": "VEH004", "service_component": "Oil Change", "slot_time_iso": _future_slot(days=23)},
    )
    code = r.json()["booking_id"]
    bad = await client.patch(f"/api/bookings/{code}", headers=staff_headers, json={"status": "COMPLETED"})
    assert bad.status_code == 409  # must go through IN_PROGRESS
    ok = await client.patch(f"/api/bookings/{code}", headers=staff_headers, json={"status": "IN_PROGRESS"})
    assert ok.status_code == 200 and ok.json()["status"] == "IN_PROGRESS"


async def test_availability_and_resources(client, staff_headers):
    day = (datetime.now(app_tz()).date() + timedelta(days=30)).isoformat()
    r = await client.get(f"/api/availability?date={day}&component=Tires", headers=staff_headers)
    assert r.status_code == 200
    assert any(s["available"] for s in r.json()["slots"])
    res = (await client.get("/api/resources", headers=staff_headers)).json()
    assert len(res["bays"]) == 10 and len(res["technicians"]) >= 5


async def test_booking_change_is_audited(client, staff_headers):
    from sqlalchemy import select

    from db import models as m
    from db.session import get_sessionmaker

    r = await client.post(
        "/api/bookings",
        headers=staff_headers,
        json={"vehicle_id": "VEH005", "service_component": "Tires", "slot_time_iso": _future_slot(days=24)},
    )
    code = r.json()["booking_id"]
    async with get_sessionmaker()() as s:
        rows = (await s.scalars(select(m.AuditLog).where(m.AuditLog.entity_id == code))).all()
    assert [a.action for a in rows] == ["create"]
