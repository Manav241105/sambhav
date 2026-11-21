"""
In-app service advisor (POST /api/chat).

The LLM writes the conversation; facts come from the database (current
prediction, per-part estimates, real workshop availability). The model asks
for the slot picker with the token SHOW_SLOTS; the app then creates the
booking itself through POST /api/bookings, so the server never books on the
model's say-so. (Phase 1 replaces tokens with structured tool calls.)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from api import queries
from api.deps import DB, Auth, get_vehicle_for
from api.events import DashboardEvent, hub
from core.settings import get_settings
from db import models as m
from db.base import app_tz, utcnow
from domain.parts import SCHEDULING_COMPONENT, display
from services import scheduling as sched

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])

_TOKENS = ("SHOW_SLOTS", "BOOKING_CREATED")


class ChatTurn(BaseModel):
    role: str = Field(pattern=r"^(user|assistant)$")
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    vehicle_id: str
    history: list[ChatTurn] = Field(default_factory=list, max_length=40)
    vehicle_context: dict = Field(default_factory=dict)  # optional phone-side readings


def _system_prompt(vehicle: m.Vehicle, pred: m.Prediction | None, active_booking: m.Booking | None) -> str:
    vm = vehicle.vehicle_model
    lines = [
        f"You are AutoPredict's in-app service advisor for the owner's {vm.make} {vm.model} ({vehicle.year}).",
        f"Odometer: {vehicle.odometer_km:,} km.",
    ]
    if pred and pred.component:
        lines += [
            f"Main finding ({pred.model_version}): {pred.reasoning}",
            f"Severity {pred.severity}, priority {pred.priority}, estimated {pred.rul_days} days left"
            + (f" (about {pred.km_left_low:,}–{pred.km_left_high:,} km)" if pred.km_left_low is not None else "")
            + ".",
            f"Recommended: {pred.recommended_action}.",
        ]
    elif pred:
        lines.append("No part currently needs attention; next periodic service as scheduled.")
    else:
        lines.append("No assessment yet for this car.")
    parts = (pred.details or {}).get("parts", {}) if pred else {}
    worn = sorted(parts.values(), key=lambda p: -p["risk"])[:3]
    if worn:
        lines.append(
            "Most-worn parts (share of typical life already USED; 100% = due): "
            + "; ".join(f"{p['name']} {round(p['wear_ratio'] * 100)}% used" for p in worn)
        )
    if active_booking:
        local = active_booking.slot_start.astimezone(app_tz())
        lines.append(
            f"The owner already has a {active_booking.service_component} booking on {local:%a %d %b at %I:%M %p}. "
            "Do not offer another booking; answer questions about it instead."
        )
    lines += [
        "",
        "Rules:",
        "- Use only the facts above. If asked about prices, warranty or anything not above, say you'll check with the workshop.",
        "- Be warm and brief (2-3 sentences). No pressure tactics.",
        "- If the owner wants to book and has no booking, end your reply with the token SHOW_SLOTS.",
    ]
    return "\n".join(lines)


async def _calendar(db: DB, component: str, days: int = 7) -> list[dict]:
    today = datetime.now(app_tz()).date()
    out = []
    for i in range(days):
        day = today + timedelta(days=i)
        slots = await sched.availability(db, day, component)
        for s in slots:
            s["date_label"] = day.strftime("%a, %d %b")
            s["component"] = component  # the app books this slot for this job
        out.append({"date": day.isoformat(), "label": day.strftime("%A, %d %B"), "slots": slots})
    return out


@router.post("/chat")
async def service_chat(body: ChatRequest, current: Auth, db: DB) -> dict:
    vehicle = await get_vehicle_for(db, current, body.vehicle_id)
    vehicle = await db.scalar(queries.vehicle_query().where(m.Vehicle.id == vehicle.id))
    pred = (await queries.current_predictions(db, [vehicle.id])).get(vehicle.id)
    active = await db.scalar(
        select(m.Booking)
        .where(m.Booking.vehicle_id == vehicle.id, m.Booking.status.in_(("PENDING", "CONFIRMED")), m.Booking.slot_start >= utcnow())
        .order_by(m.Booking.slot_start)
        .limit(1)
    )

    settings = get_settings()
    messages = [{"role": "system", "content": _system_prompt(vehicle, pred, active)}]
    messages += [t.model_dump() for t in body.history[-10:]]
    messages.append({"role": "user", "content": body.message})

    llm_ok = True
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 220},
                },
            )
            resp.raise_for_status()
            reply = (resp.json().get("message", {}).get("content") or "").strip()
    except httpx.HTTPError as exc:
        log.warning("Chat LLM unavailable: %s", exc)
        llm_ok, reply = False, ""
    if not reply:
        reply = (
            "The assistant is unavailable right now. You can still book from the Bookings tab."
            if not llm_ok
            else "Could you tell me a bit more about what you need?"
        )

    action, action_data = None, {}
    if "SHOW_SLOTS" in reply and active is None:
        component = SCHEDULING_COMPONENT.get(pred.component, "Full Service") if pred and pred.component else "Full Service"
        action = "SHOW_SLOTS"
        action_data = {"component": component, "calendar": await _calendar(db, component)}
    for token in _TOKENS:
        reply = reply.replace(token, "")
    reply = reply.strip()

    # Keep the thread in the database so staff can see it.
    conv = await db.scalar(
        select(m.Conversation)
        .where(m.Conversation.vehicle_id == vehicle.id, m.Conversation.channel == "APP", m.Conversation.status == "OPEN")
        .order_by(m.Conversation.started_at.desc())
        .limit(1)
    )
    if conv is None:
        conv = m.Conversation(vehicle_id=vehicle.id, owner_id=vehicle.owner_id, channel="APP", status="OPEN")
        db.add(conv)
        await db.flush()
    turn = len((await db.scalars(select(m.Message.id).where(m.Message.conversation_id == conv.id))).all())
    now = utcnow()
    db.add_all(
        [
            m.Message(
                conversation_id=conv.id,
                direction="INBOUND",
                channel="APP",
                text=body.message,
                agent="customer",
                turn_number=turn + 1,
                created_at=now,
            ),
            m.Message(
                conversation_id=conv.id,
                direction="OUTBOUND",
                channel="APP",
                text=reply,
                agent="service_advisor_llm" if llm_ok else "system",
                turn_number=turn + 2,
                created_at=now + timedelta(milliseconds=1),
            ),
        ]
    )
    await db.commit()
    await hub.publish(DashboardEvent.CONVERSATION_TURN, {"vehicle_id": vehicle.code, "direction": "INBOUND"})
    return {
        "reply": reply,
        "action": action,
        "action_data": action_data,
        "assistant_available": llm_ok,
        "component_label": display(pred.component) if pred and pred.component else None,
    }
