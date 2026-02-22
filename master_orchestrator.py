"""
Master Orchestrator - v5.0
Event-driven autonomous orchestrator for multi-tenant system.
Now includes domain routing, per-tenant conversation state, and conflict resolution.
"""

import json
from typing import Dict, Optional
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat

from event_system import Event, TenantState
from config import EventTypes
from utils import JSONParser
from master_orchestrator_router import MasterOrchestratorRouter, BOOKING_INTENTS, FOLLOWUP_ANALYSIS_INTENTS, ESCALATION_INTENTS


class MasterOrchestrator:
    """
    v5.0 — Event-driven Master Orchestrator with domain routing.
    Routes intents to Scheduling, Follow-up, Escalation, or Conversation agents.
    Maintains per-tenant conversation state and handles conflict resolution.
    """
    
    SYSTEM_MESSAGE = """You are the MASTER ORCHESTRATOR in a multi-tenant autonomous agent system.

CRITICAL: Respond with ONLY valid JSON. No markdown, no explanations.

SYSTEM MODEL:
- Each vehicle is an independent tenant
- Each tenant runs a continuous, event-driven execution loop
- Agents never communicate directly with each other
- All coordination, replanning, and escalation decisions are made by you

CORE RESPONSIBILITIES:
1. Plan workflows dynamically per tenant (vehicle)
2. React to events instead of static sequences
3. Monitor agent confidence, execution quality, and customer responses
4. Trigger replanning, escalation, or abort decisions
5. Maintain lifecycle state per tenant
6. Enable self-learning by updating memory signals

EVENT-DRIVEN BEHAVIOR:
You must react to these events:
- DATA_ANALYSIS_COMPLETED: Data analysis agent finished
- LOW_CONFIDENCE_DETECTED: Agent confidence below threshold
- DIAGNOSIS_UPDATED: New diagnosis available
- CUSTOMER_RESPONSE_RECEIVED: Customer replied
- CUSTOMER_NON_RESPONSIVE: Customer didn't respond in time
- HIGH_FAILURE_PROBABILITY: Critical component failure predicted
- SLA_VIOLATION_RISK: Service deadline at risk
- AGENT_EXECUTION_FAILURE: Agent failed to execute

REPLANNING RULES:
- Replan if confidence < 0.6
- Replan if customer declines or reschedules
- Escalate if P0/P1 risk AND customer unresponsive
- Abort only on compliance or safety violation

MULTI-TENANT GUARANTEE:
- Decisions MUST be isolated per vehicle
- Never mix states, memory, or outcomes across tenants

OUTPUT FORMAT FOR PLANNING (JSON ONLY):
{
  "action": "PLAN|REPLAN|ESCALATE|ABORT|WAIT",
  "strategy": "standard|expedited|deep_analysis|customer_recovery",
  "risk_level": "low|medium|high|critical",
  "steps": [
    {"agent": "Data_Analysis_Agent", "purpose": "Analyze telematics data"},
    {"agent": "Diagnosis_Agent", "purpose": "Predict failures"},
    {"agent": "Customer_Engagement_Agent", "purpose": "Contact customer"}
  ],
  "reasoning": "Why this plan/action",
  "monitoring_expectations": {
    "confidence_threshold": 0.7,
    "max_replans": 3,
    "sla_deadline_hours": 24
  },
  "next_events_to_watch": ["CUSTOMER_RESPONSE_RECEIVED", "DIAGNOSIS_UPDATED"]
}

PLANNING STRATEGIES:
- standard: Normal flow for routine maintenance
- expedited: Fast-track for P0/P1 priorities
- deep_analysis: Additional analysis for unclear cases
- customer_recovery: Special handling for declined/unresponsive customers

Start response with { and end with }. Nothing else."""
    
    def __init__(self, model_client, event_bus):
        self.model_client = model_client
        self.event_bus = event_bus
        self.agent = AssistantAgent(
            name="Master_Orchestrator",
            model_client=model_client,
            system_message=self.SYSTEM_MESSAGE
        )
        self.json_parser = JSONParser()

        # Domain router (v5.0)
        self.domain_router = MasterOrchestratorRouter()

        # Subscribe to events
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        """Subscribe to relevant events"""
        event_types = [
            EventTypes.DATA_ANALYSIS_COMPLETED,
            EventTypes.DIAGNOSIS_UPDATED,
            EventTypes.CUSTOMER_RESPONSE_RECEIVED,
            EventTypes.LOW_CONFIDENCE_DETECTED,
            EventTypes.HIGH_FAILURE_PROBABILITY,
            EventTypes.CUSTOMER_NON_RESPONSIVE,
            EventTypes.SLA_VIOLATION_RISK,
            EventTypes.AGENT_EXECUTION_FAILURE,
            # New v5.0 events
            "BOOKING_INTENT_DETECTED",
            "FOLLOWUP_REQUESTED",
            "ESCALATION_REQUESTED",
        ]

        for event_type in event_types:
            self.event_bus.subscribe(event_type, self.handle_event)
    
    async def handle_event(self, event: Event):
        """
        Main event handler - reacts to events for specific tenant
        This is the core of event-driven orchestration
        """
        
        print(f"\n🧠 MASTER ORCHESTRATOR: Handling {event.event_type}")
        print(f"   Tenant: {event.tenant_id}")
        print(f"   Priority: {event.priority}")
        
        # Route to specific handler based on event type
        if event.event_type == EventTypes.DATA_ANALYSIS_COMPLETED:
            await self._handle_data_analysis_completed(event)
        
        elif event.event_type == EventTypes.DIAGNOSIS_UPDATED:
            await self._handle_diagnosis_updated(event)
        
        elif event.event_type == EventTypes.CUSTOMER_RESPONSE_RECEIVED:
            await self._handle_customer_response(event)
        
        elif event.event_type == EventTypes.LOW_CONFIDENCE_DETECTED:
            await self._handle_low_confidence(event)
        
        elif event.event_type == EventTypes.HIGH_FAILURE_PROBABILITY:
            await self._handle_high_failure_probability(event)
        
        elif event.event_type == EventTypes.CUSTOMER_NON_RESPONSIVE:
            await self._handle_customer_non_responsive(event)
        
        elif event.event_type == EventTypes.SLA_VIOLATION_RISK:
            await self._handle_sla_violation(event)
        
        elif event.event_type == EventTypes.AGENT_EXECUTION_FAILURE:
            await self._handle_agent_failure(event)

        # ── v5.0 Domain Routing Events ────────────────────────────────────────
        elif event.event_type == "BOOKING_INTENT_DETECTED":
            await self._handle_booking_intent(event)

        elif event.event_type == "FOLLOWUP_REQUESTED":
            await self._handle_followup_requested(event)

        elif event.event_type == "ESCALATION_REQUESTED":
            await self._handle_escalation_requested(event)

    # ── v5.0 Domain Routing Methods ───────────────────────────────────────────

    def route_to_domain_agent(self, intent: str, context: Dict,
                              customer_id: str, vehicle_id: str) -> Dict:
        """Route an intent to the correct domain agent."""
        state = self.domain_router.get_or_create_state(customer_id, vehicle_id)
        routing = self.domain_router.route_intent(intent, context, state)
        print(f"\n   🗺️  [ORCHESTRATOR] Routing '{intent}' → {routing['domain']} / {routing['action']}")
        return routing

    def get_tenant_orchestrator_state(self, customer_id: str, vehicle_id: str) -> Dict:
        """Get current orchestrator state for a customer/vehicle pair."""
        state = self.domain_router.get_or_create_state(customer_id, vehicle_id)
        return state.to_dict()

    def update_tenant_booking_state(self, customer_id: str, vehicle_id: str,
                                    booking_state: str, confirmation: Dict = None):
        """Update booking state after scheduling agent confirms/holds/cancels."""
        state = self.domain_router.get_or_create_state(customer_id, vehicle_id)
        state.update(booking_state=booking_state)
        if confirmation:
            state.booking_confirmation = confirmation
        print(f"   🗺️  [ORCHESTRATOR] Booking state: {booking_state}")

    def resolve_scheduling_conflict(self, customer_id: str, vehicle_id: str,
                                    slot_available: bool, parts_available: bool,
                                    booking_confirmation: Dict = None) -> Dict:
        """Resolve scheduling conflicts (slot vs parts availability)."""
        state = self.domain_router.get_or_create_state(customer_id, vehicle_id)
        resolution = self.domain_router.resolve_conflict(
            slot_available, parts_available, booking_confirmation, state
        )
        print(f"   🗺️  [ORCHESTRATOR] Conflict resolved: {resolution['resolution']}")
        return resolution

    async def _handle_booking_intent(self, event: Event):
        """Handle booking intent detected event."""
        customer_id = event.data.get("customer_id", "")
        vehicle_id = event.tenant_id
        intent = event.data.get("intent", "READY_TO_BOOK")
        self.route_to_domain_agent(intent, event.data, customer_id, vehicle_id)

    async def _handle_followup_requested(self, event: Event):
        """Handle follow-up requested event."""
        customer_id = event.data.get("customer_id", "")
        vehicle_id = event.tenant_id
        state = self.domain_router.get_or_create_state(customer_id, vehicle_id)
        state.update(
            followup_cycle_number=state.followup_cycle_number + 1,
            customer_journey_stage="FOLLOWUP_SCHEDULED"
        )
        print(f"\n   📅 [ORCHESTRATOR] Follow-up cycle {state.followup_cycle_number} scheduled")

    async def _handle_escalation_requested(self, event: Event):
        """Handle escalation requested event — only for explicit requests."""
        customer_id = event.data.get("customer_id", "")
        vehicle_id = event.tenant_id
        state = self.domain_router.get_or_create_state(customer_id, vehicle_id)
        state.update(escalated_to_human=True)
        print(f"\n   🔺 [ORCHESTRATOR] Escalation to human advisor confirmed")

    async def create_initial_plan(self, tenant_state: TenantState,
                                 telematics: Dict, vehicle: Dict) -> Dict:
        """Create initial plan for new tenant workflow"""
        
        prompt = f"""Create initial workflow plan for new tenant:

TENANT: {tenant_state.tenant_id}
VEHICLE: {vehicle['make']} {vehicle['model']}

TELEMATICS:
- Brake Pads: {telematics.get('brake_pad_mm')}mm
- Battery: {telematics.get('battery_voltage_v')}V
- Coolant: {telematics.get('coolant_temp_c')}°C

CURRENT STATE: {tenant_state.workflow_state}

Create execution plan. Respond with JSON only."""
        
        plan = await self._execute_orchestrator_task(prompt)
        
        # Update tenant state
        tenant_state.update_state(
            current_plan=plan,
            workflow_state="EXECUTING"
        )
        
        return plan
    
    async def _handle_data_analysis_completed(self, event: Event):
        """React to data analysis completion"""
        
        analysis_result = event.data.get('analysis_result', {})
        confidence = analysis_result.get('confidence', 0.0)
        
        # Check if confidence is acceptable
        if confidence < 0.6:
            # Trigger low confidence event
            low_conf_event = Event(
                event_type=EventTypes.LOW_CONFIDENCE_DETECTED,
                tenant_id=event.tenant_id,
                timestamp=datetime.now().isoformat(),
                data={"source": "Data_Analysis_Agent", "confidence": confidence},
                priority="MEDIUM"
            )
            await self.event_bus.publish(low_conf_event)
        else:
            # Proceed to diagnosis
            print(f"   ✓ Data analysis acceptable (confidence: {confidence:.2f})")
            print(f"   → Next: Trigger diagnosis")
    
    async def _handle_diagnosis_updated(self, event: Event):
        """React to diagnosis update"""
        
        diagnosis = event.data.get('diagnosis', {})
        failure_prob = diagnosis.get('failure_probability', 0.0)
        
        # Check if high failure probability
        if failure_prob > 0.7:
            # Trigger high failure probability event
            high_fail_event = Event(
                event_type=EventTypes.HIGH_FAILURE_PROBABILITY,
                tenant_id=event.tenant_id,
                timestamp=datetime.now().isoformat(),
                data={"diagnosis": diagnosis, "failure_probability": failure_prob},
                priority="CRITICAL"
            )
            await self.event_bus.publish(high_fail_event)
        else:
            print(f"   ✓ Diagnosis completed (failure prob: {failure_prob:.1%})")
            print(f"   → Next: Customer engagement")
    
    async def _handle_customer_response(self, event: Event):
        """React to customer response - KEY DYNAMIC BEHAVIOR"""
        
        interpretation = event.data.get('interpretation', {})
        customer_response = interpretation.get('customer_response', 'UNKNOWN')
        
        print(f"   📧 Customer Response: {customer_response}")
        
        if customer_response == "ACCEPTED":
            print(f"   ✓ Customer accepted - proceed to work order")
            # Workflow can complete
        
        elif customer_response == "DECLINED":
            print(f"   ⚠️  Customer declined - triggering replanning")
            # Create replan
            await self._trigger_replanning(event.tenant_id, "Customer declined service")
        
        elif customer_response == "REQUESTED_RESCHEDULE":
            print(f"   🔄 Customer requested reschedule - adaptive planning")
            # Create flexible scheduling plan
            await self._trigger_replanning(event.tenant_id, "Customer requested reschedule")
        
        else:
            print(f"   ❓ Customer response unclear - may need follow-up")
    
    async def _handle_low_confidence(self, event: Event):
        """React to low confidence detection"""
        
        source = event.data.get('source', 'Unknown')
        confidence = event.data.get('confidence', 0.0)
        
        print(f"   ⚠️  Low confidence from {source}: {confidence:.2f}")
        print(f"   → Triggering replanning for deeper analysis")
        
        await self._trigger_replanning(
            event.tenant_id,
            f"Low confidence from {source} ({confidence:.2f})"
        )
    
    async def _handle_high_failure_probability(self, event: Event):
        """React to high failure probability - expedited handling"""
        
        failure_prob = event.data.get('failure_probability', 0.0)
        
        print(f"   🚨 HIGH FAILURE PROBABILITY: {failure_prob:.1%}")
        print(f"   → Escalating to expedited workflow")
        
        # Trigger escalation
        escalation_event = Event(
            event_type=EventTypes.ESCALATION_REQUIRED,
            tenant_id=event.tenant_id,
            timestamp=datetime.now().isoformat(),
            data={"reason": "High failure probability", "failure_prob": failure_prob},
            priority="CRITICAL"
        )
        await self.event_bus.publish(escalation_event)
    
    async def _handle_customer_non_responsive(self, event: Event):
        """React to customer non-responsiveness"""
        
        hours_elapsed = event.data.get('hours_elapsed', 0)
        priority = event.data.get('priority', 'P2')
        
        print(f"   ⏰ Customer non-responsive for {hours_elapsed}h (Priority: {priority})")
        
        if priority in ["P0", "P1"]:
            print(f"   → Escalating due to urgency")
            # Escalate
            escalation_event = Event(
                event_type=EventTypes.ESCALATION_REQUIRED,
                tenant_id=event.tenant_id,
                timestamp=datetime.now().isoformat(),
                data={"reason": "Customer non-responsive on urgent matter"},
                priority="HIGH"
            )
            await self.event_bus.publish(escalation_event)
        else:
            print(f"   → Scheduling follow-up communication")
    
    async def _handle_sla_violation(self, event: Event):
        """React to SLA violation risk"""
        
        deadline = event.data.get('deadline', 'Unknown')
        
        print(f"   ⏱️  SLA VIOLATION RISK: Deadline {deadline}")
        print(f"   → Triggering expedited escalation")
        
        # Immediate escalation
        escalation_event = Event(
            event_type=EventTypes.ESCALATION_REQUIRED,
            tenant_id=event.tenant_id,
            timestamp=datetime.now().isoformat(),
            data={"reason": "SLA violation risk", "deadline": deadline},
            priority="CRITICAL"
        )
        await self.event_bus.publish(escalation_event)
    
    async def _handle_agent_failure(self, event: Event):
        """React to agent execution failure"""
        
        agent_name = event.data.get('agent_name', 'Unknown')
        error = event.data.get('error', 'Unknown error')
        
        print(f"   ❌ AGENT FAILURE: {agent_name}")
        print(f"   Error: {error[:60]}")
        print(f"   → Triggering replanning with fallback strategy")
        
        await self._trigger_replanning(
            event.tenant_id,
            f"Agent {agent_name} failed: {error[:50]}"
        )
    
    async def _trigger_replanning(self, tenant_id: str, reason: str):
        """Trigger replanning event"""
        
        replan_event = Event(
            event_type=EventTypes.REPLANNING_TRIGGERED,
            tenant_id=tenant_id,
            timestamp=datetime.now().isoformat(),
            data={"reason": reason},
            priority="HIGH"
        )
        
        await self.event_bus.publish(replan_event)
    
    async def _execute_orchestrator_task(self, prompt: str) -> Dict:
        """Execute orchestrator reasoning task"""
        
        default_plan = {
            "action": "PLAN",
            "strategy": "standard",
            "risk_level": "medium",
            "steps": [
                {"agent": "Data_Analysis_Agent", "purpose": "Analyze data"},
                {"agent": "Diagnosis_Agent", "purpose": "Predict failures"},
                {"agent": "Customer_Engagement_Agent", "purpose": "Contact customer"}
            ],
            "reasoning": "Standard workflow",
            "monitoring_expectations": {
                "confidence_threshold": 0.7,
                "max_replans": 3
            },
            "next_events_to_watch": ["CUSTOMER_RESPONSE_RECEIVED"]
        }
        
        try:
            team = RoundRobinGroupChat([self.agent], max_turns=1)
            stream = team.run_stream(task=prompt)
            
            response_text = ""
            async for message in stream:
                if hasattr(message, 'content'):
                    response_text += str(message.content)
            
            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx+1]
                plan = json.loads(json_str)
                return plan
        
        except Exception as e:
            print(f"   ⚠️  Orchestrator error: {str(e)[:50]}")
        
        return default_plan