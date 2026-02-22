"""
Personalization Context Engine - Autonomous Service Orchestration Platform v1.0
Upgraded personalization engine with deep behavioral, vehicle relationship,
and emotional context integration.

Extends PersonalizationContextBuilder with:
  - Response speed pattern
  - Channel preference intelligence
  - Trust sensitivity scoring
  - Decline tendency tracking
  - Past service satisfaction score
  - Price sensitivity signals
  - Ownership duration + service loyalty
  - Recurring failure patterns
  - Driving intensity + mileage trend
  - Frustration history
  - Trust damage events
  - Time stress detection
  - Safety concern sensitivity
"""

from typing import Dict, List, Optional


class PersonalizationContextEngine:
    """
    Deep personalization engine for the Autonomous Service Orchestration Platform.
    Builds a rich customer context profile used to adapt every conversation turn.
    """

    def build(self, customer_data: Dict, vehicle: Dict, telematics: Dict,
              maintenance_history: List[Dict], customer_memory_signals: Dict,
              conversation_memory_summary: Dict,
              reanalysis_result=None) -> Dict:
        """
        Build complete personalization context.

        Args:
            customer_data: Customer profile (name, phone, preferences)
            vehicle: Vehicle master data
            telematics: Current telematics readings
            maintenance_history: Service history records
            customer_memory_signals: Behavioral signals from memory store
            conversation_memory_summary: Current conversation memory
            reanalysis_result: Optional ReanalysisResult for follow-up cycles

        Returns:
            Complete personalization context dict
        """
        behavioral = self._build_behavioral_profile(customer_data, customer_memory_signals)
        vehicle_rel = self._build_vehicle_relationship(vehicle, telematics, maintenance_history)
        emotional = self._build_emotional_profile(
            customer_memory_signals, conversation_memory_summary
        )
        comm_style = self._determine_comm_style(behavioral, emotional)
        urgency_frame = self._build_urgency_frame(vehicle_rel, emotional, telematics)
        reanalysis_context = self._build_reanalysis_context(reanalysis_result)

        return {
            "behavioral": behavioral,
            "vehicle_relationship": vehicle_rel,
            "emotional": emotional,
            "comm_style": comm_style,
            "urgency_frame": urgency_frame,
            "reanalysis_context": reanalysis_context,
            "first_name": self._get_first_name(customer_data),
            "vehicle_desc": self._build_vehicle_desc(vehicle),
            "personalization_notes": self._build_notes(
                behavioral, vehicle_rel, emotional, reanalysis_context
            ),
        }

    # ── Behavioral Profile ────────────────────────────────────────────────────

    def _build_behavioral_profile(self, customer_data: Dict, signals: Dict) -> Dict:
        """Build behavioral profile from customer data and memory signals."""
        return {
            # Response patterns
            "is_quick_responder": signals.get("QUICK_RESPONDER", False),
            "avg_response_hours": signals.get("avg_response_hours", 24),
            "response_speed": self._classify_response_speed(
                signals.get("avg_response_hours", 24)
            ),

            # Channel preferences
            "preferred_channel": customer_data.get("preferred_channel",
                                                   signals.get("preferred_channel", "EMAIL")),
            "channel_engagement_rate": signals.get("channel_engagement_rate", 0.5),

            # Trust and decline patterns
            "trust_sensitivity": signals.get("trust_sensitivity", "MEDIUM"),
            "often_declines": signals.get("OFTEN_DECLINES", False),
            "decline_rate": signals.get("decline_rate", 0.0),
            "is_high_trust": signals.get("HIGH_TRUST_CUSTOMER", False),

            # Data and price preferences
            "prefers_data": signals.get("PREFERS_DATA", False),
            "price_sensitive": signals.get("PRICE_SENSITIVE", False),
            "price_sensitivity_score": signals.get("price_sensitivity_score", 0.5),

            # Satisfaction
            "past_satisfaction_score": signals.get("past_satisfaction_score", 0.7),
            "has_complained_before": signals.get("has_complained_before", False),

            # Interaction history
            "total_interactions": signals.get("total_interactions", 0),
            "total_bookings": signals.get("total_bookings", 0),
        }

    def _classify_response_speed(self, avg_hours: float) -> str:
        if avg_hours < 2:
            return "VERY_FAST"
        elif avg_hours < 6:
            return "FAST"
        elif avg_hours < 24:
            return "NORMAL"
        elif avg_hours < 72:
            return "SLOW"
        return "VERY_SLOW"

    # ── Vehicle Relationship ──────────────────────────────────────────────────

    def _build_vehicle_relationship(self, vehicle: Dict, telematics: Dict,
                                    maintenance_history: List[Dict]) -> Dict:
        """Build vehicle relationship profile."""
        odometer = telematics.get("odo_km", 0)
        year = vehicle.get("year", 2020)
        age_years = 2026 - int(year) if year else 0
        service_count = len(maintenance_history)

        # Loyalty classification
        if service_count >= 8:
            loyalty = "PLATINUM"
        elif service_count >= 5:
            loyalty = "HIGH"
        elif service_count >= 2:
            loyalty = "MEDIUM"
        else:
            loyalty = "LOW"

        # Recurring failures
        service_types = [h.get("service_type", "") for h in maintenance_history]
        recurring = [s for s in set(service_types) if service_types.count(s) > 1]

        # Mileage intensity
        expected_annual_km = 15000
        actual_annual_km = odometer / max(age_years, 1)
        mileage_intensity = "HIGH" if actual_annual_km > expected_annual_km * 1.3 else (
            "LOW" if actual_annual_km < expected_annual_km * 0.7 else "NORMAL"
        )

        return {
            "vehicle_age_years": age_years,
            "odometer_km": odometer,
            "service_count": service_count,
            "loyalty_level": loyalty,
            "recurring_issues": recurring[:3],
            "high_mileage": odometer > 80000,
            "long_ownership": age_years >= 3,
            "mileage_intensity": mileage_intensity,
            "annual_km_estimate": int(actual_annual_km),
            "is_loyal_customer": service_count >= 5,
        }

    # ── Emotional Profile ─────────────────────────────────────────────────────

    def _build_emotional_profile(self, signals: Dict,
                                 memory_summary: Dict) -> Dict:
        """Build emotional context profile."""
        trust_score = memory_summary.get("trust_score", 0.5)
        trust_trend = memory_summary.get("trust_trend", "stable")
        resistance = memory_summary.get("resistance_level", 0)
        trust_damage = memory_summary.get("trust_damage", False)

        # Frustration history
        frustration_history = signals.get("frustration_events", 0)
        trust_damage_events = signals.get("trust_damage_events", 0)

        # Time stress signals
        time_stress = signals.get("time_stressed", False)

        # Safety concern sensitivity
        safety_sensitive = signals.get("safety_concern_sensitive", False)

        # Determine emotional state
        if trust_damage or trust_damage_events > 0:
            state = "TRUST_DAMAGED"
        elif trust_score < 0.35:
            state = "DISTRUSTFUL"
        elif trust_score < 0.5 and trust_trend == "falling":
            state = "BECOMING_RESISTANT"
        elif resistance >= 3 or frustration_history > 2:
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
            "frustration_history": frustration_history,
            "trust_damage_events": trust_damage_events,
            "time_stressed": time_stress,
            "safety_concern_sensitive": safety_sensitive,
            "needs_reassurance": trust_score < 0.5 or trust_damage,
            "needs_space": resistance >= 3,
            "is_engaged": trust_score > 0.65,
        }

    # ── Communication Style ───────────────────────────────────────────────────

    def _determine_comm_style(self, behavioral: Dict, emotional: Dict) -> str:
        """Determine optimal communication style."""
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
        elif behavioral["is_high_trust"]:
            return "DIRECT_ADVISORY"
        return "WARM_PROFESSIONAL"

    # ── Urgency Frame ─────────────────────────────────────────────────────────

    def _build_urgency_frame(self, vehicle_rel: Dict, emotional: Dict,
                             telematics: Dict) -> str:
        """Determine how urgency should be framed for this customer."""
        if emotional["emotional_state"] in ("TRUST_DAMAGED", "DISTRUSTFUL"):
            return "NO_PRESSURE"  # Never use urgency language with damaged trust
        elif emotional["needs_space"]:
            return "GENTLE"
        elif vehicle_rel["is_loyal_customer"]:
            return "INVESTMENT_PROTECTION"  # "Protect your investment"
        elif vehicle_rel["high_mileage"]:
            return "RELIABILITY_FOCUSED"
        elif emotional["safety_concern_sensitive"]:
            return "SAFETY_FIRST"
        return "BALANCED"

    # ── Reanalysis Context ────────────────────────────────────────────────────

    def _build_reanalysis_context(self, reanalysis_result) -> Optional[Dict]:
        """Build context from reanalysis result if available."""
        if not reanalysis_result:
            return None
        return {
            "has_reanalysis": True,
            "tone_mode": reanalysis_result.tone_mode,
            "days_elapsed": reanalysis_result.days_elapsed,
            "updated_failure_prob": reanalysis_result.updated_failure_prob,
            "updated_rul_days": reanalysis_result.updated_rul_days,
            "delta_summary": reanalysis_result.delta_summary,
        }

    # ── Personalization Notes ─────────────────────────────────────────────────

    def _build_notes(self, behavioral: Dict, vehicle_rel: Dict,
                     emotional: Dict, reanalysis_context: Optional[Dict]) -> List[str]:
        """Build actionable personalization notes for the conversation agent."""
        notes = []

        # Behavioral notes
        if behavioral["often_declines"]:
            notes.append("History of declining — avoid pressure language, lead with empathy")
        if behavioral["is_high_trust"]:
            notes.append("High-trust customer — can be more direct with recommendations")
        if behavioral["prefers_data"]:
            notes.append("Data-oriented customer — lead with specific measurements and percentages")
        if behavioral["price_sensitive"]:
            notes.append("Price-sensitive — frame cost of inaction vs. cost of repair")
        if behavioral["response_speed"] == "VERY_SLOW":
            notes.append("Slow responder — keep messages concise and non-pressuring")
        if behavioral["past_satisfaction_score"] < 0.5:
            notes.append("Low past satisfaction — acknowledge and validate before any ask")

        # Vehicle relationship notes
        if vehicle_rel["loyalty_level"] in ("HIGH", "PLATINUM"):
            notes.append(f"Loyal customer ({vehicle_rel['service_count']} services) — acknowledge their loyalty")
        if vehicle_rel["recurring_issues"]:
            notes.append(f"Recurring issues: {', '.join(vehicle_rel['recurring_issues'])}")
        if vehicle_rel["high_mileage"]:
            notes.append("High-mileage vehicle — frame as protecting their investment")
        if vehicle_rel["mileage_intensity"] == "HIGH":
            notes.append("High driving intensity — component wear is accelerated")

        # Emotional notes
        if emotional["needs_reassurance"]:
            notes.append("Lead with empathy and reassurance before data")
        if emotional["needs_space"]:
            notes.append("Give space — avoid scheduling pressure, offer control")
        if emotional["time_stressed"]:
            notes.append("Time-stressed customer — offer quick, efficient options")
        if emotional["safety_concern_sensitive"]:
            notes.append("Safety-sensitive — safety framing resonates strongly")
        if emotional["trust_damage_events"] > 0:
            notes.append("Past trust damage events — mandatory trust recovery protocol")

        # Reanalysis notes
        if reanalysis_context and reanalysis_context.get("has_reanalysis"):
            tone = reanalysis_context["tone_mode"]
            notes.append(f"Follow-up cycle: use {tone} tone mode for opening")

        return notes

    # ── Helpers ───────────────────────────────────────────────────────────────

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
