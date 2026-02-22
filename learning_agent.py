"""
Learning and Memory Agent - v4.1
Self-learning system with multi-cycle pattern recognition
"""

import json
from typing import Dict, List
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat

from models import MemoryStore, CustomerMemory, VehicleMemory
from utils import JSONParser, DataConverter


class LearningAgent:
    """
    Autonomous learning agent that updates memory profiles
    Enhanced for multi-cycle workflow learning
    """
    
    SYSTEM_MESSAGE = """You are a LEARNING AND MEMORY AGENT.

CRITICAL: Respond with ONLY valid JSON. Start with { end with }. No explanations.

YOUR ROLE: Update memory based on workflow outcomes, including multi-cycle patterns.

NEW FOR v4.1:
- Multi-cycle learning: Learn from multi-cycle workflow outcomes
- Degradation pattern recognition: Identify recurring degradation patterns
- Optimal timing prediction: Learn best contact times based on cycle data
- Escalation effectiveness: Track what triggers customer acceptance after escalation

OUTPUT FORMAT (JSON ONLY):
{
  "memory_updates": {
    "customer_profile": {
      "preferences": {"preferred_channel": "WHATSAPP"},
      "behavior_signals": {"PREFERS_WHATSAPP": true, "HIGH_TRUST_CUSTOMER": true},
      "multi_cycle_patterns": {
        "accepts_after_escalation": true,
        "typical_response_time_hours": 12.5,
        "responds_to_urgency": true
      }
    },
    "vehicle_profile": {
      "reliability_signals": {"HIGH_RELIABILITY": true},
      "recurring_issues": [],
      "degradation_patterns": {
        "brake_pad_degradation_rate": "ACCELERATED",
        "typical_cycle_interval_days": 2
      }
    }
  },
  "learning_notes": "Brief explanation",
  "confidence_adjustment": 0.0,
  "recommended_actions": [],
  "cycle_insights": {
    "optimal_contact_timing": "After 2 days if declined",
    "escalation_trigger_threshold": "Component degradation >10%"
  }
}

MULTI-CYCLE LEARNING RULES:
- If accepted in cycle 2 after decline in cycle 1 → "accepts_after_follow_up": true
- If accepted after escalation → "responds_to_urgency": true
- If declined in cycle 1, accepted in cycle 2 → learn optimal wait time
- Track degradation rate between cycles for predictive modeling

STANDARD RULES:
- If accepted via WhatsApp → PREFERS_WHATSAPP = true
- If declined 3+ times → OFTEN_DECLINES = true
- If response time > 24h → RESPONDS_SLOWLY = true
- If always accepts P0/P1 → HIGH_TRUST_CUSTOMER = true

Start with { end with }. Nothing else."""
    
    def __init__(self, model_client, memory_store: MemoryStore):
        self.model_client = model_client
        self.memory_store = memory_store
        self.agent = AssistantAgent(
            name="Learning_and_Memory_Agent",
            model_client=model_client,
            system_message=self.SYSTEM_MESSAGE
        )
        self.json_parser = JSONParser()
        self.data_converter = DataConverter()
    
    async def update_memory(self, tenant_id: str, customer_id: str,
                           vehicle_id: str, workflow_outcome: Dict) -> Dict:
        """Update memory based on workflow outcome"""
        
        # Get current memory context
        customer_memory = self.memory_store.get_customer_memory(customer_id)
        vehicle_memory = self.memory_store.get_vehicle_memory(vehicle_id)
        
        # Default updates (rule-based fallback)
        fallback = self._get_default_updates(workflow_outcome, customer_memory)
        
        try:
            # Build learning context
            prompt = self._build_learning_prompt(
                tenant_id, customer_id, vehicle_id, workflow_outcome
            )
            
            # Run learning agent
            team = RoundRobinGroupChat([self.agent], max_turns=1)
            stream = team.run_stream(task=prompt)
            
            response_text = ""
            async for message in stream:
                if hasattr(message, 'content'):
                    response_text += str(message.content)
            
            # Strict JSON extraction
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Extract ONLY the JSON portion
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
                print(f"   ⚠️  No valid JSON in learning response, using fallback")
                result = fallback
            else:
                json_str = response_text[start_idx:end_idx+1]
                
                try:
                    result = json.loads(json_str)
                    result = self.data_converter.convert_numpy_types(result)
                except json.JSONDecodeError as e:
                    print(f"   ⚠️  JSON parse error: {str(e)[:40]}, using fallback")
                    result = fallback
            
            # Apply memory updates
            self._apply_memory_updates(result, customer_memory, vehicle_memory)
            
            # Add metadata
            result["updated_at"] = datetime.now().isoformat()
            result["tenant_id"] = tenant_id
            
            learning_note = result.get('learning_notes', 'Updates applied')
            if len(learning_note) > 60:
                learning_note = learning_note[:57] + "..."
            print(f"   🧠 Memory Updated: {learning_note}")
            
            return result
            
        except Exception as e:
            print(f"   ⚠️  Learning error: {str(e)[:50]}, using fallback")
            # Still apply fallback updates
            self._apply_memory_updates(fallback, customer_memory, vehicle_memory)
            return fallback
    
    def _build_learning_prompt(self, tenant_id: str, customer_id: str,
                               vehicle_id: str, workflow_outcome: Dict) -> str:
        """Build learning prompt from workflow outcome"""
        
        customer_response = workflow_outcome.get('final_customer_response', 'UNKNOWN')
        channel_used = workflow_outcome.get('communication_channel', 'EMAIL')
        response_time_hours = workflow_outcome.get('response_time_hours', 24.0)
        cycle_count = workflow_outcome.get('cycle_count', 1)
        replanning_count = workflow_outcome.get('replanning_count', 0)
        
        # Build multi-cycle context if applicable
        multi_cycle_context = ""
        if cycle_count > 1:
            multi_cycle_context = f"""
MULTI-CYCLE CONTEXT:
- Total Cycles: {cycle_count}
- Replanning Count: {replanning_count}
- Pattern: Cycle 1 likely DECLINED, Cycle {cycle_count} {customer_response}
- Learning Opportunity: Understand what changed customer's mind
"""
        
        return f"""Analyze workflow outcome and update memory:

OUTCOME:
- Customer Response: {customer_response}
- Channel Used: {channel_used}
- Response Time: {response_time_hours:.1f}h
- Cycle Count: {cycle_count}
{multi_cycle_context}

Update memory with multi-cycle insights. Respond with JSON only."""
    
    def _get_default_updates(self, workflow_outcome: Dict,
                            customer_memory: CustomerMemory) -> Dict:
        """Get default memory updates based on simple rules"""
        
        customer_response = workflow_outcome.get('final_customer_response', 'UNKNOWN')
        channel = workflow_outcome.get('communication_channel', 'EMAIL')
        response_time = workflow_outcome.get('response_time_hours', 24.0)
        cycle_count = workflow_outcome.get('cycle_count', 1)
        
        # Enhanced updates structure for v4.1
        updates = {
            "memory_updates": {
                "customer_profile": {
                    "preferences": {},
                    "behavior_signals": {},
                    "multi_cycle_patterns": {}
                },
                "vehicle_profile": {
                    "reliability_signals": {},
                    "recurring_issues": [],
                    "degradation_patterns": {}
                }
            },
            "learning_notes": "Default updates applied",
            "confidence_adjustment": 0.0,
            "recommended_actions": [],
            "cycle_insights": {}
        }
        
        # Update channel preference
        if customer_response == "ACCEPTED":
            updates["memory_updates"]["customer_profile"]["preferences"]["preferred_channel"] = channel
        
        # Update response speed signal
        if response_time > 24:
            updates["memory_updates"]["customer_profile"]["behavior_signals"]["RESPONDS_SLOWLY"] = True
        elif response_time < 6:
            updates["memory_updates"]["customer_profile"]["behavior_signals"]["RESPONDS_QUICKLY"] = True
        
        # Update decline signal
        if customer_response == "DECLINED":
            hist = customer_memory.interaction_history
            if hist["acceptance_rate"] < 0.6:
                updates["memory_updates"]["customer_profile"]["behavior_signals"]["OFTEN_DECLINES"] = True
        
        # Multi-cycle learning
        if cycle_count > 1:
            if customer_response == "ACCEPTED":
                # Customer accepted in follow-up cycle
                updates["memory_updates"]["customer_profile"]["multi_cycle_patterns"]["accepts_after_follow_up"] = True
                updates["memory_updates"]["customer_profile"]["multi_cycle_patterns"]["typical_response_time_hours"] = response_time
                
                # If it took 2+ cycles, they might respond to urgency
                if cycle_count >= 2:
                    updates["memory_updates"]["customer_profile"]["multi_cycle_patterns"]["responds_to_urgency"] = True
                
                updates["learning_notes"] = f"Customer accepted after {cycle_count} cycles - responds to follow-up"
            
            # Track cycle interval for future optimization
            updates["memory_updates"]["vehicle_profile"]["degradation_patterns"]["typical_cycle_interval_days"] = 2
            updates["cycle_insights"]["optimal_contact_timing"] = "2-3 days after initial decline"
        
        return updates
    
    def _apply_memory_updates(self, updates: Dict, 
                             customer_memory: CustomerMemory,
                             vehicle_memory: VehicleMemory):
        """Apply memory updates to memory store"""
        
        memory_updates = updates.get("memory_updates", {})
        
        # Update customer memory
        if "customer_profile" in memory_updates:
            customer_updates = memory_updates["customer_profile"]
            
            if "preferences" in customer_updates:
                customer_memory.preferences.update(customer_updates["preferences"])
            
            if "behavior_signals" in customer_updates:
                customer_memory.behavior_signals.update(customer_updates["behavior_signals"])
            
            # NEW: Multi-cycle patterns
            if "multi_cycle_patterns" in customer_updates:
                if not hasattr(customer_memory, 'multi_cycle_patterns'):
                    customer_memory.multi_cycle_patterns = {}
                customer_memory.multi_cycle_patterns.update(customer_updates["multi_cycle_patterns"])
        
        # Update vehicle memory
        if "vehicle_profile" in memory_updates:
            vehicle_updates = memory_updates["vehicle_profile"]
            
            if "reliability_signals" in vehicle_updates:
                vehicle_memory.reliability_signals.update(vehicle_updates["reliability_signals"])
            
            if "recurring_issues" in vehicle_updates:
                issues = vehicle_updates["recurring_issues"]
                for issue in issues:
                    if issue not in vehicle_memory.maintenance_patterns["recurring_issues"]:
                        vehicle_memory.maintenance_patterns["recurring_issues"].append(issue)
            
            # NEW: Degradation patterns
            if "degradation_patterns" in vehicle_updates:
                if "degradation_history" not in vehicle_memory.maintenance_patterns:
                    vehicle_memory.maintenance_patterns["degradation_history"] = {}
                vehicle_memory.maintenance_patterns["degradation_history"].update(
                    vehicle_updates["degradation_patterns"]
                )
        
        # Mark as updated
        customer_memory.updated_at = datetime.now()
        vehicle_memory.updated_at = datetime.now()
    
    def get_memory_summary(self, customer_id: str, vehicle_id: str) -> Dict:
        """Get summary of current memory for debugging"""
        
        customer_memory = self.memory_store.get_customer_memory(customer_id)
        vehicle_memory = self.memory_store.get_vehicle_memory(vehicle_id)
        
        # Get multi-cycle patterns if available
        multi_cycle_patterns = {}
        if hasattr(customer_memory, 'multi_cycle_patterns'):
            multi_cycle_patterns = customer_memory.multi_cycle_patterns
        
        return {
            "customer": {
                "id": customer_id,
                "preferred_channel": customer_memory.get_recommended_channel("P2"),
                "trust_level": "HIGH" if customer_memory.behavior_signals.get("HIGH_TRUST_CUSTOMER") else "NORMAL",
                "acceptance_rate": customer_memory.interaction_history["acceptance_rate"],
                "interactions": customer_memory.interaction_history["total_interactions"],
                "multi_cycle_patterns": multi_cycle_patterns
            },
            "vehicle": {
                "id": vehicle_id,
                "reliability": "HIGH" if vehicle_memory.reliability_signals.get("HIGH_RELIABILITY") else "NORMAL",
                "recurring_issues": vehicle_memory.maintenance_patterns["recurring_issues"],
                "total_maintenance": vehicle_memory.maintenance_patterns["total_maintenance_events"],
                "degradation_history": vehicle_memory.maintenance_patterns.get("degradation_history", {})
            }
        }