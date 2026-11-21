"""Append-only audit trail for writes made through the API."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from db import models as m


def record(
    session: AsyncSession,
    actor_user_id: int | None,
    action: str,
    entity: str,
    entity_id: str,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> None:
    """Add an audit row to the current transaction (committed with the change)."""
    session.add(m.AuditLog(actor_user_id=actor_user_id, action=action, entity=entity, entity_id=entity_id, before=before, after=after))
