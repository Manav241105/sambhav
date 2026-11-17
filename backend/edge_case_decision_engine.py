"""
Edge Case Decision Engine - Autonomous Service Orchestration Platform v1.0
Extended edge case library with 7 critical scenarios.

New cases added over EdgeCaseReasoningEngine v2.0:
  EC6: Silent After Follow-Up Promise → Re-analyze vehicle → Send updated risk message
  EC7: Customer Asks For Supervisor → Only then escalate to human advisor

All existing cases retained:
  EC1: Past Bad Service / Trust Damage
  EC2: Family Mechanic / Second Opinion
  EC3: Out of Town with High Risk
  EC4: Cost Sensitivity
  EC5: Skeptical But Polite
"""

from typing import Dict, Optional, Tuple


# ── Detection Keyword Banks ───────────────────────────────────────────────────

PAST_BAD_SERVICE_SIGNALS = [
    "last time", "before", "previously", "bad experience", "terrible",
    "awful", "disappointed", "let down", "didn't fix", "came back",
    "same problem", "charged me", "overcharged", "ripped off",
    "not happy", "unhappy", "never again", "last visit", "last service",
    "6 days", "days late", "wasn't fixed", "issue wasn't", "problem wasn't",
    "trust", "don't trust", "can't trust", "won't trust"
]

FAMILY_MECHANIC_SIGNALS = [
    "family mechanic", "my mechanic", "uncle", "cousin", "friend",
    "knows cars", "second opinion", "another mechanic", "local garage",
    "trusted mechanic", "my guy", "someone i know", "someone who knows"
]

OUT_OF_TOWN_SIGNALS = [
    "out of town", "travelling", "traveling", "away", "not in the city",
    "out of station", "abroad", "on a trip", "on holiday", "on vacation",
    "not here", "not around", "will be back", "returning"
]

COST_SENSITIVE_SIGNALS = [
    "expensive", "costly", "too much", "can't afford", "afford",
    "price", "cost", "quote", "how much", "cheaper", "discount",
    "budget", "tight", "money", "financial", "payment plan",
    "installment", "emi", "worth it", "not worth"
]

SKEPTICAL_SIGNALS = [
    "really", "are you sure", "how do you know", "prove it",
    "sounds like", "seems like", "just trying", "trying to sell",
    "upsell", "unnecessary", "not necessary", "do i really need",
    "is it urgent", "can it wait", "how bad is it"
]

SILENT_SIGNALS = [
    "no response", "didn't respond", "hasn't replied", "silent",
    "ghosted", "no reply", "not responding"
]

SUPERVISOR_SIGNALS = [
    "supervisor", "manager", "speak to someone", "speak to a person",
    "human", "real person", "not a bot", "not ai", "escalate",
    "complaint", "formal complaint", "legal", "lawyer", "consumer court",
    "warranty dispute", "ombudsman"
]


class EdgeCaseDecisionEngine:
    """
    Extended edge case decision engine with 7 critical scenarios.
    Detects edge cases and returns deterministic, premium-quality responses.
    """

    def detect_edge_case(self, user_reply: str, intent: str,
                         memory_summary: Dict,
                         is_silent: bool = False) -> Optional[str]:
        """
        Detect which edge case applies (if any).

        Priority order:
        1. Past Bad Service (highest — trust damage must be addressed first)
        2. Supervisor Request (explicit escalation)
        3. Silent After Promise (no reply after follow-up promise)
        4. Family Mechanic
        5. Out of Town
        6. Cost Sensitive
        7. Skeptical Polite

        Returns edge case name or None.
        """
        lower = user_reply.lower().strip() if user_reply else ""

        # EC1: Past bad service / trust damage (highest priority)
        if (any(sig in lower for sig in PAST_BAD_SERVICE_SIGNALS) or
                intent in ("PAST_BAD_SERVICE", "TRUST_DAMAGE") or
                memory_summary.get("trust_damage", False)):
            return "PAST_BAD_SERVICE"

        # EC7: Supervisor / escalation request
        if (any(sig in lower for sig in SUPERVISOR_SIGNALS) or
                intent in ("SUPERVISOR_REQUEST", "LEGAL_DISPUTE", "EXTREME_COMPLAINT")):
            return "SUPERVISOR_REQUEST"

        # EC6: Silent after follow-up promise
        if is_silent or intent == "SILENT_AFTER_PROMISE":
            return "SILENT_AFTER_PROMISE"

        # EC2: Family mechanic / second opinion
        if (any(sig in lower for sig in FAMILY_MECHANIC_SIGNALS) or
                intent == "FAMILY_MECHANIC"):
            return "FAMILY_MECHANIC"

        # EC3: Out of town with high risk
        if (any(sig in lower for sig in OUT_OF_TOWN_SIGNALS) or
                intent == "OUT_OF_TOWN"):
            return "OUT_OF_TOWN"

        # EC4: Cost sensitivity
        if (any(sig in lower for sig in COST_SENSITIVE_SIGNALS) or
                intent in ("COST_OBJECTION", "PRICE_INQUIRY")):
            return "COST_SENSITIVE"

        # EC5: Skeptical but polite
        if (any(sig in lower for sig in SKEPTICAL_SIGNALS) or
                intent == "SKEPTICAL"):
            return "SKEPTICAL_POLITE"

        return None

    def handle(self, edge_case: str, user_reply: str, intent: str,
               memory_summary: Dict, personalization_context: Dict,
               vehicle_data: Dict, diagnosis: Dict,
               reanalysis_result=None) -> Tuple[str, str, bool]:
        """
        Handle a detected edge case.

        Returns:
            (response_text, routing_path, requires_llm_polish)
        """
        handlers = {
            "PAST_BAD_SERVICE":       self._handle_past_bad_service,
            "SUPERVISOR_REQUEST":     self._handle_supervisor_request,
            "SILENT_AFTER_PROMISE":   self._handle_silent_after_promise,
            "FAMILY_MECHANIC":        self._handle_family_mechanic,
            "OUT_OF_TOWN":            self._handle_out_of_town,
            "COST_SENSITIVE":         self._handle_cost_sensitive,
            "SKEPTICAL_POLITE":       self._handle_skeptical_polite,
        }
        handler = handlers.get(edge_case)
        if not handler:
            return ("", "EDGE_CASE_UNKNOWN", False)

        return handler(
            user_reply, intent, memory_summary, personalization_context,
            vehicle_data, diagnosis, reanalysis_result
        )

    # ── EC1: Past Bad Service ─────────────────────────────────────────────────

    def _handle_past_bad_service(self, user_reply: str, intent: str,
                                 memory_summary: Dict, personalization: Dict,
                                 vehicle_data: Dict, diagnosis: Dict,
                                 reanalysis_result) -> Tuple[str, str, bool]:
        first_name = personalization.get("first_name", "there")
        component = diagnosis.get("primary_component", "component")

        response = (
            f"{first_name}, I hear you — and I want to acknowledge that directly. "
            f"What you experienced before was not acceptable, and I completely understand "
            f"why that would make you hesitant to trust us again.\n\n"
            f"I'm not going to brush past that. If we let you down before, "
            f"that's on us — and it's something we take seriously.\n\n"
            f"Here's what's different now: before I even reach out to you, "
            f"I pull the live data on your vehicle. I'm not guessing — "
            f"I'm working from real readings. And if you decide to come in, "
            f"you'll have a dedicated technician assigned before you arrive, "
            f"a live status tracker so you know exactly what's happening, "
            f"and a direct line to me if anything feels off.\n\n"
            f"I'm not asking you to trust us blindly. I'm asking for the chance "
            f"to show you that this time is different. "
            f"You're in complete control of this — no pressure, no rush."
        )
        return (response, "EC1_PAST_BAD_SERVICE", True)

    # ── EC7: Supervisor Request ───────────────────────────────────────────────

    def _handle_supervisor_request(self, user_reply: str, intent: str,
                                   memory_summary: Dict, personalization: Dict,
                                   vehicle_data: Dict, diagnosis: Dict,
                                   reanalysis_result) -> Tuple[str, str, bool]:
        first_name = personalization.get("first_name", "there")

        response = (
            f"Absolutely, {first_name} — I completely understand, and I respect that. "
            f"I'm connecting you with our Service Manager right now.\n\n"
            f"Before I transfer you, I want to make sure they have the full picture: "
            f"your vehicle data, the current diagnosis, and our conversation history — "
            f"so you don't have to repeat yourself.\n\n"
            f"You'll be connected within the next few minutes. "
            f"Is there anything specific you'd like me to flag for them before the transfer?"
        )
        return (response, "EC7_SUPERVISOR_REQUEST_ESCALATION", True)

    # ── EC6: Silent After Follow-Up Promise ───────────────────────────────────

    def _handle_silent_after_promise(self, user_reply: str, intent: str,
                                     memory_summary: Dict, personalization: Dict,
                                     vehicle_data: Dict, diagnosis: Dict,
                                     reanalysis_result) -> Tuple[str, str, bool]:
        first_name = personalization.get("first_name", "there")
        component = diagnosis.get("primary_component", "component")
        failure_prob = diagnosis.get("failure_probability", 0.5) * 100
        rul_days = diagnosis.get("rul_days", 30)

        # Use reanalysis data if available
        if reanalysis_result:
            failure_prob = reanalysis_result.updated_failure_prob
            rul_days = reanalysis_result.updated_rul_days
            tone = reanalysis_result.tone_mode
            opening = reanalysis_result.get_opening_line(first_name, component)
        else:
            tone = "STABLE"
            opening = (
                f"{first_name}, I wanted to check in — I know life gets busy "
                f"and things come up. No pressure at all."
            )

        response = (
            f"{opening}\n\n"
            f"I've just pulled the latest data on your {component}: "
            f"the failure probability is now at {failure_prob:.0f}% "
            f"within {rul_days} days.\n\n"
            f"I'm not reaching out to pressure you — I genuinely want to make sure "
            f"you have the most current information so you can make the right call "
            f"for yourself.\n\n"
            f"If now still isn't a good time, just let me know when works for you "
            f"and I'll follow up then. You're in control."
        )
        return (response, "EC6_SILENT_AFTER_PROMISE_REANALYSIS", True)

    # ── EC2: Family Mechanic ──────────────────────────────────────────────────

    def _handle_family_mechanic(self, user_reply: str, intent: str,
                                memory_summary: Dict, personalization: Dict,
                                vehicle_data: Dict, diagnosis: Dict,
                                reanalysis_result) -> Tuple[str, str, bool]:
        first_name = personalization.get("first_name", "there")
        component = diagnosis.get("primary_component", "component")

        response = (
            f"That makes complete sense, {first_name} — having someone you trust "
            f"look at it is always a good call.\n\n"
            f"I'd actually like to support that. I can share the full diagnostic report "
            f"with your mechanic — the exact sensor readings, failure probability model, "
            f"and the specific measurements that triggered our alert. "
            f"That way they have everything they need to give you an informed second opinion.\n\n"
            f"Would it help if I sent that over? It's your data — you should have it."
        )
        return (response, "EC2_FAMILY_MECHANIC_SUPPORT", True)

    # ── EC3: Out of Town ──────────────────────────────────────────────────────

    def _handle_out_of_town(self, user_reply: str, intent: str,
                            memory_summary: Dict, personalization: Dict,
                            vehicle_data: Dict, diagnosis: Dict,
                            reanalysis_result) -> Tuple[str, str, bool]:
        first_name = personalization.get("first_name", "there")
        component = diagnosis.get("primary_component", "component")
        failure_prob = diagnosis.get("failure_probability", 0.5) * 100
        rul_days = diagnosis.get("rul_days", 30)

        # High risk = more urgent safety coaching
        if failure_prob > 60:
            safety_note = (
                f"Given the current {failure_prob:.0f}% failure risk within {rul_days} days, "
                f"I'd recommend avoiding highway speeds and keeping extra following distance "
                f"while you're away. If you notice any changes — unusual sounds, vibration, "
                f"or warning lights — please pull over safely and contact roadside assistance."
            )
        else:
            safety_note = (
                f"The {component} is being monitored at {failure_prob:.0f}% risk — "
                f"please drive gently and let me know if anything changes while you're away."
            )

        response = (
            f"No problem at all, {first_name} — I completely understand. "
            f"Travel comes first.\n\n"
            f"{safety_note}\n\n"
            f"I can also check if there's an authorised service centre near where "
            f"you're travelling, if that would be helpful. "
            f"And when you're back, I'll have a slot ready for you — "
            f"just let me know your return date and I'll pre-book it."
        )
        return (response, "EC3_OUT_OF_TOWN_SAFETY_COACHING", True)

    # ── EC4: Cost Sensitive ───────────────────────────────────────────────────

    def _handle_cost_sensitive(self, user_reply: str, intent: str,
                               memory_summary: Dict, personalization: Dict,
                               vehicle_data: Dict, diagnosis: Dict,
                               reanalysis_result) -> Tuple[str, str, bool]:
        first_name = personalization.get("first_name", "there")
        component = diagnosis.get("primary_component", "component")
        failure_prob = diagnosis.get("failure_probability", 0.5) * 100

        response = (
            f"I completely understand, {first_name} — cost is a real consideration "
            f"and I want to be transparent with you.\n\n"
            f"Here's the honest picture: addressing the {component} now typically "
            f"costs significantly less than dealing with a failure — which can cascade "
            f"into additional damage to surrounding components.\n\n"
            f"A few options I can explore for you:\n"
            f"• **Exact quote** — I can get you a firm price before you commit to anything\n"
            f"• **Payment plan** — we offer flexible payment options if that helps\n"
            f"• **Priority scheduling** — if we book early, we can sometimes lock in "
            f"better pricing\n\n"
            f"Would you like me to pull a quote first? No obligation — "
            f"just so you have the full picture."
        )
        return (response, "EC4_COST_SENSITIVE_VALUE_FRAME", True)

    # ── EC5: Skeptical Polite ─────────────────────────────────────────────────

    def _handle_skeptical_polite(self, user_reply: str, intent: str,
                                 memory_summary: Dict, personalization: Dict,
                                 vehicle_data: Dict, diagnosis: Dict,
                                 reanalysis_result) -> Tuple[str, str, bool]:
        first_name = personalization.get("first_name", "there")
        component = diagnosis.get("primary_component", "component")
        failure_prob = diagnosis.get("failure_probability", 0.5) * 100
        rul_days = diagnosis.get("rul_days", 30)

        # Pull specific telematics data for credibility
        telematics = vehicle_data.get("telematics", {})
        brake_mm = telematics.get("brake_pad_mm", None)
        battery_v = telematics.get("battery_voltage_v", None)

        data_line = ""
        if brake_mm and "brake" in component.lower():
            data_line = (
                f"The sensor reading shows your brake pad at {brake_mm:.2f}mm — "
                f"the safe minimum is 3mm. "
            )
        elif battery_v and "battery" in component.lower():
            data_line = (
                f"The battery voltage reading is {battery_v:.2f}V — "
                f"healthy range is 12.4V+. "
            )

        response = (
            f"That's a completely fair question, {first_name} — "
            f"and I'd rather show you the data than just ask you to take my word for it.\n\n"
            f"{data_line}"
            f"Our predictive model is flagging a {failure_prob:.0f}% failure probability "
            f"within {rul_days} days based on these live readings.\n\n"
            f"I can send you the full diagnostic report — every sensor reading, "
            f"the model inputs, and the output — so you can see exactly how we arrived "
            f"at this assessment. Would that help?"
        )
        return (response, "EC5_SKEPTICAL_DATA_TRANSPARENCY", True)
