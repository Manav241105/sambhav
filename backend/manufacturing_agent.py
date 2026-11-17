"""
Manufacturing Agent - v1.0
Stubbed DTC (Diagnostic Trouble Codes) lookup and NHTSA recall check.

Designed to plug into the AutoGen agent framework used by the rest of the
system.  For now every method is deterministic / mock — in production the
NHTSA lookup would hit https://api.nhtsa.gov/recalls/recallsByVehicle and
the DTC decoder would query an OBD-II database.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Static DTC catalogue (SAE J2012 style codes)
# ──────────────────────────────────────────────────────────────────────────────
_DTC_CATALOGUE: List[Dict] = [
    {"code": "P0128", "system": "Powertrain", "description": "Coolant thermostat — temperature below regulating range",  "severity": "warning"},
    {"code": "P0300", "system": "Powertrain", "description": "Random/multiple cylinder misfire detected",               "severity": "critical"},
    {"code": "P0420", "system": "Powertrain", "description": "Catalyst system efficiency below threshold (Bank 1)",     "severity": "warning"},
    {"code": "P0171", "system": "Powertrain", "description": "System too lean (Bank 1)",                                "severity": "warning"},
    {"code": "P0442", "system": "Powertrain", "description": "EVAP emission control system leak detected (small leak)", "severity": "low"},
    {"code": "C0035", "system": "Chassis",    "description": "Left front wheel speed sensor circuit malfunction",       "severity": "critical"},
    {"code": "C0050", "system": "Chassis",    "description": "Right rear wheel speed sensor circuit malfunction",       "severity": "warning"},
    {"code": "B0100", "system": "Body",       "description": "Driver frontal airbag deployment loop resistance high",   "severity": "critical"},
    {"code": "U0100", "system": "Network",    "description": "Lost communication with ECM/PCM 'A'",                    "severity": "critical"},
    {"code": "U0140", "system": "Network",    "description": "Lost communication with body control module",             "severity": "warning"},
]

# ──────────────────────────────────────────────────────────────────────────────
# Static NHTSA recall catalogue (mock)
# ──────────────────────────────────────────────────────────────────────────────
_RECALL_CATALOGUE: List[Dict] = [
    {
        "nhtsa_campaign": "24V-987",
        "component": "Airbag",
        "summary": "Frontal airbag inflator may produce excessive internal pressure. Risk of metal fragments striking occupants.",
        "remedy": "Dealers will replace the airbag inflator free of charge.",
        "make_match": ["Toyota", "Honda"],
    },
    {
        "nhtsa_campaign": "23V-654",
        "component": "Brake System",
        "summary": "Brake fluid may leak at the master cylinder causing reduced braking performance.",
        "remedy": "Dealers will inspect and replace the master cylinder if necessary.",
        "make_match": ["Ford", "BMW"],
    },
    {
        "nhtsa_campaign": "25V-112",
        "component": "Battery (HV)",
        "summary": "High-voltage battery contactors may overheat during fast charging.",
        "remedy": "Software update via OTA or at dealer.",
        "make_match": ["Tesla"],
    },
    {
        "nhtsa_campaign": "24V-321",
        "component": "Fuel System",
        "summary": "Fuel pump relay may intermittently fail causing engine stall.",
        "remedy": "Dealers will replace the fuel pump control module.",
        "make_match": ["Honda", "Toyota", "Ford"],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# Manufacturing Agent
# ──────────────────────────────────────────────────────────────────────────────
class ManufacturingAgent:
    """
    Lightweight agent that checks for:
      1. Active DTC codes (simulated OBD-II scan)
      2. Open NHTSA recalls matching the vehicle make/model

    In the current stub all data is deterministic based on the vehicle's
    numeric ID so results are reproducible across calls.
    """

    def __init__(self):
        self.name = "ManufacturingAgent"

    # ── Public API ────────────────────────────────────────────────────────────

    def check_vehicle(self, vehicle_id: str) -> Dict:
        """
        Run a full manufacturing check for *vehicle_id*.
        Returns a combined dict of DTC codes and recall matches.
        """
        dtc_codes = self.get_dtc_codes(vehicle_id)
        recalls = self.get_recalls(vehicle_id)

        has_critical = any(d["severity"] == "critical" for d in dtc_codes) or len(recalls) > 0

        return {
            "vehicle_id": vehicle_id,
            "checked_at": datetime.now().isoformat(),
            "dtc_codes": dtc_codes,
            "dtc_count": len(dtc_codes),
            "recalls": recalls,
            "recall_count": len(recalls),
            "has_critical_issue": has_critical,
        }

    # ── DTC scan (mock) ──────────────────────────────────────────────────────

    def get_dtc_codes(self, vehicle_id: str) -> List[Dict]:
        """
        Simulate an OBD-II scan.
        Uses *vehicle_id* hash to deterministically pick 0-3 DTCs.
        """
        seed = self._vehicle_seed(vehicle_id)
        rng = random.Random(seed)

        count = rng.choices([0, 1, 2, 3], weights=[0.40, 0.30, 0.20, 0.10])[0]
        if count == 0:
            return []

        selected = rng.sample(_DTC_CATALOGUE, k=min(count, len(_DTC_CATALOGUE)))
        results = []
        for dtc in selected:
            results.append({
                "code": dtc["code"],
                "system": dtc["system"],
                "description": dtc["description"],
                "severity": dtc["severity"],
                "first_seen": (datetime.now() - timedelta(days=rng.randint(1, 60))).strftime("%Y-%m-%d"),
                "occurrence_count": rng.randint(1, 12),
                "mil_status": "ON" if dtc["severity"] == "critical" else "PENDING",
            })

        return results

    # ── NHTSA recall check (mock) ────────────────────────────────────────────

    def get_recalls(self, vehicle_id: str) -> List[Dict]:
        """
        Check open recalls for the vehicle's make.
        Looks up the vehicle in app_state (or falls back to data_generator)
        to determine the make, then matches against the recall catalogue.
        """
        make = self._resolve_make(vehicle_id)
        if not make:
            return []

        matches = []
        for recall in _RECALL_CATALOGUE:
            if make in recall["make_match"]:
                matches.append({
                    "nhtsa_campaign": recall["nhtsa_campaign"],
                    "component": recall["component"],
                    "summary": recall["summary"],
                    "remedy": recall["remedy"],
                    "status": "OPEN",
                })

        return matches

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _vehicle_seed(vehicle_id: str) -> int:
        """Derive a deterministic seed from the vehicle ID."""
        num_part = "".join(c for c in vehicle_id if c.isdigit()) or "0"
        return int(num_part) * 7919  # prime multiplier

    @staticmethod
    def _resolve_make(vehicle_id: str) -> Optional[str]:
        """Try to get the vehicle make from app_state, else from data_generator."""
        try:
            from app_state import app_state
            v = app_state.get_vehicle(vehicle_id)
            if v and v.get("make"):
                return v["make"]
        except Exception:
            pass

        # Fallback: use data_generator
        try:
            from data_generator import VehicleDataGenerator
            master = VehicleDataGenerator().generate_vehicle_master(vehicle_id)
            return master.get("make")
        except Exception:
            return None
