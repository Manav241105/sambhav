"""
Diagnosis service: turns database state into predictions.

Two paths
- Baseline (cheap, every cycle): `domain.baseline_predictor` on observable
  evidence. A new prediction row is written only when the result changes.
- LLM pipeline (expensive, on demand or for a small batch of risky cars):
  the existing Data Analysis + Diagnosis agents, then the rule engine sets
  priority — never lower than the baseline's rule-based priority.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, time, timedelta

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.events import DashboardEvent, hub
from core.settings import get_settings
from db import models as m
from db.base import app_tz, utcnow
from db.session import get_sessionmaker
from domain import baseline_predictor as bp
from domain.parts import PARTS, display
from rule_engine import MaintenanceRuleEngine

log = logging.getLogger(__name__)
_rules = MaintenanceRuleEngine()
_PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
LLM_MODEL_VERSION = "llm-diagnosis-v1"


# ── Evidence from the database ────────────────────────────────────────────────


async def build_evidence(session: AsyncSession, vehicle: m.Vehicle, as_of: datetime | None = None) -> bp.VehicleEvidence:
    as_of = as_of or utcnow()
    purchased_at = datetime.combine(vehicle.purchase_date or as_of.date(), time(11, 0), app_tz())

    replaced = await session.execute(
        select(m.ServiceItem.part, m.ServiceRecord.odometer_km, m.ServiceRecord.service_date, m.ServiceRecord.service_type)
        .join(m.ServiceRecord, m.ServiceItem.record_id == m.ServiceRecord.id)
        .where(m.ServiceRecord.vehicle_id == vehicle.id, m.ServiceItem.action == "replaced", m.ServiceRecord.service_date <= as_of)
        .order_by(m.ServiceRecord.service_date)
    )
    last: dict[str, bp.LastService] = {}
    unplanned: dict[str, list[datetime]] = {}
    for part, km, at, service_type in replaced.all():
        last[part] = bp.LastService(km=km, at=at)
        if service_type in ("repair", "breakdown"):
            unplanned.setdefault(part, []).append(at)
    recurring = {p for p, dates in unplanned.items() if sum(1 for d in dates if as_of - d < timedelta(days=730)) >= 2}

    tele = await session.scalar(
        select(m.TelemetrySnapshot)
        .where(
            m.TelemetrySnapshot.vehicle_id == vehicle.id,
            m.TelemetrySnapshot.recorded_at <= as_of,
            m.TelemetrySnapshot.recorded_at >= as_of - timedelta(days=7),
        )
        .order_by(m.TelemetrySnapshot.recorded_at.desc())
        .limit(1)
    )
    telemetry = None
    if tele is not None:
        telemetry = {k: getattr(tele, k) for k in ("brake_pad_mm", "battery_voltage_v", "coolant_temp_c", "oil_pressure_bar")}

    symptoms = (
        await session.execute(
            select(m.SymptomReport.part_hint, m.SymptomReport.urgency, m.SymptomReport.reported_at).where(
                m.SymptomReport.vehicle_id == vehicle.id,
                m.SymptomReport.part_hint.is_not(None),
                m.SymptomReport.reported_at <= as_of,
                m.SymptomReport.reported_at >= as_of - timedelta(days=30),
            )
        )
    ).all()
    symptom_parts = {part: urgency for part, urgency, at in symptoms if part in PARTS and (part not in last or last[part].at <= at)}

    age_days = max(30, (as_of - purchased_at).days)
    return bp.VehicleEvidence(
        as_of=as_of,
        purchased_at=purchased_at,
        odometer_km=vehicle.odometer_km,
        daily_km=vehicle.odometer_km / age_days,
        part_lifetimes=vehicle.vehicle_model.part_lifetimes,
        last_replaced=last,
        telemetry=telemetry,
        symptom_parts=symptom_parts,
        recurring_parts=recurring,
    )


# ── Persisting predictions ────────────────────────────────────────────────────


async def _current(session: AsyncSession, vehicle_id: int) -> m.Prediction | None:
    return await session.scalar(select(m.Prediction).where(m.Prediction.vehicle_id == vehicle_id, m.Prediction.is_current.is_(True)))


def _changed(old: m.Prediction | None, new: dict) -> bool:
    if old is None:
        return True
    return old.priority != new["priority"] or old.component != new["component"] or abs(old.health_score - new["health_score"]) >= 0.03


async def save_prediction(session: AsyncSession, vehicle: m.Vehicle, result: dict) -> m.Prediction:
    previous = await _current(session, vehicle.id)
    await session.execute(
        update(m.Prediction).where(m.Prediction.vehicle_id == vehicle.id, m.Prediction.is_current.is_(True)).values(is_current=False)
    )
    pred = m.Prediction(vehicle_id=vehicle.id, is_current=True, **result)
    session.add(pred)
    await session.flush()

    escalated = pred.priority in ("P0", "P1") and (previous is None or _PRIORITY_RANK[previous.priority] > _PRIORITY_RANK[pred.priority])
    if escalated:
        model = vehicle.vehicle_model
        alert = m.Alert(
            vehicle_id=vehicle.id,
            priority=pred.priority,
            component=pred.component,
            source=pred.model_version,
            message=f"{model.make} {model.model}: {display(pred.component)} risk {pred.severity.lower()}",
        )
        session.add(alert)
    await session.commit()

    await hub.publish(DashboardEvent.DIAGNOSIS_UPDATED, {"vehicle_id": vehicle.code, "priority": pred.priority, "severity": pred.severity})
    if escalated:
        await hub.publish(
            DashboardEvent.ALERT_FIRED,
            {"vehicle_id": vehicle.code, "priority": pred.priority, "component": pred.component, "message": alert.message},
        )
    return pred


async def refresh_baseline(session: AsyncSession, vehicle: m.Vehicle) -> m.Prediction | None:
    """Recompute the baseline; write a new prediction only if it changed."""
    result = bp.predict(await build_evidence(session, vehicle))
    if not _changed(await _current(session, vehicle.id), result):
        return None
    return await save_prediction(session, vehicle, result)


# ── LLM pipeline ──────────────────────────────────────────────────────────────


def _llm_context(vehicle: m.Vehicle, ev: bp.VehicleEvidence, baseline: dict) -> dict:
    model = vehicle.vehicle_model
    return {
        "vehicle": {
            "code": vehicle.code,
            "make": model.make,
            "model": model.model,
            "year": vehicle.year,
            "fuel": model.fuel,
            "odometer_km": vehicle.odometer_km,
            "avg_km_per_day": round(ev.daily_km, 1),
        },
        "telematics": ev.telemetry,  # None for cars without a reading source
        "service_history": {p: {"km_at_replacement": s.km, "replaced_on": s.at.date().isoformat()} for p, s in ev.last_replaced.items()},
        "reported_symptoms": ev.symptom_parts,
        "baseline_estimate": {
            p: {"wear_ratio": d["wear_ratio"], "rul_days": d["rul_days"]} for p, d in baseline["details"]["parts"].items()
        },
    }


async def run_llm_diagnosis(session: AsyncSession, vehicle: m.Vehicle) -> m.Prediction:
    """Run the AutoGen agents for one vehicle and store the rule-checked result."""
    from diagnosis_orchestrator import get_orchestrator

    run = m.WorkflowRun(vehicle_id=vehicle.id, kind="diagnosis", phase="analysis", state={})
    session.add(run)
    await session.flush()

    ev = await build_evidence(session, vehicle)
    baseline = bp.predict(ev)
    try:
        report = await get_orchestrator().analyse(_llm_context(vehicle, ev, baseline), vehicle.code, vehicle.vehicle_model.make)
    except Exception as exc:
        run.status, run.error = "FAILED", str(exc)[:500]
        await session.commit()
        raise

    fallback = bool(report.get("fallback"))
    component = report.get("predicted_component") if report.get("predicted_component") in PARTS else baseline["component"]
    severity = str(report.get("severity") or baseline["severity"]).upper()
    rul = report.get("rul_days") if isinstance(report.get("rul_days"), int) else baseline["rul_days"]
    prob = report.get("failure_probability")
    prob = float(prob) if isinstance(prob, (int, float)) else baseline["failure_probability"]
    t = ev.telemetry or {}
    rule_priority = _rules.assign_priority(
        failure_probability=prob,
        rul_days=rul if rul is not None else 365,
        severity=severity,
        recurring_defect=bool(report.get("recurring_defect")),
        brake_pad_mm=t.get("brake_pad_mm", 10.0),
        battery_voltage=t.get("battery_voltage_v", 12.7),
        coolant_temp=t.get("coolant_temp_c"),
    )
    # Safety: the LLM path may raise the priority, never lower it below the baseline rules.
    priority = min(rule_priority, baseline["priority"], key=_PRIORITY_RANK.get)

    result = {
        **baseline,
        "component": component,
        "severity": severity if severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL") else baseline["severity"],
        "priority": priority,
        "failure_probability": round(prob, 2),
        "rul_days": rul,
        "confidence": float(report.get("confidence") or baseline["confidence"]),
        "model_version": LLM_MODEL_VERSION + ("+fallback" if fallback else ""),
        "reasoning": report.get("diagnostic_reasoning") or baseline["reasoning"],
        "recommended_action": report.get("recommended_action") or baseline["recommended_action"],
        "details": {
            **baseline["details"],
            **{
                k: report[k]
                for k in ("data_analysis", "manufacturing", "suggested_schedule", "failure_mode", "secondary_risks")
                if k in report
            },
            "fallback": fallback,
        },
        "sources": sorted(set(baseline["sources"]) | {"llm_agents"}),
    }
    pred = await save_prediction(session, vehicle, result)
    run.status, run.phase, run.state = "DONE", "saved", {"prediction_id": pred.id, "fallback": fallback}
    await session.commit()
    return pred


# ── Background loop ───────────────────────────────────────────────────────────


async def load_vehicle(session: AsyncSession, code: str) -> m.Vehicle | None:
    return await session.scalar(select(m.Vehicle).options(selectinload(m.Vehicle.vehicle_model)).where(m.Vehicle.code == code))


async def diagnosis_cycle(llm_batch: int = 3) -> dict[str, int]:
    """One pass: refresh every baseline, then LLM-check a few risky cars."""
    updated = llm_runs = 0
    async with get_sessionmaker()() as session:
        vehicles = (await session.scalars(select(m.Vehicle).options(selectinload(m.Vehicle.vehicle_model)))).all()
        for v in vehicles:
            if await refresh_baseline(session, v):
                updated += 1

        # Risky cars with no LLM diagnosis yet, or one older than a day.
        stale = utcnow() - timedelta(hours=24)
        candidates = (
            await session.scalars(
                select(m.Prediction)
                .where(
                    m.Prediction.is_current.is_(True),
                    m.Prediction.priority.in_(("P0", "P1")),
                    or_(~m.Prediction.model_version.startswith(LLM_MODEL_VERSION), m.Prediction.created_at < stale),
                )
                .order_by(m.Prediction.priority, m.Prediction.created_at)
                .limit(llm_batch)
            )
        ).all()
        by_id = {v.id: v for v in vehicles}
        for p in candidates:
            try:
                await run_llm_diagnosis(session, by_id[p.vehicle_id])
                llm_runs += 1
            except Exception as exc:
                log.warning("LLM diagnosis failed for %s: %s", by_id[p.vehicle_id].code, exc)
    return {"vehicles": len(vehicles), "baseline_updated": updated, "llm_runs": llm_runs}


async def background_loop() -> None:
    interval = get_settings().diagnosis_interval_minutes * 60
    while True:
        await asyncio.sleep(interval)
        try:
            stats = await diagnosis_cycle()
            log.info("Diagnosis cycle: %s", stats)
        except Exception:
            log.exception("Diagnosis cycle failed")
