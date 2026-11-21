"""
Inbound customer replies (Twilio WhatsApp/SMS, email parse services).

Each reply is matched to an owner by phone/email, stored on their latest
conversation with the interpreted intent, and published on the event bus.
Phase 1 subscribes the Master Orchestrator to that event; until then the
dashboard shows the reply and its interpretation.
"""

from __future__ import annotations

import hmac
import logging
import re

from fastapi import APIRouter, Form, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from api.deps import DB, Staff
from api.events import DashboardEvent, hub
from config import EventTypes
from core.settings import get_settings, is_configured
from db import models as m
from db.base import utcnow
from event_system import Event, EventBus

log = logging.getLogger(__name__)
router = APIRouter(tags=["webhooks"])

event_bus = EventBus()  # Phase 1 attaches subscribers (Master Orchestrator)
_interpreter = None


def _get_interpreter():
    """Lazily create the LLM reply interpreter (it falls back to keywords if Ollama is down)."""
    global _interpreter
    if _interpreter is None:
        from config import LlamaModelClient
        from customer_interpreter import CustomerResponseInterpreter

        _interpreter = CustomerResponseInterpreter(LlamaModelClient.create_customer_interpreter_client())
    return _interpreter


async def _verify_twilio(request: Request) -> None:
    settings = get_settings()
    if not is_configured(settings.twilio_auth_token):
        if settings.is_dev:
            return  # local testing without Twilio
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Twilio is not configured")
    from twilio.request_validator import RequestValidator

    form = dict(await request.form())
    url = str(request.url)
    if settings.webhook_base_url:  # behind a tunnel/proxy the public URL differs
        url = settings.webhook_base_url.rstrip("/") + request.url.path
    if not RequestValidator(settings.twilio_auth_token).validate(url, form, request.headers.get("X-Twilio-Signature", "")):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid Twilio signature")


async def _record_reply(db: DB, owner: m.Owner, channel: str, text: str) -> dict:
    conv = await db.scalar(
        select(m.Conversation).where(m.Conversation.owner_id == owner.id).order_by(m.Conversation.started_at.desc()).limit(1)
    )
    if conv is None:
        vehicle = await db.scalar(select(m.Vehicle).where(m.Vehicle.owner_id == owner.id).limit(1))
        if vehicle is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Sender has no vehicle on file")
        conv = m.Conversation(vehicle_id=vehicle.id, owner_id=owner.id, channel=channel, status="OPEN")
        db.add(conv)
        await db.flush()
    vehicle = await db.get(m.Vehicle, conv.vehicle_id)

    interpretation = await _get_interpreter().interpret(raw_message=text, channel=channel, context={"owner": owner.code})
    sentiment = str(interpretation.get("sentiment") or "NEUTRAL").upper()
    turn = len((await db.scalars(select(m.Message.id).where(m.Message.conversation_id == conv.id))).all())
    db.add(
        m.Message(
            conversation_id=conv.id,
            direction="INBOUND",
            channel=channel,
            text=text,
            agent="customer",
            intent=str(interpretation.get("customer_response") or "")[:40] or None,
            sentiment=sentiment if sentiment in ("POSITIVE", "NEUTRAL", "NEGATIVE") else None,
            turn_number=turn + 1,
            created_at=utcnow(),
        )
    )
    if conv.status == "CLOSED":
        conv.status, conv.closed_at = "OPEN", None
    await db.commit()

    await event_bus.publish(
        Event(
            event_type=EventTypes.CUSTOMER_RESPONSE_RECEIVED,
            tenant_id=vehicle.code,
            timestamp=utcnow().isoformat(),
            data={"interpretation": interpretation, "channel": channel, "conversation_id": conv.id},
            priority="HIGH",
        )
    )
    await hub.publish(DashboardEvent.CONVERSATION_TURN, {"vehicle_id": vehicle.code, "direction": "INBOUND"})
    return {
        "status": "processed",
        "vehicle_id": vehicle.code,
        "conversation_id": conv.id,
        "interpretation": interpretation.get("customer_response"),
    }


async def _owner_by_phone(db: DB, raw: str) -> m.Owner:
    phone = re.sub(r"^whatsapp:", "", raw.strip())
    owner = await db.scalar(select(m.Owner).where(m.Owner.phone == phone).limit(1))
    if owner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown sender")
    return owner


@router.post("/webhook/whatsapp")
async def whatsapp(request: Request, db: DB, From: str = Form(...), Body: str = Form(...)) -> dict:
    await _verify_twilio(request)
    return await _record_reply(db, await _owner_by_phone(db, From), "WHATSAPP", Body)


@router.post("/webhook/sms")
async def sms(request: Request, db: DB, From: str = Form(...), Body: str = Form(...)) -> dict:
    await _verify_twilio(request)
    return await _record_reply(db, await _owner_by_phone(db, From), "SMS", Body)


class EmailReply(BaseModel):
    sender: EmailStr = Field(alias="from")
    subject: str = ""
    body: str = Field(min_length=1, max_length=20000)


@router.post("/webhook/email")
async def email(payload: EmailReply, request: Request, db: DB) -> dict:
    settings = get_settings()
    secret = request.headers.get("X-Webhook-Secret")
    expected = settings.email_webhook_secret
    if is_configured(expected):
        if not secret or not hmac.compare_digest(secret, expected):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Missing or invalid webhook secret")
    elif not settings.is_dev:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "EMAIL_WEBHOOK_SECRET is not configured")
    owner = await db.scalar(select(m.Owner).where(m.Owner.email == str(payload.sender).lower()).limit(1))
    if owner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown sender")
    return await _record_reply(db, owner, "EMAIL", payload.body)


class SimulatedReply(BaseModel):
    vehicle_id: str
    message: str = Field(min_length=1, max_length=2000)
    channel: str = Field("WHATSAPP", pattern=r"^(WHATSAPP|SMS|EMAIL|APP)$")


@router.post("/test/simulate-response")
async def simulate_response(body: SimulatedReply, current: Staff, db: DB) -> dict:
    """Dev-only: inject a customer reply as if it came from a channel."""
    if not get_settings().is_dev:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    vehicle = await db.scalar(select(m.Vehicle).where(m.Vehicle.code == body.vehicle_id))
    if vehicle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vehicle not found")
    owner = await db.get(m.Owner, vehicle.owner_id)
    return await _record_reply(db, owner, body.channel, body.message)
