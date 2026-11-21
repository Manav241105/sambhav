"""
Canonical part names and the mapping to display / scheduling names.

One vocabulary across the simulator, the predictor, bookings and the API,
so analytics never have to reconcile "brake_pads" vs "Brake Pads".
"""

from __future__ import annotations

PARTS: tuple[str, ...] = (
    "brake_pads",
    "battery",
    "engine_oil",
    "coolant_system",
    "tires",
    "air_filter",
)

DISPLAY_NAME = {
    "brake_pads": "Brake Pads",
    "battery": "Battery",
    "engine_oil": "Engine Oil",
    "coolant_system": "Cooling System",
    "tires": "Tires",
    "air_filter": "Air Filter",
}

# Keys used by scheduling_agent.SERVICE_DURATIONS / technician skills.
SCHEDULING_COMPONENT = {
    "brake_pads": "Brake Pads",
    "battery": "Battery",
    "engine_oil": "Oil Change",
    "coolant_system": "Cooling System",
    "tires": "Tires",
    "air_filter": "Full Service",
    "periodic_service": "Full Service",
}

# Standard job durations in hours (mirrors scheduling_agent.SERVICE_DURATIONS).
JOB_HOURS = {
    "Brake Pads": 1.5,
    "Battery": 0.75,
    "Cooling System": 2.0,
    "Engine": 3.0,
    "Transmission": 4.0,
    "Tires": 1.0,
    "Oil Change": 0.5,
    "Full Service": 3.5,
}


def display(part: str | None) -> str:
    if not part:
        return "General"
    return DISPLAY_NAME.get(part, part.replace("_", " ").title())
