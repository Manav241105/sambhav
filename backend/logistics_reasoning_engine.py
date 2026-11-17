"""
Logistics Reasoning Engine - Enterprise Conversation Intelligence
Handles real-world scheduling constraints and generates logistics solutions.

Scenarios handled:
  - Customer out of town longer than RUL window
  - Customer busy / tight schedule
  - Customer in different city / location
  - Customer wants to delay beyond safe window
"""

from typing import Dict, List, Optional
import re


class LogisticsReasoningEngine:
    """
    Analyzes customer logistics constraints and generates appropriate solutions.
    Handles cases where customer availability conflicts with safety window.
    """

    # Keywords indicating logistics blockers
    TRAVEL_KEYWORDS = [
        "out of town", "not in town", "travelling", "traveling", "travel", "trip",
        "away", "out of city", "vacation", "holiday", "station", "posted",
        "transfer", "another city", "not here", "not around", "business trip",
        "conference", "work trip", "not available", "out of country"
    ]

    DELAY_KEYWORDS = [
        "15 days", "two weeks", "2 weeks", "few weeks", "next month", "month",
        "when i'm back", "when i return", "back in", "come back", "after",
        "later", "some time", "eventually", "not now", "not today"
    ]

    BUSY_KEYWORDS = [
        "busy", "schedule", "can't make it", "cannot make it", "not free",
        "tied up", "occupied", "commitments", "no time", "hectic"
    ]

    def analyze_constraint(self, user_reply: str, rul_days: int,
                           failure_prob: float) -> Dict:
        """
        Analyze the logistics constraint from customer's message.
        Returns constraint type, severity, and recommended solutions.
        """
        lower_reply = user_reply.lower()

        is_travel = any(kw in lower_reply for kw in self.TRAVEL_KEYWORDS)
        is_delay = any(kw in lower_reply for kw in self.DELAY_KEYWORDS)
        is_busy = any(kw in lower_reply for kw in self.BUSY_KEYWORDS)

        # Try to extract days mentioned
        mentioned_days = self._extract_days(lower_reply)

        # Determine if delay exceeds RUL window
        delay_exceeds_rul = False
        if mentioned_days and mentioned_days > rul_days:
            delay_exceeds_rul = True
        elif is_travel and rul_days <= 15:
            delay_exceeds_rul = True  # Assume travel is at least a few days

        constraint_type = "NONE"
        if is_travel:
            constraint_type = "TRAVEL"
        elif is_delay:
            constraint_type = "DELAY"
        elif is_busy:
            constraint_type = "BUSY_SCHEDULE"

        severity = "LOW"
        if delay_exceeds_rul and failure_prob > 0.6:
            severity = "CRITICAL"
        elif delay_exceeds_rul:
            severity = "HIGH"
        elif failure_prob > 0.7:
            severity = "HIGH"

        solutions = self._generate_solutions(
            constraint_type, severity, rul_days, failure_prob,
            mentioned_days, is_travel
        )

        return {
            "constraint_type": constraint_type,
            "severity": severity,
            "delay_exceeds_rul": delay_exceeds_rul,
            "mentioned_days": mentioned_days,
            "is_travel": is_travel,
            "is_delay": is_delay,
            "is_busy": is_busy,
            "solutions": solutions,
            "primary_solution": solutions[0] if solutions else None,
        }

    def _extract_days(self, text: str) -> Optional[int]:
        """Try to extract a number of days from the text"""
        # Match patterns like "15 days", "2 weeks", "a month"
        day_match = re.search(r'(\d+)\s*day', text)
        if day_match:
            return int(day_match.group(1))

        week_match = re.search(r'(\d+)\s*week', text)
        if week_match:
            return int(week_match.group(1)) * 7

        if "month" in text:
            return 30

        if "two weeks" in text or "2 weeks" in text:
            return 14

        if "few days" in text:
            return 3

        if "few weeks" in text:
            return 21

        return None

    def _generate_solutions(self, constraint_type: str, severity: str,
                            rul_days: int, failure_prob: float,
                            mentioned_days: Optional[int],
                            is_travel: bool) -> List[str]:
        """Generate ordered list of logistics solutions"""
        solutions = []

        if constraint_type == "TRAVEL":
            solutions.append(
                f"REMOTE_BOOKING: Offer to pre-book appointment for when they return. "
                f"Lock in a slot so they don't have to worry about it."
            )
            if severity in ("HIGH", "CRITICAL"):
                solutions.append(
                    f"LOCAL_PARTNER: Suggest finding a certified service center near their "
                    f"current location — many dealerships have nationwide partner networks."
                )
                solutions.append(
                    f"SAFETY_PRECAUTIONS: Provide specific driving precautions for the "
                    f"next {mentioned_days or rul_days} days until they can get service."
                )
            solutions.append(
                f"MONITORING_FOLLOWUP: Offer to send a reminder when they return "
                f"and monitor their vehicle remotely via telematics."
            )

        elif constraint_type == "BUSY_SCHEDULE":
            solutions.append(
                "FLEXIBLE_TIMING: Offer early morning, evening, or weekend slots. "
                "Many service centers offer drop-off service — leave the car, pick it up later."
            )
            solutions.append(
                "ADVANCE_BOOKING: Book now for a future date that works for them. "
                "No commitment needed today — just reserve the slot."
            )
            if severity in ("HIGH", "CRITICAL"):
                solutions.append(
                    "MOBILE_SERVICE: Check if mobile mechanic service is available in their area."
                )

        elif constraint_type == "DELAY":
            if severity == "CRITICAL":
                solutions.append(
                    f"URGENCY_REFRAME: Gently explain that with {rul_days} days RUL and "
                    f"{failure_prob*100:.0f}% failure probability, waiting {mentioned_days or 'that long'} "
                    f"days significantly increases risk. Offer interim precautions."
                )
            solutions.append(
                "ADVANCE_BOOKING: Book the appointment now for their preferred future date. "
                "This ensures availability and gives them peace of mind."
            )
            solutions.append(
                "SAFETY_PRECAUTIONS: Provide specific precautions to minimize risk during the delay."
            )

        return solutions

    def get_precautions_for_component(self, component: str, rul_days: int,
                                      failure_prob: float) -> str:
        """Generate specific driving precautions for the affected component"""
        component_lower = component.lower()

        if "brake" in component_lower:
            return (
                f"Until your service appointment, please follow these brake safety precautions: "
                f"(1) Avoid sudden or hard braking — always brake gently and early, "
                f"(2) Maintain extra following distance (at least 4 seconds behind the vehicle ahead), "
                f"(3) Avoid highway speeds above 80 km/h if possible, "
                f"(4) Listen for grinding, squealing, or vibration when braking — if you hear metal-on-metal, "
                f"stop driving immediately and call us, "
                f"(5) Avoid steep downhill driving. "
                f"With {failure_prob*100:.0f}% failure risk in {rul_days} days, these precautions are critical."
            )
        elif "battery" in component_lower:
            return (
                f"Battery precautions until service: "
                f"(1) Avoid leaving lights or accessories on when engine is off, "
                f"(2) Keep jumper cables or a portable jump starter in your vehicle, "
                f"(3) Avoid short trips that don't allow the battery to recharge, "
                f"(4) If the car struggles to start, don't ignore it — call us immediately, "
                f"(5) Avoid extreme temperatures if possible (park in shade/garage)."
            )
        elif "coolant" in component_lower or "engine" in component_lower:
            return (
                f"Engine cooling precautions: "
                f"(1) Monitor the temperature gauge — if it moves toward red, pull over immediately, "
                f"(2) Keep coolant level topped up (check weekly), "
                f"(3) Avoid long highway drives or heavy traffic in hot weather, "
                f"(4) If steam comes from the hood, stop immediately and call roadside assistance, "
                f"(5) Avoid towing or carrying heavy loads."
            )
        else:
            return (
                f"General precautions for your {component}: "
                f"(1) Drive conservatively and avoid aggressive acceleration/braking, "
                f"(2) Listen for any unusual sounds or vibrations, "
                f"(3) Monitor your dashboard warning lights closely, "
                f"(4) If anything feels different about how the car drives, contact us immediately, "
                f"(5) Avoid long highway trips until the issue is resolved."
            )
