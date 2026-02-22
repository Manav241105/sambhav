"""
Personalization Context Builder - Enterprise Conversation Intelligence v2.0
Builds rich personalization context from customer memory, vehicle data, and behavioral signals.
"""

from typing import Dict, List, Optional


class PersonalizationContextBuilder:
    """Builds personalization context for response generation."""

    def build(self, customer_data: Dict, vehicle: Dict, telematics: Dict,
              maintenance_history: List[Dict], customer_memory_signals: Dict,
              conversation_memory_summary: Dict) -> Dict:
        behavioral = self._build_behavioral_profile(customer_data, customer_memory_signals)
        vehicle_rel = self._build_vehicle_relationship(vehicle, telematics, maintenance_history)
        emotional = self._build_emotional_profile(customer_memory_signals, conversation_memory_summary)
        comm_style = self._determine_comm_style(behavioral, emotional)
        return {
            "behavioral": behavioral,
            "vehicle_relationship": vehicle_rel,
            "emotional": emotional,
            "comm_style": comm_style,
            "first_name": self._get_first_name(customer_data),
            "vehicle_desc": self._build_vehicle_desc(vehicle),
            "personalization_notes": self._build_notes(behavioral, vehicle_rel, emotional),
        }

    def _build_behavioral_profile(self, customer_data: Dict, signals: Dict) -> Dict:
        return {
            "is_quick_responder": signals.get("QUICK_RESPONDER", False),
            "often_declines": signals.get("OFTEN_DECLINES", False),
            "is_high_trust": signals.get("HIGH_TRUST_CUSTOMER", False),
            "prefers_data": signals.get("PREFERS_DATA", False),
            "price_sensitive": signals.get("PRICE_SENSITIVE", False),
            "total_interactions": signals.get("total_interactions", 0),
            "preferred_channel": customer_data.get("preferred_channel", "EMAIL"),
        }

    def _build_vehicle_relationship(self, vehicle: Dict, telematics: Dict,
                                     maintenance_history: List[Dict]) -> Dict:
        odometer = telematics.get("odo_km", 0)
        year = vehicle.get("year", 2020)
        age_years = 2026 - int(year) if year else 0
        service_count = len(maintenance_history)
        loyalty = "HIGH" if service_count >= 5 else ("MEDIUM" if service_count >= 2 else "LOW")
        service_types = [h.get("service_type", "") for h in maintenance_history]
        recurring = [s for s in set(service_types) if service_types.count(s) > 1]
        return {
            "vehicle_age_years": age_years,
            "odometer_km": odometer,
            "service_count": service_count,
            "loyalty_level": loyalty,
            "recurring_issues": recurring[:3],
            "high_mileage": odometer > 80000,
            "long_ownership": age_years >= 3,
        }

    def _build_emotional_profile(self, signals: Dict, memory_summary: Dict) -> Dict:
        trust_score = memory_summary.get("trust_score", 0.5)
        trust_trend = memory_summary.get("trust_trend", "stable")
        resistance = memory_summary.get("resistance_level", 0)
        trust_damage = memory_summary.get("trust_damage", False)
        if trust_damage:
            state = "TRUST_DAMAGED"
        elif trust_score < 0.35:
            state = "DISTRUSTFUL"
        elif trust_score < 0.5 and trust_trend == "falling":
            state = "BECOMING_RESISTANT"
        elif resistance >= 3:
            state = "FRUSTRATED"
        elif trust_score > 0.7:
            state = "ENGAGED"
        else:
            state = "NEUTRAL"
        return {
            "emotional_state": state,
            "trust_score": trust_score,
            "trust_trend": trust_trend,
            "resistance_level": resistance,
            "needs_reassurance": trust_score < 0.5 or trust_damage,
            "needs_space": resistance >= 3,
            "is_engaged": trust_score > 0.65,
        }

    def _determine_comm_style(self, behavioral: Dict, emotional: Dict) -> str:
        if emotional["emotional_state"] in ("TRUST_DAMAGED", "DISTRUSTFUL"):
            return "TRUST_REPAIR"
        elif emotional["emotional_state"] == "FRUSTRATED":
            return "EMPATHY_FIRST"
        elif behavioral["prefers_data"]:
            return "DATA_FORWARD"
        elif behavioral["price_sensitive"]:
            return "VALUE_FOCUSED"
        elif emotional["is_engaged"]:
            return "COLLABORATIVE"
        return "WARM_PROFESSIONAL"

    def _get_first_name(self, customer_data: Dict) -> str:
        name = customer_data.get("name", "there") if customer_data else "there"
        return name.split()[0] if name and name != "there" else "there"

    def _build_vehicle_desc(self, vehicle: Dict) -> str:
        if not vehicle:
            return "your vehicle"
        make = vehicle.get("make", "")
        model = vehicle.get("model", "")
        year = vehicle.get("year", "")
        color = vehicle.get("color", "")
        if color and make and model:
            return f"your {color} {year} {make} {model}".strip()
        elif make and model:
            return f"your {year} {make} {model}".strip()
        return "your vehicle"

    def _build_notes(self, behavioral: Dict, vehicle_rel: Dict, emotional: Dict) -> List[str]:
        notes = []
        if behavioral["often_declines"]:
            notes.append("Customer has a history of declining — avoid pressure language")
        if behavioral["is_high_trust"]:
            notes.append("High-trust customer — can be more direct with recommendations")
        if vehicle_rel["loyalty_level"] == "HIGH":
            notes.append("Loyal customer — acknowledge their loyalty")
        if vehicle_rel["recurring_issues"]:
            notes.append(f"Recurring issues: {', '.join(vehicle_rel['recurring_issues'])}")
        if vehicle_rel["high_mileage"]:
            notes.append("High-mileage vehicle — frame as protecting their investment")
        if emotional["needs_reassurance"]:
            notes.append("Lead with empathy before data")
        if emotional["needs_space"]:
            notes.append("Give space — avoid scheduling pressure")
        return notes
