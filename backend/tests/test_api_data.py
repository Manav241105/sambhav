"""Dashboard data: every endpoint works, numbers are stable and consistent."""

from __future__ import annotations

import pytest

ANALYTICS = [
    "fleet",
    "kpi-trends",
    "executive-summary",
    "revenue",
    "revenue-by-component",
    "revenue-forecast",
    "cost-avoidance",
    "roi",
    "monthly",
    "workload",
    "bay-occupancy",
    "service-duration",
    "booking-velocity",
    "conversation-volume",
    "agent-performance",
    "booking-funnel",
    "alert-funnel",
    "conversion-by-make",
    "escalations",
    "escalation-heatmap",
    "escalation-trend",
    "component-failure-rate",
    "recall-heatmap",
    "recall-details",
]


@pytest.mark.parametrize("name", ANALYTICS)
async def test_analytics_endpoint_is_deterministic(client, staff_headers, name):
    a = await client.get(f"/api/analytics/{name}", headers=staff_headers)
    b = await client.get(f"/api/analytics/{name}", headers=staff_headers)
    assert a.status_code == 200, a.text
    strip = lambda d: {k: v for k, v in d.items() if k != "generated_at"}  # noqa: E731
    assert strip(a.json()) == strip(b.json()), "analytics must not change between identical requests"


async def test_money_is_in_rupees(client, staff_headers):
    for name in ("revenue", "roi", "cost-avoidance", "revenue-by-component"):
        body = (await client.get(f"/api/analytics/{name}", headers=staff_headers)).text
        assert "_usd" not in body, name


async def test_summary_matches_vehicle_list(client, staff_headers):
    summary = (await client.get("/api/dashboard/summary", headers=staff_headers)).json()
    vehicles = (await client.get("/api/vehicles", headers=staff_headers)).json()
    assert summary["total_vehicles"] == len(vehicles) == 40
    assert summary["critical_vehicles"] == sum(v["priority"] in ("P0", "P1") for v in vehicles)
    assert summary["ai_accuracy"] is None or 0 <= summary["ai_accuracy"] <= 1


async def test_vehicle_detail_shape(client, staff_headers):
    v = (await client.get("/api/vehicles/VEH001", headers=staff_headers)).json()
    for key in ("vehicle_id", "make", "model", "priority", "health_score", "diagnosis", "customer", "telematics"):
        assert key in v
    assert len(v["diagnosis"]["parts"]) == 6
    assert v["priority"] in ("P0", "P1", "P2", "P3")
    if v["priority"] != "P3":
        assert v["diagnosis"]["predicted_component"]


async def test_alert_acknowledge(client, staff_headers):
    alerts = (await client.get("/api/dashboard/alerts", headers=staff_headers)).json()
    if not alerts:
        pytest.skip("no open alerts in this seed")
    r = await client.post(f"/api/dashboard/alerts/{alerts[0]['id']}/ack", headers=staff_headers)
    assert r.status_code == 200 and r.json()["acknowledged"] is True
    remaining = (await client.get("/api/dashboard/alerts", headers=staff_headers)).json()
    assert alerts[0]["id"] not in {a["id"] for a in remaining}


async def test_service_history_and_manufacturing(client, staff_headers):
    hist = (await client.get("/api/vehicles/VEH002/service-history", headers=staff_headers)).json()
    assert hist["records"], "simulated cars have service history"
    mfg = (await client.get("/api/vehicles/VEH002/manufacturing", headers=staff_headers)).json()
    assert mfg["dtc_source"] == "simulated"


async def test_baseline_refresh_is_idempotent(seeded_db):
    from sqlalchemy import func, select

    from db import models as m
    from db.session import get_sessionmaker
    from services.diagnosis import diagnosis_cycle

    async with get_sessionmaker()() as s:
        before = await s.scalar(select(func.count()).select_from(m.Prediction))
    stats = await diagnosis_cycle(llm_batch=0)
    again = await diagnosis_cycle(llm_batch=0)
    async with get_sessionmaker()() as s:
        after = await s.scalar(select(func.count()).select_from(m.Prediction))
        current = await s.scalar(select(func.count()).select_from(m.Prediction).where(m.Prediction.is_current.is_(True)))
    assert again["baseline_updated"] == 0, "a second pass with no new data must not write predictions"
    assert after == before + stats["baseline_updated"]
    assert current == 40
