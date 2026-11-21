"""Declarative base, shared column types and timezone helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator

from core.settings import get_settings

# Stable constraint names so Alembic migrations are deterministic on every backend.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UTCDateTime(TypeDecorator):
    """
    Timezone-aware datetimes stored as naive UTC.

    SQLite drops timezone info and PostgreSQL keeps it; normalising to naive
    UTC on write and re-attaching UTC on read behaves the same on both.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Naive datetime passed to UTCDateTime; use utcnow() or attach a tz")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


def utcnow() -> datetime:
    return datetime.now(UTC)


@lru_cache
def app_tz() -> ZoneInfo:
    return ZoneInfo(get_settings().app_timezone)


def to_local(value: datetime | None) -> datetime | None:
    return value.astimezone(app_tz()) if value else None


def iso_local(value: datetime | None) -> str | None:
    """ISO-8601 string in the app timezone, with offset (what the clients display)."""
    local = to_local(value)
    return local.isoformat() if local else None
