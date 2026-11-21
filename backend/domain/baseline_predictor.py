"""
Baseline wear predictor (model_version = "baseline-rules-v1").

Estimates, per part, how far along its service life a vehicle is, using only
data a real deployment would have:
  - the vehicle model's typical part lifetimes,
  - km / months since the part was last replaced (service history),
  - average daily km (usage logs),
  - the latest readings, when a reading source exists,
  - recent owner-reported symptoms.

It never sees the simulator's hidden ground truth. Final priority comes from
`rule_engine.MaintenanceRuleEngine`, which stays the safety authority.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime

from domain.parts import PARTS, display
from rule_engine import MaintenanceRuleEngine

MODEL_VERSION = "baseline-rules-v1"

# Wear ratio (km or months used / typical life) at which failure becomes likely.
# Pads, batteries and tyres are "worn out" at 1.0; fluids and filters are only
# due at 1.0 and become risky when well overdue.
FAILURE_MARGIN = {
    "brake_pads": 1.0,
    "battery": 1.0,
    "tires": 1.0,
    "engine_oil": 2.0,
    "coolant_system": 1.4,
    "air_filter": 2.0,
}

_rules = MaintenanceRuleEngine()


@dataclass
class LastService:
    km: int
    at: datetime


@dataclass
class VehicleEvidence:
    as_of: datetime
    purchased_at: datetime
    odometer_km: int
    daily_km: float
    part_lifetimes: dict[str, dict]
    last_replaced: dict[str, LastService] = field(default_factory=dict)
    telemetry: dict | None = None
    symptom_parts: dict[str, str] = field(default_factory=dict)  # part -> urgency
    recurring_parts: set[str] = field(default_factory=set)


def _telemetry_wear(part: str, t: dict) -> float | None:
    """Translate a reading into a wear ratio on the same 0..1+ scale."""
    if part == "brake_pads" and t.get("brake_pad_mm") is not None:
        return max(0.0, (10.0 - t["brake_pad_mm"]) / 8.0)  # 10 mm new, 2 mm worn out
    if part == "battery" and t.get("battery_voltage_v") is not None:
        return max(0.0, (12.7 - t["battery_voltage_v"]) / 1.2)  # 12.7 V healthy, 11.5 V failing
    if part == "coolant_system" and t.get("coolant_temp_c") is not None:
        return max(0.0, (t["coolant_temp_c"] - 95.0) / 15.0) * FAILURE_MARGIN[part]
    if part == "engine_oil" and t.get("oil_pressure_bar") is not None:
        return max(0.0, (3.6 - t["oil_pressure_bar"]) / 1.4) * FAILURE_MARGIN[part]
    return None


def _usage_wear(part: str, ev: VehicleEvidence) -> tuple[float, float | None, float | None]:
    """Return (wear ratio, km since replacement, months since replacement)."""
    life = ev.part_lifetimes.get(part, {})
    last = ev.last_replaced.get(part)
    km_since = ev.odometer_km - (last.km if last else 0)
    since_at = last.at if last else ev.purchased_at
    months_since = max(0.0, (ev.as_of - since_at).days / 30.44)

    ratios = []
    if life.get("life_km"):
        ratios.append(km_since / life["life_km"])
    if life.get("life_months"):
        ratios.append(months_since / life["life_months"])
    return (max(ratios) if ratios else 0.0), km_since, months_since


def _failure_probability(risk: float) -> float:
    return 1.0 / (1.0 + math.exp(-12.0 * (risk - 0.92)))


# Risk needed for each severity. Estimates from usage alone are uncertain, so
# they need a wider margin before escalating than corroborated ones.
_SEVERITY_AT = {
    "corroborated": {"CRITICAL": 1.0, "HIGH": 0.9, "MEDIUM": 0.75},
    "usage_only": {"CRITICAL": 1.15, "HIGH": 1.05, "MEDIUM": 0.8},
}
_SYMPTOM_FLOOR = {"HIGH": 0.92, "MEDIUM": 0.8, "LOW": 0.6}  # risk implied by a reported symptom


def _severity(risk: float, corroborated: bool) -> str:
    cut = _SEVERITY_AT["corroborated" if corroborated else "usage_only"]
    for level in ("CRITICAL", "HIGH", "MEDIUM"):
        if risk >= cut[level]:
            return level
    return "LOW"


def predict(ev: VehicleEvidence) -> dict:
    """Return a dict ready to become a `Prediction` row (plus per-part detail)."""
    parts: dict[str, dict] = {}
    daily_km = max(ev.daily_km, 1.0)

    for part in PARTS:
        usage_wear, km_since, months_since = _usage_wear(part, ev)
        tele_wear = _telemetry_wear(part, ev.telemetry) if ev.telemetry else None
        # Conservative: whichever source says the part is more worn wins.
        wear = max(usage_wear, tele_wear) if tele_wear is not None else usage_wear
        if part in ev.symptom_parts:
            floor = _SYMPTOM_FLOOR.get(ev.symptom_parts[part], 0.8)
            wear = max(wear, floor * FAILURE_MARGIN[part])
        risk = wear / FAILURE_MARGIN[part]

        life = ev.part_lifetimes.get(part, {})
        margin = FAILURE_MARGIN[part]
        rul_candidates = []
        km_low = km_high = None
        if life.get("life_km"):
            remaining_km = margin * life["life_km"] * (1 - risk)
            rul_candidates.append(remaining_km / daily_km)
            km_low = max(0, int(remaining_km - 0.2 * margin * life["life_km"]))
            km_high = max(0, int(remaining_km + 0.2 * margin * life["life_km"]))
        if life.get("life_months"):
            rul_candidates.append(margin * life["life_months"] * (1 - risk) * 30.44)
        rul_days = max(0, int(min(rul_candidates))) if rul_candidates else None

        parts[part] = {
            "part": part,
            "name": display(part),
            "wear_ratio": round(wear, 3),
            "risk": round(risk, 3),
            "km_since_replacement": int(km_since) if km_since is not None else None,
            "months_since_replacement": round(months_since, 1) if months_since is not None else None,
            "rul_days": rul_days,
            "km_left_low": km_low,
            "km_left_high": km_high,
            "evidence": [
                s
                for s, present in (
                    ("service_history", part in ev.last_replaced),
                    ("telemetry", tele_wear is not None),
                    ("symptom_report", part in ev.symptom_parts),
                )
                if present
            ]
            or ["vehicle_model_catalogue"],
        }

    worst = max(parts.values(), key=lambda p: p["risk"])
    risks = sorted((p["risk"] for p in parts.values()), reverse=True)
    # Mostly driven by the worst part, squared so moderate wear doesn't read as poor health.
    health = 1.0 - 0.85 * min(risks[0], 1.0) ** 2 - 0.15 * sum(min(r, 1.0) for r in risks[:3]) / 3
    health_score = round(min(0.99, max(0.02, health)), 2)

    failure_probability = round(_failure_probability(worst["risk"]), 2)
    corroborated = bool({"telemetry", "symptom_report"} & set(worst["evidence"]))
    severity = _severity(worst["risk"], corroborated)
    rul_days = worst["rul_days"] if worst["rul_days"] is not None else 365
    recurring = worst["part"] in ev.recurring_parts

    t = ev.telemetry or {}
    priority = _rules.assign_priority(
        failure_probability=failure_probability,
        rul_days=rul_days,
        severity=severity,
        recurring_defect=recurring,
        brake_pad_mm=t.get("brake_pad_mm", 10.0),
        battery_voltage=t.get("battery_voltage_v", 12.7),
        coolant_temp=t.get("coolant_temp_c"),
    )

    confidence = 0.55
    confidence += 0.15 if ev.telemetry else 0.0
    confidence += 0.15 if ev.last_replaced else 0.0
    confidence += 0.10 if ev.daily_km > 1 else 0.0

    reason = f"{worst['name']}: "
    if worst["km_since_replacement"] is not None and ev.part_lifetimes.get(worst["part"], {}).get("life_km"):
        reason += (
            f"{worst['km_since_replacement']:,} km since last replacement "
            f"(typical life {int(ev.part_lifetimes[worst['part']]['life_km']):,} km)"
        )
    else:
        reason += f"{worst['months_since_replacement']} months since last replacement"
    if "telemetry" in worst["evidence"]:
        reason += "; latest reading agrees"
    if "symptom_report" in worst["evidence"]:
        reason += "; owner reported a related symptom"
    reason += "."

    action = (
        f"Book {worst['name'].lower()} service now"
        if severity in ("HIGH", "CRITICAL")
        else f"Plan {worst['name'].lower()} service within {rul_days} days"
        if severity == "MEDIUM"
        else "No action needed; next periodic service as scheduled"
    )

    return {
        # Name the part whenever anything is flagged, so a P2 from a reading rule still says what to check.
        "component": worst["part"] if severity != "LOW" or priority != "P3" else None,
        "severity": severity,
        "priority": priority,
        "health_score": health_score,
        "failure_probability": failure_probability,
        "rul_days": rul_days,
        "km_left_low": worst["km_left_low"],
        "km_left_high": worst["km_left_high"],
        "confidence": round(min(confidence, 0.95), 2),
        "model_version": MODEL_VERSION,
        "reasoning": reason,
        "recommended_action": action,
        "details": {"parts": parts, "recurring_defect": recurring},
        "sources": sorted({s for p in parts.values() for s in p["evidence"]}),
    }
