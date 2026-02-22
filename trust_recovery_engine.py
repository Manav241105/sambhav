"""
Trust Recovery Engine - Enterprise Conversation Intelligence v2.0
Activated when past service failure, trust damage, or dealership avoidance is detected.

Trust Recovery Protocol (6 Steps):
  1. Acknowledge past bad experience (specific, not generic)
  2. Validate emotional impact (empathy without defensiveness)
  3. Show process improvement (concrete changes made)
  4. Offer transparency tools (diagnostic report, live tracking)
  5. Offer control back to customer (their timeline, their choice)
  6. Remove all pressure (no urgency language in trust recovery mode)
"""

from typing import Dict, Optional


class TrustRecoveryEngine:
    """
    Generates trust repair responses when past service failure or trust damage is detected.
    Follows a strict 6-step protocol. Never defensive, never pressuring.
    """

    # Intent → specific acknowledgment language
    INTENT_ACKNOWLEDGMENTS = {
        "PAST_SERVICE_FAILURE": (
            "What you went through — that's not okay, and I want to acknowledge that directly."
        ),
        "SERVICE_DELAY_TRAUMA": (
            "A 6-day delay beyond the promised date, and then having to bring it back again — "
            "that's genuinely frustrating, and you had every right to be upset."
        ),
        "REPAIR_QUALITY_DOUBT": (
            "If the repair didn't solve the problem the first time, "
            "that's a failure on our part — not yours."
        ),
        "TRUST_DAMAGE_EVENT": (
            "It sounds like a past experience left you with real doubts about whether "
            "you can trust what we tell you. That's completely understandable."
        ),
        "DEALERSHIP_AVOIDANCE_PATTERN": (
            "I understand why you'd be hesitant to come back after what happened. "
            "That reaction makes complete sense."
        ),
        "PRICE_SHOCK_HISTORY": (
            "If you've been surprised by unexpected costs in the past, "
            "I completely understand why you'd be cautious now."
        ),
    }

    # Process improvements to reference
    PROCESS_IMPROVEMENTS = [
        "We now provide a guaranteed completion time in writing before any work begins",
        "Every repair includes a post-service quality check by a senior technician",
        "You receive real-time SMS updates at each stage of the repair process",
        "If a repair takes longer than promised, we provide a complimentary loaner vehicle",
        "All work comes with a 12-month / 20,000 km warranty — if the issue recurs, we fix it free",
        "You can track your vehicle's repair status live through our customer portal",
    ]

    # Transparency tools to offer
    TRANSPARENCY_TOOLS = [
        "the complete diagnostic report with all sensor readings and measurements",
        "a video walkthrough of the exact issue on your vehicle",
        "a written quote with itemized costs before any work begins",
        "a dedicated service advisor who will be your single point of contact",
        "a post-repair inspection report with before/after measurements",
    ]

    def generate_trust_recovery_response(
        self,
        user_reply: str,
        intent: str,
        first_name: str,
        vehicle_desc: str,
        component: str,
        failure_prob: float,
        rul_days: int,
        brake_mm: float = 0,
        turn_number: int = 1,
    ) -> str:
        """
        Generate a full 6-step trust recovery response.
        Adapts to the specific trust damage type detected.
        """
        lower_reply = user_reply.lower()

        # Step 1: Specific acknowledgment
        acknowledgment = self.INTENT_ACKNOWLEDGMENTS.get(
            intent,
            "What you experienced sounds genuinely frustrating, and I want to acknowledge that."
        )

        # Step 2: Validate emotional impact — detect specific details from their message
        emotional_validation = self._build_emotional_validation(lower_reply, first_name)

        # Step 3: Process improvement (pick 2 most relevant)
        improvements = self._select_improvements(lower_reply)

        # Step 4: Transparency tool offer
        transparency = self._select_transparency_tool(lower_reply)

        # Step 5: Control return
        control_statement = (
            f"This is entirely your decision, {first_name}. "
            f"I'm not here to pressure you — I'm here to give you the information you need "
            f"to make the right choice for yourself."
        )

        # Step 6: Safety positioning (without pressure)
        safety_note = (
            f"The one thing I do want to make sure you have: "
            f"{vehicle_desc}'s {component} is at {brake_mm:.2f}mm with a {failure_prob:.0f}% "
            f"failure risk in {rul_days} days. "
            f"Whatever you decide, please drive cautiously — avoid hard braking and "
            f"keep extra distance from vehicles ahead."
        )

        # Assemble full response
        response = (
            f"{first_name}, {acknowledgment} "
            f"{emotional_validation} "
            f"\n\nSince then, we've made real changes: {improvements[0]}, and {improvements[1]}. "
            f"I'd also like to offer you {transparency} — completely upfront, before any commitment. "
            f"\n\n{control_statement} "
            f"\n\n{safety_note} "
            f"\n\nWould you be open to at least seeing the diagnostic data, "
            f"even if you decide to have someone else do the repair?"
        )

        return response

    def generate_short_trust_acknowledgment(
        self, intent: str, first_name: str, user_reply: str
    ) -> str:
        """
        Generate a shorter trust acknowledgment for mid-conversation trust signals.
        Used when trust damage is detected but full recovery protocol isn't needed yet.
        """
        acknowledgment = self.INTENT_ACKNOWLEDGMENTS.get(
            intent,
            "I hear you — and I want to acknowledge that directly."
        )
        return (
            f"{first_name}, {acknowledgment} "
            f"I want to be completely transparent with you about everything we're seeing. "
            f"What would help you feel more confident about this?"
        )

    def _build_emotional_validation(self, lower_reply: str, first_name: str) -> str:
        """Build specific emotional validation based on what customer said"""
        if "6 day" in lower_reply or "six day" in lower_reply or "late" in lower_reply:
            return (
                f"Waiting 6 days longer than expected, then having to come back again — "
                f"that's two separate failures, and your frustration is completely justified."
            )
        elif "not solved" in lower_reply or "not fixed" in lower_reply or "again" in lower_reply:
            return (
                "Having to return for the same issue after paying for a repair "
                "is one of the most frustrating experiences a car owner can have."
            )
        elif "trust" in lower_reply or "why should i" in lower_reply:
            return (
                f"Your question — 'why should I trust you again?' — is completely fair. "
                f"You shouldn't have to just take my word for it."
            )
        elif "money" in lower_reply or "cost" in lower_reply or "paid" in lower_reply:
            return (
                "Paying for a service and not getting the result you were promised "
                "is unacceptable. I understand why you'd be cautious."
            )
        else:
            return (
                f"Your experience left a real impression, {first_name}, "
                f"and it makes complete sense that you'd be hesitant now."
            )

    def _select_improvements(self, lower_reply: str) -> list:
        """Select the 2 most relevant process improvements"""
        if "late" in lower_reply or "delay" in lower_reply or "days" in lower_reply:
            return [self.PROCESS_IMPROVEMENTS[0], self.PROCESS_IMPROVEMENTS[3]]
        elif "not solved" in lower_reply or "not fixed" in lower_reply or "again" in lower_reply:
            return [self.PROCESS_IMPROVEMENTS[1], self.PROCESS_IMPROVEMENTS[4]]
        elif "update" in lower_reply or "communication" in lower_reply:
            return [self.PROCESS_IMPROVEMENTS[2], self.PROCESS_IMPROVEMENTS[5]]
        else:
            return [self.PROCESS_IMPROVEMENTS[0], self.PROCESS_IMPROVEMENTS[1]]

    def _select_transparency_tool(self, lower_reply: str) -> str:
        """Select the most relevant transparency tool"""
        if "data" in lower_reply or "proof" in lower_reply or "show" in lower_reply:
            return self.TRANSPARENCY_TOOLS[0]
        elif "cost" in lower_reply or "price" in lower_reply or "money" in lower_reply:
            return self.TRANSPARENCY_TOOLS[2]
        elif "mechanic" in lower_reply or "check" in lower_reply:
            return self.TRANSPARENCY_TOOLS[0]
        else:
            return self.TRANSPARENCY_TOOLS[3]
