"""
Static reference data for the demo world.

IMPORTANT: service intervals, part lifetimes and costs below are approximate
typical values for the Indian market, NOT figures copied from owner's manuals.
Before relying on them, replace each row with the manufacturer's published
schedule (Phase 2 ingests the manuals) and a real price list.
"""

from __future__ import annotations

from domain import workshop as _workshop_rules

APPROX_SOURCE = "approximate typical values; replace with owner's manual and workshop price list"

# Base part lifetimes for a hatchback driven in mixed conditions.
_BASE_LIFETIMES = {
    "brake_pads": {"life_km": 35_000, "life_months": None},
    "battery": {"life_km": None, "life_months": 42},
    "engine_oil": {"life_km": 10_000, "life_months": 12},
    "coolant_system": {"life_km": 40_000, "life_months": 36},
    "tires": {"life_km": 45_000, "life_months": 60},
    "air_filter": {"life_km": 20_000, "life_months": None},
}

# Cost of the planned job vs. cost when the part is left to fail (INR, hatchback),
# and the rough chance that a worn part actually fails before its next service.
_BASE_COSTS = {
    "brake_pads": {"service_inr": 3_000, "breakdown_inr": 9_000, "failure_probability": 0.6},
    "battery": {"service_inr": 5_500, "breakdown_inr": 8_000, "failure_probability": 0.5},
    "engine_oil": {"service_inr": 3_500, "breakdown_inr": 45_000, "failure_probability": 0.08},
    "coolant_system": {"service_inr": 1_800, "breakdown_inr": 25_000, "failure_probability": 0.25},
    "tires": {"service_inr": 16_000, "breakdown_inr": 20_000, "failure_probability": 0.3},
    "air_filter": {"service_inr": 600, "breakdown_inr": 1_500, "failure_probability": 0.05},
}

_SEGMENT_COST_FACTOR = {"hatchback": 1.0, "sedan": 1.2, "compact_suv": 1.25, "suv": 1.45, "muv": 1.5}
_SEGMENT_LIFE_FACTOR = {"hatchback": 1.0, "sedan": 1.05, "compact_suv": 0.95, "suv": 0.9, "muv": 0.85}

VEHICLE_MODELS = [
    # make, model, fuel, segment, service interval km, interval months, share of fleet
    ("Maruti Suzuki", "Swift", "petrol", "hatchback", 10_000, 12, 0.18),
    ("Maruti Suzuki", "Baleno", "petrol", "hatchback", 10_000, 12, 0.14),
    ("Hyundai", "Creta", "petrol", "suv", 10_000, 12, 0.13),
    ("Tata", "Nexon", "petrol", "compact_suv", 10_000, 12, 0.13),
    ("Honda", "City", "petrol", "sedan", 10_000, 12, 0.11),
    ("Kia", "Seltos", "petrol", "suv", 10_000, 12, 0.10),
    ("Mahindra", "XUV700", "diesel", "suv", 10_000, 12, 0.10),
    ("Toyota", "Innova Crysta", "diesel", "muv", 10_000, 12, 0.11),
]


def model_rows() -> list[dict]:
    rows = []
    for make, model, fuel, segment, interval_km, interval_months, _share in VEHICLE_MODELS:
        life_f = _SEGMENT_LIFE_FACTOR[segment]
        cost_f = _SEGMENT_COST_FACTOR[segment]
        lifetimes = {
            part: {
                "life_km": round(spec["life_km"] * life_f, -2) if spec["life_km"] else None,
                "life_months": spec["life_months"],
            }
            for part, spec in _BASE_LIFETIMES.items()
        }
        costs = {
            part: {k: (int(round(v * cost_f, -1)) if k.endswith("_inr") else v) for k, v in spec.items()}
            for part, spec in _BASE_COSTS.items()
        }
        rows.append(
            dict(
                make=make,
                model=model,
                fuel=fuel,
                segment=segment,
                service_interval_km=interval_km,
                service_interval_months=interval_months,
                part_lifetimes=lifetimes,
                part_costs=costs,
                source=APPROX_SOURCE,
            )
        )
    return rows


def model_weights() -> list[float]:
    return [row[-1] for row in VEHICLE_MODELS]


# One partner workshop: the staff dashboard is a single-workshop view.
WORKSHOP = {
    "code": "WS-PUNE-01",
    "name": "AutoPredict Partner Service Centre",
    "city": "Pune",
    "address": "Baner Road, Pune 411045",
    "phone": None,
    "open_hour": 8,
    "close_hour": 18,
}

BAYS = [
    ("BAY-1", "GENERAL"),
    ("BAY-2", "ENGINE_COOLING"),
    ("BAY-3", "BRAKES_TIRES"),
    ("BAY-4", "ELECTRICAL"),
    ("BAY-5", "TRANSMISSION"),
    ("BAY-6", "BODY"),
    ("BAY-7", "EXPRESS"),
    ("BAY-8", "DIAGNOSTICS"),
    ("BAY-9", "ALIGNMENT_TIRES"),
    ("BAY-10", "HEAVY"),
]

BAY_FOR_COMPONENT = _workshop_rules.BAY_FOR_COMPONENT

# The first five match scheduling_agent.TECHNICIANS.
TECHNICIANS = [
    ("T001", "Rajesh Kumar", "SENIOR", ["Brake Pads", "Tires", "Oil Change"]),
    ("T002", "Amit Sharma", "SENIOR", ["Battery", "Electrical"]),
    ("T003", "Priya Nair", "LEAD", ["Cooling System", "Engine"]),
    ("T004", "Suresh Patel", "SENIOR", ["Transmission", "Full Service"]),
    ("T005", "Deepak Mehta", "JUNIOR", ["Brake Pads", "Battery", "Tires"]),
    ("T006", "Kavita Joshi", "SENIOR", ["Full Service", "Oil Change", "Battery"]),
    ("T007", "Imran Shaikh", "SENIOR", ["Tires", "Brake Pads"]),
    ("T008", "Neha Kulkarni", "LEAD", ["Full Service", "Cooling System", "Engine"]),
]

PUNE_AREAS = [
    "Baner",
    "Aundh",
    "Kothrud",
    "Hinjewadi",
    "Wakad",
    "Viman Nagar",
    "Kharadi",
    "Hadapsar",
    "Shivajinagar",
    "Pimple Saudagar",
    "Magarpatta",
    "Bavdhan",
]

FIRST_NAMES = [
    "Aarav",
    "Vivaan",
    "Aditya",
    "Vihaan",
    "Arjun",
    "Sai",
    "Reyansh",
    "Ayaan",
    "Krishna",
    "Ishaan",
    "Ananya",
    "Diya",
    "Aadhya",
    "Saanvi",
    "Pari",
    "Anika",
    "Navya",
    "Myra",
    "Sara",
    "Ira",
    "Rohan",
    "Kunal",
    "Siddharth",
    "Nikhil",
    "Rahul",
    "Pooja",
    "Sneha",
    "Neha",
    "Priyanka",
    "Shruti",
    "Manish",
    "Amol",
    "Sachin",
    "Vikram",
    "Harsh",
    "Meera",
    "Tanvi",
    "Ritika",
    "Gauri",
    "Mrunal",
]
LAST_NAMES = [
    "Sharma",
    "Patil",
    "Deshmukh",
    "Kulkarni",
    "Joshi",
    "Iyer",
    "Reddy",
    "Nair",
    "Gupta",
    "Mehta",
    "Shah",
    "Pawar",
    "Jadhav",
    "Bhosale",
    "Singh",
    "Verma",
    "Rao",
    "Menon",
    "Chavan",
    "Gokhale",
]

# Recall catalogue is still the mock from manufacturing_agent until Phase 2.
