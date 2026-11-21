"""
Conversations.

- Staff: every conversation turn (for the dashboard inbox).
- Owners: their in-app thread with the assistant.

The in-app assistant here is still a simple intent router. Phase 1 replaces
it with the Customer Engagement Agent; until then it answers only from data
in the database and never invents slots or prices.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api import queries, serializers
from api.deps import DB, Auth, Staff, get_vehicle_for
from api.events import DashboardEvent, hub
from db import models as m
from db.base import app_tz, iso_local, utcnow
from domain.parts import SCHEDULING_COMPONENT
from services import scheduling as sched

router = APIRouter(prefix="/api", tags=["conversations"])


class ConversationMessage(BaseModel):
    vehicle_id: str
    message: str = Field(min_length=1, max_length=2000)
    customer_id: str | None = None  # ignored; identity comes from the token


@router.get("/conversations")
async def all_turns(current: Staff, db: DB, limit: int = Query(1500, ge=1, le=5000)) -> list[dict]:
    """Every conversation turn, newest first."""
    rows = (
        await db.execute(
            select(m.Message, m.Conversation)
            .join(m.Conversation, m.Message.conversation_id == m.Conversation.id)
            .options(selectinload(m.Conversation.vehicle), selectinload(m.Conversation.owner))
            .order_by(m.Message.created_at.desc())
            .limit(limit)
        )
    ).all()
    return [serializers.message_turn_dict(msg, conv) for msg, conv in rows]


@router.get("/conversations/{vehicle_code}")
async def vehicle_thread(vehicle_code: str, current: Auth, db: DB) -> list[dict]:
    """Chat history for one car (app format: role user|ai)."""
    v = await get_vehicle_for(db, current, vehicle_code)
    msgs = (
        await db.scalars(
            select(m.Message)
            .join(m.Conversation, m.Message.conversation_id == m.Conversation.id)
            .where(m.Conversation.vehicle_id == v.id)
            .order_by(m.Message.created_at)
        )
    ).all()
    return [
        {"role": "user" if x.direction == "INBOUND" else "ai", "text": x.text, "channel": x.channel, "ts": iso_local(x.created_at)}
        for x in msgs
    ]


async def _app_conversation(db: DB, vehicle: m.Vehicle) -> m.Conversation:
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
    return conv


@router.post("/conversations/message")
async def post_message(body: ConversationMessage, current: Auth, db: DB) -> dict:
    vehicle = await get_vehicle_for(db, current, body.vehicle_id)
    pred = (await queries.current_predictions(db, [vehicle.id])).get(vehicle.id)
    text = body.message.lower()
    action = None

    if any(k in text for k in ("book", "appointment", "service", "schedule")):
        component = SCHEDULING_COMPONENT.get(pred.component, "Full Service") if pred and pred.component else "Full Service"
        tomorrow = datetime.now(app_tz()).date() + timedelta(days=1)
        free = [s for s in await sched.availability(db, tomorrow, component) if s["available"]]
        if free:
            reply = f"Tomorrow I can offer {free[0]['slot_time']} for {component.lower()}. Want me to show all slots?"
            action = {"type": "SHOW_BOOKING_CARD", "payload": {"slot_time_iso": free[0]["slot_time_iso"], "component": component}}
        else:
            reply = "Tomorrow is fully booked. Open Bookings to pick another day."
    elif any(k in text for k in ("diagnosis", "health", "status", "check", "problem", "issue")):
        if pred and pred.component:
            reply = f"{pred.reasoning} Recommended: {pred.recommended_action.lower()}."
        elif pred:
            reply = f"No part needs attention right now (health score {round(pred.health_score * 100)}%)."
        else:
            reply = "I don't have enough data for this car yet. Add a service invoice to get started."
        action = {"type": "SHOW_DIAGNOSIS", "payload": {"vehicle_id": vehicle.code, "health_score": pred.health_score if pred else None}}
    elif any(k in text for k in ("cancel", "cancellation")):
        reply = "Open My Bookings and tap the booking you want to cancel."
    else:
        reply = "I can check your car's health, explain what's due, or book a service. What would you like to do?"

    conv = await _app_conversation(db, vehicle)
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
                agent="intent_router",
                turn_number=turn + 2,
                created_at=now + timedelta(milliseconds=1),
            ),
        ]
    )
    await db.commit()
    await hub.publish(DashboardEvent.CONVERSATION_TURN, {"vehicle_id": vehicle.code, "direction": "INBOUND"})
    return {"message": reply, "action": action}
