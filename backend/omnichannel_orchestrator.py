"""
Omnichannel Orchestrator - v4.3
Unified orchestration across SMS, WhatsApp, and Voice
Manages customer state and channel switching
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from models import MemoryStore
from communication_service import CommunicationService
from sentiment_analyzer import SentimentAnalyzer


@dataclass
class CustomerState:
    """
    Unified customer state across all channels
    Tracks conversation history, sentiment, and context
    """
    
    customer_id: str
    current_channel: str = "SMS"
    preferred_channel: Optional[str] = None
    conversation_history: List[Dict] = field(default_factory=list)
    sentiment_history: List[Dict] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    last_interaction: Optional[datetime] = None
    frustration_count: int = 0
    
    def add_message(self, channel: str, message: str, sentiment: Dict,
                   speaker: str = "customer"):
        """Add message to conversation history"""
        
        entry = {
            "channel": channel,
            "message": message,
            "sentiment": sentiment,
            "speaker": speaker,
            "timestamp": datetime.now()
        }
        
        self.conversation_history.append(entry)
        self.sentiment_history.append(sentiment)
        self.last_interaction = datetime.now()
        
        # Track frustration
        if sentiment.get('emotion') == 'FRUSTRATED':
            self.frustration_count += 1
        else:
            # Reset if not frustrated
            self.frustration_count = max(0, self.frustration_count - 1)
    
    def should_switch_to_voice(self) -> bool:
        """
        Determine if should escalate to voice call
        
        Criteria:
        - 2+ frustrated messages in last 3 interactions
        - Critical urgency detected
        - Critical objection detected
        """
        
        if not self.sentiment_history:
            return False
        
        # Check last 3 messages
        recent = self.sentiment_history[-3:]
        
        # Count frustrated messages
        frustrated_count = sum(
            1 for s in recent 
            if s.get('emotion') == 'FRUSTRATED'
        )
        
        if frustrated_count >= 2:
            return True
        
        # Check for critical urgency
        if any(s.get('urgency') == 'CRITICAL' for s in recent):
            return True
        
        # Check for critical objections
        if any(
            s.get('objection_severity') == 'CRITICAL' 
            for s in recent
        ):
            return True
        
        return False
    
    def get_context_summary(self, max_messages: int = 5) -> str:
        """Get summary of recent conversation for context"""
        
        recent = self.conversation_history[-max_messages:]
        
        summary_parts = []
        for msg in recent:
            speaker = msg['speaker'].capitalize()
            channel = msg['channel']
            text = msg['message'][:100]  # Truncate long messages
            summary_parts.append(f"[{channel}] {speaker}: {text}")
        
        return " | ".join(summary_parts) if summary_parts else "No prior conversation"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        
        return {
            "customer_id": self.customer_id,
            "current_channel": self.current_channel,
            "preferred_channel": self.preferred_channel,
            "conversation_count": len(self.conversation_history),
            "sentiment_summary": self._get_sentiment_summary(),
            "frustration_count": self.frustration_count,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None
        }
    
    def _get_sentiment_summary(self) -> Dict:
        """Get summary of sentiment trends"""
        
        if not self.sentiment_history:
            return {"dominant_emotion": "NEUTRAL", "avg_urgency": "LOW"}
        
        # Count emotions
        emotion_counts = {}
        urgency_levels = []
        
        for s in self.sentiment_history:
            emotion = s.get('emotion', 'NEUTRAL')
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            urgency_levels.append(s.get('urgency', 'LOW'))
        
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        
        # Most common urgency
        urgency_count = {}
        for u in urgency_levels:
            urgency_count[u] = urgency_count.get(u, 0) + 1
        avg_urgency = max(urgency_count, key=urgency_count.get)
        
        return {
            "dominant_emotion": dominant_emotion,
            "avg_urgency": avg_urgency,
            "emotion_distribution": emotion_counts
        }


class OmnichannelOrchestrator:
    """
    Orchestrates communication across multiple channels
    
    Features:
    - Unified customer state management
    - Intelligent channel selection
    - Automatic escalation to voice
    - Context preservation across channels
    """
    
    def __init__(self, memory_store: MemoryStore, 
                 communication_service: CommunicationService):
        self.memory_store = memory_store
        self.communication_service = communication_service
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Active customer states
        self.customer_states: Dict[str, CustomerState] = {}
    
    def get_customer_state(self, customer_id: str) -> CustomerState:
        """Get or create customer state"""
        
        if customer_id not in self.customer_states:
            # Load from memory if exists
            customer_memory = self.memory_store.get_customer_memory(customer_id)
            
            self.customer_states[customer_id] = CustomerState(
                customer_id=customer_id,
                preferred_channel=customer_memory.preferences.get('preferred_channel')
            )
        
        return self.customer_states[customer_id]
    
    def process_incoming_message(self, customer_id: str, channel: str,
                                 message: str) -> Dict:
        """
        Process incoming message from any channel
        
        Returns:
            {
                "should_escalate": bool,
                "recommended_channel": str,
                "sentiment": dict,
                "response": str
            }
        """
        
        # Get customer state
        customer_state = self.get_customer_state(customer_id)
        
        # Analyze sentiment
        sentiment = self.sentiment_analyzer.analyze(message)
        
        # Add to history
        customer_state.add_message(channel, message, sentiment, speaker="customer")
        
        # Check if should escalate to voice
        should_escalate = customer_state.should_switch_to_voice()
        
        # Determine best channel
        recommended_channel = self.select_best_channel(customer_state, sentiment)
        
        return {
            "should_escalate": should_escalate,
            "recommended_channel": recommended_channel,
            "sentiment": sentiment,
            "customer_state": customer_state,
            "context": customer_state.get_context_summary()
        }
    
    def select_best_channel(self, customer_state: CustomerState,
                           sentiment: Dict = None,
                           diagnosis: Dict = None) -> str:
        """
        Select best communication channel
        
        Priority:
        1. Critical diagnosis → Voice
        2. High frustration → Voice
        3. Customer preference
        4. Default to current channel
        """
        
        # Critical diagnosis → Voice
        if diagnosis and diagnosis.get('severity') == 'CRITICAL':
            return 'VOICE'
        
        # High frustration → Voice
        if customer_state.should_switch_to_voice():
            return 'VOICE'
        
        # Critical urgency → Voice
        if sentiment and sentiment.get('urgency') == 'CRITICAL':
            return 'VOICE'
        
        # Customer preference
        if customer_state.preferred_channel:
            return customer_state.preferred_channel
        
        # Default to current channel
        return customer_state.current_channel
    
    async def send_message(self, customer_id: str, channel: str,
                          message: str, priority: str = "P2") -> Dict:
        """
        Send message through specified channel
        
        Tracks in customer state
        """
        
        customer_state = self.get_customer_state(customer_id)
        
        # Send via communication service
        result = await self.communication_service.send_message(
            channel=channel,
            recipient=customer_id,
            message=message,
            priority=priority
        )
        
        # Add to history
        sentiment = {"emotion": "NEUTRAL", "score": 0.5}  # Agent messages are neutral
        customer_state.add_message(channel, message, sentiment, speaker="agent")
        
        # Update current channel
        customer_state.current_channel = channel
        
        return result
    
    def should_switch_channel(self, customer_state: CustomerState,
                             current_channel: str,
                             diagnosis: Dict = None) -> Optional[str]:
        """
        Determine if should switch to different channel
        
        Returns:
            New channel if should switch, None otherwise
        """
        
        # Get recommended channel
        recommended = self.select_best_channel(customer_state, None, diagnosis)
        
        # Switch if different from current
        if recommended != current_channel:
            return recommended
        
        return None
    
    def get_channel_history(self, customer_id: str, channel: str) -> List[Dict]:
        """Get conversation history for specific channel"""
        
        customer_state = self.get_customer_state(customer_id)
        
        return [
            msg for msg in customer_state.conversation_history
            if msg['channel'] == channel
        ]
    
    def get_cross_channel_context(self, customer_id: str) -> str:
        """
        Get context from all channels for voice call
        
        This is key for maintaining context when switching from SMS to Voice
        """
        
        customer_state = self.get_customer_state(customer_id)
        
        # Get recent messages from all channels
        recent_messages = customer_state.conversation_history[-10:]
        
        if not recent_messages:
            return "No prior conversation"
        
        # Group by channel
        channel_summaries = {}
        for msg in recent_messages:
            channel = msg['channel']
            if channel not in channel_summaries:
                channel_summaries[channel] = []
            
            speaker = "Customer" if msg['speaker'] == 'customer' else "Agent"
            channel_summaries[channel].append(f"{speaker}: {msg['message'][:80]}")
        
        # Build context string
        context_parts = []
        for channel, messages in channel_summaries.items():
            context_parts.append(f"{channel}: {' | '.join(messages[-3:])}")
        
        return " || ".join(context_parts)
    
    def mark_channel_preference(self, customer_id: str, channel: str):
        """Learn customer's preferred channel"""
        
        customer_state = self.get_customer_state(customer_id)
        customer_state.preferred_channel = channel
        
        # Update in memory store
        customer_memory = self.memory_store.get_customer_memory(customer_id)
        customer_memory.preferences['preferred_channel'] = channel
    
    def get_escalation_reason(self, customer_state: CustomerState) -> str:
        """Get human-readable reason for escalation"""
        
        reasons = []
        
        if customer_state.frustration_count >= 2:
            reasons.append(f"Customer frustrated ({customer_state.frustration_count} times)")
        
        recent_sentiment = customer_state.sentiment_history[-1] if customer_state.sentiment_history else {}
        
        if recent_sentiment.get('urgency') == 'CRITICAL':
            reasons.append("Critical urgency detected")
        
        if recent_sentiment.get('objection_severity') == 'CRITICAL':
            objection_type = recent_sentiment.get('objection_type', 'unknown')
            reasons.append(f"Critical objection: {objection_type}")
        
        return "; ".join(reasons) if reasons else "Proactive escalation"
