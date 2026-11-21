"""Workshop rules shared by the simulator and the booking API."""

from __future__ import annotations

# Which bay types suit which job (first match preferred).
BAY_FOR_COMPONENT: dict[str, list[str]] = {
    "Brake Pads": ["BRAKES_TIRES", "GENERAL"],
    "Tires": ["ALIGNMENT_TIRES", "BRAKES_TIRES", "GENERAL"],
    "Battery": ["ELECTRICAL", "EXPRESS", "GENERAL"],
    "Cooling System": ["ENGINE_COOLING", "GENERAL"],
    "Oil Change": ["EXPRESS", "GENERAL"],
    "Engine": ["ENGINE_COOLING", "HEAVY", "GENERAL"],
    "Transmission": ["TRANSMISSION", "HEAVY"],
    "Full Service": ["GENERAL", "HEAVY", "DIAGNOSTICS"],
}

BAY_LABELS: dict[str, str] = {
    "GENERAL": "General Service",
    "ENGINE_COOLING": "Engine & Cooling",
    "BRAKES_TIRES": "Brakes & Tires",
    "ELECTRICAL": "Electrical / Battery",
    "TRANSMISSION": "Transmission",
    "BODY": "Body & Detailing",
    "EXPRESS": "Express Service",
    "DIAGNOSTICS": "Diagnostics",
    "ALIGNMENT_TIRES": "Alignment & Tyres",
    "HEAVY": "Heavy Repairs",
}

# Jobs a technician without the exact skill may still take.
GENERALIST_SKILL = "Full Service"

ACTIVE_BOOKING_STATUSES = ("PENDING", "CONFIRMED", "IN_PROGRESS")

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "PENDING": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"IN_PROGRESS", "CANCELLED", "NO_SHOW", "PENDING"},
    "IN_PROGRESS": {"COMPLETED", "CONFIRMED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
    "NO_SHOW": {"CONFIRMED"},
}
