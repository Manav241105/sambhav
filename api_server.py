"""
API Server - v1.0
FastAPI router with all REST + WebSocket endpoints for the Dashboard layer.

Mount this inside webhook_server.py (or any FastAPI app):
    from api_server import api_router
    app.include_router(api_router)
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app_state import app_state, DashboardEvent
from data_generator import VehicleDataGenerator
from manufacturing_agent import ManufacturingAgent

# ──────────────────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────────────────
api_router = APIRouter(prefix="/api", tags=["Dashboard API"])

# Shared data generator for seeding mock data
_data_gen = VehicleDataGenerator()


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str
    role: str  # ops | manager | executive


class LoginResponse(BaseModel):
    token: str
    role: str
    email: str
    expires_at: str


# ──────────────────────────────────────────────────────────────────────────────
# Seed helpers — populate app_state with mock vehicles if empty
# ──────────────────────────────────────────────────────────────────────────────
_MOCK_VEHICLE_IDS = [f"VEH{str(i).zfill(3)}" for i in range(1, 11)]
_SCENARIOS = ["normal", "normal", "normal", "normal", "warning", "warning", "warning", "critical", "critical", "normal"]
_PRIORITY_MAP = {"normal": "P3", "warning": "P2", "critical": "P0"}


def _seed_mock_vehicles():
    """Populate app_state with 10 mock vehicles if none exist yet."""
    if app_state.vehicles:
        return

    for vid, scenario in zip(_MOCK_VEHICLE_IDS, _SCENARIOS):
        telem = _data_gen.generate_telematics_timeseries(vid, scenario)
        master = _data_gen.generate_vehicle_master(vid)
        customer = _data_gen.generate_customer_profile(master["customer_id"])
        history = _data_gen.generate_maintenance_history(vid)

        priority = _PRIORITY_MAP.get(scenario, "P3")
        health_score = {"P0": random.uniform(0.15, 0.35),
                        "P1": random.uniform(0.35, 0.55),
                        "P2": random.uniform(0.55, 0.75),
                        "P3": random.uniform(0.80, 0.98)}[priority]

        failure_prob = round(1 - health_score, 2)

        merged = {
            **master,
            "telematics": telem,
            "customer": customer,
            "maintenance_history": history,
            "priority": priority,
            "scenario": scenario,
            "health_score": round(health_score, 2),
            "failure_probability": failure_prob,
            "diagnosis": {
                "status": "completed" if scenario != "normal" else "healthy",
                "severity": scenario,
                "predicted_component": random.choice(["brake_pads", "battery", "coolant_system", "tires"]) if scenario != "normal" else None,
                "rul_days": random.randint(5, 30) if scenario != "normal" else None,
                "confidence": round(random.uniform(0.7, 0.95), 2),
            },
            "workflow_state": "completed",
        }

        app_state.upsert_vehicle(vid, merged)

        # Fire alerts for critical vehicles
        if priority in ("P0", "P1"):
            app_state.fire_alert({
                "vehicle_id": vid,
                "priority": priority,
                "message": f"{master['make']} {master['model']} — {scenario} condition detected",
                "component": merged["diagnosis"]["predicted_component"],
            })


def _seed_mock_bookings():
    """Populate app_state with mock bookings if none exist."""
    if app_state.bookings:
        return

    techs = ["Alice Rodriguez", "Bob Chen", "Carlos Diaz", "Diana Kim"]
    bays = ["BAY-A", "BAY-B", "BAY-C", "BAY-D"]
    components = ["brake_pads", "battery", "coolant_system", "tires"]

    for i in range(6):
        slot = datetime.now().replace(hour=9, minute=0, second=0) + timedelta(hours=i * 2)
        vid = random.choice(_MOCK_VEHICLE_IDS)
        vehicle = app_state.get_vehicle(vid) or {}

        app_state.add_booking({
            "booking_id": f"BK{datetime.now().strftime('%Y%m%d')}-{i:04d}",
            "vehicle_id": vid,
            "customer_id": vehicle.get("customer_id", f"CUST{i:03d}"),
            "customer_name": vehicle.get("customer", {}).get("name", "N/A"),
            "slot_time": slot.strftime("%A, %d %B %Y at %I:%M %p"),
            "slot_time_iso": slot.isoformat(),
            "technician_name": techs[i % len(techs)],
            "bay": bays[i % len(bays)],
            "service_component": components[i % len(components)],
            "service_duration_hours": round(random.uniform(1.0, 3.0), 1),
            "priority": vehicle.get("priority", "P3"),
            "status": "CONFIRMED",
        })


def _seed_mock_conversations():
    """Populate app_state with mock conversation turns."""
    if app_state.conversations:
        return

    templates = [
        ("OUTBOUND", "Hi {name}, our diagnostics flagged a potential {comp} issue on your {car}. When works for a quick service?"),
        ("INBOUND",  "How urgent is it? I'm pretty busy this week."),
        ("OUTBOUND", "Our data shows about {days} days of remaining life. We'd recommend booking within the next few days to be safe."),
        ("INBOUND",  "Alright, I can do Thursday morning."),
        ("OUTBOUND", "Perfect — I've booked you for Thursday at 10 AM with technician Alice. You'll get a confirmation SMS shortly."),
    ]

    for vid in random.sample(_MOCK_VEHICLE_IDS, min(4, len(_MOCK_VEHICLE_IDS))):
        vehicle = app_state.get_vehicle(vid) or {}
        name = vehicle.get("customer", {}).get("name", "Customer")
        car = f"{vehicle.get('make', 'Vehicle')} {vehicle.get('model', '')}"
        comp = vehicle.get("diagnosis", {}).get("predicted_component") or "brake_pads"
        days = vehicle.get("diagnosis", {}).get("rul_days") or 15

        for j, (direction, tpl) in enumerate(templates):
            msg = tpl.format(name=name.split()[0], comp=comp.replace("_", " "), car=car, days=days)
            app_state.add_conversation_turn({
                "vehicle_id": vid,
                "customer_id": vehicle.get("customer_id"),
                "customer_name": name,
                "direction": direction,
                "channel": "WHATSAPP",
                "message": msg,
                "turn_number": j + 1,
                "status": "OPEN",
            })


def seed_all():
    """Seed mock data into app_state (idempotent)."""
    _seed_mock_vehicles()
    _seed_mock_bookings()
    _seed_mock_conversations()


# ──────────────────────────────────────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────────────────────────────────────
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """
    Mock login — accepts any credentials, returns a fake JWT.
    The frontend stores this in localStorage.
    """
    import base64

    payload = {
        "role": body.role,
        "email": body.email,
        "exp": (datetime.now() + timedelta(hours=24)).isoformat(),
    }
    token = base64.b64encode(json.dumps(payload).encode()).decode()

    return LoginResponse(
        token=token,
        role=body.role,
        email=body.email,
        expires_at=payload["exp"],
    )


# ──────────────────────────────────────────────────────────────────────────────
# VEHICLES
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/vehicles")
async def list_vehicles():
    """Return all vehicles currently tracked in app_state."""
    return app_state.get_all_vehicles()


@api_router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    """Return a single vehicle with full telemetry + diagnosis."""
    v = app_state.get_vehicle(vehicle_id)
    if not v:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")
    return v


@api_router.get("/vehicles/{vehicle_id}/manufacturing")
async def get_vehicle_manufacturing(vehicle_id: str):
    """Return DTC codes + recall data for a vehicle."""
    mfg = app_state.get_manufacturing(vehicle_id)
    if mfg:
        return mfg

    # Lazy-generate manufacturing data via the agent
    try:
        from manufacturing_agent import ManufacturingAgent
        agent = ManufacturingAgent()
        data = agent.check_vehicle(vehicle_id)
        app_state.set_manufacturing(vehicle_id, data)
        return data
    except Exception as e:
        return {"vehicle_id": vehicle_id, "dtc_codes": [], "recalls": [], "error": str(e)}


# ──────────────────────────────────────────────────────────────────────────────
# BOOKINGS
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/bookings")
async def list_bookings():
    """All bookings (confirmed + pending)."""
    return app_state.get_all_bookings()


@api_router.get("/bookings/today")
async def list_todays_bookings():
    """Only today's bookings — used for the bay calendar."""
    return app_state.get_todays_bookings()


@api_router.post("/bookings")
async def create_booking(body: dict = Body(...)):
    """
    Create a new booking from the dashboard (operator manually adds).
    Expects: vehicle_id, service_component, slot_time_iso, technician_name,
             bay, priority, service_duration_hours (optional, default 1.5).
    """
    import uuid
    booking = {
        "booking_id":            f"BK{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        "vehicle_id":            body.get("vehicle_id", "UNKNOWN"),
        "service_component":     body.get("service_component", "General"),
        "slot_time_iso":         body.get("slot_time_iso", datetime.now().isoformat()),
        "technician_name":       body.get("technician_name", "Unassigned"),
        "bay":                   body.get("bay", "BAY-1"),
        "priority":              body.get("priority", "P3"),
        "status":                body.get("status", "CONFIRMED"),
        "service_duration_hours":float(body.get("service_duration_hours", 1.5)),
        "customer_name":         body.get("customer_name", ""),
        "created_at":            datetime.now().isoformat(),
        "source":                "dashboard",
    }
    app_state.add_booking(booking)
    return booking


@api_router.patch("/bookings/{booking_id}")
async def update_booking(booking_id: str, body: dict = Body(...)):
    """
    Update an existing booking (slot time, status, duration, technician, bay).
    The frontend uses this for drag/drop reschedule + status changes.
    """
    for b in app_state.bookings:   # iterate real list, not a copy
        if b.get("booking_id") == booking_id:
            b.update({k: v for k, v in body.items() if v is not None})
            b["updated_at"] = datetime.now().isoformat()
            return b
    raise HTTPException(404, f"Booking {booking_id} not found")


@api_router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str):
    """Cancel (delete) a booking by ID."""
    for i, b in enumerate(app_state.bookings):   # iterate real list, not a copy
        if b.get("booking_id") == booking_id:
            cancelled = app_state.bookings.pop(i)
            cancelled["status"] = "CANCELLED"
            cancelled["cancelled_at"] = datetime.now().isoformat()
            app_state._broadcast(DashboardEvent.make(
                DashboardEvent.BOOKING_CANCELLED,
                {"booking_id": booking_id},
            ))
            return cancelled
    raise HTTPException(404, f"Booking {booking_id} not found")


@api_router.get("/availability")
async def get_availability(date: str = Query(None, description="ISO date YYYY-MM-DD")):
    """
    Return available service slots for a given date.
    Stubs 8 one-hour slots per day; subtracts any existing bookings.
    """
    target = date or datetime.now().strftime("%Y-%m-%d")

    try:
        target_dt = datetime.strptime(target, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "Invalid date format — use YYYY-MM-DD")

    # Build raw slots 9 AM – 5 PM
    all_slots = []
    for hour in range(9, 17):
        slot_dt = target_dt.replace(hour=hour, minute=0, second=0)
        all_slots.append({
            "slot_time": slot_dt.strftime("%I:%M %p"),
            "slot_time_iso": slot_dt.isoformat(),
            "available": True,
        })

    # Mark booked slots
    booked_hours = set()
    for b in app_state.get_all_bookings():
        iso = b.get("slot_time_iso", "")
        if iso[:10] == target:
            try:
                booked_hours.add(datetime.fromisoformat(iso).hour)
            except Exception:
                pass

    for slot in all_slots:
        try:
            h = datetime.fromisoformat(slot["slot_time_iso"]).hour
            if h in booked_hours:
                slot["available"] = False
        except Exception:
            pass

    return {"date": target, "slots": all_slots}


# ──────────────────────────────────────────────────────────────────────────────
# CONVERSATIONS
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/conversations")
async def list_conversations():
    """Return all conversation turns, newest first."""
    convos = app_state.get_all_conversations()
    return list(reversed(convos))


# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/dashboard/summary")
async def dashboard_summary():
    """Aggregated KPIs for the dashboard header cards."""
    return app_state.get_summary()


@api_router.get("/dashboard/alerts")
async def dashboard_alerts():
    """Active P0/P1 alerts."""
    return app_state.get_active_alerts()


# ──────────────────────────────────────────────────────────────────────────────
# MANUFACTURING / RECALLS
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/manufacturing/summary")
async def manufacturing_summary():
    """
    Aggregated DTC + recall summary across all tracked vehicles.
    """
    total_dtcs = 0
    total_recalls = 0
    vehicles_with_recalls = []

    for vid in app_state.vehicles:
        mfg = app_state.get_manufacturing(vid)
        if not mfg:
            # Lazy-generate
            try:
                from manufacturing_agent import ManufacturingAgent
                agent = ManufacturingAgent()
                mfg = agent.check_vehicle(vid)
                app_state.set_manufacturing(vid, mfg)
            except Exception:
                continue

        dtcs = mfg.get("dtc_codes", [])
        recalls = mfg.get("recalls", [])
        total_dtcs += len(dtcs)
        total_recalls += len(recalls)

        if recalls:
            vehicles_with_recalls.append({
                "vehicle_id": vid,
                "recall_count": len(recalls),
                "recalls": recalls,
            })

    return {
        "total_vehicles_checked": len(app_state.vehicles),
        "total_dtc_codes": total_dtcs,
        "total_open_recalls": total_recalls,
        "vehicles_with_recalls": vehicles_with_recalls,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/monthly")
async def analytics_monthly():
    """
    Month-over-month analytics stub.
    Returns 6 months of mock data — will switch to real aggregation in Week 5.
    """
    months = []
    now = datetime.now()

    for i in range(5, -1, -1):
        month_dt = now - timedelta(days=30 * i)
        month_label = month_dt.strftime("%b %Y")

        months.append({
            "month": month_label,
            "bookings": random.randint(40, 120),
            "acceptance_rate": round(random.uniform(0.65, 0.92), 2),
            "avg_rul_days": random.randint(8, 25),
            "cost_avoidance_usd": random.randint(8000, 35000),
            "vehicles_serviced": random.randint(30, 100),
        })

    return {"months": months}


# ──────────────────────────────────────────────────────────────────────────────
# AI DIAGNOSIS (Phase 1)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.post("/vehicles/{vehicle_id}/diagnose")
async def trigger_diagnosis(vehicle_id: str):
    """
    Trigger the full AI diagnosis pipeline for a single vehicle.
    Calls DataAnalysisAgentV4 → DiagnosisAgentV4 → ManufacturingAgent → SchedulingAgent.
    Returns the merged diagnosis result.
    """
    v = app_state.get_vehicle(vehicle_id)
    if not v:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    from diagnosis_orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    try:
        result = await orchestrator.run_diagnosis(vehicle_id)
        return {"vehicle_id": vehicle_id, "diagnosis": result}
    except Exception as e:
        raise HTTPException(500, f"Diagnosis failed: {str(e)}")


# ──────────────────────────────────────────────────────────────────────────────
# VEHICLE TELEMATICS HISTORY (Phase 1)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/vehicles/{vehicle_id}/history")
async def get_vehicle_history(vehicle_id: str, days: int = Query(7, ge=1, le=30)):
    """
    Return 7-day (default) telematics time-series for a vehicle.
    Used by sparkline / trend charts on the frontend.
    """
    v = app_state.get_vehicle(vehicle_id)
    if not v:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    scenario = v.get("scenario", "normal")
    history = _data_gen.generate_telematics_history(vehicle_id, scenario, days=days)
    return {"vehicle_id": vehicle_id, "days": days, "history": history}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — FLEET (Phase 1)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/fleet")
async def analytics_fleet():
    """
    Fleet-wide aggregated KPIs derived from real app_state data.
    """
    vehicles = app_state.get_all_vehicles()
    total = len(vehicles)
    if total == 0:
        return {"total": 0}

    health_scores = [v.get("health_score", 0.5) for v in vehicles]
    rul_values = [
        v.get("diagnosis", {}).get("rul_days")
        for v in vehicles
        if v.get("diagnosis", {}).get("rul_days") is not None
    ]

    critical = sum(1 for v in vehicles if v.get("priority") in ("P0", "P1"))
    warning = sum(1 for v in vehicles if v.get("priority") == "P2")
    healthy = total - critical - warning

    bookings = app_state.get_all_bookings()
    completed = sum(1 for b in bookings if b.get("status") == "COMPLETED")
    pending = sum(1 for b in bookings if b.get("status") in ("CONFIRMED", "PENDING"))

    return {
        "total_vehicles": total,
        "critical": critical,
        "warning": warning,
        "healthy": healthy,
        "avg_health_score": round(sum(health_scores) / total, 2),
        "avg_rul_days": round(sum(rul_values) / len(rul_values), 1) if rul_values else None,
        "rul_distribution": {
            "under_7": sum(1 for r in rul_values if r < 7),
            "7_to_30": sum(1 for r in rul_values if 7 <= r <= 30),
            "over_30": sum(1 for r in rul_values if r > 30),
        } if rul_values else {},
        "bookings_total": len(bookings),
        "bookings_completed": completed,
        "bookings_pending": pending,
        "service_completion_rate": round(completed / len(bookings), 2) if bookings else 0,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — REVENUE (Phase 1)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/revenue")
async def analytics_revenue():
    """
    Revenue trend derived from bookings + maintenance cost data.
    Returns 6 months of data (real bookings for current month, projected for past).
    """
    now = datetime.now()
    months = []

    for i in range(5, -1, -1):
        month_dt = now - timedelta(days=30 * i)
        label = month_dt.strftime("%b %Y")

        if i == 0:
            # Current month — derive from actual bookings
            bookings = app_state.get_all_bookings()
            revenue = sum(
                random.uniform(150, 800) for b in bookings
            )
            cost_avoidance = sum(
                random.uniform(200, 1200)
                for v in app_state.get_all_vehicles()
                if v.get("priority") in ("P0", "P1", "P2")
            )
        else:
            # Historical months — realistic projections
            base_revenue = random.randint(12000, 45000)
            revenue = base_revenue
            cost_avoidance = random.randint(8000, 35000)

        months.append({
            "month": label,
            "revenue_usd": round(revenue, 2),
            "cost_avoidance_usd": round(cost_avoidance, 2),
            "net_value": round(revenue + cost_avoidance, 2),
        })

    return {"months": months}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — WORKLOAD (Phase 1)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/workload")
async def analytics_workload():
    """
    Technician utilisation per bay — derived from today's bookings.
    """
    bookings = app_state.get_all_bookings()

    tech_hours: Dict[str, float] = {}
    bay_hours: Dict[str, float] = {}

    for b in bookings:
        tech = b.get("technician_name", "Unknown")
        bay = b.get("bay", "Unknown")
        dur = b.get("service_duration_hours", 2.0)

        tech_hours[tech] = tech_hours.get(tech, 0) + dur
        bay_hours[bay] = bay_hours.get(bay, 0) + dur

    max_hours = 8.0  # 8-hour work day
    technicians = [
        {
            "name": t,
            "hours_booked": round(h, 1),
            "utilisation": round(min(h / max_hours, 1.0), 2),
        }
        for t, h in sorted(tech_hours.items(), key=lambda x: -x[1])
    ]
    bays = [
        {
            "bay": b,
            "hours_booked": round(h, 1),
            "utilisation": round(min(h / max_hours, 1.0), 2),
        }
        for b, h in sorted(bay_hours.items(), key=lambda x: -x[1])
    ]

    return {"technicians": technicians, "bays": bays}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — ESCALATIONS (Phase 1)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/escalations")
async def analytics_escalations():
    """
    Escalation rate and reasons breakdown.
    Derives data from alerts + conversation state.
    """
    alerts = app_state.get_active_alerts()
    vehicles = app_state.get_all_vehicles()

    # Break down escalation reasons
    reasons: Dict[str, int] = {}
    for a in alerts:
        comp = a.get("component", "unknown")
        reasons[comp] = reasons.get(comp, 0) + 1

    # SLA breach risk: vehicles with RUL < 7 and no booking
    booked_vids = {b.get("vehicle_id") for b in app_state.get_all_bookings()}
    sla_risk = []
    for v in vehicles:
        rul = v.get("diagnosis", {}).get("rul_days")
        vid = v.get("vehicle_id")
        if rul is not None and rul < 7 and vid not in booked_vids:
            sla_risk.append({
                "vehicle_id": vid,
                "rul_days": rul,
                "priority": v.get("priority"),
                "component": v.get("diagnosis", {}).get("predicted_component"),
            })

    total_vehicles = len(vehicles) or 1
    return {
        "total_alerts": len(alerts),
        "escalation_rate": round(len(alerts) / total_vehicles, 2),
        "reasons_breakdown": [
            {"reason": r, "count": c} for r, c in sorted(reasons.items(), key=lambda x: -x[1])
        ],
        "sla_breach_risk": sla_risk,
        "sla_breach_count": len(sla_risk),
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — CONVERSATION VOLUME (Phase 3)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/conversation-volume")
async def analytics_conversation_volume():
    """30-day daily conversation volume — real from conversations + synthetic backfill."""
    convos = app_state.get_all_conversations()
    now = datetime.now()

    # Build a 30-day series with realistic synthetic data
    daily = {}
    for i in range(29, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily[day] = {"date": day, "inbound": 0, "outbound": 0, "total": 0}

    # Fill from real conversation data
    for c in convos:
        ts = c.get("created_at", now.isoformat())[:10]
        if ts in daily:
            d = c.get("direction", "INBOUND")
            daily[ts]["inbound" if d == "INBOUND" else "outbound"] += 1
            daily[ts]["total"] += 1

    # Backfill empty days with realistic synthetic data
    for day_key, row in daily.items():
        if row["total"] == 0:
            base = random.randint(4, 18)
            row["inbound"] = base
            row["outbound"] = random.randint(max(1, base - 5), base + 3)
            row["total"] = row["inbound"] + row["outbound"]

    return {"days": list(daily.values())}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — AGENT PERFORMANCE (Phase 3)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/agent-performance")
async def analytics_agent_performance():
    """Per-agent radar metrics: conversion, escalation, booking velocity, sentiment, response time."""
    convos = app_state.get_all_conversations()
    bookings = app_state.get_all_bookings()
    tech_names = list({b.get("technician_name", "Unknown") for b in bookings})

    if not tech_names:
        tech_names = ["Alice Rodriguez", "Bob Chen", "Carlos Diaz", "Diana Kim"]

    agents = []
    for name in tech_names:
        agents.append({
            "agent": name,
            "conversion": random.randint(55, 95),
            "escalation": random.randint(5, 35),
            "booking_velocity": random.randint(40, 90),
            "sentiment": random.randint(60, 95),
            "response_time": random.randint(50, 95),
        })
    return {"agents": agents}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — BOOKING FUNNEL (Phase 3)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/booking-funnel")
async def analytics_booking_funnel():
    """Prospect → Contacted → Booked → Serviced funnel derived from conversations + bookings."""
    vehicles = app_state.get_all_vehicles()
    convos = app_state.get_all_conversations()
    bookings = app_state.get_all_bookings()

    total = len(vehicles)
    contacted_vids = {c.get("vehicle_id") for c in convos}
    booked_vids = {b.get("vehicle_id") for b in bookings}
    serviced_vids = {b.get("vehicle_id") for b in bookings if b.get("status") == "COMPLETED"}

    return {
        "funnel": [
            {"stage": "Prospects", "count": total},
            {"stage": "Contacted", "count": len(contacted_vids)},
            {"stage": "Booked", "count": len(booked_vids)},
            {"stage": "Serviced", "count": len(serviced_vids)},
        ]
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — ESCALATION HEATMAP (Phase 3)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/escalation-heatmap")
async def analytics_escalation_heatmap():
    """Day-of-week × hour heatmap of escalation frequency (synthetic + real signals)."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = list(range(8, 20))  # 8 AM to 7 PM

    cells = []
    for d in days:
        for h in hours:
            # Peak escalations Mon/Tue mornings and Friday afternoons
            base = 1
            if d in ("Mon", "Tue") and h < 12:
                base = random.randint(3, 8)
            elif d == "Fri" and h > 14:
                base = random.randint(4, 9)
            elif d in ("Sat", "Sun"):
                base = random.randint(0, 2)
            else:
                base = random.randint(1, 5)
            cells.append({"day": d, "hour": h, "count": base})

    return {"heatmap": cells, "days": days, "hours": hours}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — ESCALATION TREND (Phase 3)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/escalation-trend")
async def analytics_escalation_trend():
    """Week-over-week escalation trend for the last 8 weeks."""
    now = datetime.now()
    weeks = []
    for i in range(7, -1, -1):
        week_start = now - timedelta(weeks=i)
        label = f"W{week_start.isocalendar()[1]}"
        weeks.append({
            "week": label,
            "escalations": random.randint(3, 18),
            "resolved": random.randint(2, 15),
        })
    # Ensure resolved <= escalations
    for w in weeks:
        w["resolved"] = min(w["resolved"], w["escalations"])
    return {"weeks": weeks}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — REVENUE BY COMPONENT (Phase 3)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/revenue-by-component")
async def analytics_revenue_by_component():
    """Revenue breakdown by service component type."""
    bookings = app_state.get_all_bookings()
    comp_rev = {}
    for b in bookings:
        comp = (b.get("service_component") or "general").replace("_", " ").title()
        cost = random.uniform(150, 800)
        comp_rev[comp] = comp_rev.get(comp, 0) + cost

    # If no live data, use realistic defaults
    if not comp_rev:
        comp_rev = {
            "Brake Pads": 12400, "Battery": 9800, "Coolant System": 7600,
            "Tires": 11200, "Oil Change": 5400, "Transmission": 15600,
        }

    return {
        "components": [
            {"component": c, "revenue_usd": round(v, 2)}
            for c, v in sorted(comp_rev.items(), key=lambda x: -x[1])
        ]
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — REVENUE FORECAST (Phase 3)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/revenue-forecast")
async def analytics_revenue_forecast():
    """6-month historical + 3-month forecast using simple linear projection."""
    now = datetime.now()
    historical = []

    for i in range(5, -1, -1):
        month_dt = now - timedelta(days=30 * i)
        label = month_dt.strftime("%b %Y")
        rev = random.randint(18000, 45000)
        historical.append({"month": label, "revenue_usd": rev, "type": "actual"})

    # Simple linear forecast: take last 3 months average and project
    last3 = [h["revenue_usd"] for h in historical[-3:]]
    avg = sum(last3) / 3
    growth = 0.05  # 5% month-over-month growth assumption

    forecast = []
    for i in range(1, 4):
        month_dt = now + timedelta(days=30 * i)
        label = month_dt.strftime("%b %Y")
        projected = round(avg * (1 + growth * i))
        forecast.append({"month": label, "revenue_usd": projected, "type": "forecast"})

    return {"historical": historical, "forecast": forecast, "all": historical + forecast}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — BAY OCCUPANCY (Phase 3)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/bay-occupancy")
async def analytics_bay_occupancy():
    """Bay occupancy timeline for Gantt chart — today's bookings per bay."""
    bookings = app_state.get_all_bookings()
    slots = []

    for b in bookings:
        iso = b.get("slot_time_iso")
        if not iso:
            continue
        try:
            start = datetime.fromisoformat(iso)
        except Exception:
            continue
        dur = b.get("service_duration_hours", 2.0)
        end = start + timedelta(hours=dur)
        slots.append({
            "bay": b.get("bay", "BAY-?"),
            "vehicle_id": b.get("vehicle_id"),
            "technician": b.get("technician_name", "Unassigned"),
            "start_hour": start.hour + start.minute / 60,
            "end_hour": end.hour + end.minute / 60,
            "duration_hours": dur,
            "priority": b.get("priority", "P3"),
            "component": (b.get("service_component") or "general").replace("_", " "),
        })

    # Sort by bay then start time
    slots.sort(key=lambda s: (s["bay"], s["start_hour"]))
    bays = sorted({s["bay"] for s in slots})
    return {"slots": slots, "bays": bays}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — SERVICE DURATION STATS (Phase 3)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/service-duration")
async def analytics_service_duration():
    """Service duration statistics for box plot — grouped by service type."""
    bookings = app_state.get_all_bookings()
    comp_durations: Dict[str, list] = {}

    for b in bookings:
        comp = (b.get("service_component") or "general").replace("_", " ").title()
        dur = b.get("service_duration_hours", 2.0)
        comp_durations.setdefault(comp, []).append(dur)

    # Backfill with synthetic data if sparse
    defaults = {"Brake Pads": [1.2, 1.5, 1.8, 2.0, 2.3, 1.6, 2.5],
                "Battery": [0.8, 1.0, 1.2, 1.5, 1.1, 0.9, 1.3],
                "Coolant System": [1.5, 2.0, 2.5, 2.8, 1.8, 2.2, 3.0],
                "Tires": [0.5, 0.8, 1.0, 1.2, 0.7, 0.9, 1.1],
                "Transmission": [3.0, 3.5, 4.0, 4.5, 3.2, 3.8, 5.0]}

    for comp, vals in defaults.items():
        if comp not in comp_durations or len(comp_durations[comp]) < 3:
            comp_durations[comp] = vals

    result = []
    for comp, durations in comp_durations.items():
        s = sorted(durations)
        n = len(s)
        q1 = s[n // 4] if n >= 4 else s[0]
        median = s[n // 2]
        q3 = s[3 * n // 4] if n >= 4 else s[-1]
        result.append({
            "component": comp,
            "min": round(s[0], 1),
            "q1": round(q1, 1),
            "median": round(median, 1),
            "q3": round(q3, 1),
            "max": round(s[-1], 1),
            "values": [round(v, 1) for v in s],
        })

    return {"components": result}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — BOOKING VELOCITY (Phase 3)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/booking-velocity")
async def analytics_booking_velocity():
    """Bookings per hour today vs same day last week."""
    bookings = app_state.get_all_bookings()
    now = datetime.now()

    today_count = 0
    for b in bookings:
        iso = b.get("slot_time_iso")
        if iso:
            try:
                bt = datetime.fromisoformat(iso)
                if bt.date() == now.date():
                    today_count += 1
            except Exception:
                pass

    hours_elapsed = max(now.hour - 8, 1)  # assume 8 AM start
    velocity_today = round(today_count / hours_elapsed, 1)
    velocity_last_week = round(random.uniform(0.5, 2.5), 1)

    return {
        "today_total": today_count,
        "velocity_per_hour_today": velocity_today,
        "velocity_per_hour_last_week": velocity_last_week,
        "delta_pct": round(((velocity_today - velocity_last_week) / max(velocity_last_week, 0.1)) * 100, 1),
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — COST AVOIDANCE (Phase 1)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/cost-avoidance")
async def analytics_cost_avoidance():
    """
    Cost saved by predictive maintenance — cumulative waterfall.
    Real logic: every vehicle diagnosed as critical/high that was subsequently
    booked counts as an avoided roadside breakdown ($1,500-$5,000 saved).
    """
    vehicles = app_state.get_all_vehicles()
    booked_vids = {b.get("vehicle_id") for b in app_state.get_all_bookings()}

    items = []
    cumulative = 0
    for v in vehicles:
        vid = v.get("vehicle_id")
        sev = v.get("diagnosis", {}).get("severity", "").upper() if isinstance(v.get("diagnosis", {}).get("severity"), str) else ""
        if sev in ("CRITICAL", "HIGH", "WARNING", "critical", "warning") and vid in booked_vids:
            avoided = random.uniform(1500, 5000)
            cumulative += avoided
            items.append({
                "vehicle_id": vid,
                "component": v.get("diagnosis", {}).get("predicted_component", "unknown"),
                "severity": sev,
                "cost_avoided_usd": round(avoided, 2),
                "cumulative_usd": round(cumulative, 2),
            })

    return {
        "total_cost_avoided_usd": round(cumulative, 2),
        "vehicles_saved": len(items),
        "breakdown": items,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — RECALL HEATMAP (Phase 1)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/recall-heatmap")
async def analytics_recall_heatmap():
    """
    Make/model vs recall component matrix.
    Scans all vehicles' manufacturing data for open recalls.
    """
    vehicles = app_state.get_all_vehicles()
    matrix: Dict[str, Dict[str, int]] = {}  # make → {component → count}
    campaigns: Dict[str, Dict] = {}

    for v in vehicles:
        vid = v.get("vehicle_id")
        make = v.get("make", "Unknown")
        mfg = app_state.get_manufacturing(vid)

        if not mfg:
            try:
                mfg_agent = ManufacturingAgent()
                mfg = mfg_agent.check_vehicle(vid)
                app_state.set_manufacturing(vid, mfg)
            except Exception:
                continue

        for recall in mfg.get("recalls", []):
            comp = recall.get("component", "Unknown")
            matrix.setdefault(make, {})
            matrix[make][comp] = matrix[make].get(comp, 0) + 1

            cid = recall.get("nhtsa_campaign", "")
            if cid and cid not in campaigns:
                campaigns[cid] = {
                    "campaign": cid,
                    "component": comp,
                    "summary": recall.get("summary", ""),
                    "remedy": recall.get("remedy", ""),
                    "affected_makes": [],
                }
            if cid and make not in campaigns[cid]["affected_makes"]:
                campaigns[cid]["affected_makes"].append(make)

    # Flatten matrix for frontend
    heatmap = []
    for make, comps in matrix.items():
        for comp, count in comps.items():
            heatmap.append({"make": make, "component": comp, "count": count})

    return {
        "heatmap": heatmap,
        "campaigns": list(campaigns.values()),
        "total_open_recalls": sum(c for row in matrix.values() for c in row.values()),
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — COMPONENT FAILURE RATE (Phase 4)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/component-failure-rate")
async def analytics_component_failure_rate():
    """Which components fail most across the fleet."""
    vehicles = app_state.get_all_vehicles()
    comp_counts: Dict[str, int] = {}
    for v in vehicles:
        comp = v.get("diagnosis", {}).get("predicted_component")
        if comp:
            label = comp.replace("_", " ").title()
            comp_counts[label] = comp_counts.get(label, 0) + 1

    if not comp_counts:
        comp_counts = {"Brake Pads": 4, "Battery": 3, "Coolant System": 2, "Tires": 3, "Transmission": 1}

    return {
        "components": [
            {"component": c, "failures": n}
            for c, n in sorted(comp_counts.items(), key=lambda x: -x[1])
        ]
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — PREDICTIVE ALERT FUNNEL (Phase 4)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/alert-funnel")
async def analytics_alert_funnel():
    """Alerts → Diagnosed → Booked → Serviced funnel."""
    alerts = app_state.get_active_alerts()
    vehicles = app_state.get_all_vehicles()
    bookings = app_state.get_all_bookings()

    diagnosed_count = sum(1 for v in vehicles if v.get("diagnosis", {}).get("status") not in (None, "healthy"))
    booked_vids = {b.get("vehicle_id") for b in bookings}
    serviced_vids = {b.get("vehicle_id") for b in bookings if b.get("status") == "COMPLETED"}

    return {
        "funnel": [
            {"stage": "Alerts Fired", "count": max(len(alerts), diagnosed_count)},
            {"stage": "Diagnosed", "count": diagnosed_count},
            {"stage": "Booked", "count": len(booked_vids)},
            {"stage": "Serviced", "count": len(serviced_vids)},
        ]
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — CONVERSION BY MAKE (Phase 4)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/conversion-by-make")
async def analytics_conversion_by_make():
    """Booking conversion rate per vehicle make — for scatter plot."""
    vehicles = app_state.get_all_vehicles()
    bookings = app_state.get_all_bookings()
    convos = app_state.get_all_conversations()

    booked_vids = {b.get("vehicle_id") for b in bookings}
    contacted_vids = {c.get("vehicle_id") for c in convos}

    make_stats: Dict[str, Dict] = {}
    for v in vehicles:
        make = v.get("make", "Unknown")
        vid = v.get("vehicle_id")
        if make not in make_stats:
            make_stats[make] = {"make": make, "total": 0, "contacted": 0, "booked": 0}
        make_stats[make]["total"] += 1
        if vid in contacted_vids:
            make_stats[make]["contacted"] += 1
        if vid in booked_vids:
            make_stats[make]["booked"] += 1

    result = []
    for ms in make_stats.values():
        contacted = max(ms["contacted"], 1)
        result.append({
            "make": ms["make"],
            "total_vehicles": ms["total"],
            "contacted": ms["contacted"],
            "booked": ms["booked"],
            "conversion_pct": round((ms["booked"] / contacted) * 100, 1),
        })

    return {"makes": result}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — KPI TRENDS (Phase 4)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/kpi-trends")
async def analytics_kpi_trends():
    """Month-over-month KPI deltas for 6 key metrics."""
    now = datetime.now()
    vehicles = app_state.get_all_vehicles()
    bookings = app_state.get_all_bookings()
    alerts = app_state.get_active_alerts()

    health_scores = [v.get("health_score", 0.5) for v in vehicles]
    avg_health = round(sum(health_scores) / max(len(health_scores), 1), 2)

    completed = sum(1 for b in bookings if b.get("status") == "COMPLETED")
    total_bookings = max(len(bookings), 1)
    completion_rate = round((completed / total_bookings) * 100, 1)

    # Simulate previous month values for delta comparison
    kpis = [
        {"kpi": "Avg Health Score", "current": avg_health, "previous": round(avg_health - random.uniform(-0.05, 0.08), 2), "unit": "", "higher_is_better": True},
        {"kpi": "Service Completion", "current": completion_rate, "previous": round(completion_rate - random.uniform(-5, 8), 1), "unit": "%", "higher_is_better": True},
        {"kpi": "Active Alerts", "current": len(alerts), "previous": len(alerts) + random.randint(-3, 5), "unit": "", "higher_is_better": False},
        {"kpi": "Fleet Size", "current": len(vehicles), "previous": len(vehicles), "unit": "", "higher_is_better": True},
        {"kpi": "Bookings", "current": len(bookings), "previous": len(bookings) + random.randint(-4, 4), "unit": "", "higher_is_better": True},
        {"kpi": "Avg RUL", "current": round(sum((v.get("diagnosis") or {}).get("rul_days") or 30 for v in vehicles) / max(len(vehicles), 1), 1), "previous": round(random.uniform(12, 22), 1), "unit": "d", "higher_is_better": True},
    ]

    for kpi in kpis:
        diff = kpi["current"] - kpi["previous"]
        kpi["delta"] = round(diff, 2)
        if kpi["previous"] != 0:
            kpi["delta_pct"] = round((diff / abs(kpi["previous"])) * 100, 1)
        else:
            kpi["delta_pct"] = 0
        # Determine if the change is positive (good)
        kpi["is_positive"] = (diff > 0) == kpi["higher_is_better"]

    return {"kpis": kpis}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — EXECUTIVE SUMMARY (Phase 4)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/executive-summary")
async def analytics_executive_summary():
    """Generate an AI-style executive summary paragraph from fleet data."""
    vehicles = app_state.get_all_vehicles()
    bookings = app_state.get_all_bookings()
    alerts = app_state.get_active_alerts()

    total = len(vehicles)
    critical = sum(1 for v in vehicles if v.get("priority") in ("P0", "P1"))
    healthy = total - critical
    completed = sum(1 for b in bookings if b.get("status") == "COMPLETED")
    health_scores = [v.get("health_score", 0.5) for v in vehicles]
    avg_health = round(sum(health_scores) / max(total, 1) * 100)

    summary = (
        f"Fleet Status: {total} vehicles monitored, {healthy} healthy, {critical} requiring attention. "
        f"Average fleet health score is {avg_health}%. "
        f"{len(bookings)} service bookings scheduled with {completed} completed. "
        f"{len(alerts)} active alerts flagged by the AI pipeline. "
    )

    if critical > 0:
        crit_vehicles = [v.get("vehicle_id") for v in vehicles if v.get("priority") in ("P0", "P1")][:3]
        summary += f"Priority vehicles: {', '.join(crit_vehicles)}. Immediate scheduling recommended. "
    else:
        summary += "No critical vehicles detected — fleet is operating within normal parameters. "

    rul_low = sum(1 for v in vehicles if (v.get("diagnosis", {}).get("rul_days") or 999) < 7)
    if rul_low > 0:
        summary += f"{rul_low} vehicle(s) have RUL below 7 days and should be serviced urgently."

    return {"summary": summary, "generated_at": datetime.now().isoformat()}


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — ROI DASHBOARD (Phase 4)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/roi")
async def analytics_roi():
    """Cost avoidance vs system operating cost over 6 months."""
    now = datetime.now()
    months = []

    for i in range(5, -1, -1):
        month_dt = now - timedelta(days=30 * i)
        label = month_dt.strftime("%b %Y")
        cost_avoided = random.randint(12000, 45000)
        operating_cost = random.randint(3000, 8000)
        months.append({
            "month": label,
            "cost_avoided_usd": cost_avoided,
            "operating_cost_usd": operating_cost,
            "net_roi_usd": cost_avoided - operating_cost,
            "roi_ratio": round(cost_avoided / max(operating_cost, 1), 1),
        })

    total_saved = sum(m["cost_avoided_usd"] for m in months)
    total_cost = sum(m["operating_cost_usd"] for m in months)

    return {
        "months": months,
        "total_cost_avoided_usd": total_saved,
        "total_operating_cost_usd": total_cost,
        "net_roi_usd": total_saved - total_cost,
        "overall_roi_ratio": round(total_saved / max(total_cost, 1), 1),
    }


# ──────────────────────────────────────────────────────────────────────────────
# ANALYTICS — RECALL DETAILS (Phase 4)
# ──────────────────────────────────────────────────────────────────────────────
@api_router.get("/analytics/recall-details")
async def analytics_recall_details():
    """Recall completion stats + timeline data for donut and bar charts."""
    vehicles = app_state.get_all_vehicles()
    open_recalls = 0
    remedied_recalls = 0
    timeline_items = []

    for v in vehicles:
        vid = v.get("vehicle_id")
        mfg = app_state.get_manufacturing(vid)
        if not mfg:
            continue

        for recall in mfg.get("recalls", []):
            status = recall.get("status", "open").lower()
            if status in ("remedied", "completed", "fixed"):
                remedied_recalls += 1
            else:
                open_recalls += 1
            timeline_items.append({
                "vehicle_id": vid,
                "make": v.get("make", "Unknown"),
                "campaign": recall.get("nhtsa_campaign", "N/A"),
                "component": recall.get("component", "Unknown"),
                "summary": recall.get("summary", ""),
                "status": status,
                "discovery_date": recall.get("discovery_date", "2024-01-15"),
                "remedy_date": recall.get("remedy_date") if status in ("remedied", "completed", "fixed") else None,
            })

    # Backfill if no data
    if not timeline_items:
        open_recalls = 3
        remedied_recalls = 5
        timeline_items = [
            {"vehicle_id": "VEH001", "make": "Toyota", "campaign": "24V-987", "component": "Airbag", "summary": "Front airbag inflator recall", "status": "open", "discovery_date": "2024-01-15", "remedy_date": None},
            {"vehicle_id": "VEH003", "make": "Ford", "campaign": "24V-112", "component": "Brake Line", "summary": "Brake line corrosion", "status": "remedied", "discovery_date": "2024-02-10", "remedy_date": "2024-03-15"},
            {"vehicle_id": "VEH005", "make": "Honda", "campaign": "24V-445", "component": "Fuel Pump", "summary": "Fuel pump failure risk", "status": "open", "discovery_date": "2024-03-01", "remedy_date": None},
        ]

    return {
        "open": open_recalls,
        "remedied": remedied_recalls,
        "total": open_recalls + remedied_recalls,
        "completion_pct": round(remedied_recalls / max(open_recalls + remedied_recalls, 1) * 100, 1),
        "timeline": timeline_items,
    }


# ──────────────────────────────────────────────────────────────────────────────
# WEBSOCKET  —  /ws/dashboard
# ──────────────────────────────────────────────────────────────────────────────
ws_router = APIRouter(tags=["WebSocket"])


@ws_router.websocket("/ws/dashboard")
async def ws_dashboard(ws: WebSocket):
    """
    Live push events for the dashboard.
    On connect: sends a snapshot of current state so charts populate immediately.
    Then streams JSON events whenever app_state mutates.
    """
    await ws.accept()
    queue: asyncio.Queue = asyncio.Queue(maxsize=256)
    app_state.register_ws(queue)

    # ── Send cached snapshot on connect ──────────────────────────────────
    try:
        summary = app_state.get_summary()
        await ws.send_json({
            "type": "SNAPSHOT",
            "payload": {
                "summary": summary,
                "vehicle_count": summary.get("total_vehicles", 0),
                "alert_count": summary.get("active_alerts", 0),
                "booking_count": summary.get("total_bookings", 0),
            },
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })
    except Exception:
        pass  # Non-critical — client will fetch via REST anyway

    # ── Stream events ────────────────────────────────────────────────────
    try:
        while True:
            event = await queue.get()
            await ws.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        app_state.unregister_ws(queue)


# ══════════════════════════════════════════════════════════════════════════════
#  MOBILE / FLUTTER ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

# ── In-memory OTP store (replace with real SMS in prod) ──────────────────────
_otp_store: Dict[str, str] = {}
_customer_fcm: Dict[str, str] = {}

class OtpRequest(BaseModel):
    phone: str

class OtpVerify(BaseModel):
    phone: str
    otp: str

class ConversationMessage(BaseModel):
    vehicle_id: Optional[str] = None
    customer_id: Optional[str] = None
    message: str

class FcmRegister(BaseModel):
    customer_id: str
    token: str

# ── 1. Send OTP ───────────────────────────────────────────────────────────────
@api_router.post("/auth/otp/send")
async def send_otp(body: OtpRequest):
    """Send a 6-digit OTP to the given phone number (mock: always 000000)."""
    otp = "000000"  # TODO: replace with real Twilio/SMS call
    _otp_store[body.phone] = otp
    return {"status": "sent", "phone": body.phone, "debug_otp": otp}


# ── 2. Verify OTP ─────────────────────────────────────────────────────────────
@api_router.post("/auth/otp/verify")
async def verify_otp(body: OtpVerify):
    """Verify OTP and return a session token."""
    stored = _otp_store.get(body.phone)
    if stored is None:
        raise HTTPException(400, "No OTP sent for this phone number")
    if stored != body.otp:
        raise HTTPException(401, "Invalid OTP")
    _otp_store.pop(body.phone, None)
    # Minimal session token (replace with JWT in prod)
    import base64, json as _json
    payload = _json.dumps({"phone": body.phone, "exp": (datetime.now() + timedelta(days=7)).isoformat()})
    token = base64.b64encode(payload.encode()).decode()
    return {"status": "verified", "token": token, "phone": body.phone}


# ── 3. Register customer ──────────────────────────────────────────────────────
@api_router.post("/auth/register")
async def register_customer(body: dict = Body(...)):
    """Register a new customer and link initial vehicle."""
    customer_id = f"CUST-{body.get('phone', 'UNKNOWN')[-4:]}"
    vehicle_id = body.get("vehicle_id")
    entry = {
        "customer_id": customer_id,
        "phone": body.get("phone"),
        "name": body.get("name", ""),
        "vehicle_ids": [vehicle_id] if vehicle_id else [],
        "created_at": datetime.now().isoformat(),
    }
    # Store in a simple dict on app_state (extend as needed)
    if not hasattr(app_state, "_customers"):
        app_state._customers = {}
    app_state._customers[customer_id] = entry
    return entry


# ── 4. Get customer vehicles ──────────────────────────────────────────────────
@api_router.get("/customer/{customer_id}/vehicles")
async def get_customer_vehicles(customer_id: str):
    """Return vehicles linked to a customer account."""
    if not hasattr(app_state, "_customers") or customer_id not in app_state._customers:
        # Fall back to returning all vehicles if customer not registered yet
        return app_state.get_all_vehicles()[:3]
    cust = app_state._customers[customer_id]
    vehicle_ids = cust.get("vehicle_ids", [])
    all_v = {v["vehicle_id"]: v for v in app_state.get_all_vehicles()}
    return [all_v[vid] for vid in vehicle_ids if vid in all_v]


# ── 5. AI Conversation Message ───────────────────────────────────────────────
@api_router.post("/conversations/message")
async def conversation_message(body: ConversationMessage):
    """
    Route a customer message to the AI agent and return a response.
    The AI agent has full context of the vehicle's diagnosis, bookings, alerts.
    Returns: { message: str, action?: { type: str, payload: dict } }
    """
    vehicle_id = body.vehicle_id
    user_text  = body.message.lower().strip()

    # Fetch vehicle context
    vehicle = None
    if vehicle_id:
        all_v = {v["vehicle_id"]: v for v in app_state.get_all_vehicles()}
        vehicle = all_v.get(vehicle_id)

    # Simple intent routing (extend by wiring to customer_engagement.py)
    action = None
    if any(kw in user_text for kw in ["book", "appointment", "service", "schedule"]):
        # Find available slot
        avail_slots = []
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        avail_slots = [
            {"bay": "BAY-3", "time": f"{tomorrow}T10:00:00", "technician": "Rajesh Kumar"},
            {"bay": "BAY-1", "time": f"{tomorrow}T14:00:00", "technician": "Priya Nair"},
        ]
        reply = (
            f"I've found available slots for you. Here's the best match based on your vehicle's diagnosis:\n"
            f"📅 {tomorrow} · 10:00 AM · Bay 3 · Rajesh Kumar"
        )
        action = {"type": "SHOW_BOOKING_CARD", "payload": avail_slots[0]}

    elif any(kw in user_text for kw in ["diagnosis", "health", "status", "check", "problem", "issue"]):
        health_score = vehicle.get("health_score", 75) if vehicle else 75
        alerts = [a for a in app_state.get_all_alerts() if a.get("vehicle_id") == vehicle_id]
        critical = [a for a in alerts if a.get("severity") == "P0"]
        if critical:
            reply = (
                f"⚠️ Your vehicle has {len(critical)} critical issue(s):\n"
                + "\n".join(f"• {a.get('component', 'Unknown')}: {a.get('message', '')}" for a in critical[:3])
                + f"\nOverall health score: {health_score}%. I recommend booking a service soon."
            )
        else:
            reply = f"Your vehicle looks mostly healthy (score: {health_score}%). No critical issues detected right now."
        action = {"type": "SHOW_DIAGNOSIS", "payload": {"vehicle_id": vehicle_id, "health_score": health_score}}

    elif any(kw in user_text for kw in ["cancel", "cancellation"]):
        reply = "To cancel a booking, please go to My Bookings and tap the booking you'd like to cancel."

    elif any(kw in user_text for kw in ["hello", "hi", "hey", "help"]):
        reply = (
            "Hi! I'm your AutoPredict AI assistant. I can help you:\n"
            "• Check your vehicle's health and diagnosis\n"
            "• Book a service appointment\n"
            "• Answer questions about your car\n"
            "What would you like to do?"
        )
    else:
        # Generic fallback
        reply = (
            f"I understand you said: \"{body.message}\". "
            f"I can help with diagnosis, booking, or vehicle health. What do you need?"
        )

    # Store in conversation history
    if not hasattr(app_state, "_conversations"):
        app_state._conversations = {}
    conv_key = vehicle_id or body.customer_id or "general"
    if conv_key not in app_state._conversations:
        app_state._conversations[conv_key] = []
    app_state._conversations[conv_key].append({
        "role": "user", "text": body.message, "ts": datetime.now().isoformat()
    })
    app_state._conversations[conv_key].append({
        "role": "ai", "text": reply, "action": action, "ts": datetime.now().isoformat()
    })

    return {"message": reply, "action": action}


# ── 6. Get conversation history ───────────────────────────────────────────────
@api_router.get("/conversations/{vehicle_id}")
async def get_conversation_history(vehicle_id: str):
    """Return conversation history for a vehicle."""
    if not hasattr(app_state, "_conversations"):
        return []
    return app_state._conversations.get(vehicle_id, [])


# ── 7. Register FCM token ─────────────────────────────────────────────────────
@api_router.post("/fcm/register")
async def register_fcm(body: FcmRegister):
    """Store FCM token for push notification delivery."""
    _customer_fcm[body.customer_id] = body.token
    return {"status": "registered", "customer_id": body.customer_id}


# ── 8. Send push notification (internal helper) ───────────────────────────────
@api_router.post("/fcm/notify")
async def send_push(body: dict = Body(...)):
    """
    Send a push notification to a customer via FCM.
    body: { customer_id, title, message, data? }
    """
    customer_id = body.get("customer_id")
    token = _customer_fcm.get(customer_id)
    if not token:
        raise HTTPException(404, f"No FCM token registered for customer {customer_id}")
    # TODO: call firebase_admin.messaging.send() with the token
    return {
        "status": "queued",
        "customer_id": customer_id,
        "title": body.get("title"),
        "message": body.get("message"),
    }
