"""
Customer Response Interpreter - v4.0
Interprets raw customer messages from webhooks into structured intent
"""

import json
from typing import Dict, Optional
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat

from utils import JSONParser, DataConverter


class CustomerResponseInterpreter:
    """
    Interprets customer responses from various channels
    Converts raw text to structured intent for workflow decisions
    """
    
    SYSTEM_MESSAGE = """You are a CUSTOMER RESPONSE INTERPRETER for an autonomous maintenance system.

CRITICAL: Respond with ONLY valid JSON. No markdown, no explanations.

YOUR TASK:
Convert raw customer messages into structured intent for autonomous decision-making.

INPUT CONTEXT:
- Raw customer message text
- Communication channel (EMAIL, WHATSAPP, SMS, VOICE_CALL)
- Previous interaction context
- Vehicle issue details

INTERPRETATION RULES:
1. Be CONSERVATIVE - if unclear, mark as UNKNOWN
2. Extract sentiment from tone and word choice
3. Identify urgency signals in customer language
4. Detect hesitation vs firm decisions

RESPONSE CATEGORIES:
- ACCEPTED: "Yes", "OK", "Book it", "Schedule", "Sounds good", "I'll come"
- DECLINED: "No", "Can't", "Not now", "Maybe later", "I'll pass"
- REQUESTED_RESCHEDULE: "Reschedule", "Different time", "Next week", "Can we move it"
- UNKNOWN: Unclear, ambiguous, or off-topic responses

SENTIMENT INDICATORS:
- positive: Cooperative tone, thank you, appreciative language
- neutral: Matter-of-fact, short responses, questions
- negative: Frustrated tone, complaints, dismissive language

URGENCY SIGNALS:
- high: "ASAP", "urgent", "immediately", "right away", "can't wait"
- medium: "soon", "this week", "important"
- low: "whenever", "no rush", "eventually"

OUTPUT FORMAT (JSON ONLY):
{
  "customer_response": "ACCEPTED|DECLINED|REQUESTED_RESCHEDULE|UNKNOWN",
  "sentiment": "positive|neutral|negative",
  "urgency_signal": "low|medium|high",
  "confidence": 0.85,
  "extracted_details": {
    "preferred_date": "date if mentioned",
    "preferred_time": "time if mentioned",
    "concerns": ["any concerns mentioned"],
    "questions": ["any questions asked"]
  },
  "interpretation_notes": "Brief reasoning for classification"
}

EXAMPLES:

Input: "Sure, I can bring it in tomorrow morning"
Output:
{
  "customer_response": "ACCEPTED",
  "sentiment": "positive",
  "urgency_signal": "high",
  "confidence": 0.95,
  "extracted_details": {"preferred_date": "tomorrow", "preferred_time": "morning"},
  "interpretation_notes": "Clear acceptance with specific timing"
}

Input: "I'm traveling this week, can we do next Tuesday?"
Output:
{
  "customer_response": "REQUESTED_RESCHEDULE",
  "sentiment": "neutral",
  "urgency_signal": "medium",
  "confidence": 0.90,
  "extracted_details": {"preferred_date": "next Tuesday"},
  "interpretation_notes": "Reschedule request with preferred date"
}

Input: "Thanks but I'll handle it myself"
Output:
{
  "customer_response": "DECLINED",
  "sentiment": "neutral",
  "urgency_signal": "low",
  "confidence": 0.85,
  "extracted_details": {"concerns": ["Prefers self-service"]},
  "interpretation_notes": "Polite decline, wants to handle independently"
}

Start response with { and end with }. Nothing else."""
    
    def __init__(self, model_client):
        self.model_client = model_client
        self.agent = AssistantAgent(
            name="Customer_Response_Interpreter",
            model_client=model_client,
            system_message=self.SYSTEM_MESSAGE
        )
        self.json_parser = JSONParser()
        self.data_converter = DataConverter()
    
    async def interpret(self, raw_message: str, channel: str,
                       context: Dict = None) -> Dict:
        """Interpret customer response"""
        
        # Build interpretation prompt
        prompt = self._build_interpretation_prompt(raw_message, channel, context)
        
        # Get default fallback
        fallback = self._get_default_interpretation(raw_message)
        
        try:
            # Run interpreter agent
            team = RoundRobinGroupChat([self.agent], max_turns=1)
            stream = team.run_stream(task=prompt)
            
            response_text = ""
            async for message in stream:
                if hasattr(message, 'content'):
                    response_text += str(message.content)
            
            # Parse JSON response
            result = self.json_parser.parse_json_safe(response_text, fallback)
            result = self.data_converter.convert_numpy_types(result)
            
            # Add metadata
            result["interpreted_at"] = datetime.now().isoformat()
            result["channel"] = channel
            result["raw_message"] = raw_message[:200]  # Store truncated
            
            return result
            
        except Exception as e:
            print(f"   ⚠️  Interpretation error: {str(e)[:50]}")
            fallback["error"] = str(e)[:100]
            return fallback
    
    def _build_interpretation_prompt(self, raw_message: str, 
                                    channel: str, context: Dict = None) -> str:
        """Build interpretation prompt"""
        
        context_str = ""
        if context:
            issue = context.get('issue', 'maintenance needed')
            priority = context.get('priority', 'P2')
            previous = context.get('previous_response', 'None')
            
            context_str = f"""
CONTEXT:
- Issue: {issue}
- Priority: {priority}
- Previous Response: {previous}
"""
        
        return f"""Interpret this customer response:

CHANNEL: {channel}
RAW MESSAGE: "{raw_message}"
{context_str}

Provide interpretation. Respond with JSON only."""
    
    def _get_default_interpretation(self, raw_message: str) -> Dict:
        """Get default interpretation based on simple keyword matching"""
        
        message_lower = raw_message.lower()
        
        # Simple keyword matching for fallback
        if any(word in message_lower for word in ['yes', 'ok', 'sure', 'book', 'schedule']):
            response = "ACCEPTED"
            sentiment = "positive"
        elif any(word in message_lower for word in ['no', "can't", 'not now', 'decline']):
            response = "DECLINED"
            sentiment = "neutral"
        elif any(word in message_lower for word in ['reschedule', 'different', 'next week', 'move']):
            response = "REQUESTED_RESCHEDULE"
            sentiment = "neutral"
        else:
            response = "UNKNOWN"
            sentiment = "neutral"
        
        return {
            "customer_response": response,
            "sentiment": sentiment,
            "urgency_signal": "medium",
            "confidence": 0.50,  # Low confidence for fallback
            "extracted_details": {},
            "interpretation_notes": "Fallback interpretation based on keywords",
            "fallback_used": True
        }
    
    def interpret_sync(self, raw_message: str, channel: str,
                      context: Dict = None) -> Dict:
        """Synchronous interpretation (for webhook handlers)"""
        import asyncio
        return asyncio.run(self.interpret(raw_message, channel, context))


class WebhookHandler:
    """
    Handles incoming webhooks from communication channels
    Routes customer responses to interpreter and triggers events
    """
    
    def __init__(self, interpreter: CustomerResponseInterpreter, event_bus):
        self.interpreter = interpreter
        self.event_bus = event_bus
    
    async def handle_email_response(self, email_data: Dict) -> Dict:
        """Handle incoming email response"""
        
        from_email = email_data.get('from')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        
        # Extract tenant_id from subject or body (should contain vehicle ID)
        tenant_id = self._extract_tenant_id(subject, body)
        
        if not tenant_id:
            return {"error": "Could not identify tenant/vehicle ID"}
        
        # Interpret response
        interpretation = await self.interpreter.interpret(
            raw_message=body,
            channel="EMAIL",
            context={"source": from_email}
        )
        
        # Publish event
        from event_system import Event
        from config import EventTypes
        
        event = Event(
            event_type=EventTypes.CUSTOMER_RESPONSE_RECEIVED,
            tenant_id=tenant_id,
            timestamp=datetime.now().isoformat(),
            data={
                "interpretation": interpretation,
                "channel": "EMAIL",
                "from": from_email
            },
            priority="HIGH"
        )
        
        await self.event_bus.publish(event)
        
        return interpretation
    
    async def handle_whatsapp_webhook(self, webhook_data: Dict) -> Dict:
        """Handle WhatsApp webhook (Twilio format)"""
        
        from_number = webhook_data.get('From', '')
        body = webhook_data.get('Body', '')
        
        # Extract tenant_id (would be from conversation context in production)
        tenant_id = webhook_data.get('tenant_id', 'UNKNOWN')
        
        if tenant_id == 'UNKNOWN':
            # In production, lookup by phone number
            return {"error": "Could not identify tenant"}
        
        # Interpret response
        interpretation = await self.interpreter.interpret(
            raw_message=body,
            channel="WHATSAPP",
            context={"from_number": from_number}
        )
        
        # Publish event
        from event_system import Event
        from config import EventTypes
        
        event = Event(
            event_type=EventTypes.CUSTOMER_RESPONSE_RECEIVED,
            tenant_id=tenant_id,
            timestamp=datetime.now().isoformat(),
            data={
                "interpretation": interpretation,
                "channel": "WHATSAPP",
                "from": from_number
            },
            priority="HIGH"
        )
        
        await self.event_bus.publish(event)
        
        return interpretation
    
    async def handle_sms_webhook(self, webhook_data: Dict) -> Dict:
        """Handle SMS webhook (Twilio format)"""
        
        from_number = webhook_data.get('From', '')
        body = webhook_data.get('Body', '')
        
        tenant_id = webhook_data.get('tenant_id', 'UNKNOWN')
        
        if tenant_id == 'UNKNOWN':
            return {"error": "Could not identify tenant"}
        
        # Interpret response
        interpretation = await self.interpreter.interpret(
            raw_message=body,
            channel="SMS",
            context={"from_number": from_number}
        )
        
        # Publish event
        from event_system import Event
        from config import EventTypes
        
        event = Event(
            event_type=EventTypes.CUSTOMER_RESPONSE_RECEIVED,
            tenant_id=tenant_id,
            timestamp=datetime.now().isoformat(),
            data={
                "interpretation": interpretation,
                "channel": "SMS",
                "from": from_number
            },
            priority="HIGH"
        )
        
        await self.event_bus.publish(event)
        
        return interpretation
    
    def _extract_tenant_id(self, subject: str, body: str) -> Optional[str]:
        """Extract tenant/vehicle ID from message"""
        import re
        
        # Look for pattern like VEH001, VEH002, etc.
        text = f"{subject} {body}"
        match = re.search(r'VEH\d{3}', text)
        
        if match:
            return match.group(0)
        
        return None