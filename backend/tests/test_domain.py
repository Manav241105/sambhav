"""Pure domain logic: rule engine, baseline predictor, security helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from core import security
from domain import baseline_predictor as bp
from rule_engine import MaintenanceRuleEngine
from sim.catalogue import model_rows

rules = MaintenanceRuleEngine()
LIFETIMES = model_rows()[0]["part_lifetimes"]
NOW = datetime(2026, 11, 21, 12, tzinfo=UTC)


# ── Rule engine: the safety authority ─────────────────────────────────────────


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"brake_pad_mm": 2.5}, "P0"),
        ({"battery_voltage": 11.4}, "P0"),
        ({"coolant_temp": 112.0}, "P0"),
        ({"severity": "HIGH"}, "P0"),
        ({"rul_days": 3}, "P0"),
        ({"failure_probability": 0.75}, "P1"),
        ({"brake_pad_mm": 3.5}, "P1"),
        ({"rul_days": 20}, "P2"),
        ({}, "P3"),
    ],
)
def test_rule_engine_priorities(kwargs, expected):
    base = dict(
        failure_probability=0.1,
        rul_days=200,
        severity="LOW",
        recurring_defect=False,
        brake_pad_mm=9.0,
        battery_voltage=12.6,
        coolant_temp=90.0,
    )
    assert rules.assign_priority(**{**base, **kwargs}) == expected


# ── Baseline predictor ────────────────────────────────────────────────────────


def _evidence(**kw) -> bp.VehicleEvidence:
    base = dict(as_of=NOW, purchased_at=NOW - timedelta(days=400), odometer_km=12_000, daily_km=30.0, part_lifetimes=LIFETIMES)
    return bp.VehicleEvidence(**{**base, **kw})


def test_new_car_is_healthy():
    p = bp.predict(_evidence(last_replaced={"engine_oil": bp.LastService(11_000, NOW - timedelta(days=30))}))
    assert p["priority"] == "P3"
    assert p["severity"] == "LOW"
    assert p["component"] is None
    assert p["health_score"] > 0.7
    assert p["model_version"] == bp.MODEL_VERSION


def test_usage_only_estimate_needs_wider_margin_before_high():
    # Pads at ~100% of typical life by km, but no reading or symptom to back it up.
    life = LIFETIMES["brake_pads"]["life_km"]
    fresh = {
        part: bp.LastService(int(life) - 500, NOW - timedelta(days=20))
        for part in ("battery", "engine_oil", "coolant_system", "tires", "air_filter")
    }
    p = bp.predict(_evidence(odometer_km=int(life * 1.0), last_replaced=fresh))
    assert p["details"]["parts"]["brake_pads"]["risk"] >= 0.99
    assert p["component"] == "brake_pads"
    assert p["severity"] in ("MEDIUM", "LOW")  # uncorroborated: not HIGH yet


def test_reading_corroborates_and_escalates():
    p = bp.predict(_evidence(telemetry={"brake_pad_mm": 2.4, "battery_voltage_v": 12.6, "coolant_temp_c": 90.0, "oil_pressure_bar": 3.6}))
    assert p["component"] == "brake_pads"
    assert p["priority"] == "P0"  # rule engine: pads under 3 mm
    assert "telemetry" in p["sources"]


def test_high_urgency_symptom_raises_risk():
    p = bp.predict(_evidence(symptom_parts={"brake_pads": "HIGH"}))
    assert p["component"] == "brake_pads"
    assert p["severity"] in ("HIGH", "CRITICAL")
    assert "symptom_report" in p["details"]["parts"]["brake_pads"]["evidence"]


def test_flagged_priority_always_names_a_part():
    # Pads at 5.5 mm: the rule engine says P2 even though severity is LOW.
    p = bp.predict(_evidence(telemetry={"brake_pad_mm": 5.5, "battery_voltage_v": 12.6, "coolant_temp_c": 90.0, "oil_pressure_bar": 3.6}))
    assert p["priority"] == "P2"
    assert p["component"] is not None


# ── Security helpers ──────────────────────────────────────────────────────────


def test_password_hash_roundtrip():
    h = security.hash_secret("correct horse")
    assert security.verify_secret("correct horse", h)
    assert not security.verify_secret("wrong", h)
    assert not security.verify_secret("anything", None)


def test_access_token_roundtrip_and_tamper():
    token, _ = security.create_access_token(5, "ops")
    assert security.decode_access_token(token)["sub"] == "5"
    with pytest.raises(security.TokenError):
        security.decode_access_token(token[:-2] + ("A" if token[-1] != "A" else "B") + token[-1])


def test_otp_is_six_digits():
    codes = {security.generate_otp() for _ in range(50)}
    assert all(len(c) == 6 and c.isdigit() for c in codes)
    assert len(codes) > 40  # not constant


def test_cors_origins_accepts_comma_separated(monkeypatch):
    from core.settings import Settings

    monkeypatch.setenv("CORS_ORIGINS", "http://a.example, http://b.example")
    assert Settings().cors_origins == ["http://a.example", "http://b.example"]
    monkeypatch.setenv("CORS_ORIGINS", '["http://c.example"]')
    assert Settings().cors_origins == ["http://c.example"]
