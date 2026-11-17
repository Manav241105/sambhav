"""
Strategy Response Router - Enterprise Conversation Intelligence v2.0
THE CRITICAL BINDING LAYER: Routes intent + stage + trust + resistance to deterministic responses.

Architecture:
  Intent + Stage + Trust + Resistance
  → Edge Case Check (highest priority)
  → Trust Recovery Check
  → Strategy-Specific Deterministic Response
  → LLM Polish (optional, never changes direction)

RULE: LLM NEVER decides core response direction. It only polishes.
RULE: No generic fallback after Stage 2 or when trust < 0.6 or resistance > 2.
"""

from typing import Dict, List, Optional, Tuple
from edge_case_reasoning_engine import EdgeCaseReasoningEngine
from trust_recovery_engine import TrustRecoveryEngine
from logistics_reasoning_engine import LogisticsReasoningEngine


class StrategyResponseRouter:
    """
    Routes conversation state to the correct deterministic response.
    This is the core intelligence binding layer — eliminates generic fallbacks.
    """

    def __init__(self):
        self.edge_case_engine = EdgeCaseReasoningEngine()
        self.trust_recovery_engine = TrustRecoveryEngine()
        self.logistics_engine = LogisticsReasoningEngine()

    def route(
        self,
        user_reply: str,
        intent: str,
        stage: str,
        trust_score: float,
        resistance_level: int,
        memory_summary: Dict,
        # Diagnosis data
        component: str,
        failure_prob: float,
        rul_days: int,
        severity: str,
        reasoning: str,
        failure_mode: str,
        recommended_action: str,
        # Personalization
        first_name: str,
        vehicle_desc: str,
        brake_mm: float,
        battery_v: float,
        odometer: int,
        # Context
        turn_number: int,
        strategies_used: List[str],
        topics_covered: List[str],
        personalization_notes: List[str],
    ) -> Tuple[str, str, bool]:
        """
        Route to the correct response.

        Returns:
          (response_text, routing_path, requires_llm_polish)
          routing_path: describes which engine generated the response (for logging)
          requires_llm_polish: True if LLM should naturalize the response
        """
        # ── PRIORITY 1: Edge Case Detection ──────────────────────────────────
        edge_case = self.edge_case_engine.detect_edge_case(user_reply, intent, memory_summary)

        if edge_case == "EC_PAST_BAD_SERVICE":
            response = self.edge_case_engine.handle_past_bad_service(
                user_reply, first_name, vehicle_desc, component,
                failure_prob, rul_days, brake_mm
            )
            return response, "EDGE_CASE:PAST_BAD_SERVICE", False

        if edge_case == "EC_FAMILY_MECHANIC":
            response = self.edge_case_engine.handle_family_mechanic(
                user_reply, first_name, vehicle_desc, component,
                failure_prob, rul_days, brake_mm
            )
            return response, "EDGE_CASE:FAMILY_MECHANIC", False

        if edge_case == "EC_OUT_OF_TOWN_HIGH_RISK":
            logistics = self.logistics_engine.analyze_constraint(
                user_reply, rul_days, failure_prob / 100
            )
            response = self.edge_case_engine.handle_out_of_town(
                user_reply, first_name, vehicle_desc, component,
                failure_prob, rul_days, brake_mm,
                logistics.get("mentioned_days"),
                logistics.get("delay_exceeds_rul", False)
            )
            return response, "EDGE_CASE:OUT_OF_TOWN", False

        if edge_case == "EC_SKEPTICAL_POLITE":
            response = self.edge_case_engine.handle_skeptical_polite(
                user_reply, first_name, vehicle_desc, component,
                failure_prob, rul_days, brake_mm, reasoning
            )
            return response, "EDGE_CASE:SKEPTICAL", False

        if edge_case == "EC_COST_SENSITIVE":
            response = self.edge_case_engine.handle_cost_sensitive(
                user_reply, first_name, vehicle_desc, component,
                failure_prob, rul_days, brake_mm
            )
            return response, "EDGE_CASE:COST_SENSITIVE", False

        # ── PRIORITY 2: Trust Recovery ────────────────────────────────────────
        if memory_summary.get("trust_damage") or trust_score < 0.35:
            response = self.trust_recovery_engine.generate_trust_recovery_response(
                user_reply, intent, first_name, vehicle_desc,
                component, failure_prob, rul_days, brake_mm, turn_number
            )
            return response, "TRUST_RECOVERY", False

        # ── PRIORITY 3: Anti-Generic Rule ─────────────────────────────────────
        # If stage >= HANDLE_OBJECTIONS or trust < 0.6 or resistance > 2,
        # we MUST provide a value response — never generic open-ended filler.
        must_provide_value = (
            stage in ("STAGE_3_HANDLE_OBJECTIONS", "STAGE_4_DECISION_SUPPORT", "STAGE_5_SOFT_CLOSE")
            or trust_score < 0.6
            or resistance_level > 2
        )

        # ── PRIORITY 4: Strategy-Specific Deterministic Response ──────────────
        response = self._generate_strategy_response(
            intent, stage, user_reply, first_name, vehicle_desc,
            component, failure_prob, rul_days, severity, reasoning,
            brake_mm, battery_v, odometer, turn_number,
            strategies_used, topics_covered, must_provide_value
        )

        if response:
            # Allow LLM to naturalize if response is template-based
            return response, f"STRATEGY:{intent}:{stage}", True

        # ── PRIORITY 5: Absolute Last Resort (never generic after objection stage) ──
        if must_provide_value:
            response = self._value_guaranteed_response(
                intent, first_name, vehicle_desc, component,
                failure_prob, rul_days, brake_mm, reasoning, turn_number
            )
            return response, "VALUE_GUARANTEED_FALLBACK", False

        # Only allow generic if early stage and low resistance
        return (
            f"I appreciate you sharing that, {first_name}. "
            f"What specific aspect of {vehicle_desc}'s {component} situation "
            f"would be most helpful for me to explain?",
            "MINIMAL_FALLBACK",
            True
        )

    def _generate_strategy_response(
        self, intent: str, stage: str, user_reply: str,
        first_name: str, vehicle_desc: str, component: str,
        failure_prob: float, rul_days: int, severity: str, reasoning: str,
        brake_mm: float, battery_v: float, odometer: int, turn_number: int,
        strategies_used: List[str], topics_covered: List[str],
        must_provide_value: bool
    ) -> Optional[str]:
        """Generate strategy-specific deterministic response"""

        # SECOND_OPINION_SEEKING — always deterministic
        if intent == "SECOND_OPINION_SEEKING":
            return (
                f"Absolutely, {first_name} — that's a smart move, and I fully support it. "
                f"Let me prepare the complete diagnostic report for {vehicle_desc}: "
                f"the exact {component} measurement ({brake_mm:.2f}mm vs 3mm critical threshold), "
                f"the sensor trend data, and the {failure_prob:.0f}% failure probability calculation. "
                f"Any qualified mechanic will be able to verify these numbers independently. "
                f"I'm confident in what the data shows — and I want you to be too. "
                f"Shall I email you the full report so you can share it with them?"
            )

        # LOGISTICS_BLOCKER — always deterministic
        if intent == "LOGISTICS_BLOCKER":
            logistics = self.logistics_engine.analyze_constraint(
                user_reply, rul_days, failure_prob / 100
            )
            mentioned_days = logistics.get("mentioned_days")
            delay_exceeds = logistics.get("delay_exceeds_rul", False)
            if delay_exceeds:
                precautions = self.logistics_engine.get_precautions_for_component(
                    component, rul_days, failure_prob / 100
                )
                return (
                    f"I completely understand, {first_name}. "
                    f"Since your return timeline goes beyond the {rul_days}-day safe window, "
                    f"here are the precautions to follow while you're away: "
                    f"{precautions[:250]}... "
                    f"I can also pre-book a slot for when you return — no payment needed now. "
                    f"Would that help?"
                )
            return (
                f"No problem, {first_name} — since you'll be back within the safe window, "
                f"let me pre-book a slot for your return. "
                f"Drive cautiously in the meantime — avoid hard braking if possible. "
                f"When do you expect to be back?"
            )

        # SOFT_DECLINE — empathy + precautions + door open
        if intent == "SOFT_DECLINE":
            return (
                f"I completely understand, {first_name}, and I respect that. "
                f"Before we leave it there — {vehicle_desc}'s {component} has a "
                f"{failure_prob:.0f}% failure risk in {rul_days} days. "
                f"Please drive cautiously: avoid hard braking, keep extra following distance, "
                f"and listen for any grinding sounds. "
                f"If anything feels different about how the car drives, please reach out immediately. "
                f"I'll be here whenever you're ready."
            )

        # HARD_DECLINE — graceful exit with safety note
        if intent == "HARD_DECLINE":
            return (
                f"I completely respect your decision, {first_name}. "
                f"One thing I want to leave you with: {vehicle_desc}'s {component} "
                f"is at {brake_mm:.2f}mm with {failure_prob:.0f}% failure risk in {rul_days} days. "
                f"Please drive cautiously and reach out anytime if you change your mind. "
                f"Your safety is what matters most. Take care!"
            )

        # READY_TO_BOOK — confirm and schedule
        if intent == "READY_TO_BOOK":
            return (
                f"That's great to hear, {first_name}! "
                f"I'll get that booked for {vehicle_desc} right away. "
                f"We'll take care of the {component} and have you back on the road safely. "
                f"What day and time works best for you?"
            )

        # INFO_GATHERING — provide specific new data
        if intent == "INFO_GATHERING":
            # Pick data not yet shared
            if "brake_measurement" not in topics_covered and brake_mm > 0:
                return (
                    f"Great question, {first_name}. Here's the specific data: "
                    f"{vehicle_desc}'s {component} is at {brake_mm:.2f}mm. "
                    f"The manufacturer's warning threshold is 5mm — you're already below that. "
                    f"The critical threshold (where braking performance degrades significantly) is 3mm. "
                    f"At the current degradation rate: {reasoning}. "
                    f"This gives us {failure_prob:.0f}% confidence in a failure within {rul_days} days. "
                    f"What else would you like to understand?"
                )
            elif "failure_mode" not in topics_covered:
                return (
                    f"To explain what actually happens if this is left unaddressed, {first_name}: "
                    f"{failure_mode}. "
                    f"In practical terms, this means {self._explain_failure_consequence(component)}. "
                    f"That's why we're reaching out now rather than waiting. "
                    f"Does that help clarify the urgency?"
                )
            else:
                return (
                    f"Here's something you might not know yet, {first_name}: "
                    f"industry safety standards (FMVSS 105) require brake replacement "
                    f"before pads reach 2mm. At {brake_mm:.2f}mm, {vehicle_desc} is "
                    f"approaching that threshold. This isn't just our recommendation — "
                    f"it's a universal automotive safety standard. "
                    f"What other questions can I answer?"
                )

        # For all other intents in must_provide_value mode
        if must_provide_value:
            return None  # Fall through to value_guaranteed_response

        return None

    def _value_guaranteed_response(
        self, intent: str, first_name: str, vehicle_desc: str,
        component: str, failure_prob: float, rul_days: int,
        brake_mm: float, reasoning: str, turn_number: int
    ) -> str:
        """
        Absolute guarantee: never returns generic filler.
        Always provides specific value when must_provide_value is True.
        """
        return (
            f"{first_name}, I want to make sure I'm actually helping you here. "
            f"Let me be direct: {vehicle_desc}'s {component} is at {brake_mm:.2f}mm "
            f"(critical threshold: 3mm) with {failure_prob:.0f}% failure risk in {rul_days} days. "
            f"That's based on live sensor data — {reasoning}. "
            f"I understand you have concerns, and I want to address them specifically. "
            f"What's the main thing holding you back right now?"
        )

    def _explain_failure_consequence(self, component: str) -> str:
        """Explain what failure actually means in plain language"""
        lower = component.lower()
        if "brake" in lower:
            return (
                "braking distance increases significantly, and in an emergency stop situation, "
                "the vehicle may not stop in time — creating serious accident risk"
            )
        elif "battery" in lower:
            return (
                "the vehicle may fail to start, or worse, stall while driving — "
                "leaving you stranded or creating a safety hazard"
            )
        elif "coolant" in lower or "engine" in lower:
            return (
                "the engine can overheat, leading to warped cylinder heads, "
                "blown gaskets, or complete engine seizure — a repair that costs "
                "10-20x more than addressing the cooling issue now"
            )
        return (
            "the component fails while driving, potentially causing a safety incident "
            "and significantly more expensive emergency repairs"
        )
