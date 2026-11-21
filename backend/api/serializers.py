"""
DB rows -> JSON shapes the web dashboard and the Flutter app already read.

Field names follow the legacy in-memory API (vehicle_id, slot_time_iso,
technician_name, ...) so the clients keep working; values now come from the
database. Times are ISO-8601 in the app timezone with an explicit offset.
"""

from __future__ import annotations

from typing import Any

from db import models as m
from db.base import iso_local, to_local
from domain.parts import display

_SCENARIO = {"P0": "critical", "P1": "critical", "P2": "warning", "P3": "normal"}


def telemetry_dict(t: m.TelemetrySnapshot | None, vehicle_code: str) -> dict[str, Any] | None:
    if t is None:
        return None
    return {
        "vehicle_id": vehicle_code,
        "timestamp": iso_local(t.recorded_at),
        "odo_km": t.odo_km,
        "brake_pad_mm": t.brake_pad_mm,
        "battery_voltage_v": t.battery_voltage_v,
        "coolant_temp_c": t.coolant_temp_c,
        "oil_pressure_bar": t.oil_pressure_bar,
        "tire_pressure_psi": {"fl": t.tire_fl_psi, "fr": t.tire_fr_psi, "rl": t.tire_rl_psi, "rr": t.tire_rr_psi},
        "engine_rpm": t.engine_rpm,
        "speed_kmh": t.speed_kmh,
        "source": t.source,
    }


def owner_dict(o: m.Owner) -> dict[str, Any]:
    return {
        "customer_id": o.code,
        "name": o.name,
        "phone": o.phone,
        "email": o.email,
        "city": o.city,
        "language": o.language,
        "preferred_contact_method": o.preferred_channel,
        "preferred_contact_time": o.preferred_contact_time,
    }


def diagnosis_dict(p: m.Prediction | None, include_parts: bool = False) -> dict[str, Any]:
    if p is None:
        return {"status": "pending", "severity": None, "predicted_component": None, "rul_days": None, "confidence": None}
    details = p.details or {}
    out = {
        "status": "healthy" if p.severity == "LOW" else "completed",
        "severity": p.severity,
        "predicted_component": p.component,
        "predicted_component_label": display(p.component) if p.component else None,
        "rul_days": p.rul_days,
        "km_left_low": p.km_left_low,
        "km_left_high": p.km_left_high,
        "confidence": p.confidence,
        "failure_probability": p.failure_probability,
        "diagnostic_reasoning": p.reasoning,
        "recommended_action": p.recommended_action,
        "recurring_defect": bool(details.get("recurring_defect")),
        "model_version": p.model_version,
        "sources": p.sources,
        "diagnosed_at": iso_local(p.created_at),
    }
    # Extra fields written by the LLM diagnosis pipeline, when present.
    for key in ("data_analysis", "manufacturing", "suggested_schedule", "failure_mode", "secondary_risks"):
        if key in details:
            out[key] = details[key]
    if include_parts:
        out["parts"] = list((details.get("parts") or {}).values())
    return out


def vehicle_dict(
    v: m.Vehicle,
    prediction: m.Prediction | None,
    telemetry: m.TelemetrySnapshot | None,
    last_service_at=None,
    include_parts: bool = False,
) -> dict[str, Any]:
    vm = v.vehicle_model
    priority = prediction.priority if prediction else "P3"
    return {
        "vehicle_id": v.code,
        "customer_id": v.owner.code,
        "make": vm.make,
        "model": vm.model,
        "year": v.year,
        "fuel": vm.fuel,
        "engine_type": "Diesel" if vm.fuel == "diesel" else "Petrol" if vm.fuel == "petrol" else vm.fuel.title(),
        "segment": vm.segment,
        "vin": v.vin,
        "reg_no": v.reg_no,
        "city": v.city,
        "odometer_km": v.odometer_km,
        "monthly_km": v.monthly_km,
        "driving_profile": v.driving_profile,
        "purchase_date": v.purchase_date.isoformat() if v.purchase_date else None,
        "last_service_date": to_local(last_service_at).date().isoformat() if last_service_at else None,
        "customer": owner_dict(v.owner),
        "telematics": telemetry_dict(telemetry, v.code),
        "priority": priority,
        "scenario": _SCENARIO.get(priority, "normal"),
        "health_score": prediction.health_score if prediction else None,
        "failure_probability": prediction.failure_probability if prediction else None,
        "diagnosis": diagnosis_dict(prediction, include_parts=include_parts),
        "workflow_state": "completed" if prediction else "pending",
        "is_demo": v.is_demo,
        "updated_at": iso_local(prediction.created_at if prediction else v.updated_at),
    }


def booking_dict(b: m.Booking) -> dict[str, Any]:
    start = to_local(b.slot_start)
    return {
        "id": b.id,
        "booking_id": b.code,
        "vehicle_id": b.vehicle.code,
        "customer_id": b.vehicle.owner.code,
        "customer_name": b.vehicle.owner.name,
        "slot_time": start.strftime("%A, %d %B %Y at %I:%M %p"),
        "slot_time_iso": start.isoformat(),
        "technician_id": b.technician.code if b.technician else None,
        "technician_name": b.technician.name if b.technician else "Unassigned",
        "bay": b.bay.code if b.bay else None,
        "service_component": b.service_component,
        "service_duration_hours": b.duration_hours,
        "actual_duration_hours": b.actual_duration_hours,
        "priority": b.priority,
        "status": b.status,
        "source": b.source,
        "cost_inr": b.cost_inr,
        "created_at": iso_local(b.created_at),
        "updated_at": iso_local(b.updated_at),
        "completed_at": iso_local(b.completed_at),
    }


def message_turn_dict(msg: m.Message, conv: m.Conversation) -> dict[str, Any]:
    status = "ESCALATED" if conv.status == "ESCALATED" else ("OPEN" if conv.status == "OPEN" else "CLOSED")
    return {
        "id": msg.id,
        "conversation_id": conv.id,
        "vehicle_id": conv.vehicle.code,
        "customer_id": conv.owner.code,
        "customer_name": conv.owner.name,
        "direction": msg.direction,
        "channel": msg.channel,
        "message": msg.text,
        "intent": msg.intent,
        "sentiment": msg.sentiment,
        "agent": msg.agent,
        "turn_number": msg.turn_number,
        "status": status,
        "outcome": conv.outcome,
        "escalation_reason": conv.escalation_reason,
        "timestamp": iso_local(msg.created_at),
        "created_at": iso_local(msg.created_at),
    }


def alert_dict(a: m.Alert, vehicle_code: str) -> dict[str, Any]:
    return {
        "id": a.id,
        "vehicle_id": vehicle_code,
        "priority": a.priority,
        "component": a.component,
        "message": a.message,
        "source": a.source,
        "fired_at": iso_local(a.fired_at),
        "acknowledged": a.acknowledged_at is not None,
        "acknowledged_at": iso_local(a.acknowledged_at),
    }


def recall_dict(r: m.VehicleRecall) -> dict[str, Any]:
    return {
        "nhtsa_campaign": r.campaign,
        "component": r.component,
        "summary": r.summary,
        "remedy": r.remedy,
        "status": r.status,
        "notified_at": iso_local(r.notified_at),
        "remedied_at": iso_local(r.remedied_at),
        "source": r.source,
    }
