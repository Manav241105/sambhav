"""
Contact Timing Agent - v4.2
Agentic AI agent for optimal contact timing prediction
Uses ML insights + LLM reasoning
"""

import json
from typing import Dict
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat

from models import MemoryStore
from utils import JSONParser


class ContactTimingAgent:
    """
    Agentic AI agent that determines optimal contact timing
    Combines ML predictions with LLM reasoning
    """
    
    SYSTEM_MESSAGE = """You are a CONTACT TIMING OPTIMIZATION AGENT.

Your role: Determine the OPTIMAL TIME to contact a customer about vehicle maintenance.

CRITICAL: Respond with ONLY valid JSON. Start with { end with }. No markdown, no explanations.

OUTPUT (JSON ONLY):
{
  "optimal_contact_time": "2026-01-25T19:30:00",
  "should_wait": false,
  "wait_hours": 2.5,
  "recommended_channel": "WHATSAPP",
  "confidence": 0.85,
  "reasoning": "Brief explanation of timing decision",
  "avoid_work_hours": true,
  "is_weekend_contact": false
}

RULES:
1. AVOID work hours (9 AM - 5 PM) on weekdays unless CRITICAL (P0)
2. Respect customer's historical preferences
3. Evening (6-8 PM) is generally best for non-urgent matters
4. Weekend contact only if customer prefers it
5. Critical issues (P0) - contact immediately regardless of time
6. High priority (P1) - contact within 2 hours, avoid work hours if possible

PRIORITY LEVELS:
- P0 (CRITICAL): Immediate contact, ignore timing preferences
- P1 (HIGH): Contact soon, but try to avoid work hours
- P2 (MEDIUM): Optimize for customer convenience
- P3 (LOW): Fully optimize for best acceptance time

Consider:
- Current time vs optimal time
- Customer's response history
- Priority level
- ML prediction insights

Start with { end with }. Nothing else."""
    
    def __init__(self, model_client, memory_store: MemoryStore, ml_optimizer):
        self.agent = AssistantAgent(
            name="Contact_Timing_Agent",
            model_client=model_client,
            system_message=self.SYSTEM_MESSAGE
        )
        self.memory_store = memory_store
        self.ml_optimizer = ml_optimizer
        self.json_parser = JSONParser()
    
    async def determine_optimal_timing(self, customer_id: str, 
                                      priority: str,
                                      diagnosis: Dict) -> Dict:
        """
        Determine optimal contact timing using ML + LLM reasoning
        
        Args:
            customer_id: Customer identifier
            priority: Priority level (P0-P3)
            diagnosis: Diagnosis information
            
        Returns:
            Dict with optimal timing recommendation
        """
        
        # Get customer memory
        customer_memory = self.memory_store.get_customer_memory(customer_id)
        
        # Get ML prediction
        ml_prediction = self.ml_optimizer.predict_optimal_time(
            customer_memory.to_dict(), priority
        )
        
        # Build prompt for LLM
        prompt = self._build_prompt(customer_memory, ml_prediction, priority, diagnosis)
        
        # Execute agent
        try:
            team = RoundRobinGroupChat([self.agent], max_turns=1)
            stream = team.run_stream(task=prompt)
            
            response_text = ""
            async for message in stream:
                if hasattr(message, 'content'):
                    response_text += str(message.content)
            
            # Parse JSON
            result = self.json_parser.parse_json_safe(response_text, {})
            
            if result:
                # Add ML insights to result
                result['ml_prediction'] = ml_prediction
                return result
            
        except Exception as e:
            print(f"      ⚠️  Contact timing agent error: {str(e)[:50]}")
        
        # Fallback to ML prediction
        return self._format_ml_prediction(ml_prediction)
    
    def _build_prompt(self, customer_memory, ml_prediction: Dict,
                     priority: str, diagnosis: Dict) -> str:
        """Build prompt for LLM"""
        
        current_time = datetime.now()
        
        # Access interaction history
        hist = customer_memory.interaction_history
        
        prompt = f"""Determine optimal contact timing:

CURRENT TIME: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
DAY OF WEEK: {current_time.strftime('%A')}
HOUR: {current_time.hour}

PRIORITY: {priority}
SEVERITY: {diagnosis.get('severity', 'MEDIUM')}
COMPONENT: {diagnosis.get('affected_component', 'Unknown')}
FAILURE PROBABILITY: {diagnosis.get('failure_probability', 0.5):.1%}

CUSTOMER HISTORY:
- Total Interactions: {hist.get('total_interactions', 0)}
- Acceptance Rate: {hist.get('acceptance_rate', 1.0):.1%}
- Avg Response Time: {hist.get('avg_response_time_hours', 24.0):.1f} hours
- Preferred Channel: {customer_memory.get_recommended_channel(priority)}

ML PREDICTION:
- Optimal Time: {ml_prediction['optimal_contact_time']}
- Optimal Hour: {ml_prediction['optimal_hour']}
- Should Wait: {ml_prediction['should_wait']}
- Wait Hours: {ml_prediction['wait_hours']:.1f}
- Is Work Hours Now: {ml_prediction['is_work_hours']}
- Acceptance Probability: {ml_prediction['acceptance_probability']:.1%}
- ML Reasoning: {ml_prediction['reasoning']}

Provide your expert timing recommendation. JSON only."""
        
        return prompt
    
    def _format_ml_prediction(self, ml_prediction: Dict) -> Dict:
        """Format ML prediction as fallback"""
        
        return {
            "optimal_contact_time": ml_prediction['optimal_contact_time'],
            "should_wait": ml_prediction['should_wait'],
            "wait_hours": ml_prediction['wait_hours'],
            "recommended_channel": "EMAIL",
            "confidence": ml_prediction['confidence'],
            "reasoning": ml_prediction['reasoning'],
            "avoid_work_hours": ml_prediction['is_work_hours'],
            "is_weekend_contact": ml_prediction['is_weekend'],
            "ml_prediction": ml_prediction,
            "source": "ml_fallback"
        }
