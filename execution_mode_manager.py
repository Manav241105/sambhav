"""
Execution Mode Manager - v4.0 DYNAMIC BOOKING CONTROL
======================================================

CORE PRINCIPLE:
  Customer Acceptance ≠ Final Slot Lock
  Execution is ONLY allowed after:
    1. Customer accepts booking intent  (INTENT_ACCEPTED)
    2. Customer selects specific slot   (SLOT_SELECTED)
    3. Customer confirms that slot      (SLOT_CONFIRMED)
    4. System executes booking          (EXECUTION)

4-State Booking Model:
  STATE 1 — INTENT_ACCEPTED   : Customer wants booking, slot not finalized
  STATE 2 — SLOT_SELECTION    : Customer choosing/modifying date/time
  STATE 3 — SLOT_CONFIRMED    : Customer confirmed specific slot
  STATE 4 — EXECUTION         : Booking created

Date Change Rule:
  If customer provides new date/time AFTER slot shown → SLOT_OVERRIDE
  Cancel previous slot candidate, show new options, ask confirmation.

Slot Consistency Check:
  Before booking: selected_slot_date == last_customer_requested_date
  If mismatch → STOP, reconfirm slot.

Priority: Latest Customer Instruction > Previous Slot > Previous Acceptance
"""

import re
from typing import Dict, Optional, List


# ── STRONG CONFIRMATION — Execute immediately ─────────────────────────────────
STRONG_CONFIRMATION_PHRASES = [
    "yes book", "yes, book",
    "book it", "book the appointment", "book appointment",
    "schedule it", "schedule the appointment", "schedule appointment", "schedule visit",
    "book service", "book the service",
    "accept", "i accept",
    "yes", "yes!", "yes.",
    "go ahead", "go ahead and book", "go ahead please",
    "confirm", "confirmed", "confirm booking", "confirm the booking",
    "please book", "please book it", "please schedule",
    "do it", "yes do it", "just do it",
    "proceed", "proceed with booking",
    "ok book", "ok schedule", "ok, book", "ok, schedule",
    "fine schedule it", "fine, schedule it",
    "let's do it", "lets do it",
    "set it up", "set up the appointment",
    "yes schedule", "yes, schedule",
    "yes go ahead", "yes, go ahead",
    "i want to book", "i'd like to book",
    "i agree schedule it", "i agree, schedule it",
    "yes please book", "yes, please book",
    "yes confirm", "yes, confirm",
]

# ── MEDIUM CONFIRMATION — Ask ONE final question, then execute ────────────────
MEDIUM_CONFIRMATION_PHRASES = [
    "sounds good", "sounds good to me",
    "okay", "ok",
    "sure", "sure thing",
    "works for me", "that works for me", "that works",
    "that's fine", "thats fine", "that's okay", "thats okay",
    "alright", "all right",
    "fine", "fine by me",
    "i guess", "i suppose",
    "yeah", "yep", "yup",
    "agreed", "i agree",
    "absolutely", "definitely",
]

# ── SLOT MODIFICATION KEYWORDS — Treat as SLOT_OVERRIDE, not execution ────────
SLOT_MODIFICATION_PHRASES = [
    "make it", "change to", "change it to", "move to", "move it to",
    "instead", "instead of", "reschedule to", "shift to", "push to",
    "delay to", "can we do", "how about", "what about",
    "prefer", "i prefer", "i'd prefer", "i would prefer",
    "rather", "i'd rather", "i would rather",
    "different date", "different day", "different time",
    "another date", "another day", "another time",
    "not that day", "not that date", "not that time",
    "earlier", "later date", "later time",
]

# ── LOGISTICS BLOCKER — Block execution, use safe template ───────────────────
LOGISTICS_BLOCKER_PHRASES = [
    "out of town", "out of the country", "travelling", "traveling",
    "i am away", "i'm away", "i'll be away", "i will be away",
    "not available", "not in town", "going away", "on a trip",
    "on vacation", "on holiday", "busy", "tied up",
    "can it wait", "can this wait", "how long can it wait",
    "is it urgent", "how urgent", "how serious",
    "what is the issue", "what's the issue", "what is the problem",
    "what's wrong", "what exactly", "tell me more",
    "maybe later", "not now", "some other time",
    "need to think", "let me think", "i'll think about it",
    "i need to check", "let me check",
]

# ── AMBIGUITY SIGNALS ─────────────────────────────────────────────────────────
AMBIGUITY_SIGNALS = [
    "not sure", "unsure", "don't know", "not certain",
    "depends", "it depends", "maybe", "perhaps", "possibly",
]

# ── QUESTION WORDS ────────────────────────────────────────────────────────────
QUESTION_WORDS = ["what", "why", "how", "when", "where", "which", "who"]

# ── AVAILABILITY QUESTION SIGNALS ─────────────────────────────────────────────
AVAILABILITY_QUESTION_SIGNALS = [
    "is ", "any ", "there", "available", "do you have",
    "are there", "what slots", "what time", "which slots",
    "any slot", "any time", "any appointment", "slot available",
]

# ── RESCHEDULE / CANCEL ───────────────────────────────────────────────────────
RESCHEDULE_PHRASES = ["reschedule", "change my appointment", "move my appointment"]
CANCEL_PHRASES = ["cancel my booking", "cancel the appointment", "don't want to book anymore",
                  "cancel the booking", "not booking", "don't want to book"]

# ── DATE/TIME EXTRACTION PATTERNS ────────────────────────────────────────────
DATE_PATTERNS = [
    r'\b(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*(\d{1,2})\b',
    r'\b(\d{1,2})[/-](\d{1,2})\b',
    r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
    r'\b(tomorrow|today|next week|this week|weekend|weekday)\b',
]
TIME_PATTERNS = [
    r'\b(morning|afternoon|evening|night)\b',
    r'\b(\d{1,2})\s*(am|pm)\b',
    r'\b(\d{1,2}):(\d{2})\b',
]


def _extract_date_mention(text: str) -> Optional[str]:
    """Extract date/time mention from text. Returns normalized string or None."""
    lower = text.lower()
    for pattern in DATE_PATTERNS + TIME_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            return match.group(0).strip()
    return None


class ConversationState:
    """
    Tracks the 4-state booking model per customer.

    Booking States:
      TRUST_BUILDING   → building trust, no booking intent yet
      INFORMATION      → answering questions
      CLARIFICATION    → resolving ambiguity
      CONSENT_REQUEST  → asked medium confirmation question
      INTENT_ACCEPTED  → customer wants booking, slot not finalized
      SLOT_SELECTION   → customer choosing/modifying slot
      SLOT_CONFIRMED   → customer confirmed specific slot
      EXECUTION        → booking created
    """

    STAGES = [
        "TRUST_BUILDING", "INFORMATION", "CLARIFICATION", "CONSENT_REQUEST",
        "INTENT_ACCEPTED", "SLOT_SELECTION", "SLOT_CONFIRMED", "EXECUTION"
    ]

    def __init__(self):
        self.stage: str = "TRUST_BUILDING"
        self.explicit_consent: bool = False
        self.consent_tier: str = "NONE"           # "STRONG" | "MEDIUM" | "NONE"
        self.logistics_blocked: bool = False
        self.logistics_context: str = ""
        self.medium_confirmation_asked: bool = False

        # ── Slot tracking (Dynamic Booking Control) ───────────────────────────
        self.pending_slot_date: Optional[str] = None    # Last date shown to customer
        self.pending_slot_confirmed: bool = False        # Customer confirmed this slot
        self.last_requested_date: Optional[str] = None  # Latest date customer mentioned
        self.slot_override_count: int = 0               # How many times slot was changed

    def advance_to(self, stage: str):
        """Advance to a stage — only forward, never skip."""
        if stage in self.STAGES:
            current_idx = self.STAGES.index(self.stage)
            target_idx = self.STAGES.index(stage)
            if target_idx > current_idx:
                self.stage = stage

    def set_stage(self, stage: str):
        """Force set stage (for slot override — can go back to SLOT_SELECTION)."""
        if stage in self.STAGES:
            self.stage = stage

    def reset_slot(self):
        """Reset slot tracking — called on slot override."""
        self.pending_slot_date = None
        self.pending_slot_confirmed = False
        self.slot_override_count += 1

    def reset_to_trust_building(self):
        """Full reset — only called on explicit decline."""
        self.stage = "TRUST_BUILDING"
        self.explicit_consent = False
        self.consent_tier = "NONE"
        self.medium_confirmation_asked = False
        self.pending_slot_date = None
        self.pending_slot_confirmed = False
        self.last_requested_date = None
        self.slot_override_count = 0

    def slot_is_consistent(self) -> bool:
        """
        Slot consistency check:
        If customer requested a specific date, the pending slot must match it.
        If no specific date was requested, always consistent.
        """
        if self.last_requested_date and self.pending_slot_date:
            # Normalize both for comparison
            req = self.last_requested_date.lower().strip()
            pending = self.pending_slot_date.lower().strip()
            # Check if requested date appears in pending slot
            return req in pending or pending in req
        return True  # No specific date requested — consistent

    def to_dict(self) -> Dict:
        return {
            "stage": self.stage,
            "explicit_consent": self.explicit_consent,
            "consent_tier": self.consent_tier,
            "logistics_blocked": self.logistics_blocked,
            "logistics_context": self.logistics_context,
            "medium_confirmation_asked": self.medium_confirmation_asked,
            "pending_slot_date": self.pending_slot_date,
            "pending_slot_confirmed": self.pending_slot_confirmed,
            "last_requested_date": self.last_requested_date,
            "slot_override_count": self.slot_override_count,
        }


class ExecutionModeManager:
    """
    Dynamic Booking Control v4.0

    4-State Booking Model:
      INTENT_ACCEPTED → SLOT_SELECTION → SLOT_CONFIRMED → EXECUTION

    Key rules:
    - STRONG confirmation → enter INTENT_ACCEPTED, show slots
    - MEDIUM confirmation → ask one final question
    - Slot modification keywords → SLOT_OVERRIDE (reset slot, show new options)
    - Availability question → CHECK_AVAILABILITY_FOR_DATE (show slots, no booking)
    - EXECUTE_BOOKING only when: slot selected + slot confirmed + slot consistent
    - Anti-paralysis: never revert to trust-building after acceptance
    """

    def __init__(self):
        self._states: Dict[str, ConversationState] = {}

    def _get_state(self, customer_id: str) -> ConversationState:
        if customer_id not in self._states:
            self._states[customer_id] = ConversationState()
        return self._states[customer_id]

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────

    def detect_and_switch(self, intent: str, user_reply: str,
                          current_mode: str, customer_id: str,
                          memory_summary: Dict) -> Dict:
        """
        Evaluate customer reply and return mode decision.

        Returns:
          {
            "mode": "EXECUTION_MODE" | "TRUST_BUILDING",
            "switched": bool,
            "scheduling_action": str,
            "suppress_trust_narrative": bool,
            "suppress_education_loops": bool,
            "reason": str,
            "state": dict,
            "explicit_consent": bool,
            "consent_tier": str,
            "ambiguity_score": float,
            "logistics_blocked": bool,
            "requested_date": str | None,   # Date customer mentioned
          }
        """
        lower = user_reply.lower().strip()
        state = self._get_state(customer_id)

        # Extract any date/time mention from this reply
        mentioned_date = _extract_date_mention(user_reply)

        # ── Explicit decline / cancel ─────────────────────────────────────────
        if self._is_explicit_decline(lower):
            state.reset_to_trust_building()
            return self._build_result(
                mode="TRUST_BUILDING", switched=(current_mode == "EXECUTION_MODE"),
                action="NONE", suppress_trust=False, suppress_edu=False,
                reason="Customer declined — resetting to trust building",
                state=state, tier="NONE", ambiguity=0.0, logistics=False,
                requested_date=None
            )

        # ── Reschedule existing booking ───────────────────────────────────────
        if any(p in lower for p in RESCHEDULE_PHRASES) and state.explicit_consent:
            return self._build_result(
                mode="EXECUTION_MODE", switched=(current_mode != "EXECUTION_MODE"),
                action="RESCHEDULE_BOOKING", suppress_trust=True, suppress_edu=True,
                reason="Reschedule request with prior consent",
                state=state, tier=state.consent_tier, ambiguity=0.0, logistics=False,
                requested_date=mentioned_date
            )

        # ── Cancel booking ────────────────────────────────────────────────────
        if any(p in lower for p in CANCEL_PHRASES):
            state.reset_to_trust_building()
            return self._build_result(
                mode="TRUST_BUILDING", switched=(current_mode == "EXECUTION_MODE"),
                action="CANCEL_BOOKING", suppress_trust=False, suppress_edu=False,
                reason="Cancel request",
                state=state, tier="NONE", ambiguity=0.0, logistics=False,
                requested_date=None
            )

        # ── SLOT MODIFICATION KEYWORDS — override pending slot ────────────────
        # "make it 21 feb", "change to friday", "move to morning" etc.
        is_slot_modification = self._is_slot_modification(lower)
        if is_slot_modification and state.explicit_consent:
            if mentioned_date:
                state.last_requested_date = mentioned_date
            state.reset_slot()
            state.set_stage("SLOT_SELECTION")
            return self._build_result(
                mode="EXECUTION_MODE", switched=False,
                action="SLOT_OVERRIDE",
                suppress_trust=True, suppress_edu=True,
                reason=f"Slot modification requested — cancelling previous slot, showing new options for '{mentioned_date}'",
                state=state, tier=state.consent_tier, ambiguity=0.0, logistics=False,
                requested_date=mentioned_date
            )

        # ── In INTENT_ACCEPTED / SLOT_SELECTION / SLOT_CONFIRMED states ───────
        if state.stage in ("INTENT_ACCEPTED", "SLOT_SELECTION", "SLOT_CONFIRMED", "EXECUTION") \
                and state.explicit_consent:

            is_strong = self._is_strong_confirmation(lower)
            is_avail_question = self._is_availability_question(lower, user_reply)
            has_slot = self._has_slot_preference(lower)

            # ── New date/time mentioned AFTER slot was shown → SLOT_OVERRIDE ──
            if mentioned_date and not is_strong and state.pending_slot_date:
                # Customer mentioned a new date — check if it's different from pending
                if not self._dates_match(mentioned_date, state.pending_slot_date):
                    state.last_requested_date = mentioned_date
                    state.reset_slot()
                    state.set_stage("SLOT_SELECTION")
                    return self._build_result(
                        mode="EXECUTION_MODE", switched=False,
                        action="SLOT_OVERRIDE",
                        suppress_trust=True, suppress_edu=True,
                        reason=f"New date '{mentioned_date}' differs from pending slot — slot override",
                        state=state, tier=state.consent_tier, ambiguity=0.0, logistics=False,
                        requested_date=mentioned_date
                    )

            # ── Availability question for specific date ────────────────────────
            if has_slot and is_avail_question:
                if mentioned_date:
                    state.last_requested_date = mentioned_date
                return self._build_result(
                    mode="EXECUTION_MODE", switched=False,
                    action="CHECK_AVAILABILITY_FOR_DATE",
                    suppress_trust=True, suppress_edu=True,
                    reason=f"Availability question for '{mentioned_date}' — show slots, do not book",
                    state=state, tier=state.consent_tier, ambiguity=0.0, logistics=False,
                    requested_date=mentioned_date
                )

            # ── SLOT CONFIRMED — customer confirmed the specific slot ──────────
            if is_strong and state.pending_slot_date:
                # ── SLOT CONSISTENCY CHECK ────────────────────────────────────
                if not state.slot_is_consistent():
                    # Mismatch between what customer asked for and what we showed
                    return self._build_result(
                        mode="EXECUTION_MODE", switched=False,
                        action="SLOT_MISMATCH_RECONFIRM",
                        suppress_trust=True, suppress_edu=True,
                        reason=f"Slot mismatch: requested='{state.last_requested_date}' vs pending='{state.pending_slot_date}'",
                        state=state, tier=state.consent_tier, ambiguity=0.0, logistics=False,
                        requested_date=state.last_requested_date
                    )
                # Consistent — execute booking
                state.pending_slot_confirmed = True
                state.advance_to("SLOT_CONFIRMED")
                state.advance_to("EXECUTION")
                return self._build_result(
                    mode="EXECUTION_MODE", switched=False,
                    action="EXECUTE_BOOKING",
                    suppress_trust=True, suppress_edu=True,
                    reason=f"Slot confirmed and consistent — executing booking for '{state.pending_slot_date}'",
                    state=state, tier=state.consent_tier, ambiguity=0.0, logistics=False,
                    requested_date=state.pending_slot_date
                )

            # ── Slot preference given ─────────────────────────────────────────
            if has_slot and not is_avail_question:
                if mentioned_date:
                    state.last_requested_date = mentioned_date

                # If we already showed slots (pending_slot_date is set), the
                # customer is PICKING from those options — not requesting new ones.
                # Treat this as slot confirmation → EXECUTE_BOOKING.
                if state.pending_slot_date:
                    state.pending_slot_confirmed = True
                    state.advance_to("SLOT_CONFIRMED")
                    state.advance_to("EXECUTION")
                    return self._build_result(
                        mode="EXECUTION_MODE", switched=False,
                        action="EXECUTE_BOOKING",
                        suppress_trust=True, suppress_edu=True,
                        reason=f"Customer picked slot from shown options — booking for '{state.last_requested_date or state.pending_slot_date}'",
                        state=state, tier=state.consent_tier, ambiguity=0.0, logistics=False,
                        requested_date=state.last_requested_date or state.pending_slot_date
                    )

                # No slot shown yet — present options for this date
                state.advance_to("SLOT_SELECTION")
                return self._build_result(
                    mode="EXECUTION_MODE", switched=False,
                    action="SUGGEST_BEST_SLOT",
                    suppress_trust=True, suppress_edu=True,
                    reason=f"Slot preference '{mentioned_date}' — show options and ask confirmation",
                    state=state, tier=state.consent_tier, ambiguity=0.0, logistics=False,
                    requested_date=mentioned_date
                )


            # ── Still in INTENT_ACCEPTED — present slot options ───────────────
            return self._build_result(
                mode="EXECUTION_MODE", switched=False,
                action="SUGGEST_BEST_SLOT",
                suppress_trust=True, suppress_edu=True,
                reason="In INTENT_ACCEPTED — presenting slot options",
                state=state, tier=state.consent_tier, ambiguity=0.0, logistics=False,
                requested_date=mentioned_date
            )

        # ── MEDIUM confirmation follow-up ─────────────────────────────────────
        if state.medium_confirmation_asked and not self._is_logistics_blocker(lower, intent):
            is_strong = self._is_strong_confirmation(lower)
            is_medium = self._is_medium_confirmation(lower)
            if is_strong or is_medium:
                state.explicit_consent = True
                state.consent_tier = "STRONG"
                state.advance_to("INTENT_ACCEPTED")
                return self._build_result(
                    mode="EXECUTION_MODE", switched=(current_mode != "EXECUTION_MODE"),
                    action="SUGGEST_BEST_SLOT", suppress_trust=True, suppress_edu=True,
                    reason="Customer confirmed after final question — entering INTENT_ACCEPTED",
                    state=state, tier="STRONG", ambiguity=0.0, logistics=False,
                    requested_date=mentioned_date
                )

        # ── Compute signals ───────────────────────────────────────────────────
        is_strong = self._is_strong_confirmation(lower)
        is_medium = self._is_medium_confirmation(lower)
        is_logistics = self._is_logistics_blocker(lower, intent)
        is_question = self._is_question(lower, user_reply) and not is_strong
        ambiguity_score = self._compute_ambiguity(lower, user_reply, is_logistics)

        # ── LOGISTICS BLOCKER ─────────────────────────────────────────────────
        if is_logistics and not is_strong:
            state.logistics_blocked = True
            state.logistics_context = user_reply[:200]
            state.advance_to("CLARIFICATION")
            return self._build_result(
                mode="TRUST_BUILDING", switched=False,
                action="LOGISTICS_BLOCKER_DETECTED",
                suppress_trust=False, suppress_edu=False,
                reason=f"Logistics blocker (intent={intent}) — safe template required",
                state=state, tier="NONE", ambiguity=1.0, logistics=True,
                requested_date=mentioned_date
            )

        # ── STRONG CONFIRMATION ───────────────────────────────────────────────
        if is_strong:
            state.explicit_consent = True
            state.consent_tier = "STRONG"
            state.logistics_blocked = False
            if mentioned_date:
                state.last_requested_date = mentioned_date
            state.advance_to("INTENT_ACCEPTED")
            return self._build_result(
                mode="EXECUTION_MODE", switched=(current_mode != "EXECUTION_MODE"),
                action="SUGGEST_BEST_SLOT",
                suppress_trust=True, suppress_edu=True,
                reason="STRONG confirmation — entering INTENT_ACCEPTED, show slot options",
                state=state, tier="STRONG", ambiguity=0.0, logistics=False,
                requested_date=mentioned_date
            )

        # ── MEDIUM CONFIRMATION ───────────────────────────────────────────────
        if is_medium and not is_question and ambiguity_score < 0.4:
            state.consent_tier = "MEDIUM"
            state.medium_confirmation_asked = True
            state.advance_to("CONSENT_REQUEST")
            return self._build_result(
                mode="TRUST_BUILDING", switched=False,
                action="ASK_FINAL_CONFIRMATION",
                suppress_trust=True, suppress_edu=True,
                reason="MEDIUM confirmation — asking one final confirmation question",
                state=state, tier="MEDIUM", ambiguity=ambiguity_score, logistics=False,
                requested_date=mentioned_date
            )

        # ── QUESTION ──────────────────────────────────────────────────────────
        if is_question:
            state.advance_to("INFORMATION")
            return self._build_result(
                mode="TRUST_BUILDING", switched=False,
                action="ANSWER_QUESTION",
                suppress_trust=False, suppress_edu=False,
                reason="Customer asked a question — answer first",
                state=state, tier="NONE", ambiguity=ambiguity_score, logistics=False,
                requested_date=mentioned_date
            )

        # ── AMBIGUOUS ─────────────────────────────────────────────────────────
        if ambiguity_score >= 0.3:
            state.advance_to("CLARIFICATION")
            return self._build_result(
                mode="TRUST_BUILDING", switched=False,
                action="CLARIFY",
                suppress_trust=False, suppress_edu=False,
                reason=f"Ambiguous reply (score={ambiguity_score:.2f})",
                state=state, tier="NONE", ambiguity=ambiguity_score, logistics=False,
                requested_date=mentioned_date
            )

        # ── CHECK AVAILABILITY (informational) ────────────────────────────────
        if intent == "ASK_SLOT_AVAILABILITY":
            state.advance_to("INFORMATION")
            return self._build_result(
                mode="TRUST_BUILDING", switched=False,
                action="CHECK_AVAILABILITY",
                suppress_trust=False, suppress_edu=False,
                reason="Availability check — informational only",
                state=state, tier="NONE", ambiguity=ambiguity_score, logistics=False,
                requested_date=mentioned_date
            )

        # ── DEFAULT ───────────────────────────────────────────────────────────
        return self._build_result(
            mode="TRUST_BUILDING", switched=False,
            action="NONE",
            suppress_trust=False, suppress_edu=False,
            reason="No booking signal — continue trust building",
            state=state, tier="NONE", ambiguity=ambiguity_score, logistics=False,
            requested_date=mentioned_date
        )

    # ─────────────────────────────────────────────────────────────────────────
    # SIGNAL DETECTORS
    # ─────────────────────────────────────────────────────────────────────────

    def _is_strong_confirmation(self, lower: str) -> bool:
        return any(phrase in lower for phrase in STRONG_CONFIRMATION_PHRASES)

    def _is_medium_confirmation(self, lower: str) -> bool:
        return any(phrase in lower for phrase in MEDIUM_CONFIRMATION_PHRASES)

    def _is_slot_modification(self, lower: str) -> bool:
        """Detect slot modification keywords — treat as SLOT_OVERRIDE."""
        return any(phrase in lower for phrase in SLOT_MODIFICATION_PHRASES)

    def _is_logistics_blocker(self, lower: str, intent: str) -> bool:
        if intent == "LOGISTICS_BLOCKER":
            return True
        return any(phrase in lower for phrase in LOGISTICS_BLOCKER_PHRASES)

    def _is_question(self, lower: str, original: str) -> bool:
        if "?" in original:
            return True
        return any(lower.startswith(q) or f" {q} " in f" {lower} " for q in QUESTION_WORDS)

    def _is_availability_question(self, lower: str, original: str) -> bool:
        """Detect availability questions — show slots but don't book."""
        has_question_signal = (
            "?" in original or
            any(sig in lower for sig in AVAILABILITY_QUESTION_SIGNALS)
        )
        return has_question_signal and not self._is_strong_confirmation(lower)

    def _has_slot_preference(self, lower: str) -> bool:
        """Detect if customer gave a slot preference (day/time)."""
        days = ["monday", "tuesday", "wednesday", "thursday", "friday",
                "saturday", "sunday", "tomorrow", "today", "next week",
                "this week", "weekend", "weekday"]
        times = ["morning", "afternoon", "evening", "9", "10", "11",
                 "12", "1", "2", "3", "4", "5", "am", "pm"]
        months = ["jan", "feb", "mar", "apr", "may", "jun",
                  "jul", "aug", "sep", "oct", "nov", "dec"]
        has_day = any(d in lower for d in days)
        has_time = any(t in lower for t in times)
        has_month = any(m in lower for m in months)
        has_number_date = bool(re.search(r'\b\d{1,2}\b', lower))
        return has_day or has_time or has_month or has_number_date

    def _dates_match(self, date1: str, date2: str) -> bool:
        """Check if two date strings refer to the same date."""
        d1 = date1.lower().strip()
        d2 = date2.lower().strip()
        return d1 in d2 or d2 in d1

    def _compute_ambiguity(self, lower: str, original: str, is_logistics: bool) -> float:
        if is_logistics:
            return 1.0
        score = 0.0
        if "?" in original:
            score += 0.35
        if any(q in lower for q in QUESTION_WORDS):
            score += 0.15
        uncertainty_count = sum(1 for s in AMBIGUITY_SIGNALS if s in lower)
        score += min(uncertainty_count * 0.15, 0.4)
        return min(score, 1.0)

    def _is_explicit_decline(self, lower: str) -> bool:
        decline_phrases = [
            "don't want to book", "not booking", "not interested anymore",
            "forget it", "never mind", "don't book", "no booking",
            "i don't want", "i do not want", "stop", "leave me alone",
            "remove me", "stop contacting", "no way", "absolutely not",
            "definitely not",
        ]
        return any(p in lower for p in decline_phrases)

    # ─────────────────────────────────────────────────────────────────────────
    # UTILITY
    # ─────────────────────────────────────────────────────────────────────────

    def _build_result(self, mode: str, switched: bool, action: str,
                      suppress_trust: bool, suppress_edu: bool, reason: str,
                      state: ConversationState, tier: str,
                      ambiguity: float, logistics: bool,
                      requested_date: Optional[str]) -> Dict:
        return {
            "mode": mode,
            "switched": switched,
            "scheduling_action": action,
            "suppress_trust_narrative": suppress_trust,
            "suppress_education_loops": suppress_edu,
            "reason": reason,
            "state": state.to_dict(),
            "explicit_consent": state.explicit_consent,
            "consent_tier": tier,
            "ambiguity_score": ambiguity,
            "logistics_blocked": logistics,
            "requested_date": requested_date,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC HELPERS (called by customer_engagement.py)
    # ─────────────────────────────────────────────────────────────────────────

    def is_execution_mode(self, customer_id: str) -> bool:
        state = self._get_state(customer_id)
        return state.stage in ("INTENT_ACCEPTED", "SLOT_SELECTION", "SLOT_CONFIRMED", "EXECUTION")

    def get_conversation_stage(self, customer_id: str) -> str:
        return self._get_state(customer_id).stage

    def has_explicit_consent(self, customer_id: str) -> bool:
        return self._get_state(customer_id).explicit_consent

    def set_pending_slot(self, customer_id: str, slot_date: str):
        """Called by customer_engagement.py after showing slot options to customer."""
        state = self._get_state(customer_id)
        state.pending_slot_date = slot_date
        state.advance_to("SLOT_SELECTION")

    def force_execution_mode(self, customer_id: str):
        """Force INTENT_ACCEPTED (called after ACCEPTED status from _determine_status)."""
        state = self._get_state(customer_id)
        state.explicit_consent = True
        state.consent_tier = "STRONG"
        state.advance_to("INTENT_ACCEPTED")

    def reset(self, customer_id: str):
        self._states.pop(customer_id, None)
