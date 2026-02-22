"""
Edge Case Reasoning Engine - Enterprise Conversation Intelligence v2.0
Handles 5 critical edge cases with fully deterministic, premium-quality responses.

Edge Cases:
  EC_OUT_OF_TOWN_HIGH_RISK    → Safety coaching + mitigation + remote booking
  EC_FAMILY_MECHANIC          → Support + data share + relationship preservation
  EC_PAST_BAD_SERVICE         → Trust Recovery Mode (delegates to TrustRecoveryEngine)
  EC_SKEPTICAL_POLITE         → Data Transparency Mode
  EC_COST_SENSITIVE           → Financial Safety Mode
"""

from typing import Dict, Optional, Tuple


class EdgeCaseReasoningEngine:
    """
    Detects and handles edge cases with deterministic, high-quality responses.
    Each edge case has a specific response protocol.
    """

    def detect_edge_case(self, user_reply: str, intent: str,
                         memory_summary: Dict) -> Optional[str]:
        """
        Detect which edge case applies (if any).
        Returns edge case code or None.
        Priority order: trust damage > family mechanic > out of town > cost > skeptical
        """
        lower = user_reply.lower()

        # EC1: Past bad service / trust damage (highest priority)
        trust_damage_intents = {
            "PAST_SERVICE_FAILURE", "TRUST_DAMAGE_EVENT",
            "SERVICE_DELAY_TRAUMA", "REPAIR_QUALITY_DOUBT",
            "DEALERSHIP_AVOIDANCE_PATTERN", "PRICE_SHOCK_HISTORY"
        }
        trust_damage_keywords = [
            "last time", "previously", "before", "last service", "past experience",
            "came late", "not fixed", "not solved", "had to come back", "again",
            "why should i trust", "don't trust", "trusted you before",
            "6 days", "delayed", "poor service", "bad experience", "disappointed",
            "never again", "same issue", "issue not resolved", "came back"
        ]
        if intent in trust_damage_intents or any(kw in lower for kw in trust_damage_keywords):
            return "EC_PAST_BAD_SERVICE"

        # EC2: Family mechanic / second opinion
        family_mechanic_keywords = [
            "family mechanic", "my mechanic", "local mechanic", "trusted mechanic",
            "second opinion", "check elsewhere", "my guy", "regular mechanic",
            "want to check", "let me check", "will check", "someone else",
            "another garage", "another workshop", "verify", "confirm"
        ]
        if intent == "SECOND_OPINION_SEEKING" or any(kw in lower for kw in family_mechanic_keywords):
            return "EC_FAMILY_MECHANIC"

        # EC3: Out of town with high risk
        travel_keywords = [
            "out of town", "not in town", "travelling", "traveling", "travel",
            "trip", "away", "out of city", "vacation", "holiday", "not here",
            "not around", "business trip", "conference", "not available"
        ]
        if intent == "LOGISTICS_BLOCKER" or any(kw in lower for kw in travel_keywords):
            return "EC_OUT_OF_TOWN_HIGH_RISK"

        # EC4: Cost sensitivity
        cost_keywords = [
            "expensive", "cost", "price", "afford", "money", "budget",
            "how much", "quote", "estimate", "too much", "pricey", "costly",
            "financial", "payment plan", "installment"
        ]
        if intent == "COST_CONCERN" or any(kw in lower for kw in cost_keywords):
            return "EC_COST_SENSITIVE"

        # EC5: Skeptical but polite
        skeptical_keywords = [
            "don't think", "not that serious", "really?", "are you sure",
            "how do you know", "doubt", "not convinced", "seems fine",
            "drives fine", "no problem", "no issue", "feels okay",
            "nothing wrong", "seems okay", "looks fine"
        ]
        if intent == "SKEPTICISM" or any(kw in lower for kw in skeptical_keywords):
            return "EC_SKEPTICAL_POLITE"

        return None

    def handle_out_of_town(
        self, user_reply: str, first_name: str, vehicle_desc: str,
        component: str, failure_prob: float, rul_days: int,
        brake_mm: float, mentioned_days: Optional[int],
        delay_exceeds_rul: bool
    ) -> str:
        """EC_OUT_OF_TOWN_HIGH_RISK: Safety coaching + mitigation + remote booking"""
        days_str = f"{mentioned_days} days" if mentioned_days else "your trip"

        if delay_exceeds_rul:
            return (
                f"{first_name}, I completely understand — being away is a real constraint, "
                f"and I appreciate you telling me. "
                f"Here's what concerns me: with {rul_days} days estimated until potential failure "
                f"and {failure_prob:.0f}% risk, your return timeline of {days_str} "
                f"goes beyond the safe window. So let me give you two things right now:\n\n"
                f"🛡️ **Safety precautions for while you're away:**\n"
                f"• Avoid hard or sudden braking — always brake gently and early\n"
                f"• Keep at least 4 seconds of following distance from the car ahead\n"
                f"• Avoid speeds above 80 km/h on highways if possible\n"
                f"• Listen for grinding or squealing when braking — if you hear metal-on-metal, "
                f"stop driving and call roadside assistance immediately\n"
                f"• Avoid steep downhill roads\n\n"
                f"📅 **Logistics options:**\n"
                f"• I can pre-book a slot for the day you return — no payment needed now, "
                f"just a reservation so you're not scrambling for availability\n"
                f"• If there's a certified service center near where you are, "
                f"I can help you find one\n\n"
                f"Which would be more helpful — the pre-booking, or finding a local center?"
            )
        else:
            return (
                f"No problem at all, {first_name} — since you'll be back before the "
                f"{rul_days}-day window, we have some flexibility. "
                f"A few precautions while you're away: brake gently, keep extra distance, "
                f"and listen for any unusual sounds. "
                f"Shall I pre-book a slot for when you return so it's one less thing to think about?"
            )

    def handle_family_mechanic(
        self, user_reply: str, first_name: str, vehicle_desc: str,
        component: str, failure_prob: float, rul_days: int,
        brake_mm: float
    ) -> str:
        """EC_FAMILY_MECHANIC: Support + data share + relationship preservation"""
        return (
            f"Absolutely, {first_name} — having a mechanic you trust is genuinely valuable, "
            f"and I fully support you getting a second opinion. That's a smart move.\n\n"
            f"Here's what I'd suggest: let me prepare the complete diagnostic report "
            f"for {vehicle_desc} — it includes:\n"
            f"• The exact {component} measurement: {brake_mm:.2f}mm "
            f"(manufacturer warning threshold: 5mm, critical: 3mm)\n"
            f"• The sensor trend data showing the degradation rate\n"
            f"• The failure probability calculation: {failure_prob:.0f}% within {rul_days} days\n"
            f"• The full telematics readout\n\n"
            f"Any qualified mechanic will be able to verify these numbers independently. "
            f"I'm confident in what the data shows — and I want you to be too, "
            f"whether that's through us or through your trusted mechanic.\n\n"
            f"Shall I email you the full report so you can share it with them?"
        )

    def handle_skeptical_polite(
        self, user_reply: str, first_name: str, vehicle_desc: str,
        component: str, failure_prob: float, rul_days: int,
        brake_mm: float, reasoning: str
    ) -> str:
        """EC_SKEPTICAL_POLITE: Data Transparency Mode"""
        return (
            f"That's a completely fair reaction, {first_name} — "
            f"I'd want to understand the specifics too before making any decisions.\n\n"
            f"Let me walk you through exactly what we're seeing:\n\n"
            f"📊 **The measurement:** {vehicle_desc}'s {component} is currently at "
            f"{brake_mm:.2f}mm. The manufacturer's warning threshold is 5mm — "
            f"you're already below that. The critical threshold (where braking performance "
            f"becomes significantly compromised) is 3mm.\n\n"
            f"📈 **The trend:** {reasoning}. "
            f"This gives us {failure_prob:.0f}% confidence in a failure within {rul_days} days "
            f"based on the current degradation rate.\n\n"
            f"🔬 **How we know:** This isn't a visual inspection estimate — "
            f"it's continuous sensor data from {vehicle_desc}'s onboard telematics system, "
            f"cross-referenced with our predictive model trained on thousands of similar vehicles.\n\n"
            f"I'd encourage you to have any mechanic verify these measurements. "
            f"The data will look the same to them. "
            f"What specific part of this would you like me to explain further?"
        )

    def handle_cost_sensitive(
        self, user_reply: str, first_name: str, vehicle_desc: str,
        component: str, failure_prob: float, rul_days: int,
        brake_mm: float
    ) -> str:
        """EC_COST_SENSITIVE: Financial Safety Mode"""
        return (
            f"Cost is a completely valid concern, {first_name}, "
            f"and I want to give you the full financial picture — not just the repair cost.\n\n"
            f"💰 **Cost of early repair** (now): Brake pad replacement on {vehicle_desc} "
            f"typically runs ₹3,000–₹6,000 depending on the pad grade.\n\n"
            f"⚠️ **Cost of delayed repair** (if pads fail):\n"
            f"• Rotor damage from metal-on-metal contact: ₹8,000–₹15,000 additional\n"
            f"• Caliper damage if rotors are ignored: ₹12,000–₹25,000\n"
            f"• Emergency towing + urgent service premium: ₹2,000–₹5,000\n"
            f"• Total potential cost of failure: 4–8x the cost of doing it now\n\n"
            f"🗓️ **Payment options we offer:**\n"
            f"• Pay on pickup (no upfront payment needed)\n"
            f"• We can discuss a staged repair plan if budget is tight\n\n"
            f"With {failure_prob:.0f}% failure risk in {rul_days} days, "
            f"early action is genuinely the most cost-effective path. "
            f"Would a detailed written quote help you plan?"
        )

    def handle_past_bad_service(
        self, user_reply: str, first_name: str, vehicle_desc: str,
        component: str, failure_prob: float, rul_days: int,
        brake_mm: float
    ) -> str:
        """
        EC_PAST_BAD_SERVICE: Trust Recovery Mode.
        Delegates to TrustRecoveryEngine for full 6-step protocol.
        This method provides the edge case routing — actual response built by TrustRecoveryEngine.
        """
        # Detect specific details from their message
        lower = user_reply.lower()

        # Build specific acknowledgment based on what they said
        if "6 day" in lower or "six day" in lower or ("late" in lower and "day" in lower):
            specific_ack = (
                f"A 6-day delay beyond the promised date, and then the issue wasn't even resolved — "
                f"that's two separate failures, and your frustration is completely justified."
            )
        elif "not solved" in lower or "not fixed" in lower or ("again" in lower and "visit" in lower):
            specific_ack = (
                f"Having to bring your car back for the same issue after paying for a repair — "
                f"that's a failure on our part, full stop."
            )
        elif "why should i trust" in lower or "trust" in lower:
            specific_ack = (
                f"'Why should I trust you again?' — that's the most honest question you could ask, "
                f"and you deserve a direct answer."
            )
        else:
            specific_ack = (
                f"What you experienced — that's not the standard we hold ourselves to, "
                f"and I want to acknowledge it directly."
            )

        return (
            f"{first_name}, {specific_ack}\n\n"
            f"I'm not going to make excuses for what happened. "
            f"What I can tell you is what's changed:\n\n"
            f"✅ **What's different now:**\n"
            f"• Every repair now comes with a guaranteed completion date in writing — "
            f"if we miss it, you get a complimentary loaner vehicle\n"
            f"• You receive real-time SMS updates at every stage of the repair\n"
            f"• A senior technician signs off on every job before the car is returned\n"
            f"• All brake work comes with a 12-month / 20,000 km warranty — "
            f"if the issue recurs, we fix it at no charge\n"
            f"• You can track your vehicle's repair status live through our portal\n\n"
            f"🔍 **What I'm offering you:**\n"
            f"• The complete diagnostic report — every measurement, every data point — "
            f"so you can verify it independently\n"
            f"• A dedicated advisor (me) as your single point of contact throughout\n"
            f"• A written quote with itemized costs before any work begins\n\n"
            f"This is entirely your decision, {first_name}. "
            f"I'm not here to pressure you — I'm here to earn back your trust, "
            f"and I understand that takes more than words.\n\n"
            f"One thing I do want you to have regardless: "
            f"{vehicle_desc}'s {component} is at {brake_mm:.2f}mm with {failure_prob:.0f}% "
            f"failure risk in {rul_days} days. "
            f"Please drive cautiously — avoid hard braking and keep extra following distance. "
            f"If you hear any grinding, stop driving immediately.\n\n"
            f"Would you be open to at least seeing the full diagnostic report, "
            f"even if you decide to have someone else do the repair?"
        )
