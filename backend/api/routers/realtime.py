"""WebSocket push for the dashboard, and push-token registration for the app."""

from __future__ import annotations

import contextlib
import logging

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from api.deps import DB, Auth, Staff, user_from_token
from api.events import hub, make_event
from db import models as m
from db.session import get_sessionmaker

log = logging.getLogger(__name__)
router = APIRouter(tags=["realtime"])


@router.websocket("/ws/dashboard")
async def ws_dashboard(ws: WebSocket, token: str = Query(...)) -> None:
    """Browsers can't set headers on WebSockets, so the access token comes as ?token=."""
    async with get_sessionmaker()() as session:
        try:
            current = await user_from_token(session, token)
        except HTTPException:
            await ws.close(code=4401)
            return
        if not current.is_staff:
            await ws.close(code=4403)
            return
        from api.routers.dashboard import summary

        snapshot = await summary(current, session)

    await ws.accept()
    queue = hub.register()
    try:
        await ws.send_json(
            make_event(
                "SNAPSHOT",
                {
                    "summary": snapshot,
                    "vehicle_count": snapshot["total_vehicles"],
                    "alert_count": snapshot["active_alerts"],
                    "booking_count": snapshot["total_bookings"],
                },
            )
        )
        while True:
            await ws.send_json(await queue.get())
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # network errors on a closing socket
        log.debug("WebSocket closed: %s", exc)
    finally:
        hub.unregister(queue)
        with contextlib.suppress(Exception):
            await ws.close()


class FcmRegister(BaseModel):
    token: str = Field(min_length=10, max_length=512)
    platform: str = Field("android", pattern=r"^(android|ios|web)$")


@router.post("/api/fcm/register")
async def register_push_token(body: FcmRegister, current: Auth, db: DB) -> dict:
    existing = await db.scalar(select(m.FcmToken).where(m.FcmToken.token == body.token))
    if existing:
        existing.user_id, existing.platform = current.id, body.platform
    else:
        db.add(m.FcmToken(user_id=current.id, token=body.token, platform=body.platform))
    await db.commit()
    return {"status": "registered"}


@router.post("/api/fcm/notify", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def send_push(current: Staff) -> dict:
    """Push delivery needs Firebase Admin credentials (Phase 3); fail loudly instead of pretending."""
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Push notifications are not configured yet")
