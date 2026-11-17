"""
Master Orchestrator Router - Autonomous Service Orchestration Platform v1.0
Central domain router that sits above the existing MasterOrchestrator.

Routes intents to the correct domain agent:
  BOOKING            → SchedulingAgent
  FOLLOW_UP_ANALYSIS → VehicleReanalysisEngine
  ESCALATION         → Human Advisor (explicit request / legal / VIP only)
  PARTS / PRICE      → Stub agents (future)

Maintains per-conversation state and handles conflict resolution.
"""

from typing import Dict, Optional
from datetime import datetime


# ── Domain Intent Mapping ─────────────────────────────────────────────────────
BOOKING_INTENTS = {
    "READY_TO_BOOK", "ASK_SLOT_AVAILABILITY", "GIVES_TIME_PREFERENCE",
    "RESCHEDULE_REQUEST", "CANCELLATION_REQUEST"
}

FOLLOWUP_ANALYSIS_INTENTS = {
    "FOLLOW_UP_DELAY", "CALL_LATER", "REMIND_LATER"
}

ESCALATION_INTENTS = {
    "SUPERVISOR_REQUEST", "LEGAL_DISPUTE", "WARRANTY_DISPUTE",
    "EXTREME_COMPLAINT", "VIP_MANUAL_HANDLING"
}

PARTS_INTENTS = {"PARTS_INQUIRY"}
PRICE_INTENTS = {"PRICE_INQUIRY", "QUOTE_REQUEST"}


class OrchestratorState:
    """Per-conversation state maintained by the Master Orchestrator Router."""

    def __init__(self, customer_id: str, vehicle_id: str):
        self.customer_id = customer_id
        self.vehicle_id = vehicle_id
        self.conversation_mode: str = "TRUST_BUILDING"       # TRUST_BUILDING | EXECUTION_MODE
        self.customer_journey_stage: str = "INITIAL_CONTACT"
        self.booking_state: str = "NONE"                     # NONE | SLOT_HOLD | CONFIRMED | WAITLISTED
        self.followup_cycle_number: int = 0
        self.trust_trend: str = "stable"
        self.resistance_trend: str = "stable"
        self.last_domain_routed: Optional[str] = None
        self.booking_confirmation: Optional[Dict] = None
        self.followup_tasks: list = []
        self.escalated_to_human: bool = False
        self.created_at: str = datetime.now().isoformat()
        self.updated_at: str = datetime.now().isoformat()

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "customer_id": self.customer_id,
            "vehicle_id": self.vehicle_id,
            "conversation_mode": self.conversation_mode,
            "customer_journey_stage": self.customer_journey_stage,
            "booking_state": self.booking_state,
            "followup_cycle_number": self.followup_cycle_number,
            "trust_trend": self.trust_trend,
            "resistance_trend": self.resistance_trend,
            "last_domain_routed": self.last_domain_routed,
            "escalated_to_human": self.escalated_to_human,
        }


class MasterOrchestratorRouter:
    """
    Central domain router for the Autonomous Service Orchestration Platform.

    Responsibilities:
    1. Route intents to the correct domain agent
    2. Maintain per-conversation orchestrator state
    3. Handle conflict resolution (e.g., slot available but parts unavailable)
    4. Enforce human escalation rules (ONLY on explicit request / legal / VIP)
    """

    def __init__(self):
        self._states: Dict[str, OrchestratorState] = {}

    # ── State Management ──────────────────────────────────────────────────────

    def get_or_create_state(self, customer_id: str, vehicle_id: str) -> OrchestratorState:
        """Get existing state or create new one for this customer."""
        key = f"{customer_id}:{vehicle_id}"
        if key not in self._states:
            self._states[key] = OrchestratorState(customer_id, vehicle_id)
        return self._states[key]

    def get_state(self, customer_id: str, vehicle_id: str) -> Optional[OrchestratorState]:
        key = f"{customer_id}:{vehicle_id}"
        return self._states.get(key)

    # ── Domain Routing ────────────────────────────────────────────────────────

    def route_intent(self, intent: str, context: Dict,
                     state: OrchestratorState) -> Dict:
        """
        Route an intent to the correct domain agent.

        Returns:
            {
              "domain": str,          # SCHEDULING | FOLLOWUP | ESCALATION | CONVERSATION | PARTS | PRICE
              "action": str,          # What the domain agent should do
              "requires_human": bool,
              "reason": str
            }
        """
        # ── RULE 1: Human Escalation (ONLY explicit / legal / VIP) ───────────
        if intent in ESCALATION_INTENTS:
            state.update(escalated_to_human=True)
            return {
                "domain": "ESCALATION",
                "action": "TRANSFER_TO_HUMAN_ADVISOR",
                "requires_human": True,
                "reason": f"Explicit escalation trigger: {intent}"
            }

        # ── RULE 2: Booking / Scheduling ──────────────────────────────────────
        if intent in BOOKING_INTENTS:
            state.update(
                conversation_mode="EXECUTION_MODE",
                last_domain_routed="SCHEDULING",
                customer_journey_stage="BOOKING_IN_PROGRESS"
            )
            action_map = {
                "READY_TO_BOOK": "SUGGEST_BEST_SLOT",
                "ASK_SLOT_AVAILABILITY": "CHECK_AVAILABILITY",
                "GIVES_TIME_PREFERENCE": "FIND_MATCHING_SLOT",
                "RESCHEDULE_REQUEST": "RESCHEDULE_BOOKING",
                "CANCELLATION_REQUEST": "CANCEL_BOOKING",
            }
            return {
                "domain": "SCHEDULING",
                "action": action_map.get(intent, "SUGGEST_BEST_SLOT"),
                "requires_human": False,
                "reason": f"Booking intent detected: {intent}"
            }

        # ── RULE 3: Follow-Up / Delay ─────────────────────────────────────────
        if intent in FOLLOWUP_ANALYSIS_INTENTS:
            state.update(
                followup_cycle_number=state.followup_cycle_number + 1,
                last_domain_routed="FOLLOWUP"
            )
            return {
                "domain": "FOLLOWUP",
                "action": "SCHEDULE_FOLLOWUP_WITH_REANALYSIS",
                "requires_human": False,
                "reason": f"Customer requested delay: {intent}"
            }

        # ── RULE 4: Parts / Price (stub) ──────────────────────────────────────
        if intent in PARTS_INTENTS:
            return {
                "domain": "PARTS",
                "action": "CHECK_PARTS_AVAILABILITY",
                "requires_human": False,
                "reason": "Parts inquiry"
            }
        if intent in PRICE_INTENTS:
            return {
                "domain": "PRICE",
                "action": "GENERATE_QUOTE",
                "requires_human": False,
                "reason": "Price inquiry"
            }

        # ── RULE 5: Default — Conversation Agent handles ──────────────────────
        return {
            "domain": "CONVERSATION",
            "action": "CONTINUE_ENGAGEMENT",
            "requires_human": False,
            "reason": f"Conversation intent: {intent}"
        }

    # ── Conflict Resolution ───────────────────────────────────────────────────

    def resolve_conflict(self, slot_available: bool, parts_available: bool,
                         booking_confirmation: Optional[Dict],
                         state: OrchestratorState) -> Dict:
        """
        Resolve scheduling conflicts.
        Example: slot available BUT parts unavailable → hold slot + notify customer.
        """
        if slot_available and not parts_available:
            # Hold the slot, notify customer about parts delay
            if booking_confirmation:
                state.update(booking_state="SLOT_HOLD")
            return {
                "resolution": "HOLD_SLOT_PARTS_PENDING",
                "message_directive": (
                    "Hold the slot and inform the customer that parts are being sourced. "
                    "Provide an ETA for parts arrival and confirm the slot is reserved."
                ),
                "booking_state": "SLOT_HOLD"
            }

        if not slot_available and parts_available:
            return {
                "resolution": "SUGGEST_ALTERNATIVES",
                "message_directive": "No slot available — suggest next 3 available slots.",
                "booking_state": "NONE"
            }

        if not slot_available and not parts_available:
            return {
                "resolution": "WAITLIST",
                "message_directive": (
                    "Add customer to waitlist. Notify when both slot and parts are available."
                ),
                "booking_state": "WAITLISTED"
            }

        # Both available — confirm booking
        if booking_confirmation:
            state.update(booking_state="CONFIRMED")
        return {
            "resolution": "CONFIRM_BOOKING",
            "message_directive": "Confirm booking with full details.",
            "booking_state": "CONFIRMED"
        }

    # ── State Sync ────────────────────────────────────────────────────────────

    def sync_trust_state(self, state: OrchestratorState,
                         trust_trend: str, resistance_trend: str):
        """Sync trust/resistance trends from conversation agent into orchestrator state."""
        state.update(trust_trend=trust_trend, resistance_trend=resistance_trend)

    def mark_booking_confirmed(self, state: OrchestratorState,
                               confirmation: Dict):
        """Mark booking as confirmed and store confirmation details."""
        state.update(
            booking_state="CONFIRMED",
            booking_confirmation=confirmation,
            customer_journey_stage="BOOKING_CONFIRMED",
            conversation_mode="EXECUTION_MODE"
        )
        state.booking_confirmation = confirmation

    def mark_followup_scheduled(self, state: OrchestratorState,
                                followup_task: Dict):
        """Record a scheduled follow-up task."""
        state.followup_tasks.append(followup_task)
        state.update(
            customer_journey_stage="FOLLOWUP_SCHEDULED"
        )

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def print_state(self, state: OrchestratorState):
        """Print current orchestrator state for debugging."""
        print(f"\n   🗺️  [ROUTER] State for {state.customer_id}:")
        for k, v in state.to_dict().items():
            print(f"      {k}: {v}")
