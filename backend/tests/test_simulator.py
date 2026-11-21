"""The simulator must be deterministic and internally consistent."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from manufacturing_agent import _RECALL_CATALOGUE
from sim.world import SimConfig, simulate

AS_OF = datetime(2026, 11, 21, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata"))


@pytest.fixture(scope="module")
def world():
    return simulate(SimConfig(seed=11, owners=40, vehicles=60, as_of=AS_OF), _RECALL_CATALOGUE)


def _fingerprint(w):
    return (
        [(v["code"], v["odometer_km"], v["reg_no"]) for v in w.vehicles],
        [(b["code"], b["slot_start"], b["status"], b["cost_inr"]) for b in w.bookings],
        [(p["vehicle_code"], p["created_at"], p["priority"], p["component"]) for p in w.predictions],
    )


def test_same_seed_same_world(world):
    again = simulate(SimConfig(seed=11, owners=40, vehicles=60, as_of=AS_OF), _RECALL_CATALOGUE)
    assert _fingerprint(world) == _fingerprint(again)


def test_different_seed_different_world(world):
    other = simulate(SimConfig(seed=12, owners=40, vehicles=60, as_of=AS_OF), _RECALL_CATALOGUE)
    assert _fingerprint(world) != _fingerprint(other)


def test_identifiers_unique(world):
    for key, rows in (
        ("code", world.vehicles),
        ("reg_no", world.vehicles),
        ("vin", world.vehicles),
        ("code", world.bookings),
        ("phone", world.owners),
    ):
        values = [r[key] for r in rows]
        assert len(values) == len(set(values)), key


def test_no_double_booked_technician_or_bay(world):
    busy = defaultdict(list)
    for b in world.bookings:
        if b["status"] == "CANCELLED":
            continue
        end = b["slot_start"] + timedelta(hours=b["duration_hours"])
        busy[b["technician_code"]].append((b["slot_start"], end))
        busy[b["bay_code"]].append((b["slot_start"], end))
    for key, spans in busy.items():
        spans.sort()
        for (_s1, e1), (s2, _) in zip(spans, spans[1:], strict=False):
            assert s2 >= e1, f"overlap on {key} at {s2}"


def test_bookings_within_working_hours(world):
    for b in world.bookings:
        start = b["slot_start"].astimezone(AS_OF.tzinfo)
        end = start + timedelta(hours=b["duration_hours"])
        assert 8 <= start.hour and (end.hour + end.minute / 60) <= 18, b["code"]


def test_statuses_follow_the_clock(world):
    for b in world.bookings:
        if b["status"] == "COMPLETED":
            assert b["completed_at"] <= AS_OF and b["cost_inr"] is not None
        if b["status"] == "CONFIRMED":
            assert b["slot_start"] > AS_OF


def test_exactly_one_current_prediction_per_vehicle(world):
    current = [p["vehicle_code"] for p in world.predictions if p["is_current"]]
    assert sorted(current) == sorted(v["code"] for v in world.vehicles)


def test_nothing_happens_after_as_of(world):
    assert all(r["service_date"] <= AS_OF for r in world.service_records)
    assert all(m["created_at"] <= AS_OF + timedelta(minutes=5) for c in world.conversations for m in c["messages"])
