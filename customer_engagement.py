"""
Customer Engagement Agent - v7.0 AUTONOMOUS ORCHESTRATION
Full deterministic strategy-bound response architecture with autonomous scheduling.

Pipeline per turn:
  1. Intent Classification
  2. Execution Mode Check (booking intent → switch to EXECUTION_MODE)
  3. Trust Signal Detection
  4. Conversation Stage Determination
  5. Personalization Context Building (deep behavioral + emotional)
  6. Edge Case Detection (7 cases incl. silent + supervisor)
  7. Strategy Response Router (deterministic — no generic fallbacks)
  8. Scheduling Handoff (when EXECUTION_MODE active)
  9. LLM Polish (optional naturalization only)
  10. Safety Overrides
"""

import json
import httpx
from typing import Dict, List, Optional
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat

from models import MemoryStore
from communication_service import CommunicationService
from utils import JSONParser, DataConverter
from config import SystemConfig

# Intelligence Modules v1
from conversation_stage_manager import ConversationStageManager, ConversationStage
from customer_intent_classifier import CustomerIntentClassifier
from response_strategy_engine import ResponseStrategyEngine
from trust_signal_detector import TrustSignalDetector
from logistics_reasoning_engine import LogisticsReasoningEngine

# Intelligence Modules v2
from conversation_memory_tracker import ConversationMemoryTracker
from trust_recovery_engine import TrustRecoveryEngine
from edge_case_reasoning_engine import EdgeCaseReasoningEngine
from personalization_context_builder import PersonalizationContextBuilder
from strategy_response_router import StrategyResponseRouter

# Autonomous Orchestration Modules v3
from execution_mode_manager import ExecutionModeManager
from scheduling_agent import SchedulingAgent
from personalization_context_engine import PersonalizationContextEngine
from edge_case_decision_engine import EdgeCaseDecisionEngine
from followup_cycle_manager import FollowupCycleManager


class CustomerEngagementAgentV6:
    """
    v7.0 — Autonomous Orchestration with deterministic strategy-bound responses.
    Integrates ExecutionModeManager, SchedulingAgent, EdgeCaseDecisionEngine.
    LLM is used only for optional naturalization polish — never for core response direction.
    """

    SYSTEM_MESSAGE = """You are a SENIOR AUTOMOTIVE SERVICE ADVISOR at a premium dealership.
You are polishing a pre-written response to make it sound more natural and human.

RULES:
1. Keep ALL the facts, data, and specific details exactly as given
2. Make the language flow more naturally — like a trusted advisor, not a script
3. Do NOT add urgency, pressure, or sales language
4. Do NOT remove any specific measurements, percentages, or data points
5. Do NOT change the core message or direction
6. Keep it concise — no longer than the original
7. Return ONLY the polished response text — no JSON, no explanation"""

    def __init__(self, model_client, memory_store: MemoryStore,
                 communication_service: CommunicationService):
        self.model_client = model_client
        self.memory_store = memory_store
        self.communication_service = communication_service
        self.agent = AssistantAgent(
            name="Customer_Engagement_Agent",
            model_client=model_client,
            system_message=self.SYSTEM_MESSAGE
        )
        self.json_parser = JSONParser()
        self.data_converter = DataConverter()

        # Intelligence v1
        self.stage_manager = ConversationStageManager()
        self.intent_classifier = CustomerIntentClassifier()
        self.strategy_engine = ResponseStrategyEngine()
        self.trust_detector = TrustSignalDetector()
        self.logistics_engine = LogisticsReasoningEngine()

        # Intelligence v2
        self.memory_tracker = ConversationMemoryTracker()
        self.trust_recovery = TrustRecoveryEngine()
        self.edge_case_engine = EdgeCaseReasoningEngine()
        self.personalization_builder = PersonalizationContextBuilder()
        self.response_router = StrategyResponseRouter()

        # Autonomous Orchestration v3
        self.execution_mode_manager = ExecutionModeManager()
        self.scheduling_agent = SchedulingAgent()
        self.personalization_engine = PersonalizationContextEngine()
        self.edge_case_decision_engine = EdgeCaseDecisionEngine()
        self.followup_cycle_manager = FollowupCycleManager()

    async def engage_customer(self, tenant_id: str, customer_id: str,
                              customer_data: Dict, diagnosis: Dict,
                              priority: str, vehicle: Dict,
                              cycle_number: int = 1, escalated: bool = False,
                              days_elapsed: int = 0, degradation_info: Dict = None,
                              maintenance_history: list = None,
                              telematics: Dict = None,
                              reanalysis_result=None) -> Dict:
        """Engage customer with full intelligence stack."""
        customer_memory = self.memory_store.get_customer_memory(customer_id)
        if escalated and priority == "P0":
            channel = "VOICE_CALL"
        else:
            channel = customer_memory.get_recommended_channel(priority)

        component = diagnosis.get('affected_component', 'Component')
        rul_days = diagnosis.get('rul_days', 30)
        failure_prob = diagnosis.get('failure_probability', 0.5)
        maintenance_history = maintenance_history or []
        telematics = telematics or {}

        # Build initial message — inject reanalysis delta for follow-up cycles
        if reanalysis_result and cycle_number > 1:
            first_name = customer_data.get('name', 'there').split()[0]
            message = reanalysis_result.get_opening_line(first_name, component)
            message += "\n\n" + reanalysis_result.get_data_update_line(component)
        else:
            message = self._build_default_message(vehicle, component, priority, cycle_number,
                                                   escalated, days_elapsed, degradation_info)
        fallback = {
            "action": f"SEND_{channel}" if channel != "VOICE_CALL" else "PLACE_CALL",
            "urgency": "CRITICAL" if escalated else ("HIGH" if priority in ["P0", "P1"] else "MEDIUM"),
            "message": message, "expected_reply": ["YES", "NO", "RESCHEDULE"],
            "confidence": 0.75, "memory_updates": [], "escalation_tone": escalated
        }

        try:
            odometer = telematics.get('odo_km', 0)
            brake_pad = telematics.get('brake_pad_mm', 0)
            battery = telematics.get('battery_voltage_v', 0)
            coolant = telematics.get('coolant_temp_c', 0)
            past_issues = [h.get('service_type', '') for h in maintenance_history[:3]]
            past_issues_text = ", ".join(past_issues) if past_issues else "None on record"

            prompt = f"""Create an initial outreach message for a customer about their vehicle maintenance.

Customer: {customer_data.get('name', 'Customer')}
Vehicle: {vehicle.get('make', '')} {vehicle.get('model', '')} ({vehicle.get('year', '')})
Issue: {component} - {diagnosis.get('severity', 'UNKNOWN')} severity
Failure Probability: {failure_prob:.1%} within {rul_days} days
Brake Pad: {brake_pad:.2f}mm (warning: <5mm, critical: <3mm)
Battery: {battery:.2f}V | Odometer: {odometer:,} km
Diagnostic Reasoning: {diagnosis.get('diagnostic_reasoning', '')}

Write a warm, professional opening message. Be specific with data. Sound like a trusted advisor.
Return ONLY the message text — no JSON."""

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{SystemConfig.OLLAMA_BASE_URL.replace('/v1', '')}/api/generate",
                    json={"model": SystemConfig.MODEL_NAME, "prompt": prompt,
                          "stream": False, "options": {"temperature": 0.1, "num_predict": 300}}
                )
                resp.raise_for_status()
                llm_message = resp.json().get("response", "").strip()
                if llm_message and len(llm_message) > 20:
                    message = llm_message
        except Exception as e:
            print(f"      ⚠️  Initial message generation error: {str(e)[:60]}")

        # Build subject
        if cycle_number > 1:
            subject = (f"🚨 URGENT - {priority}: {component} CRITICAL" if escalated
                       else f"Follow-up: {priority} - {component} Maintenance")
        else:
            subject = f"{priority} Priority: {component} Maintenance Required"

        # Multi-channel outreach
        print(f"\n{'='*80}\n📣 MULTI-CHANNEL CUSTOMER OUTREACH\n{'='*80}")
        print(f"Contacting {customer_data.get('name')} via ALL channels...")
        for ch in ["EMAIL", "WHATSAPP", "SMS"]:
            await self.communication_service.send(
                channel=ch, to=customer_data.get('phone', '+91-0000000000'),
                message=message, subject=subject if ch == "EMAIL" else None,
                priority=priority,
                metadata={"cycle_number": cycle_number, "escalated": escalated, "priority": priority}
            )
        if priority in ["P0", "P1"] or escalated:
            print(f"\n📞 Initiating VOICE CALL due to {priority} priority...")
            await self.communication_service.send(
                channel="VOICE_CALL", to=customer_data.get('phone', '+91-0000000000'),
                message=message, subject=None, priority=priority,
                metadata={"cycle_number": cycle_number, "escalated": escalated, "priority": priority}
            )
        print(f"\n{'='*80}\n✅ Multi-channel outreach complete!\n{'='*80}\n")

        return await self._run_interactive_loop(
            "TERMINAL", message, customer_data, diagnosis, subject,
            priority, cycle_number, escalated, vehicle, telematics,
            maintenance_history, reanalysis_result=reanalysis_result
        )

    async def _run_interactive_loop(self, channel: str, initial_message: str,
                                    customer_data: Dict, diagnosis: Dict, subject: str,
                                    priority: str, cycle_number: int, escalated: bool,
                                    vehicle: Dict, telematics: Dict = None,
                                    maintenance_history: List = None,
                                    reanalysis_result=None) -> Dict:
        """Run interactive conversation with full intelligence stack."""
        print(f"\n{'='*80}")
        print(f"💬 INTERACTIVE TERMINAL CONVERSATION STARTED")
        print(f"{'='*80}")
        print(f"Customer: {customer_data.get('name', 'Customer')}")
        print(f"Channel: {channel} (Terminal Simulation)")
        print(f"Priority: {priority}")
        print(f"{'='*80}\n")

        conversation_history: List[str] = []
        current_message = initial_message
        turn_number = 0
        telematics = telematics or {}
        maintenance_history = maintenance_history or []

        # Reset intelligence modules for fresh conversation
        self.stage_manager = ConversationStageManager()
        self.memory_tracker = ConversationMemoryTracker()

        while True:
            turn_number += 1
            print(f"\n🤖 AGENT (Turn {turn_number}):")
            print(f"   {current_message}")
            conversation_history.append(f"Agent: {current_message}")

            print(f"\n{'─'*80}")
            print(f"👤 YOUR TURN (as {customer_data.get('name', 'Customer')}):")
            print(f"   💡 Type 'accept'/'book' to schedule | 'decline' to refuse | or chat naturally")
            print(f"{'─'*80}")
            user_reply = input(f"   You: ").strip()
            if not user_reply:
                user_reply = "..."
            conversation_history.append(f"Customer: {user_reply}")

            decision = await self._analyze_reply_v6(
                user_reply, conversation_history, diagnosis, turn_number,
                customer_data, vehicle, telematics, maintenance_history,
                reanalysis_result=reanalysis_result
            )

            status = decision.get('status', 'CONTINUE')

            if status == 'BOOKING_CONFIRMED':
                # Booking was created after explicit consent + slot preference
                confirmation = decision.get('booking_confirmation')
                print(f"\n{'='*80}")
                print(f"✅ BOOKING CONFIRMED (After Explicit Customer Consent)")
                print(f"{'='*80}")
                if confirmation:
                    if hasattr(confirmation, 'to_dict'):
                        conf_dict = confirmation.to_dict()
                    else:
                        conf_dict = confirmation if isinstance(confirmation, dict) else {}
                    print(f"📋 Booking ID: {conf_dict.get('booking_id', 'N/A')}")
                    print(f"📅 Slot: {conf_dict.get('slot_time', 'N/A')}")
                    print(f"👨‍🔧 Technician: {conf_dict.get('technician_name', 'N/A')} ({conf_dict.get('technician_level', 'N/A')})")
                    print(f"🏎️  Bay: {conf_dict.get('bay', 'N/A')}")
                    print(f"⏱️  Duration: {conf_dict.get('service_duration_hours', 0):.1f}h")
                print(f"⏱️  Total conversation turns: {turn_number}")
                print(f"{'='*80}\n")
                return {"action": "BOOKING_CONFIRMED", "channel_used": "MULTI_CHANNEL",
                        "customer_response": "ACCEPTED",
                        "booking_confirmation": conf_dict if confirmation else {},
                        "conversation_turns": turn_number}

            elif status == 'ESCALATED_TO_HUMAN':
                print(f"\n{'='*80}")
                print(f"🔺 ESCALATING TO HUMAN ADVISOR (Explicit Request)")
                print(f"{'='*80}")
                print(f"⏱️  Total conversation turns: {turn_number}")
                print(f"{'='*80}\n")
                return {"action": "ESCALATE_TO_HUMAN", "channel_used": "MULTI_CHANNEL",
                        "customer_response": "ESCALATED", "conversation_turns": turn_number}

            elif status == 'FOLLOWUP_SCHEDULED':
                print(f"\n{'='*80}")
                print(f"📅 FOLLOW-UP SCHEDULED")
                print(f"{'='*80}")
                print(f"⏱️  Total conversation turns: {turn_number}")
                print(f"{'='*80}\n")
                return {"action": "FOLLOWUP_SCHEDULED", "channel_used": "MULTI_CHANNEL",
                        "customer_response": "DELAYED", "conversation_turns": turn_number}

            elif status == 'ACCEPTED':
                # Customer accepted — enter EXECUTION_READY: present slot options
                # DO NOT create booking yet — wait for slot preference
                customer_id_local = customer_data.get('id', 'default')
                self.execution_mode_manager.force_execution_mode(customer_id_local)
                component_local = diagnosis.get('affected_component', 'Service')
                priority_local = diagnosis.get('priority', 'P2')
                vehicle_id_local = vehicle.get('id', 'VEH001')
                availability = self.scheduling_agent.check_availability(
                    component_local, priority_local
                )
                first_name_local = customer_data.get('name', 'there').split()[0]
                slot_options = self.scheduling_agent.format_availability_message(
                    availability, first_name_local, component_local
                )
                current_message = (
                    f"Wonderful, {first_name_local}! Here are the available slots for your "
                    f"{component_local} service:\n\n{slot_options}\n\n"
                    f"Which time works best for you — morning, afternoon, or a specific day? "
                    f"Just confirm and I'll lock it in."
                )
                print(f"   🛡️  [SAFETY] ACCEPTED → EXECUTION_READY (presenting slots, no booking yet)")

            elif status == 'DECLINED':
                print(f"\n{'='*80}")
                print(f"❌ CUSTOMER DECLINED SERVICE")
                print(f"{'='*80}")
                print(f"📝 Logging decline for future follow-up...")
                print(f"⏱️  Total conversation turns: {turn_number}")
                print(f"{'='*80}\n")
                return {"action": "LOG_DECLINE", "channel_used": "MULTI_CHANNEL",
                        "customer_response": "DECLINED", "conversation_turns": turn_number}

            else:
                current_message = decision.get('next_message',
                    "I want to make sure I'm addressing your specific concern. What would be most helpful?")

    async def _analyze_reply_v6(self, user_reply: str, history: List[str],
                                 diagnosis: Dict, turn_number: int,
                                 customer_data: Dict, vehicle: Dict,
                                 telematics: Dict, maintenance_history: List,
                                 reanalysis_result=None) -> Dict:
        """
        Full v6 intelligence pipeline:
        Intent → Trust → Stage → Personalization → Router → LLM Polish → Safety Override
        """
        # Extract diagnosis
        component = diagnosis.get('affected_component', 'component')
        severity = diagnosis.get('severity', 'UNKNOWN')
        failure_prob = diagnosis.get('failure_probability', 0) * 100
        rul_days = diagnosis.get('rul_days', 0)
        reasoning = diagnosis.get('diagnostic_reasoning', 'Component needs attention')
        failure_mode = diagnosis.get('failure_mode', 'Gradual degradation')
        recommended_action = diagnosis.get('recommended_action', f'Replace {component}')

        # Telematics
        brake_mm = telematics.get('brake_pad_mm', 0)
        battery_v = telematics.get('battery_voltage_v', 0)
        odometer = telematics.get('odo_km', 0)

        # ── STEP 1: Intent Classification ─────────────────────────────────────
        intent_result = self.intent_classifier.classify(user_reply, history)
        primary_intent = intent_result["primary_intent"]

        # ── STEP 2: Trust Signal Detection ────────────────────────────────────
        trust_result = self.trust_detector.analyze(user_reply)
        trust_delta = trust_result["trust_delta"]

        # Resistance delta: objections increase resistance, positive signals reduce it
        resistance_delta = 1 if primary_intent in (
            "SKEPTICISM", "COST_CONCERN", "LOGISTICS_BLOCKER", "SECOND_OPINION_SEEKING",
            "SOFT_DECLINE", "HARD_DECLINE", "PAST_SERVICE_FAILURE", "TRUST_DAMAGE_EVENT",
            "SERVICE_DELAY_TRAUMA", "REPAIR_QUALITY_DOUBT", "PRICE_SHOCK_HISTORY",
            "DEALERSHIP_AVOIDANCE_PATTERN"
        ) else (-1 if primary_intent == "READY_TO_BOOK" else 0)

        # ── STEP 3: Update Memory Tracker ─────────────────────────────────────
        self.memory_tracker.update(
            primary_intent, "PENDING", trust_delta, resistance_delta, turn_number
        )
        memory_summary = self.memory_tracker.get_summary()

        # ── STEP 4: Conversation Stage ────────────────────────────────────────
        objection_count = memory_summary["objection_count"]
        stage = self.stage_manager.advance_stage(
            primary_intent, turn_number, objection_count, memory_summary["trust_score"]
        )

        # ── STEP 5: Strategy Selection ────────────────────────────────────────
        strategy = self.strategy_engine.select_strategy(
            primary_intent, stage.value,
            memory_summary["strategies_used"],
            memory_summary["last_strategy"]
        )
        self.memory_tracker.update(
            primary_intent, strategy, 0, 0, turn_number  # Update strategy in memory
        )

        # ── STEP 2b: Execution Mode Check (Strict Safety Protocol v2.0) ───────────
        customer_id = customer_data.get('id', 'default')
        current_mode = "EXECUTION_MODE" if self.execution_mode_manager.is_execution_mode(customer_id) else "TRUST_BUILDING"
        mode_decision = self.execution_mode_manager.detect_and_switch(
            primary_intent, user_reply, current_mode, customer_id, memory_summary
        )
        conversation_mode = mode_decision["mode"]
        suppress_trust_narrative = mode_decision["suppress_trust_narrative"]
        scheduling_action = mode_decision["scheduling_action"]
        explicit_consent = mode_decision["explicit_consent"]
        consent_tier = mode_decision.get("consent_tier", "NONE")
        ambiguity_score = mode_decision["ambiguity_score"]
        logistics_blocked = mode_decision["logistics_blocked"]
        conv_stage = mode_decision["state"]["stage"]
        requested_date = mode_decision.get("requested_date")  # Date customer mentioned

        if mode_decision["switched"]:
            print(f"   🔄 [SAFETY] Mode: {current_mode} → {conversation_mode} | Stage: {conv_stage} | Tier: {consent_tier}")
            print(f"   🔒 [SAFETY] Consent: {explicit_consent} | Ambiguity: {ambiguity_score:.2f} | Logistics: {logistics_blocked}")
        else:
            print(f"   🔒 [SAFETY] Stage: {conv_stage} | Action: {scheduling_action} | Tier: {consent_tier} | Ambiguity: {ambiguity_score:.2f}")

        # ── STEP 6: Personalization Context (Deep Engine) ─────────────────────
        customer_memory = self.memory_store.get_customer_memory(
            customer_id
        ) if hasattr(self, 'memory_store') else None
        behavior_signals = customer_memory.behavior_signals if customer_memory else {}

        # Use upgraded PersonalizationContextEngine for deep context
        personalization = self.personalization_engine.build(
            customer_data, vehicle, telematics, maintenance_history,
            behavior_signals, memory_summary, reanalysis_result
        )
        first_name = personalization["first_name"]
        vehicle_desc = personalization["vehicle_desc"]
        personalization_notes = personalization["personalization_notes"]

        # ── STEP 6b: Edge Case Detection (Extended Engine) ────────────────────
        edge_case = self.edge_case_decision_engine.detect_edge_case(
            user_reply, primary_intent, memory_summary
        )

        # ── STEP 7: SCHEDULING HANDOFF (Strict Safety Protocol) ──────────────────
        #
        # SAFETY RULE: Only execute booking when:
        #   scheduling_action == "EXECUTE_BOOKING"  (slot preference given after consent)
        #   explicit_consent == True
        #   logistics_blocked == False
        #
        # NEVER book on: SUGGEST_BEST_SLOT / CHECK_AVAILABILITY / ANSWER_QUESTION / CLARIFY
        # ───────────────────────────────────────────────────────────────────────────────

        if scheduling_action == "LOGISTICS_BLOCKER_DETECTED":
            # ── SAFE RESPONSE TEMPLATE for logistics blockers ─────────────────────────
            # 1. Answer issue clearly
            # 2. Explain urgency honestly
            # 3. Acknowledge their situation
            # 4. Offer alternative schedule
            # 5. Ask explicit confirmation question
            rul_days = diagnosis.get('rul_days', 0)
            failure_prob = diagnosis.get('failure_probability', 0) * 100
            severity = diagnosis.get('severity', 'MEDIUM')
            component = diagnosis.get('affected_component', 'component')

            # Determine safe driving window
            if rul_days <= 3:
                urgency_msg = f"honestly, with only {rul_days} days of safe operation remaining, this is time-sensitive"
                wait_advice = "I wouldn't recommend waiting more than a few days"
            elif rul_days <= 7:
                urgency_msg = f"our diagnostics show approximately {rul_days} days before this becomes critical"
                wait_advice = "short distances should be manageable, but extended driving increases risk"
            else:
                urgency_msg = f"you have roughly {rul_days} days before this needs urgent attention"
                wait_advice = "short trips should be fine, but avoid long highway drives"

            routed_response = (
                f"Completely understand, {first_name} — let me give you the full picture so you can decide.\n\n"
                f"🔧 **The Issue:** Your {vehicle_desc}'s {component} is showing {severity.lower()} wear "
                f"({failure_prob:.0f}% failure probability). {urgency_msg.capitalize()}.\n\n"
                f"🚦 **Driving Safety:** {wait_advice.capitalize()}.\n\n"
                f"📅 **My Suggestion:** Since you're currently unavailable, I can reserve a slot for when you return — "
                f"no commitment needed right now. Would you like me to hold a tentative appointment for after you're back? "
                f"Just say 'yes book it' when you're ready to confirm."
            )
            routing_path = "LOGISTICS_BLOCKER_SAFE_TEMPLATE"
            requires_polish = False
            print(f"   🛡️  [SAFETY] Logistics blocker → safe template (NO booking created)")

        elif scheduling_action == "ANSWER_QUESTION":
            # Let the deterministic router handle the question
            routed_response, routing_path, requires_polish = self.response_router.route(
                user_reply=user_reply, intent=primary_intent, stage=stage.value,
                trust_score=memory_summary["trust_score"],
                resistance_level=memory_summary["resistance_level"],
                memory_summary=memory_summary, component=component,
                failure_prob=failure_prob, rul_days=rul_days, severity=severity,
                reasoning=reasoning, failure_mode=failure_mode,
                recommended_action=recommended_action, first_name=first_name,
                vehicle_desc=vehicle_desc, brake_mm=brake_mm, battery_v=battery_v,
                odometer=odometer, turn_number=turn_number,
                strategies_used=memory_summary["strategies_used"],
                topics_covered=memory_summary["topics_covered"],
                personalization_notes=personalization_notes,
            )
            print(f"   🛡️  [SAFETY] Question detected → answering (NO booking created)")

        elif scheduling_action == "CHECK_AVAILABILITY":
            # Informational only — show available slots, do NOT book
            vehicle_id = vehicle.get('id', 'VEH001')
            priority_level = diagnosis.get('priority', 'P2')
            availability = self.scheduling_agent.check_availability(
                component, priority_level, requested_date=requested_date
            )
            routed_response = self.scheduling_agent.format_availability_message(
                availability, first_name, component, requested_date=requested_date
            )
            routed_response += (
                f"\n\nWould you like to book one of these slots? Just say 'yes book it' "
                f"or 'go ahead' to confirm."
            )
            routing_path = "AVAILABILITY_CHECK_INFORMATIONAL"
            requires_polish = False
            print(f"   🛡️  [SAFETY] Availability check → informational only (NO booking created)")


        elif scheduling_action == "CHECK_AVAILABILITY_FOR_DATE":
            # Customer asked about a SPECIFIC date — show only those slots, DO NOT book
            vehicle_id = vehicle.get('id', 'VEH001')
            priority_level = diagnosis.get('priority', 'P2')
            availability = self.scheduling_agent.check_availability(
                component, priority_level, requested_date=requested_date
            )
            routed_response = self.scheduling_agent.format_availability_message(
                availability, first_name, component, requested_date=requested_date
            )
            _best = availability.get("best_slot")
            if _best:
                self.execution_mode_manager.set_pending_slot(
                    customer_id, _best.get("slot_display", "")
                )
            routing_path = "AVAILABILITY_CHECK_FOR_DATE"
            requires_polish = False
            print(f"   📅 [SAFETY] Date slots for '{requested_date}' shown (NO booking)")

        elif scheduling_action == "SLOT_OVERRIDE":
            # Customer wants different date/time — show new options, DO NOT book
            vehicle_id = vehicle.get('id', 'VEH001')
            priority_level = diagnosis.get('priority', 'P2')
            availability = self.scheduling_agent.check_availability(
                component, priority_level, requested_date=requested_date
            )
            routed_response = self.scheduling_agent.format_availability_message(
                availability, first_name, component, requested_date=requested_date
            )
            _best = availability.get("best_slot")
            if _best:
                self.execution_mode_manager.set_pending_slot(
                    customer_id, _best.get("slot_display", "")
                )
            routing_path = "SLOT_OVERRIDE_NEW_OPTIONS"
            requires_polish = False
            print(f"   🔄 [SAFETY] Slot override for '{requested_date}' (NO booking)")

        elif scheduling_action == "SLOT_MISMATCH_RECONFIRM":
            # Slot consistency check failed — stop, ask customer to clarify
            pending = mode_decision["state"].get("pending_slot_date", "the slot I showed")
            last_req = mode_decision["state"].get("last_requested_date", "your requested date")
            routed_response = (
                f"Just to make sure I get this right, {first_name} — "
                f"you mentioned {last_req}, but the slot I have ready is {pending}. "
                f"Which would you like me to book? Say the date and time clearly."
            )
            routing_path = "SLOT_MISMATCH_RECONFIRM"
            requires_polish = False
            print(f"   ⚠️  [SAFETY] Slot mismatch → asking reconfirmation (NO booking)")

        elif scheduling_action == "SUGGEST_BEST_SLOT" and explicit_consent:
            # Customer gave slot preference — show matching slots, DO NOT book yet
            vehicle_id = vehicle.get('id', 'VEH001')
            priority_level = diagnosis.get('priority', 'P2')
            availability = self.scheduling_agent.check_availability(
                component, priority_level, requested_date=requested_date
            )
            routed_response = self.scheduling_agent.format_availability_message(
                availability, first_name, component, requested_date=requested_date
            )
            _best = availability.get("best_slot")
            if _best:
                self.execution_mode_manager.set_pending_slot(
                    customer_id, _best.get("slot_display", "")
                )
            routing_path = "INTENT_ACCEPTED_SLOT_OPTIONS"
            requires_polish = False
            print(f"   🛡️  [SAFETY] SUGGEST_BEST_SLOT → slots presented (NO booking yet)")

        elif scheduling_action == "EXECUTE_BOOKING" and explicit_consent and not logistics_blocked:
            # ✔ ONLY place where booking is created — after explicit consent + slot confirmed
            vehicle_id = vehicle.get('id', 'VEH001')
            priority_level = diagnosis.get('priority', 'P2')
            # Use the last requested date so we book on the right date
            booked_date = mode_decision["state"].get("last_requested_date") or requested_date
            preferred_time = user_reply if self.execution_mode_manager._has_slot_preference(
                user_reply.lower()
            ) else booked_date
            result = self.scheduling_agent.create_booking(
                customer_id, vehicle_id, component, priority_level,
                preferred_time=preferred_time
            )
            if result['success'] and result['confirmation']:
                conf = result['confirmation']
                routed_response = conf.to_customer_message(first_name, vehicle_desc)
                routing_path = "EXECUTION_BOOKING_CONFIRMED"
                requires_polish = False
                self.stage_manager.mark_strategy_used(strategy)
                self.memory_tracker.mark_topic_covered(routing_path)
                print(f"   ✅ [SAFETY] EXECUTE_BOOKING → booking created (consent verified)")
                print(f"\n   🧠 [v7] Intent: {primary_intent} | Mode: EXECUTION | Route: {routing_path}")
                return {"status": "BOOKING_CONFIRMED", "next_message": routed_response,
                        "booking_confirmation": conf}
            else:
                # No slot available — show alternatives
                alts = result.get('alternatives', [])
                if alts:
                    alt_text = "\n".join(f"• {a['slot_display']}" for a in alts[:3])
                    routed_response = (
                        f"The immediate slots are filling up, {first_name}, but I have these "
                        f"upcoming options:\n\n{alt_text}\n\nWhich works best for you?"
                    )
                else:
                    routed_response = (
                        f"Let me check our schedule and get back to you with available slots, {first_name}."
                    )
                routing_path = "EXECUTION_BOOKING_ALTERNATIVES"
                requires_polish = False

        elif scheduling_action == "RESCHEDULE_BOOKING" and explicit_consent:
            existing = self.scheduling_agent.get_customer_bookings(customer_id)
            if existing:
                result = self.scheduling_agent.reschedule_booking(existing[-1].booking_id)
                if result['success']:
                    conf = result['confirmation']
                    routed_response = conf.to_customer_message(first_name, vehicle_desc)
                    routing_path = "EXECUTION_RESCHEDULED"
                    requires_polish = False
                else:
                    routed_response = f"I wasn't able to reschedule, {first_name}. Let me find a new slot for you."
                    routing_path = "EXECUTION_RESCHEDULE_FALLBACK"
                    requires_polish = False
            else:
                routed_response = f"I don't see an existing booking for you, {first_name}. What time works best for a new appointment?"
                routing_path = "EXECUTION_NO_BOOKING_FOUND"
                requires_polish = False

        elif scheduling_action == "CLARIFY":
            # Ambiguous reply — ask clarifying question
            routed_response = (
                f"I want to make sure I understand correctly, {first_name}. "
                f"Are you ready to go ahead and book the {component} service, "
                f"or would you like more information first?"
            )
            routing_path = "CLARIFICATION_QUESTION"
            requires_polish = False
            print(f"   🛡️  [SAFETY] Ambiguous reply → asking clarifying question (NO booking created)")

        elif scheduling_action == "ASK_FINAL_CONFIRMATION":
            # MEDIUM confirmation — show slots right away so next reply can book
            vehicle_id = vehicle.get('id', 'VEH001')
            priority_level = diagnosis.get('priority', 'P2')
            availability = self.scheduling_agent.check_availability(
                component, priority_level, requested_date=requested_date
            )
            slot_msg = self.scheduling_agent.format_availability_message(
                availability, first_name, component, requested_date=requested_date
            )
            _best = availability.get("best_slot")
            if _best:
                self.execution_mode_manager.set_pending_slot(
                    customer_id, _best.get("slot_display", "")
                )
            routed_response = (
                slot_msg
                + "\n\nJust say yes, confirm, or the time you prefer and I'll lock it in."
            )
            routing_path = "MEDIUM_CONFIRMATION_FINAL_QUESTION"
            requires_polish = False
            print(f"   ❓ [SAFETY] MEDIUM confirmation → showing slots, ready to book on confirm")

        # ── STEP 7b: Edge Case Handling ───────────────────────────────────────
        elif edge_case:
            # Check for supervisor escalation
            if edge_case == "SUPERVISOR_REQUEST":
                ec_response, routing_path, requires_polish = self.edge_case_decision_engine.handle(
                    edge_case, user_reply, primary_intent, memory_summary,
                    personalization, {"telematics": telematics}, diagnosis, reanalysis_result
                )
                routed_response = ec_response
                self.stage_manager.mark_strategy_used(strategy)
                self.memory_tracker.mark_topic_covered(routing_path)
                print(f"\n   🧠 [v7] Intent: {primary_intent} | EdgeCase: {edge_case} | Route: {routing_path}")
                return {"status": "ESCALATED_TO_HUMAN", "next_message": routed_response}

            ec_response, routing_path, requires_polish = self.edge_case_decision_engine.handle(
                edge_case, user_reply, primary_intent, memory_summary,
                personalization, {"telematics": telematics}, diagnosis, reanalysis_result
            )
            routed_response = ec_response if ec_response else ""

        # ── STEP 7c: DETERMINISTIC RESPONSE ROUTING ───────────────────────────
        else:
            routed_response, routing_path, requires_polish = self.response_router.route(
                user_reply=user_reply,
                intent=primary_intent,
                stage=stage.value,
                trust_score=memory_summary["trust_score"],
                resistance_level=memory_summary["resistance_level"],
                memory_summary=memory_summary,
                component=component,
                failure_prob=failure_prob,
                rul_days=rul_days,
                severity=severity,
                reasoning=reasoning,
                failure_mode=failure_mode,
                recommended_action=recommended_action,
                first_name=first_name,
                vehicle_desc=vehicle_desc,
                brake_mm=brake_mm,
                battery_v=battery_v,
                odometer=odometer,
                turn_number=turn_number,
                strategies_used=memory_summary["strategies_used"],
                topics_covered=memory_summary["topics_covered"],
                personalization_notes=personalization_notes,
            )

        # Mark strategy and topics used
        self.stage_manager.mark_strategy_used(strategy)
        self.stage_manager.mark_topic_covered(routing_path)
        self.memory_tracker.mark_topic_covered(routing_path)

        # ── STEP 8: SAFETY OVERRIDES ──────────────────────────────────────────
        # Determine status from intent + turn
        status = self._determine_status(
            user_reply, primary_intent, intent_result, turn_number, memory_summary
        )

        # If DECLINED, generate graceful exit message
        if status == "DECLINED":
            routed_response = (
                f"I completely respect your decision, {first_name}. "
                f"Please drive cautiously with {vehicle_desc}'s {component} — "
                f"avoid hard braking and keep extra following distance. "
                f"Reach out anytime if you change your mind. Take care!"
            )

        # If ACCEPTED (legacy path) — switch to EXECUTION_MODE and ask for time preference
        if status == "ACCEPTED" and conversation_mode != "EXECUTION_MODE":
            self.execution_mode_manager.force_execution_mode(customer_id)
            routed_response = (
                f"Wonderful, {first_name}! Let me pull up the available slots for {vehicle_desc}'s {component} service. "
                f"What time of day works best for you — morning, afternoon, or evening?"
            )

        # ── STEP 9: OPTIONAL LLM POLISH ───────────────────────────────────────
        # Only polish if: response is template-based AND LLM is available AND not a critical edge case
        final_response = routed_response
        if requires_polish and status == "CONTINUE" and len(routed_response) > 50:
            try:
                polish_prompt = (
                    f"Polish this service advisor response to sound more natural and human. "
                    f"Keep ALL data points, measurements, and facts exactly as written. "
                    f"Do NOT add pressure or urgency. Return ONLY the polished text:\n\n"
                    f"{routed_response}"
                )
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        f"{SystemConfig.OLLAMA_BASE_URL.replace('/v1', '')}/api/generate",
                        json={"model": SystemConfig.MODEL_NAME, "prompt": polish_prompt,
                              "stream": False, "options": {"temperature": 0.2, "num_predict": 400}}
                    )
                    resp.raise_for_status()
                    polished = resp.json().get("response", "").strip()
                    # Only use polished version if it's reasonable length and not empty
                    if polished and 30 < len(polished) < len(routed_response) * 2.5:
                        final_response = polished
            except Exception as e:
                # Polish failed — use deterministic response (this is fine, it's just polish)
                pass

        # Print intelligence summary
        strategy_label = self.strategy_engine.get_strategy_label(strategy)
        print(f"\n   🧠 [v7] Intent: {primary_intent} | Mode: {conversation_mode} | Stage: {stage.value} | Route: {routing_path}")
        print(f"   📊 [v7] Trust: {memory_summary['trust_score']:.2f} ({memory_summary['trust_trend']}) | "
              f"Resistance: {memory_summary['resistance_level']} ({memory_summary['resistance_trend']}) | "
              f"Velocity: {memory_summary['decision_velocity']}")
        print(f"   🎯 [v7] Strategy: {strategy_label} | EdgeCase: {edge_case or 'None'} | Trust Damage: {memory_summary['trust_damage']}")

        return {"status": status, "next_message": final_response}

    def _determine_status(self, user_reply: str, primary_intent: str,
                          intent_result: Dict, turn_number: int,
                          memory_summary: Dict) -> str:
        """Determine conversation status with strict rules."""
        lower = user_reply.lower().strip()
        words = lower.split()

        # Never accept before turn 3
        if turn_number < 3:
            return "CONTINUE"

        # Hard decline — explicit
        explicit_no = lower in ['no', 'nope', 'never', 'no thanks', 'not interested']
        decline_phrases = ['not booking', "don't want", 'not interested', 'cancel',
                           'stop calling', 'leave me alone', 'remove me', 'stop contacting',
                           'definitely not', 'absolutely not', 'no way', 'forget it']
        is_ok_phrase = any(ok in lower for ok in ['no problem', 'no worries', 'no questions'])
        is_explicit_decline = (explicit_no or any(p in lower for p in decline_phrases)) and not is_ok_phrase

        if is_explicit_decline:
            return "DECLINED"

        # ── STRONG CONFIRMATION (immediate execution) ─────────────────────────
        STRONG_ACCEPT = [
            "yes book", "book it", "book appointment", "book service",
            "schedule it", "schedule appointment", "schedule visit",
            "please book", "go ahead", "confirm", "confirm booking",
            "yes do it", "do it", "proceed", "ok book", "ok schedule",
            "fine schedule it", "let's do it", "lets do it", "set it up",
            "yes schedule", "yes go ahead", "i want to book", "i'd like to book",
            "yes please book", "accept", "i accept",
        ]
        # ── MEDIUM CONFIRMATION (ask one final question) ──────────────────────
        MEDIUM_ACCEPT = [
            "sounds good", "okay", "ok", "sure", "works for me",
            "that's fine", "thats fine", "alright", "all right",
            "yeah", "yep", "yup", "agreed", "absolutely", "definitely",
        ]

        has_strong_accept = any(phrase in lower for phrase in STRONG_ACCEPT)
        has_medium_accept = any(phrase in lower for phrase in MEDIUM_ACCEPT)
        has_accept = has_strong_accept or has_medium_accept

        # Block acceptance if there are questions, logistics blockers, or uncertainty
        has_question = '?' in user_reply or any(q in lower for q in ['what', 'how', 'why', 'when', 'where', 'which'])
        is_skeptical = intent_result.get("is_skeptical", False)
        is_logistics = intent_result.get("is_logistics", False) or any(
            p in lower for p in ['out of town', 'travelling', 'traveling', 'busy',
                                  'not available', 'away', 'can it wait', 'maybe later',
                                  'not sure', 'need to think', 'let me think']
        )
        is_declining = intent_result.get("is_declining", False)
        has_trust_damage = memory_summary.get("trust_damage", False)

        # Past service failure complaints are NEVER acceptance
        past_failure_keywords = ['last time', 'previously', 'before', 'late', 'not fixed',
                                  'not solved', 'had to come back', 'why should i trust',
                                  'bad experience', 'poor service']
        is_past_failure = any(kw in lower for kw in past_failure_keywords)

        if has_accept and not has_question and not is_skeptical and not is_logistics \
                and not is_declining and not is_past_failure and not has_trust_damage:
            return "ACCEPTED"

        return "CONTINUE"

    def _build_vehicle_desc(self, vehicle: Dict) -> str:
        if not vehicle:
            return "your vehicle"
        make = vehicle.get('make', '')
        model = vehicle.get('model', '')
        year = vehicle.get('year', '')
        color = vehicle.get('color', '')
        if color and make and model:
            return f"your {color} {year} {make} {model}".strip()
        elif make and model:
            return f"your {year} {make} {model}".strip()
        return "your vehicle"

    def _format_degradation_info(self, degradation_info: Dict) -> str:
        lines = []
        if not degradation_info:
            return "- Minor degradation detected"
        for component, data in degradation_info.items():
            if data.get('worsened', False):
                component_name = component.replace('_', ' ').title()
                lines.append(
                    f"- {component_name}: {data['initial']:.2f} → {data['current']:.2f} "
                    f"(change: {data['change']:+.2f})"
                )
        return '\n'.join(lines) if lines else "- Minor degradation detected"

    def _build_default_message(self, vehicle: Dict, component: str, priority: str,
                                cycle_number: int, escalated: bool, days_elapsed: int,
                                degradation_info: Dict) -> str:
        vehicle_name = f"{vehicle.get('make', '')} {vehicle.get('model', '')}".strip()
        if cycle_number == 1:
            return (f"Hello! Your {vehicle_name} requires maintenance attention. "
                    f"Our diagnostic system has detected that your {component} needs service "
                    f"(Priority: {priority}). Please contact us to schedule an appointment.")
        elif escalated:
            return (f"🚨 URGENT UPDATE: Your {vehicle_name} now requires IMMEDIATE attention. "
                    f"Your {component} is now in CRITICAL condition. "
                    f"Please call us immediately to schedule emergency service.")
        else:
            return (f"Hello again! Following up regarding your {vehicle_name}. "
                    f"Your {component} still requires attention (Priority: {priority}). "
                    f"Please let us know a convenient time.")


# Backward compatibility aliases
CustomerEngagementAgentV5 = CustomerEngagementAgentV6
CustomerEngagementAgentV4 = CustomerEngagementAgentV6


def communication_channel_map(action_str):
    """Map action strings to channel names"""
    if 'EMAIL' in action_str: return 'EMAIL'
    if 'WHATSAPP' in action_str: return 'WHATSAPP'
    if 'SMS' in action_str: return 'SMS'
    if 'CALL' in action_str: return 'VOICE_CALL'
    return 'EMAIL'
