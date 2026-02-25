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

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app_state import app_state, DashboardEvent
from data_generator import VehicleDataGenerator

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
# WEBSOCKET  —  /ws/dashboard
# ──────────────────────────────────────────────────────────────────────────────
ws_router = APIRouter(tags=["WebSocket"])


@ws_router.websocket("/ws/dashboard")
async def ws_dashboard(ws: WebSocket):
    """
    Live push events for the dashboard.
    Clients connect and receive JSON events whenever app_state mutates.
    """
    await ws.accept()
    queue: asyncio.Queue = asyncio.Queue(maxsize=256)
    app_state.register_ws(queue)

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
