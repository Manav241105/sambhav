"""
Event System Module - v4.0
Event-driven architecture for autonomous agent orchestration
"""

from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
import asyncio
from enum import Enum

from config import EventTypes


@dataclass
class Event:
    """Event object for event-driven orchestration"""
    event_type: str
    tenant_id: str  # Vehicle ID for multi-tenant isolation
    timestamp: str
    data: Dict[str, Any] = field(default_factory=dict)
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    source: str = "SYSTEM"
    event_id: str = field(default="")
    
    def __post_init__(self):
        if not self.event_id:
            import hashlib
            data_str = f"{self.event_type}_{self.tenant_id}_{self.timestamp}"
            self.event_id = hashlib.sha256(data_str.encode()).hexdigest()[:12]


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class EventBus:
    """
    Event bus for multi-tenant autonomous system
    Ensures strict tenant isolation and event-driven coordination
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: Dict[str, List[Event]] = {}  # tenant_id -> events
        self.active_tenants: set = set()
        
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to specific event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    async def publish(self, event: Event):
        """Publish event to all subscribers"""
        # Record event in tenant-specific history
        if event.tenant_id not in self.event_history:
            self.event_history[event.tenant_id] = []
        
        self.event_history[event.tenant_id].append(event)
        self.active_tenants.add(event.tenant_id)
        
        # Notify subscribers
        if event.event_type in self.subscribers:
            handlers = self.subscribers[event.event_type]
            
            # Execute handlers asynchronously
            tasks = []
            for handler in handlers:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(event))
                else:
                    tasks.append(asyncio.to_thread(handler, event))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_tenant_events(self, tenant_id: str, 
                         event_type: Optional[str] = None) -> List[Event]:
        """Get events for specific tenant (ensures isolation)"""
        if tenant_id not in self.event_history:
            return []
        
        events = self.event_history[tenant_id]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events
    
    def get_latest_event(self, tenant_id: str, event_type: str) -> Optional[Event]:
        """Get most recent event of type for tenant"""
        events = self.get_tenant_events(tenant_id, event_type)
        return events[-1] if events else None
    
    def clear_tenant_events(self, tenant_id: str):
        """Clear events for tenant (cleanup)"""
        if tenant_id in self.event_history:
            del self.event_history[tenant_id]
        
        if tenant_id in self.active_tenants:
            self.active_tenants.remove(tenant_id)
    
    def get_active_tenants(self) -> List[str]:
        """Get list of active tenant IDs"""
        return list(self.active_tenants)


class TenantState:
    """
    State manager for individual tenant (vehicle)
    Ensures complete isolation between tenants
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.workflow_state = "INITIALIZING"
        self.current_plan: Optional[Dict] = None
        self.agent_outputs: Dict[str, Any] = {}
        self.confidence_scores: List[float] = []
        self.replanning_count = 0
        self.customer_interactions = 0
        self.last_customer_response: Optional[str] = None
        self.last_customer_response_time: Optional[datetime] = None
        self.escalation_triggered = False
        self.sla_deadline: Optional[datetime] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Memory signals (for learning)
        self.memory: Dict[str, Any] = {
            "customer_preferences": {},
            "vehicle_history": {},
            "communication_patterns": {},
            "confidence_calibration": {}
        }
    
    def update_state(self, **kwargs):
        """Update tenant state"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
    
    def add_agent_output(self, agent_name: str, output: Any, confidence: float):
        """Record agent output"""
        self.agent_outputs[agent_name] = output
        self.confidence_scores.append(confidence)
        self.updated_at = datetime.now()
    
    def get_average_confidence(self) -> float:
        """Get average confidence across all agents"""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)
    
    def should_trigger_low_confidence_event(self, threshold: float = 0.6) -> bool:
        """Check if low confidence event should be triggered"""
        if len(self.confidence_scores) < 2:
            return False
        
        recent_scores = self.confidence_scores[-3:]
        avg = sum(recent_scores) / len(recent_scores)
        
        return avg < threshold
    
    def update_memory(self, category: str, updates: Dict[str, Any]):
        """Update memory for learning"""
        if category not in self.memory:
            self.memory[category] = {}
        
        self.memory[category].update(updates)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "tenant_id": self.tenant_id,
            "workflow_state": self.workflow_state,
            "current_plan": self.current_plan,
            "agent_outputs": self.agent_outputs,
            "average_confidence": self.get_average_confidence(),
            "replanning_count": self.replanning_count,
            "customer_interactions": self.customer_interactions,
            "last_customer_response": self.last_customer_response,
            "escalation_triggered": self.escalation_triggered,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class TenantRegistry:
    """
    Registry for managing multiple tenants
    Ensures strict isolation and prevents cross-tenant contamination
    """
    
    def __init__(self):
        self.tenants: Dict[str, TenantState] = {}
    
    def register_tenant(self, tenant_id: str) -> TenantState:
        """Register new tenant"""
        if tenant_id not in self.tenants:
            self.tenants[tenant_id] = TenantState(tenant_id)
        return self.tenants[tenant_id]
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantState]:
        """Get tenant state"""
        return self.tenants.get(tenant_id)
    
    def remove_tenant(self, tenant_id: str):
        """Remove tenant (cleanup)"""
        if tenant_id in self.tenants:
            del self.tenants[tenant_id]
    
    def get_all_tenants(self) -> List[TenantState]:
        """Get all active tenants"""
        return list(self.tenants.values())
    
    def get_tenant_count(self) -> int:
        """Get number of active tenants"""
        return len(self.tenants)


class EventLogger:
    """
    Event logger for audit and debugging
    Maintains complete event history per tenant
    """
    
    def __init__(self):
        self.logs: Dict[str, List[Dict]] = {}  # tenant_id -> log entries
    
    def log_event(self, event: Event, handler_name: str = "SYSTEM", 
                  result: str = "PROCESSED"):
        """Log event processing"""
        tenant_id = event.tenant_id
        
        if tenant_id not in self.logs:
            self.logs[tenant_id] = []
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_id": event.event_id,
            "event_type": event.event_type,
            "handler": handler_name,
            "result": result,
            "priority": event.priority,
            "data_summary": self._summarize_data(event.data)
        }
        
        self.logs[tenant_id].append(log_entry)
    
    def _summarize_data(self, data: Dict) -> str:
        """Create brief summary of event data"""
        if not data:
            return "No data"
        
        keys = list(data.keys())[:3]
        return f"Keys: {', '.join(keys)}"
    
    def get_tenant_logs(self, tenant_id: str, limit: int = 50) -> List[Dict]:
        """Get recent logs for tenant"""
        if tenant_id not in self.logs:
            return []
        
        return self.logs[tenant_id][-limit:]
    
    def get_event_count(self, tenant_id: str, event_type: Optional[str] = None) -> int:
        """Count events for tenant"""
        if tenant_id not in self.logs:
            return 0
        
        logs = self.logs[tenant_id]
        
        if event_type:
            logs = [log for log in logs if log['event_type'] == event_type]
        
        return len(logs)