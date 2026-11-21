"""
Live dashboard events.

Producers call `await hub.publish("BOOKING_CREATED", {...})`. Every connected
WebSocket client gets the event. Without REDIS_URL the hub fans out inside
this process; with REDIS_URL events go through Redis pub/sub so several API
workers (and background workers) reach every client.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from core.settings import get_settings

log = logging.getLogger(__name__)

CHANNEL = "autopredict:dashboard"


class DashboardEvent:
    VEHICLE_UPDATED = "VEHICLE_UPDATED"
    BOOKING_CREATED = "BOOKING_CREATED"
    BOOKING_UPDATED = "BOOKING_UPDATED"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    CONVERSATION_TURN = "CONVERSATION_TURN"
    ALERT_FIRED = "ALERT_FIRED"
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    DIAGNOSIS_UPDATED = "DIAGNOSIS_UPDATED"


def make_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {"type": event_type, "payload": payload, "timestamp": datetime.now(UTC).isoformat()}


class EventHub:
    def __init__(self) -> None:
        self._clients: set[asyncio.Queue] = set()
        self._redis = None
        self._listener: asyncio.Task | None = None

    async def start(self) -> None:
        url = get_settings().redis_url
        if not url:
            return
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(url)
            await self._redis.ping()
            self._listener = asyncio.create_task(self._listen())
            log.info("Event hub using Redis pub/sub")
        except Exception as exc:  # degrade to in-process fan-out
            log.warning("Redis unavailable (%s); using in-process events", exc)
            self._redis = None

    async def stop(self) -> None:
        if self._listener:
            self._listener.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener
        if self._redis:
            await self._redis.aclose()

    def register(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._clients.add(q)
        return q

    def unregister(self, q: asyncio.Queue) -> None:
        self._clients.discard(q)

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        event = make_event(event_type, payload)
        if self._redis:
            try:
                await self._redis.publish(CHANNEL, json.dumps(event, default=str))
                return
            except Exception as exc:
                log.warning("Redis publish failed (%s); delivering locally", exc)
        self._fan_out(event)

    def _fan_out(self, event: dict[str, Any]) -> None:
        for q in list(self._clients):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                log.debug("Dropping event for a slow WebSocket client")

    async def _listen(self) -> None:
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(CHANNEL)
        async for msg in pubsub.listen():
            if msg.get("type") == "message":
                with contextlib.suppress(ValueError):
                    self._fan_out(json.loads(msg["data"]))


hub = EventHub()
