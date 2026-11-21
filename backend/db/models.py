"""
ORM models — the single schema shared by real users and the demo simulator.

Conventions
- Integer surrogate keys; human-facing codes (VEH001, BK-…) live in `code`.
- All timestamps are `UTCDateTime` (aware UTC in Python).
- Money is stored in whole rupees (`*_inr`).
- Rows created by the simulator carry `is_demo = True` where it matters.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, UTCDateTime, utcnow

JSONType = JSON().with_variant(JSONB(), "postgresql")

USER_ROLES = ("owner", "ops", "manager", "executive", "admin")
STAFF_ROLES = ("ops", "manager", "executive", "admin")
BOOKING_STATUSES = ("PENDING", "CONFIRMED", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW")
PRIORITIES = ("P0", "P1", "P2", "P3")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)


# ── Identity & auth ───────────────────────────────────────────────────────────


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint(_in("role", USER_ROLES), name="role_valid"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    owner: Mapped[Owner | None] = relationship(back_populates="user", uselist=False)


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class OtpCode(TimestampMixin, Base):
    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), index=True)
    code_hash: Mapped[str] = mapped_column(String(255))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class FcmToken(TimestampMixin, Base):
    __tablename__ = "fcm_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(512), unique=True)
    platform: Mapped[str] = mapped_column(String(20), default="android")


# ── Owners & vehicles ─────────────────────────────────────────────────────────


class Owner(TimestampMixin, Base):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(60), default="")
    language: Mapped[str] = mapped_column(String(10), default="en")
    preferred_channel: Mapped[str] = mapped_column(String(20), default="APP")
    preferred_contact_time: Mapped[str] = mapped_column(String(20), default="EVENING")
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    user: Mapped[User | None] = relationship(back_populates="owner")
    vehicles: Mapped[list[Vehicle]] = relationship(back_populates="owner")


class VehicleModel(Base):
    __tablename__ = "vehicle_models"
    __table_args__ = (UniqueConstraint("make", "model", "fuel"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    make: Mapped[str] = mapped_column(String(60))
    model: Mapped[str] = mapped_column(String(60))
    fuel: Mapped[str] = mapped_column(String(20))
    segment: Mapped[str] = mapped_column(String(30), default="")
    service_interval_km: Mapped[int] = mapped_column(Integer)
    service_interval_months: Mapped[int] = mapped_column(Integer)
    # part -> {"life_km": int, "life_months": int | None}
    part_lifetimes: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    # part -> {"service_inr": int, "breakdown_inr": int}
    part_costs: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    source: Mapped[str] = mapped_column(String(255), default="")


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id", ondelete="CASCADE"), index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("vehicle_models.id"), index=True)
    year: Mapped[int] = mapped_column(Integer)
    reg_no: Mapped[str | None] = mapped_column(String(20), unique=True)
    vin: Mapped[str | None] = mapped_column(String(20), unique=True)
    purchase_date: Mapped[date | None] = mapped_column(Date)
    city: Mapped[str] = mapped_column(String(60), default="")
    driving_profile: Mapped[str] = mapped_column(String(20), default="mixed")
    monthly_km: Mapped[int] = mapped_column(Integer, default=1000)
    odometer_km: Mapped[int] = mapped_column(Integer, default=0)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    owner: Mapped[Owner] = relationship(back_populates="vehicles")
    vehicle_model: Mapped[VehicleModel] = relationship()


class OdometerReading(Base):
    __tablename__ = "odometer_readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    km: Mapped[int] = mapped_column(Integer)
    read_at: Mapped[datetime] = mapped_column(UTCDateTime)
    source: Mapped[str] = mapped_column(String(20), default="typed")  # typed | photo | trip | sim


class UsageLog(Base):
    """Weekly driving summary (from phone trips, or the simulator)."""

    __tablename__ = "usage_logs"
    __table_args__ = (UniqueConstraint("vehicle_id", "period_start"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    period_start: Mapped[date] = mapped_column(Date)
    days: Mapped[int] = mapped_column(Integer, default=7)
    km: Mapped[float] = mapped_column(Float)
    hard_brakes: Mapped[int] = mapped_column(Integer, default=0)
    city_share: Mapped[float] = mapped_column(Float, default=0.5)


class TelemetrySnapshot(Base):
    """
    Point-in-time vehicle readings. Today written only by the simulator
    (source='sim'); later by an optional OBD dongle. Feeds the diagnosis agents.
    """

    __tablename__ = "telemetry_snapshots"
    __table_args__ = (Index("ix_telemetry_vehicle_time", "vehicle_id", "recorded_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"))
    recorded_at: Mapped[datetime] = mapped_column(UTCDateTime)
    odo_km: Mapped[int] = mapped_column(Integer)
    brake_pad_mm: Mapped[float] = mapped_column(Float)
    battery_voltage_v: Mapped[float] = mapped_column(Float)
    coolant_temp_c: Mapped[float] = mapped_column(Float)
    oil_pressure_bar: Mapped[float] = mapped_column(Float)
    tire_fl_psi: Mapped[float] = mapped_column(Float)
    tire_fr_psi: Mapped[float] = mapped_column(Float)
    tire_rl_psi: Mapped[float] = mapped_column(Float)
    tire_rr_psi: Mapped[float] = mapped_column(Float)
    engine_rpm: Mapped[int] = mapped_column(Integer, default=0)
    speed_kmh: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(20), default="sim")


# ── Workshops ─────────────────────────────────────────────────────────────────


class Workshop(Base):
    __tablename__ = "workshops"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(60))
    address: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str | None] = mapped_column(String(20))
    open_hour: Mapped[int] = mapped_column(Integer, default=8)
    close_hour: Mapped[int] = mapped_column(Integer, default=18)


class Technician(Base):
    __tablename__ = "technicians"

    id: Mapped[int] = mapped_column(primary_key=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    level: Mapped[str] = mapped_column(String(20), default="SENIOR")
    skills: Mapped[list[str]] = mapped_column(JSONType, default=list)


class Bay(Base):
    __tablename__ = "bays"

    id: Mapped[int] = mapped_column(primary_key=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    bay_type: Mapped[str] = mapped_column(String(20), default="STANDARD")


# ── Service history & predictions ─────────────────────────────────────────────


class ServiceRecord(TimestampMixin, Base):
    __tablename__ = "service_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    workshop_id: Mapped[int | None] = mapped_column(ForeignKey("workshops.id", ondelete="SET NULL"))
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id", ondelete="SET NULL"))
    service_date: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    odometer_km: Mapped[int] = mapped_column(Integer)
    service_type: Mapped[str] = mapped_column(String(40), default="periodic")  # periodic | repair | breakdown
    total_cost_inr: Mapped[int] = mapped_column(Integer, default=0)
    invoice_file: Mapped[str | None] = mapped_column(String(255))
    extracted_by: Mapped[str] = mapped_column(String(20), default="manual")  # llm | manual | workshop | sim
    notes: Mapped[str] = mapped_column(Text, default="")

    items: Mapped[list[ServiceItem]] = relationship(back_populates="record", cascade="all, delete-orphan")


class ServiceItem(Base):
    __tablename__ = "service_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("service_records.id", ondelete="CASCADE"), index=True)
    part: Mapped[str] = mapped_column(String(40), index=True)
    action: Mapped[str] = mapped_column(String(20))  # replaced | inspected | repaired | topped_up
    finding: Mapped[str] = mapped_column(String(40), default="ok")  # ok | worn | failed | recall_remedy
    cost_inr: Mapped[int] = mapped_column(Integer, default=0)

    record: Mapped[ServiceRecord] = relationship(back_populates="items")


class SymptomReport(Base):
    __tablename__ = "symptom_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    part_hint: Mapped[str | None] = mapped_column(String(40))
    warning_light: Mapped[str | None] = mapped_column(String(40))
    urgency: Mapped[str] = mapped_column(String(10), default="MEDIUM")
    source: Mapped[str] = mapped_column(String(20), default="app")  # app | chat | sim
    reported_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)


class Prediction(TimestampMixin, Base):
    __tablename__ = "predictions"
    __table_args__ = (
        Index("ix_predictions_vehicle_current", "vehicle_id", "is_current"),
        CheckConstraint(_in("priority", PRIORITIES), name="priority_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"))
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    component: Mapped[str | None] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(10), default="LOW")  # LOW | MEDIUM | HIGH | CRITICAL
    priority: Mapped[str] = mapped_column(String(2), default="P3")
    health_score: Mapped[float] = mapped_column(Float)
    failure_probability: Mapped[float] = mapped_column(Float)
    rul_days: Mapped[int | None] = mapped_column(Integer)
    km_left_low: Mapped[int | None] = mapped_column(Integer)
    km_left_high: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    model_version: Mapped[str] = mapped_column(String(40))
    reasoning: Mapped[str] = mapped_column(Text, default="")
    recommended_action: Mapped[str] = mapped_column(Text, default="")
    details: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    sources: Mapped[list[str]] = mapped_column(JSONType, default=list)


# ── Bookings ──────────────────────────────────────────────────────────────────


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint(_in("status", BOOKING_STATUSES), name="status_valid"),
        CheckConstraint(_in("priority", PRIORITIES), name="priority_valid"),
        Index("ix_bookings_slot", "slot_start"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id"))
    technician_id: Mapped[int | None] = mapped_column(ForeignKey("technicians.id", ondelete="SET NULL"))
    bay_id: Mapped[int | None] = mapped_column(ForeignKey("bays.id", ondelete="SET NULL"))
    prediction_id: Mapped[int | None] = mapped_column(ForeignKey("predictions.id", ondelete="SET NULL"))
    service_component: Mapped[str] = mapped_column(String(40))
    slot_start: Mapped[datetime] = mapped_column(UTCDateTime)
    duration_hours: Mapped[float] = mapped_column(Float)
    actual_duration_hours: Mapped[float | None] = mapped_column(Float)
    priority: Mapped[str] = mapped_column(String(2), default="P3")
    status: Mapped[str] = mapped_column(String(20), default="CONFIRMED")
    source: Mapped[str] = mapped_column(String(20), default="dashboard")  # dashboard | app_chat | agent | sim
    cost_inr: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    vehicle: Mapped[Vehicle] = relationship()
    technician: Mapped[Technician | None] = relationship()
    bay: Mapped[Bay | None] = relationship()


class SlotHold(TimestampMixin, Base):
    __tablename__ = "slot_holds"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id", ondelete="CASCADE"))
    bay_id: Mapped[int] = mapped_column(ForeignKey("bays.id", ondelete="CASCADE"))
    slot_start: Mapped[datetime] = mapped_column(UTCDateTime)
    duration_hours: Mapped[float] = mapped_column(Float)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)


# ── Conversations ─────────────────────────────────────────────────────────────


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(20))  # APP | WHATSAPP | SMS | EMAIL | VOICE_CALL
    status: Mapped[str] = mapped_column(String(20), default="OPEN")  # OPEN | CLOSED | ESCALATED
    outcome: Mapped[str | None] = mapped_column(String(20))  # BOOKED | DECLINED | DELAYED | ESCALATED
    escalation_reason: Mapped[str | None] = mapped_column(String(120))
    escalated_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", order_by="Message.created_at", cascade="all, delete-orphan"
    )
    vehicle: Mapped[Vehicle] = relationship()
    owner: Mapped[Owner] = relationship()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    direction: Mapped[str] = mapped_column(String(10))  # INBOUND | OUTBOUND
    channel: Mapped[str] = mapped_column(String(20))
    text: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(40))
    sentiment: Mapped[str | None] = mapped_column(String(10))  # POSITIVE | NEUTRAL | NEGATIVE
    agent: Mapped[str] = mapped_column(String(40), default="customer_engagement")
    turn_number: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


# ── Alerts, recalls, workflows, memory, audit ─────────────────────────────────


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    priority: Mapped[str] = mapped_column(String(2))
    component: Mapped[str | None] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(40), default="rule_engine")
    fired_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    acknowledged_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class VehicleRecall(Base):
    __tablename__ = "vehicle_recalls"
    __table_args__ = (UniqueConstraint("vehicle_id", "campaign"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    campaign: Mapped[str] = mapped_column(String(40))
    component: Mapped[str] = mapped_column(String(60))
    summary: Mapped[str] = mapped_column(Text)
    remedy: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")  # OPEN | REMEDIED
    notified_at: Mapped[datetime] = mapped_column(UTCDateTime)
    remedied_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    source: Mapped[str] = mapped_column(String(40), default="mock_catalogue")


class WorkflowRun(TimestampMixin, Base):
    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40))  # diagnosis | engagement | followup
    phase: Mapped[str] = mapped_column(String(40), default="started")
    status: Mapped[str] = mapped_column(String(20), default="RUNNING")  # RUNNING | DONE | FAILED
    state: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)


class OwnerMemory(Base):
    __tablename__ = "owner_memory"

    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)


class VehicleMemory(Base):
    __tablename__ = "vehicle_memory"

    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    action: Mapped[str] = mapped_column(String(40))
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str] = mapped_column(String(40))
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONType)
    at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
