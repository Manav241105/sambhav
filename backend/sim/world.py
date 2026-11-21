"""
Deterministic demo-world simulator (pure Python, no database).

Given a seed and an as-of time it produces the same owners, vehicles, usage,
service history, symptoms, readings, AI outreach, bookings, alerts and
predictions every time. `sim.build` writes the result to the database.

How it works
- Each part of each car has a HIDDEN lifetime drawn from a Weibull
  distribution and shifted by driving style. Nobody outside this module sees it.
- Week by week the car is driven; parts wear; owners do (or skip) periodic
  services, report symptoms when parts get bad, and sometimes break down.
- From `platform_start` the AutoPredict platform is "live": each month the
  baseline predictor (which sees only observable data) scores every car, the
  agent contacts owners about risky parts, and bookings happen at the partner
  workshop. Workshop findings record whether the prediction was right.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from domain import baseline_predictor as bp
from domain.parts import JOB_HOURS, PARTS, SCHEDULING_COMPONENT, display
from sim import catalogue as cat

# ── Config ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SimConfig:
    seed: int = 42
    as_of: datetime | None = None  # aware; defaults to "now" in the app timezone
    owners: int = 400
    vehicles: int = 600
    tz: str = "Asia/Kolkata"
    usage_weeks: int = 104  # weekly usage logs kept for the last N weeks
    telemetry_days: int = 30  # daily readings kept for the last N days
    telemetry_share: float = 0.25  # share of cars with an (optional) reading source
    platform_months: int = 9  # how long the platform has been live

    def resolved_as_of(self) -> datetime:
        tz = ZoneInfo(self.tz)
        if self.as_of is None:
            return datetime.now(tz).replace(microsecond=0)
        return self.as_of.astimezone(tz)


# ── Static behaviour tables ───────────────────────────────────────────────────

_DILIGENCE = {  # probability of acting on things, typical delay in weeks
    "diligent": {"weight": 0.35, "service_skip": 0.03, "max_delay_w": 2, "fix_symptom": 0.7},
    "average": {"weight": 0.45, "service_skip": 0.12, "max_delay_w": 6, "fix_symptom": 0.4},
    "lax": {"weight": 0.20, "service_skip": 0.45, "max_delay_w": 12, "fix_symptom": 0.15},
}
_OUTCOME_WEIGHTS = {  # agent outreach outcome by diligence: BOOKED, DELAYED, DECLINED, ESCALATED
    "diligent": (0.78, 0.12, 0.05, 0.05),
    "average": (0.58, 0.20, 0.14, 0.08),
    "lax": (0.33, 0.25, 0.32, 0.10),
}
_STYLE = {"gentle": 0.3, "normal": 0.5, "aggressive": 0.2}
_BRAKE_STYLE_FACTOR = {"gentle": 1.2, "normal": 1.0, "aggressive": 0.75}
_TIRE_STYLE_FACTOR = {"gentle": 1.1, "normal": 1.0, "aggressive": 0.8}
_HARD_BRAKE_RATE = {"gentle": 0.5, "normal": 1.2, "aggressive": 3.0}  # per 100 km
_CHANNELS = (("APP", 0.40), ("WHATSAPP", 0.35), ("SMS", 0.15), ("EMAIL", 0.10))
_WEIBULL_SHAPE = 3.5

# True risk at which a part actually fails on the road. Pads and batteries fail
# when worn out; tyres a bit later (they get bald first); overdue fluids and
# filters only cause damage when badly neglected.
_BREAKDOWN_AT = {"brake_pads": 1.0, "battery": 1.0, "tires": 1.15, "engine_oil": 1.35, "coolant_system": 1.5, "air_filter": 2.5}
# What a mechanic replaces at a periodic service (true risk), and on a targeted repair.
_PERIODIC_REPLACE_AT = {"brake_pads": 0.68, "battery": 0.72, "tires": 0.8, "engine_oil": 0.0, "coolant_system": 0.65, "air_filter": 0.45}
_REPAIR_REPLACE_AT = 0.6

_SYMPTOMS = {
    "brake_pads": ("Squealing noise when I brake, especially in the morning.", None, "HIGH"),
    "battery": ("Car takes longer to start, cranking sounds weak.", "BATTERY", "MEDIUM"),
    "coolant_system": ("Temperature needle went higher than usual in traffic.", "COOLANT_TEMP", "HIGH"),
    "engine_oil": ("Oil warning light flickered for a second.", "OIL_PRESSURE", "HIGH"),
    "tires": ("Steering feels a bit wobbly at highway speed.", None, "MEDIUM"),
}

_REPLY_TEMPLATES = {
    "BOOKED": [
        ("Yes, please book it.", "READY_TO_BOOK", "POSITIVE"),
        ("Okay, what slots do you have this week?", "READY_TO_BOOK", "POSITIVE"),
        ("Sure, a weekend morning would be best.", "READY_TO_BOOK", "NEUTRAL"),
    ],
    "DELAYED": [
        ("I'm travelling this week, can you remind me later?", "DELAY_REQUEST", "NEUTRAL"),
        ("Not now, maybe after payday.", "DELAY_REQUEST", "NEUTRAL"),
    ],
    "DECLINED": [
        ("No thanks, my local mechanic will check it.", "SECOND_OPINION_SEEKING", "NEUTRAL"),
        ("I don't think it's needed yet.", "SOFT_DECLINE", "NEGATIVE"),
        ("Too expensive right now.", "COST_CONCERN", "NEGATIVE"),
    ],
    "ESCALATED": [
        ("I want to talk to a person, not a bot.", "HUMAN_REQUEST", "NEGATIVE"),
        ("Can someone from the workshop call me?", "HUMAN_REQUEST", "NEUTRAL"),
    ],
}


# ── Records produced (plain dicts keyed by codes; sim.build resolves ids) ─────


@dataclass
class World:
    as_of: datetime
    platform_start: datetime
    owners: list[dict] = field(default_factory=list)
    vehicles: list[dict] = field(default_factory=list)
    odometer: list[dict] = field(default_factory=list)
    usage: list[dict] = field(default_factory=list)
    telemetry: list[dict] = field(default_factory=list)
    service_records: list[dict] = field(default_factory=list)
    symptoms: list[dict] = field(default_factory=list)
    bookings: list[dict] = field(default_factory=list)
    conversations: list[dict] = field(default_factory=list)
    predictions: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)
    recalls: list[dict] = field(default_factory=list)
    booking_seq: int = 0


# ── Workshop calendar (shared across cars so bookings never collide) ──────────


class WorkshopCalendar:
    def __init__(self, tz: ZoneInfo):
        self.tz = tz
        self.busy: dict[str, list[tuple[datetime, datetime]]] = {}
        self.techs = cat.TECHNICIANS
        self.bays = cat.BAYS

    def _free(self, key: str, start: datetime, end: datetime) -> bool:
        return all(end <= s or start >= e for s, e in self.busy.get(key, ()))

    def release(self, tech: str, bay: str, start: datetime) -> None:
        for key in (tech, bay):
            self.busy[key] = [(s, e) for s, e in self.busy.get(key, ()) if s != start]

    def allocate(
        self, rng: random.Random, component: str, earliest: datetime, max_days: int = 14
    ) -> tuple[datetime, float, str, str] | None:
        """First slot from `earliest` with a skilled free technician and a suitable free bay."""
        hours = JOB_HOURS.get(component, 2.0)
        skilled = [t for t in self.techs if component in t[3]] or [t for t in self.techs if "Full Service" in t[3]]
        bay_types = cat.BAY_FOR_COMPONENT.get(component, ["GENERAL"])
        bays = [b for b in self.bays if b[1] in bay_types] or list(self.bays)
        day0 = earliest.astimezone(self.tz).date()
        for d in range(max_days):
            day = day0 + timedelta(days=d)
            if day.weekday() == 6 and rng.random() < 0.7:  # most Sundays closed
                continue
            start_hours = [h + m / 60 for h in range(cat.WORKSHOP["open_hour"], cat.WORKSHOP["close_hour"]) for m in (0, 30)]
            rng.shuffle(start_hours) if rng.random() < 0.5 else None
            for h in start_hours:
                start = datetime.combine(day, time(int(h), int(round((h % 1) * 60))), self.tz)
                end = start + timedelta(hours=hours)
                if start < earliest or end.hour + end.minute / 60 > cat.WORKSHOP["close_hour"]:
                    continue
                tech = next((t for t in skilled if self._free(t[0], start, end)), None)
                bay = next((b for b in bays if self._free(b[0], start, end)), None)
                if tech and bay:
                    self.busy.setdefault(tech[0], []).append((start, end))
                    self.busy.setdefault(bay[0], []).append((start, end))
                    return start, hours, tech[0], bay[0]
        return None


# ── Per-part hidden state ─────────────────────────────────────────────────────


@dataclass
class PartState:
    installed_km: float
    installed_at: datetime
    life_km: float | None
    life_months: float | None
    symptom_reported: bool = False


def _weibull(rng: random.Random, scale: float) -> float:
    return rng.weibullvariate(scale, _WEIBULL_SHAPE)


class VehicleSim:
    def __init__(
        self,
        world: World,
        cfg: SimConfig,
        cal: WorkshopCalendar,
        owner: dict,
        vcode: str,
        n: int,
        model_row: dict,
        rng: random.Random,
        recall_catalogue: list[dict],
    ):
        self.w, self.cfg, self.cal, self.owner, self.code, self.m, self.rng = world, cfg, cal, owner, vcode, model_row, rng
        self.tz = ZoneInfo(cfg.tz)
        self.recall_catalogue = recall_catalogue

        years_old = rng.uniform(0.5, 6.0)
        self.purchased_at = (world.as_of - timedelta(days=int(years_old * 365))).replace(hour=11, minute=0, second=0)
        self.style = rng.choices(list(_STYLE), weights=list(_STYLE.values()))[0]
        self.city_share = rng.uniform(0.35, 0.95)
        self.monthly_km = int(min(3500, max(400, rng.lognormvariate(math.log(1100), 0.35))))
        self.has_telemetry = rng.random() < cfg.telemetry_share
        self.odo = 0.0
        self.parts: dict[str, PartState] = {p: self._new_part(p, 0.0, self.purchased_at) for p in PARTS}
        self.last_periodic_km = 0.0
        self.last_periodic_at = self.purchased_at
        self.periodic_delay_w = None
        self.pending: list[tuple[datetime, str, dict]] = []  # (when, kind, payload)
        self.replacements: dict[str, list[tuple[float, datetime, str]]] = {p: [] for p in PARTS}
        self.open_outreach_until: dict[str, datetime] = {}
        self.symptoms: list[dict] = []
        letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
        self.vehicle = {
            "code": vcode,
            "owner_code": owner["code"],
            "model_key": (model_row["make"], model_row["model"], model_row["fuel"]),
            "year": self.purchased_at.year,
            # Index-based parts keep both identifiers unique across the fleet.
            "reg_no": f"MH12{letters[n % 23]}{letters[(n // 23) % 23]}{n:04d}",
            "vin": f"MA3{n:06d}{rng.randint(10**7, 10**8 - 1)}",
            "purchase_date": self.purchased_at.date(),
            "city": owner["city"],
            "driving_profile": f"{self.style}/{'city' if self.city_share > 0.65 else 'mixed'}",
            "monthly_km": self.monthly_km,
            "has_telemetry": self.has_telemetry,
        }

    # ── hidden wear model ────────────────────────────────────────────────

    def _new_part(self, part: str, km: float, at: datetime) -> PartState:
        nominal = self.m["part_lifetimes"][part]
        life_km = nominal["life_km"]
        if life_km:
            factor = 1.0
            if part == "brake_pads":
                factor = _BRAKE_STYLE_FACTOR[self.style] * (1.15 - 0.3 * self.city_share)
            elif part == "tires":
                factor = _TIRE_STYLE_FACTOR[self.style]
            life_km = _weibull(self.rng, life_km * factor)
        life_months = nominal["life_months"]
        if life_months and part == "battery":
            life_months = _weibull(self.rng, life_months * 0.95)  # hot climate shortens battery life
        return PartState(km, at, life_km, life_months)

    def _true_risk(self, part: str, at: datetime, odo: float | None = None) -> float:
        st = self.parts[part]
        odo = self.odo if odo is None else odo
        margin = bp.FAILURE_MARGIN[part]
        ratios = []
        if st.life_km:
            ratios.append((odo - st.installed_km) / st.life_km)
        if st.life_months:
            ratios.append(((at - st.installed_at).days / 30.44) / st.life_months)
        return (max(ratios) if ratios else 0.0) / margin

    def _replace(self, part: str, at: datetime, reason: str) -> None:
        self.replacements[part].append((self.odo, at, reason))
        self.parts[part] = self._new_part(part, self.odo, at)

    def reading(self, at: datetime, odo: float) -> dict:
        r = {p: max(0.0, self._true_risk(p, at, odo)) for p in PARTS}
        g = self.rng.gauss
        return {
            "odo_km": int(odo),
            "brake_pad_mm": round(max(1.0, 10 - 8 * min(r["brake_pads"], 1.1) + g(0, 0.1)), 2),
            "battery_voltage_v": round(12.75 - 1.25 * min(r["battery"], 1.2) ** 2 + g(0, 0.05), 2),
            "coolant_temp_c": round(85 + 25 * min(r["coolant_system"], 1.2) ** 2 + g(0, 1.5), 1),
            "oil_pressure_bar": round(max(1.5, 3.7 - 1.5 * min(r["engine_oil"], 1.2) ** 2 + g(0, 0.05)), 2),
            "tire_fl_psi": round(33 + g(0, 0.8), 1),
            "tire_fr_psi": round(33 + g(0, 0.8), 1),
            "tire_rl_psi": round(32.5 + g(0, 0.8), 1),
            "tire_rr_psi": round(32.5 + g(0, 0.8), 1),
            "engine_rpm": self.rng.randint(750, 2800),
            "speed_kmh": self.rng.randint(0, 80),
        }

    # ── observable evidence for the predictor ────────────────────────────

    def evidence(self, at: datetime) -> bp.VehicleEvidence:
        last = {}
        for part, reps in self.replacements.items():
            if reps:
                km, when, _ = reps[-1]
                last[part] = bp.LastService(km=int(km), at=when)
        recent_symptoms = {
            s["part_hint"]: s["urgency"]
            for s in self.symptoms
            if s["part_hint"]
            and timedelta(0) <= at - s["reported_at"] <= timedelta(days=30)
            and self.parts[s["part_hint"]].installed_at <= s["reported_at"]
        }
        recurring = {
            p
            for p, reps in self.replacements.items()
            if sum(1 for _, when, why in reps if why in ("breakdown", "repair") and at - when < timedelta(days=730)) >= 2
        }
        age_days = max(30, (at - self.purchased_at).days)
        return bp.VehicleEvidence(
            as_of=at,
            purchased_at=self.purchased_at,
            odometer_km=int(self.odo),
            daily_km=self.odo / age_days,
            part_lifetimes=self.m["part_lifetimes"],
            last_replaced=last,
            telemetry=self.reading(at, self.odo) if self.has_telemetry else None,
            symptom_parts=recent_symptoms,
            recurring_parts=recurring,
        )

    # ── events ───────────────────────────────────────────────────────────

    def _service(self, at: datetime, service_type: str, focus: str | None, booking_code: str | None, at_partner: bool) -> dict:
        """Workshop visit: inspect everything, replace what the mechanic finds worn."""
        costs = self.m["part_costs"]
        seg = self.m["segment"]
        labour = int(1200 * {"hatchback": 1.0, "sedan": 1.15, "compact_suv": 1.2, "suv": 1.35, "muv": 1.4}[seg])
        items, total = [], labour if service_type == "periodic" else 0
        for part in PARTS:
            risk = self._true_risk(part, at)
            check = service_type == "periodic" or part == focus
            if not check:
                continue
            if service_type == "breakdown" and part == focus:
                items.append({"part": part, "action": "replaced", "finding": "failed", "cost_inr": costs[part]["breakdown_inr"]})
                total += costs[part]["breakdown_inr"]
                self._replace(part, at, "breakdown")
            elif risk >= (_PERIODIC_REPLACE_AT[part] if service_type == "periodic" else _REPAIR_REPLACE_AT):
                finding = "worn" if part not in ("engine_oil", "air_filter", "coolant_system") or risk >= 0.6 else "ok"
                items.append({"part": part, "action": "replaced", "finding": finding, "cost_inr": costs[part]["service_inr"]})
                total += costs[part]["service_inr"]
                self._replace(part, at, "repair" if service_type == "repair" else "periodic")
            else:
                items.append({"part": part, "action": "inspected", "finding": "ok", "cost_inr": 0})
                if part == focus:
                    total += 500  # inspection charge when the suspected part was fine
        # Open recalls are remedied at any partner-workshop visit.
        for rc in self.w.recalls:
            if at_partner and rc["vehicle_code"] == self.code and rc["status"] == "OPEN" and rc["notified_at"] <= at:
                rc["status"], rc["remedied_at"] = "REMEDIED", at
                items.append({"part": "recall:" + rc["campaign"], "action": "repaired", "finding": "recall_remedy", "cost_inr": 0})
        if service_type == "periodic":
            self.last_periodic_km, self.last_periodic_at = self.odo, at
        record = {
            "vehicle_code": self.code,
            "service_date": at,
            "odometer_km": int(self.odo),
            "service_type": service_type,
            "total_cost_inr": total,
            "at_partner": at_partner,
            "booking_code": booking_code,
            "extracted_by": "workshop" if at_partner else "sim",
            "notes": "" if at_partner else "Invoice from another workshop (uploaded by owner)",
            "items": items,
        }
        self.w.service_records.append(record)
        return record

    def _book(self, at: datetime, component: str, priority: str, source: str, prediction_ref: str | None) -> dict | None:
        slot = self.cal.allocate(self.rng, component, at)
        if not slot:
            return None
        start, hours, tech, bay = slot
        self.w.booking_seq += 1
        code = f"BK{start:%y%m%d}-{self.w.booking_seq:05d}"
        booking = {
            "code": code,
            "vehicle_code": self.code,
            "service_component": component,
            "slot_start": start,
            "duration_hours": hours,
            "technician_code": tech,
            "bay_code": bay,
            "priority": priority,
            "status": "CONFIRMED",
            "source": source,
            "created_at": at,
            "prediction_ref": prediction_ref,
            "cost_inr": None,
            "actual_duration_hours": None,
            "completed_at": None,
        }
        self.w.bookings.append(booking)
        return booking

    def _unbook(self, booking: dict) -> None:
        self.cal.release(booking["technician_code"], booking["bay_code"], booking["slot_start"])
        self.w.bookings.remove(booking)

    def _complete(self, booking: dict, record: dict, slowdown: float = 0.0) -> None:
        booking["cost_inr"] = record["total_cost_inr"]
        booking["actual_duration_hours"] = round(booking["duration_hours"] * self.rng.lognormvariate(slowdown, 0.15), 2)
        booking["completed_at"] = booking["slot_start"] + timedelta(hours=booking["actual_duration_hours"])

    def _process_pending(self, until: datetime) -> None:
        """Run queued visits up to `until`: agent bookings and symptom-driven repairs."""
        due = sorted([p for p in self.pending if p[0] <= until], key=lambda p: p[0])
        for item in due:
            self.pending.remove(item)
            when, kind, payload = item
            component = payload["service_component"]
            part = next((p for p, c in SCHEDULING_COMPONENT.items() if c == component and p in PARTS), None)
            if kind == "booking":
                roll = self.rng.random()
                if roll < 0.04:  # owner cancelled before the day
                    payload["forced_status"] = "CANCELLED"
                    continue
                if roll < 0.07:  # owner didn't turn up
                    payload["forced_status"] = "NO_SHOW"
                    continue
                self._complete(payload, self._service(when, "repair", part, payload["code"], at_partner=True))
                continue
            # Symptom-driven repair: partner workshop (once the platform is live) or elsewhere.
            if when >= self.w.platform_start and self.rng.random() < 0.7:
                booking = self._book(when, component, "P1", "app", None)
                if booking and booking["slot_start"] <= self.w.as_of:
                    self._complete(booking, self._service(booking["slot_start"], "repair", part, booking["code"], at_partner=True))
                    continue
                if booking:  # booked for the coming days; work not done yet
                    continue
            self._service(when, "repair", part, None, at_partner=False)

    def _outreach(self, at: datetime, pred: dict, pred_ref: str) -> None:
        part = pred["component"]
        if not part or self.open_outreach_until.get(part, at - timedelta(days=1)) > at:
            return
        rng = self.rng
        outcome = rng.choices(("BOOKED", "DELAYED", "DECLINED", "ESCALATED"), weights=_OUTCOME_WEIGHTS[self.owner["diligence"]])[0]
        if pred["priority"] in ("P2", "P3") and outcome == "BOOKED" and rng.random() < 0.25:
            outcome = "DELAYED"
        channel = "VOICE_CALL" if pred["priority"] == "P0" and rng.random() < 0.3 else self.owner["preferred_channel"]
        # Contact in the evening, as the timing agent prefers.
        start = (at + timedelta(days=rng.choice((0, 1)))).replace(hour=rng.choice((18, 19, 20)), minute=rng.randint(0, 59))
        if start > self.w.as_of - timedelta(minutes=30):
            start = self.w.as_of - timedelta(minutes=rng.randint(30, 240))
        first = self.owner["name"].split()[0]
        part_name = display(part).lower()
        msgs = [
            {
                "direction": "OUTBOUND",
                "text": (
                    f"Hi {first}, this is AutoPredict for your {self.m['model']}. {pred['reasoning']} "
                    f"Would you like me to book a {part_name} check at {cat.WORKSHOP['name']}?"
                ),
                "intent": None,
                "sentiment": None,
                "agent": "customer_engagement",
                "created_at": start,
            }
        ]
        reply_at = start + timedelta(minutes=int(rng.lognormvariate(math.log(120), 0.9)))
        reply_at = min(reply_at, self.w.as_of - timedelta(minutes=5))
        reply_at = max(reply_at, start + timedelta(minutes=2))
        text, intent, sentiment = rng.choice(_REPLY_TEMPLATES[outcome])
        msgs.append(
            {"direction": "INBOUND", "text": text, "intent": intent, "sentiment": sentiment, "agent": "customer", "created_at": reply_at}
        )
        conv = {
            "vehicle_code": self.code,
            "owner_code": self.owner["code"],
            "channel": channel,
            "started_at": start,
            "status": "CLOSED",
            "outcome": outcome,
            "escalation_reason": None,
            "escalated_at": None,
            "resolved_at": None,
            "closed_at": None,
            "messages": msgs,
        }
        respond_at = reply_at + timedelta(minutes=1)
        component = SCHEDULING_COMPONENT.get(part, "Full Service")
        if outcome == "BOOKED":
            earliest = respond_at + timedelta(days=0 if pred["priority"] in ("P0", "P1") else rng.randint(1, 4))
            booking = self._book(max(earliest, respond_at + timedelta(hours=2)), component, pred["priority"], "agent", pred_ref)
            if booking:
                when = booking["slot_start"]
                msgs.append(
                    {
                        "direction": "OUTBOUND",
                        "agent": "scheduling",
                        "intent": None,
                        "sentiment": None,
                        "created_at": respond_at,
                        "text": (
                            f"Done. You're booked for {when:%a %d %b, %I:%M %p} with technician "
                            f"{dict((t[0], t[1]) for t in cat.TECHNICIANS)[booking['technician_code']]}. "
                            f"I'll send a reminder the day before."
                        ),
                    }
                )
                if when <= self.w.as_of:
                    self.pending.append((when, "booking", booking))
                conv["closed_at"] = respond_at
            else:
                conv["outcome"], conv["status"] = "DELAYED", "CLOSED"
        elif outcome == "DELAYED":
            msgs.append(
                {
                    "direction": "OUTBOUND",
                    "agent": "customer_engagement",
                    "intent": None,
                    "sentiment": None,
                    "created_at": respond_at,
                    "text": (
                        f"No problem. I'll check in again in two weeks. "
                        f"If anything feels off with the {part_name}, tell me and I'll book sooner."
                    ),
                }
            )
            conv["closed_at"] = respond_at
        elif outcome == "DECLINED":
            msgs.append(
                {
                    "direction": "OUTBOUND",
                    "agent": "customer_engagement",
                    "intent": None,
                    "sentiment": None,
                    "created_at": respond_at,
                    "text": "Understood. Your service history is in the app if your mechanic wants to see it.",
                }
            )
            conv["closed_at"] = respond_at
        else:  # ESCALATED
            msgs.append(
                {
                    "direction": "OUTBOUND",
                    "agent": "customer_engagement",
                    "intent": None,
                    "sentiment": None,
                    "created_at": respond_at,
                    "text": "Of course. I've asked a service advisor to call you.",
                }
            )
            conv["status"], conv["escalation_reason"], conv["escalated_at"] = "ESCALATED", "Customer asked for a human", respond_at
            resolve = respond_at + timedelta(hours=rng.uniform(1, 30))
            if resolve <= self.w.as_of and rng.random() < 0.85:
                conv["resolved_at"] = conv["closed_at"] = resolve
                conv["status"] = "CLOSED"
        for i, m in enumerate(msgs, start=1):
            m["turn_number"] = i
            m["channel"] = channel
        self.w.conversations.append(conv)
        self.open_outreach_until[part] = start + timedelta(days=14 if outcome != "DECLINED" else 30)

    def _predict(self, at: datetime, current: bool) -> None:
        ev = self.evidence(at)
        pred = bp.predict(ev)
        ref = f"{self.code}@{at.isoformat()}"
        self.w.predictions.append({"ref": ref, "vehicle_code": self.code, "created_at": at, "is_current": current, **pred})
        if pred["priority"] in ("P0", "P1"):
            ack = None if current else at + timedelta(hours=self.rng.uniform(0.5, 20))
            self.w.alerts.append(
                {
                    "vehicle_code": self.code,
                    "priority": pred["priority"],
                    "component": pred["component"],
                    "message": f"{self.m['make']} {self.m['model']}: {display(pred['component'])} risk {pred['severity'].lower()}",
                    "source": "baseline_predictor",
                    "fired_at": at,
                    "acknowledged_at": ack,
                }
            )
        if pred["priority"] in ("P0", "P1", "P2") and pred["component"]:
            self._outreach(at, pred, ref)

    # ── main loop ────────────────────────────────────────────────────────

    def run(self) -> None:
        rng, w, cfg = self.rng, self.w, self.cfg
        trait = _DILIGENCE[self.owner["diligence"]]
        interval_km = self.m["service_interval_km"]
        interval_d = self.m["service_interval_months"] * 30.44
        usage_from = w.as_of - timedelta(weeks=cfg.usage_weeks)
        tele_from = w.as_of - timedelta(days=cfg.telemetry_days)
        next_snapshot = w.platform_start
        last_reading_month = None

        t = self.purchased_at
        while t < w.as_of:
            week_end = min(t + timedelta(days=7), w.as_of)
            days = (week_end - t).days or 1
            km = self.monthly_km * 12 / 365 * days * rng.lognormvariate(0, 0.25)
            odo_start = self.odo
            self.odo += km
            mean_brakes = km / 100 * _HARD_BRAKE_RATE[self.style] * (0.5 + self.city_share)
            if t >= usage_from:
                w.usage.append(
                    {
                        "vehicle_code": self.code,
                        "period_start": t.date(),
                        "days": days,
                        "km": round(km, 1),
                        "hard_brakes": max(0, int(round(rng.gauss(mean_brakes, math.sqrt(mean_brakes + 1))))),
                        "city_share": round(min(1, max(0, self.city_share + rng.gauss(0, 0.05))), 2),
                    }
                )
            if t >= usage_from and (last_reading_month != (t.year, t.month)):
                last_reading_month = (t.year, t.month)
                w.odometer.append({"vehicle_code": self.code, "km": int(self.odo), "read_at": week_end, "source": "sim"})
            if self.has_telemetry and week_end > tele_from:
                for d in range(days):
                    day_at = (t + timedelta(days=d)).replace(hour=rng.randint(8, 21), minute=rng.randint(0, 59))
                    if tele_from <= day_at <= w.as_of:
                        frac = (d + 1) / days
                        w.telemetry.append(
                            {
                                "vehicle_code": self.code,
                                "recorded_at": day_at,
                                "source": "sim",
                                **self.reading(day_at, odo_start + km * frac),
                            }
                        )

            # Queued visits that fall in this week happen now.
            self._process_pending(week_end)

            # Breakdowns: a part past its true failure point fails this week.
            for part in PARTS:
                if self._true_risk(part, week_end) >= _BREAKDOWN_AT[part]:
                    at_partner = week_end >= w.platform_start and rng.random() < 0.6
                    booking = None
                    if at_partner:
                        booking = self._book(week_end, SCHEDULING_COMPONENT.get(part, "Full Service"), "P0", "dashboard", None)
                        if booking and booking["slot_start"] > w.as_of:
                            self._unbook(booking)
                            booking = None
                    rec = self._service(
                        booking["slot_start"] if booking else week_end,
                        "breakdown",
                        part,
                        booking["code"] if booking else None,
                        at_partner=bool(booking),
                    )
                    if booking:
                        self._complete(booking, rec, slowdown=0.1)

            # Symptoms: bad parts get noticed; some owners act on it.
            for part, (text, light, urgency) in _SYMPTOMS.items():
                st = self.parts[part]
                if not st.symptom_reported and self._true_risk(part, week_end) >= 0.85 and rng.random() < 0.35:
                    st.symptom_reported = True
                    at = (t + timedelta(days=rng.randint(0, days - 1 if days > 1 else 0))).replace(hour=rng.randint(8, 22))
                    report = {
                        "vehicle_code": self.code,
                        "text": text,
                        "part_hint": part,
                        "warning_light": light,
                        "urgency": urgency,
                        "source": "app" if at >= w.platform_start else "sim",
                        "reported_at": at,
                    }
                    w.symptoms.append(report)
                    self.symptoms.append(report)
                    if rng.random() < trait["fix_symptom"]:
                        fix_at = at + timedelta(days=rng.randint(2, 14))
                        if fix_at < w.as_of:
                            self.pending.append(
                                (fix_at, "symptom_fix", {"service_component": SCHEDULING_COMPONENT.get(part, "Full Service")})
                            )

            # Periodic service.
            due = self.odo - self.last_periodic_km >= interval_km or (week_end - self.last_periodic_at).days >= interval_d
            if due:
                if self.periodic_delay_w is None:
                    skip = rng.random() < trait["service_skip"]
                    self.periodic_delay_w = rng.randint(0, trait["max_delay_w"]) + (rng.randint(8, 20) if skip else 0)
                if self.periodic_delay_w <= 0:
                    at = week_end.replace(hour=rng.randint(9, 16), minute=rng.choice((0, 30)))
                    at_partner = at >= w.platform_start and rng.random() < 0.85
                    booking = None
                    if at_partner:
                        booking = self._book(at - timedelta(days=2), "Full Service", "P3", "app", None)
                        if booking and booking["slot_start"] > w.as_of:
                            self._unbook(booking)
                            booking = None
                    rec = self._service(
                        booking["slot_start"] if booking else at,
                        "periodic",
                        None,
                        booking["code"] if booking else None,
                        at_partner=bool(booking),
                    )
                    if booking:
                        self._complete(booking, rec)
                    self.periodic_delay_w = None
                else:
                    self.periodic_delay_w -= 1

            # Monthly platform snapshot (prediction → alerts → outreach).
            while next_snapshot <= week_end and next_snapshot < w.as_of:
                self._predict(next_snapshot, current=False)
                next_snapshot = next_snapshot + timedelta(days=30)

            t = week_end

        # Anything still queued in the past happens now; later items stay as bookings.
        self._process_pending(w.as_of)
        self.pending.clear()

        # Current prediction, plus a pre-booked periodic service for cars about to be due.
        self._predict(w.as_of, current=True)
        if (self.odo - self.last_periodic_km >= 0.92 * interval_km) and rng.random() < 0.5:
            self._book(w.as_of + timedelta(hours=rng.randint(1, 6 * 24)), "Full Service", "P3", "app", None)

        self.vehicle["odometer_km"] = int(self.odo)


# ── Entry point ───────────────────────────────────────────────────────────────


def _recall_matches(make: str, catalogue: list[dict]) -> list[dict]:
    # Mock catalogue uses short make names ("Toyota", "Honda").
    return [r for r in catalogue if any(m.lower() in make.lower() for m in r["make_match"])]


def simulate(cfg: SimConfig, recall_catalogue: list[dict]) -> World:
    as_of = cfg.resolved_as_of()
    tz = ZoneInfo(cfg.tz)
    world = World(
        as_of=as_of,
        platform_start=(as_of - timedelta(days=int(cfg.platform_months * 30.44))).replace(hour=9, minute=0, second=0, microsecond=0),
    )
    rng = random.Random(f"world-{cfg.seed}")
    models = cat.model_rows()
    weights = cat.model_weights()

    for i in range(1, cfg.owners + 1):
        first, last = rng.choice(cat.FIRST_NAMES), rng.choice(cat.LAST_NAMES)
        world.owners.append(
            {
                "code": f"OWN{i:04d}",
                "name": f"{first} {last}",
                "phone": f"+9198{(i * 7919) % 10**8:08d}",  # 7919 is coprime with 10^8, so unique
                "email": f"{first.lower()}.{last.lower()}{i}@example.com",
                "city": f"Pune ({rng.choice(cat.PUNE_AREAS)})",
                "language": rng.choices(("en", "hi", "mr"), weights=(0.6, 0.25, 0.15))[0],
                "preferred_channel": rng.choices([c for c, _ in _CHANNELS], weights=[w for _, w in _CHANNELS])[0],
                "preferred_contact_time": rng.choice(("MORNING", "EVENING", "EVENING", "WEEKEND")),
                "diligence": rng.choices(list(_DILIGENCE), weights=[d["weight"] for d in _DILIGENCE.values()])[0],
                "marketing_consent": rng.random() < 0.6,
            }
        )

    # Every owner gets one car; the rest go to random owners (multi-car households).
    owner_for_vehicle = list(world.owners) + [rng.choice(world.owners) for _ in range(max(0, cfg.vehicles - cfg.owners))]
    cal = WorkshopCalendar(tz)
    sims = []
    for n, owner in enumerate(owner_for_vehicle[: cfg.vehicles], start=1):
        vcode = f"VEH{n:03d}"
        model_row = rng.choices(models, weights=weights)[0]
        vrng = random.Random(f"vehicle-{cfg.seed}-{vcode}")
        sim = VehicleSim(world, cfg, cal, owner, vcode, n, model_row, vrng, recall_catalogue)
        for rc in _recall_matches(model_row["make"], recall_catalogue):
            notified = world.platform_start + timedelta(days=vrng.randint(0, 120))
            if notified < as_of:
                world.recalls.append(
                    {
                        "vehicle_code": vcode,
                        "campaign": rc["nhtsa_campaign"],
                        "component": rc["component"],
                        "summary": rc["summary"],
                        "remedy": rc["remedy"],
                        "status": "OPEN",
                        "notified_at": notified,
                        "remedied_at": None,
                    }
                )
        sims.append(sim)

    for sim in sims:
        sim.run()
        world.vehicles.append(sim.vehicle)

    # Booking status from the as-of clock.
    for b in world.bookings:
        end = b["completed_at"] or b["slot_start"] + timedelta(hours=b["duration_hours"])
        if b.get("forced_status"):
            b["status"] = b["forced_status"]
        elif b["completed_at"] is not None and b["completed_at"] <= as_of:
            b["status"] = "COMPLETED"
        elif b["slot_start"] <= as_of < end:
            b["status"] = "IN_PROGRESS"
            b["cost_inr"] = None  # not invoiced until the job finishes
        elif end <= as_of:
            b["status"] = "NO_SHOW"
        else:
            b["status"] = "CONFIRMED"
    return world
