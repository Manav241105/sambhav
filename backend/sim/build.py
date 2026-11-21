"""
Build the demo world into the database.

    python -m sim.build --seed 42                    # first run on an empty database
    python -m sim.build --seed 42 --reset            # wipe and rebuild (dev/test only)
    python -m sim.build --as-of 2026-11-21T12:00     # pin the clock for repeatable demos

Same seed + same as-of = same world. Staff logins use DEMO_STAFF_PASSWORD
from the environment; there is no default password.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from alembic import command
from alembic.config import Config
from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import configure_logging
from core.security import hash_secret
from core.settings import BACKEND_DIR, get_settings, is_configured
from db import models as m
from db.session import get_engine, get_sessionmaker
from manufacturing_agent import _RECALL_CATALOGUE
from sim import catalogue as cat
from sim.world import SimConfig, World, simulate

log = logging.getLogger("sim.build")

STAFF_USERS = [
    ("ops@autopredict.local", "ops", "Operations Lead"),
    ("manager@autopredict.local", "manager", "Service Manager"),
    ("executive@autopredict.local", "executive", "Executive"),
    ("admin@autopredict.local", "admin", "Administrator"),
]


def migrate(reset: bool) -> None:
    """Run Alembic synchronously (before any event loop starts)."""
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    if reset:
        command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


async def _bulk(session: AsyncSession, model, rows: list[dict], chunk: int = 5000) -> None:
    for i in range(0, len(rows), chunk):
        await session.execute(insert(model), rows[i : i + chunk])


async def write_world(session: AsyncSession, world: World, staff_password: str) -> dict[str, int]:
    # ── Reference data ────────────────────────────────────────────────────
    models = [m.VehicleModel(**row) for row in cat.model_rows()]
    workshop = m.Workshop(**cat.WORKSHOP)
    session.add_all([*models, workshop])
    await session.flush()
    techs = [m.Technician(workshop_id=workshop.id, code=c, name=n, level=lv, skills=sk) for c, n, lv, sk in cat.TECHNICIANS]
    bays = [m.Bay(workshop_id=workshop.id, code=c, bay_type=t) for c, t in cat.BAYS]
    session.add_all([*techs, *bays])

    pw_hash = hash_secret(staff_password)
    session.add_all([m.User(email=e, role=r, full_name=n, password_hash=pw_hash) for e, r, n in STAFF_USERS])
    await session.flush()

    model_id = {(x.make, x.model, x.fuel): x.id for x in models}
    tech_id = {t.code: t.id for t in techs}
    bay_id = {b.code: b.id for b in bays}

    # ── Owners & vehicles ─────────────────────────────────────────────────
    owners = {
        o["code"]: m.Owner(
            code=o["code"],
            name=o["name"],
            phone=o["phone"],
            email=o["email"],
            city=o["city"],
            language=o["language"],
            preferred_channel=o["preferred_channel"],
            preferred_contact_time=o["preferred_contact_time"],
            marketing_consent=o["marketing_consent"],
            is_demo=True,
        )
        for o in world.owners
    }
    session.add_all(owners.values())
    await session.flush()

    vehicles = {
        v["code"]: m.Vehicle(
            code=v["code"],
            owner_id=owners[v["owner_code"]].id,
            model_id=model_id[v["model_key"]],
            year=v["year"],
            reg_no=v["reg_no"],
            vin=v["vin"],
            purchase_date=v["purchase_date"],
            city=v["city"],
            driving_profile=v["driving_profile"],
            monthly_km=v["monthly_km"],
            odometer_km=v["odometer_km"],
            is_demo=True,
        )
        for v in world.vehicles
    }
    session.add_all(vehicles.values())
    await session.flush()
    vid = {code: v.id for code, v in vehicles.items()}

    # ── High-volume rows (core inserts) ───────────────────────────────────
    def strip(row: dict, *drop: str) -> dict:
        out = {k: v for k, v in row.items() if k not in ("vehicle_code", *drop)}
        out["vehicle_id"] = vid[row["vehicle_code"]]
        return out

    await _bulk(session, m.OdometerReading, [strip(r) for r in world.odometer])
    await _bulk(session, m.UsageLog, [strip(r) for r in world.usage])
    await _bulk(session, m.TelemetrySnapshot, [strip(r) for r in world.telemetry])
    await _bulk(session, m.SymptomReport, [strip(r) for r in world.symptoms])

    # ── Predictions (need ids for bookings) ───────────────────────────────
    pred_objs = {}
    for p in world.predictions:
        row = strip(p, "ref")
        pred_objs[p["ref"]] = m.Prediction(**row)
    session.add_all(pred_objs.values())
    await session.flush()

    # ── Bookings, then service records that reference them ────────────────
    booking_objs = {}
    for b in world.bookings:
        booking_objs[b["code"]] = m.Booking(
            code=b["code"],
            vehicle_id=vid[b["vehicle_code"]],
            workshop_id=workshop.id,
            technician_id=tech_id[b["technician_code"]],
            bay_id=bay_id[b["bay_code"]],
            prediction_id=pred_objs[b["prediction_ref"]].id if b["prediction_ref"] else None,
            service_component=b["service_component"],
            slot_start=b["slot_start"],
            duration_hours=b["duration_hours"],
            actual_duration_hours=b["actual_duration_hours"],
            priority=b["priority"],
            status=b["status"],
            source=b["source"],
            cost_inr=b["cost_inr"],
            created_at=min(b["created_at"], b["slot_start"]),
            completed_at=b["completed_at"],
        )
    session.add_all(booking_objs.values())
    await session.flush()

    for r in world.service_records:
        session.add(
            m.ServiceRecord(
                vehicle_id=vid[r["vehicle_code"]],
                workshop_id=workshop.id if r["at_partner"] else None,
                booking_id=booking_objs[r["booking_code"]].id if r["booking_code"] in booking_objs else None,
                service_date=r["service_date"],
                odometer_km=r["odometer_km"],
                service_type=r["service_type"],
                total_cost_inr=r["total_cost_inr"],
                extracted_by=r["extracted_by"],
                notes=r["notes"],
                items=[m.ServiceItem(**item) for item in r["items"]],
            )
        )

    # ── Conversations ─────────────────────────────────────────────────────
    for c in world.conversations:
        session.add(
            m.Conversation(
                vehicle_id=vid[c["vehicle_code"]],
                owner_id=owners[c["owner_code"]].id,
                channel=c["channel"],
                status=c["status"],
                outcome=c["outcome"],
                escalation_reason=c["escalation_reason"],
                escalated_at=c["escalated_at"],
                resolved_at=c["resolved_at"],
                started_at=c["started_at"],
                closed_at=c["closed_at"],
                messages=[m.Message(**msg) for msg in c["messages"]],
            )
        )

    await _bulk(session, m.Alert, [strip(a) for a in world.alerts])
    await _bulk(session, m.VehicleRecall, [strip(r) for r in world.recalls])
    await session.flush()

    return {
        "owners": len(world.owners),
        "vehicles": len(world.vehicles),
        "usage_logs": len(world.usage),
        "telemetry": len(world.telemetry),
        "service_records": len(world.service_records),
        "symptoms": len(world.symptoms),
        "predictions": len(world.predictions),
        "bookings": len(world.bookings),
        "conversations": len(world.conversations),
        "alerts": len(world.alerts),
        "recalls": len(world.recalls),
    }


async def build(cfg: SimConfig, staff_password: str) -> tuple[World, dict[str, int]]:
    async with get_sessionmaker()() as session:
        existing = await session.scalar(select(func.count()).select_from(m.Vehicle))
        if existing:
            raise SystemExit(f"Database already has {existing} vehicles. Re-run with --reset to rebuild.")
        world = simulate(cfg, _RECALL_CATALOGUE)
        counts = await write_world(session, world, staff_password)
        await session.commit()
    await get_engine().dispose()
    return world, counts


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    settings = get_settings()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--owners", type=int, default=400)
    p.add_argument("--vehicles", type=int, default=600)
    p.add_argument("--as-of", help="ISO time in the app timezone, e.g. 2026-11-21T12:00 (default: now)")
    p.add_argument("--reset", action="store_true", help="drop all data and rebuild (refused in prod)")
    args = p.parse_args(argv)

    if args.reset and settings.env == "prod":
        raise SystemExit("--reset is refused when ENV=prod")
    if not is_configured(settings.demo_staff_password) or len(settings.demo_staff_password or "") < 10:
        raise SystemExit("Set DEMO_STAFF_PASSWORD (10+ characters) in .env before building demo data.")
    if args.vehicles < args.owners:
        raise SystemExit("--vehicles must be >= --owners (every demo owner has at least one car)")

    as_of = None
    if args.as_of:
        as_of = datetime.fromisoformat(args.as_of)
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=ZoneInfo(settings.app_timezone))

    started = time.perf_counter()
    migrate(reset=args.reset)
    configure_logging()  # Alembic's fileConfig raises the root log level; restore ours
    cfg = SimConfig(seed=args.seed, as_of=as_of, owners=args.owners, vehicles=args.vehicles, tz=settings.app_timezone)
    world, counts = asyncio.run(build(cfg, settings.demo_staff_password))

    log.info(
        "Demo world built in %.1fs (seed=%s, as_of=%s)", time.perf_counter() - started, args.seed, world.as_of.isoformat(timespec="minutes")
    )
    for k, v in counts.items():
        log.info("  %-16s %7d", k, v)
    log.info("Staff logins: %s (password from DEMO_STAFF_PASSWORD)", ", ".join(e for e, _, _ in STAFF_USERS))
    sample = [o for o in world.owners[:3]]
    log.info("Owner app logins (OTP): %s", ", ".join(f"{o['name']} {o['phone']}" for o in sample))


if __name__ == "__main__":
    main()
