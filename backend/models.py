"""
Enhanced Data Models - v4.0
Multi-tenant models with memory and learning capabilities
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import hashlib
import json


class WorkflowState(Enum):
    """Enhanced workflow states for event-driven system"""
    INITIALIZING = "initializing"
    WAITING_FOR_DATA = "waiting_for_data"
    ANALYZING = "analyzing"
    DIAGNOSING = "diagnosing"
    AWAITING_CUSTOMER = "awaiting_customer"
    REPLANNING = "replanning"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class CustomerMemory:
    """
    Customer memory profile for learning and adaptation
    Tracks customer behavior patterns across interactions
    """
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.preferences = {
            "preferred_channel": None,  # EMAIL, WHATSAPP, SMS, VOICE_CALL
            "preferred_contact_time": None,  # Morning, Afternoon, Evening
            "communication_style": "NEUTRAL"  # FORMAL, CASUAL, TECHNICAL
        }
        
        self.behavior_signals = {
            "PREFERS_WHATSAPP": False,
            "OFTEN_DECLINES": False,
            "PRICE_SENSITIVE": False,
            "RESPONDS_SLOWLY": False,
            "HIGH_TRUST_CUSTOMER": False,
            "REQUIRES_FOLLOWUP": False,
            "ACCEPTS_URGENCY": True
        }
        
        self.interaction_history = {
            "total_interactions": 0,
            "acceptance_rate": 1.0,
            "avg_response_time_hours": 24.0,
            "declined_count": 0,
            "rescheduled_count": 0,
            "last_interaction": None
        }
        
        self.updated_at = datetime.now()
    
    def update_from_interaction(self, response: str, response_time_hours: float,
                               channel: str):
        """Update memory based on interaction outcome"""
        hist = self.interaction_history
        
        hist["total_interactions"] += 1
        hist["last_interaction"] = datetime.now().isoformat()
        
        # Update response time
        if hist["avg_response_time_hours"]:
            hist["avg_response_time_hours"] = (
                hist["avg_response_time_hours"] * 0.7 + response_time_hours * 0.3
            )
        else:
            hist["avg_response_time_hours"] = response_time_hours
        
        # Update based on response
        if response == "DECLINED":
            hist["declined_count"] += 1
        elif response == "REQUESTED_RESCHEDULE":
            hist["rescheduled_count"] += 1
        
        # Calculate acceptance rate
        total = hist["total_interactions"]
        declined = hist["declined_count"]
        hist["acceptance_rate"] = (total - declined) / total if total > 0 else 1.0
        
        # Update behavior signals
        self.behavior_signals["OFTEN_DECLINES"] = hist["acceptance_rate"] < 0.6
        self.behavior_signals["RESPONDS_SLOWLY"] = hist["avg_response_time_hours"] > 24
        self.behavior_signals["HIGH_TRUST_CUSTOMER"] = hist["acceptance_rate"] > 0.9
        self.behavior_signals["REQUIRES_FOLLOWUP"] = hist["rescheduled_count"] > 2
        
        # Update channel preference
        if channel:
            self.preferences["preferred_channel"] = channel
        
        self.updated_at = datetime.now()
    
    def get_recommended_channel(self, priority: str) -> str:
        """Get recommended communication channel based on memory"""
        # Critical priority always gets voice call option
        if priority == "P0" and self.behavior_signals["ACCEPTS_URGENCY"]:
            return "VOICE_CALL"
        
        # Use learned preference
        if self.preferences["preferred_channel"]:
            return self.preferences["preferred_channel"]
        
        # High priority defaults
        if priority in ["P0", "P1"]:
            if self.behavior_signals["PREFERS_WHATSAPP"]:
                return "WHATSAPP"
            return "SMS"
        
        # Default to email for lower priority
        return "EMAIL"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "customer_id": self.customer_id,
            "preferences": self.preferences,
            "behavior_signals": self.behavior_signals,
            "interaction_history": self.interaction_history,
            "updated_at": self.updated_at.isoformat()
        }


class VehicleMemory:
    """
    Vehicle memory profile for tracking maintenance patterns
    """
    
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        
        self.maintenance_patterns = {
            "recurring_issues": [],  # List of components with repeat failures
            "avg_maintenance_interval_days": 90,
            "total_maintenance_events": 0,
            "proactive_maintenance_rate": 0.0
        }
        
        self.reliability_signals = {
            "HIGH_RELIABILITY": True,
            "FREQUENT_FAILURES": False,
            "DEFERRED_MAINTENANCE": False,
            "WELL_MAINTAINED": True
        }
        
        self.component_history = {
            "brake_pads": {"last_service": None, "failure_count": 0},
            "battery": {"last_service": None, "failure_count": 0},
            "coolant_system": {"last_service": None, "failure_count": 0},
            "tires": {"last_service": None, "failure_count": 0}
        }
        
        self.updated_at = datetime.now()
    
    def record_maintenance(self, component: str, was_proactive: bool):
        """Record maintenance event"""
        self.maintenance_patterns["total_maintenance_events"] += 1
        
        # Update component history
        if component.lower() in self.component_history:
            comp_key = component.lower()
            self.component_history[comp_key]["last_service"] = datetime.now().isoformat()
            
            if not was_proactive:
                self.component_history[comp_key]["failure_count"] += 1
        
        # Update proactive rate
        total = self.maintenance_patterns["total_maintenance_events"]
        if total > 0:
            # This would be calculated from actual data
            self.maintenance_patterns["proactive_maintenance_rate"] = 0.7  # Placeholder
        
        # Update reliability signals
        self.reliability_signals["WELL_MAINTAINED"] = (
            self.maintenance_patterns["proactive_maintenance_rate"] > 0.5
        )
        
        self.updated_at = datetime.now()
    
    def check_recurring_issue(self, component: str) -> bool:
        """Check if component has recurring issues"""
        comp_key = component.lower()
        if comp_key in self.component_history:
            return self.component_history[comp_key]["failure_count"] > 2
        return False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "vehicle_id": self.vehicle_id,
            "maintenance_patterns": self.maintenance_patterns,
            "reliability_signals": self.reliability_signals,
            "component_history": self.component_history,
            "updated_at": self.updated_at.isoformat()
        }


class CommunicationLog:
    """
    Log of all communications with customer
    Tracks channel, content, responses for learning
    """
    
    def __init__(self, tenant_id: str, customer_id: str):
        self.tenant_id = tenant_id
        self.customer_id = customer_id
        self.communications: List[Dict] = []
    
    def add_communication(self, channel: str, direction: str, 
                     message: str, status: str,
                     metadata: Optional[Dict] = None):  # ADDED
        """Add communication record"""
        comm = {
            "timestamp": datetime.now().isoformat(),
            "channel": channel,
            "direction": direction,  # OUTBOUND, INBOUND
            "message": message[:200],  # Store first 200 chars
            "status": status,
            "message_id": hashlib.sha256(
                f"{self.tenant_id}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
        }
        
        self.communications.append(comm)
    
    def get_last_communication(self) -> Optional[Dict]:
        """Get most recent communication"""
        return self.communications[-1] if self.communications else None
    
    def get_channel_usage(self) -> Dict[str, int]:
        """Get usage count per channel"""
        usage = {}
        for comm in self.communications:
            channel = comm["channel"]
            usage[channel] = usage.get(channel, 0) + 1
        return usage
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "tenant_id": self.tenant_id,
            "customer_id": self.customer_id,
            "communications": self.communications,
            "total_communications": len(self.communications)
        }


class MemoryStore:
    """
    Centralized memory store for learning system
    Maintains customer and vehicle memories across tenants
    """
    
    def __init__(self):
        self.customer_memories: Dict[str, CustomerMemory] = {}
        self.vehicle_memories: Dict[str, VehicleMemory] = {}
        self.communication_logs: Dict[str, CommunicationLog] = {}
    
    def get_customer_memory(self, customer_id: str) -> CustomerMemory:
        """Get or create customer memory"""
        if customer_id not in self.customer_memories:
            self.customer_memories[customer_id] = CustomerMemory(customer_id)
        return self.customer_memories[customer_id]
    
    def get_vehicle_memory(self, vehicle_id: str) -> VehicleMemory:
        """Get or create vehicle memory"""
        if vehicle_id not in self.vehicle_memories:
            self.vehicle_memories[vehicle_id] = VehicleMemory(vehicle_id)
        return self.vehicle_memories[vehicle_id]
    
    def get_communication_log(self, tenant_id: str, customer_id: str) -> CommunicationLog:
        """Get or create communication log"""
        key = f"{tenant_id}_{customer_id}"
        if key not in self.communication_logs:
            self.communication_logs[key] = CommunicationLog(tenant_id, customer_id)
        return self.communication_logs[key]
    
    def save_to_file(self, filepath: str):
        """Save memory store to file (persistence)"""
        data = {
            "customer_memories": {
                k: v.to_dict() for k, v in self.customer_memories.items()
            },
            "vehicle_memories": {
                k: v.to_dict() for k, v in self.vehicle_memories.items()
            },
            "communication_logs": {
                k: v.to_dict() for k, v in self.communication_logs.items()
            },
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load memory store from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Reconstruct customer memories
            for cust_id, cust_data in data.get("customer_memories", {}).items():
                memory = CustomerMemory(cust_id)
                memory.preferences = cust_data["preferences"]
                memory.behavior_signals = cust_data["behavior_signals"]
                memory.interaction_history = cust_data["interaction_history"]
                self.customer_memories[cust_id] = memory
            
            # Reconstruct vehicle memories
            for veh_id, veh_data in data.get("vehicle_memories", {}).items():
                memory = VehicleMemory(veh_id)
                memory.maintenance_patterns = veh_data["maintenance_patterns"]
                memory.reliability_signals = veh_data["reliability_signals"]
                memory.component_history = veh_data["component_history"]
                self.vehicle_memories[veh_id] = memory
            
            print(f"✅ Memory store loaded from {filepath}")
            
        except FileNotFoundError:
            print(f"⚠️  Memory file not found: {filepath}, starting fresh")
        except Exception as e:
            print(f"⚠️  Error loading memory: {str(e)}")


class AuditTrail:
    """Enhanced audit trail with event tracking"""
    
    @staticmethod
    def generate_hash(data: Any, length: int = 16) -> str:
        """Generate SHA-256 hash of data"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        full_hash = hashlib.sha256(data_str.encode()).hexdigest()
        return full_hash[:length]
    
    @staticmethod
    def create_audit_record(agent_name: str, input_data: Any, 
                          output_data: Any, tenant_id: str,
                          execution_time: float = 0.0) -> Dict:
        """Create comprehensive audit record"""
        return {
            "audit_id": AuditTrail.generate_hash({
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "tenant": tenant_id
            }),
            "agent_name": agent_name,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "input_hash": AuditTrail.generate_hash(input_data),
            "output_hash": AuditTrail.generate_hash(output_data),
            "execution_time_seconds": execution_time
        }
    
    @staticmethod
    def create_event_audit(event_type: str, tenant_id: str, 
                          event_data: Dict) -> Dict:
        """Create audit record for event"""
        return {
            "audit_id": AuditTrail.generate_hash({
                "event": event_type,
                "tenant": tenant_id,
                "timestamp": datetime.now().isoformat()
            }),
            "event_type": event_type,
            "tenant_id": tenant_id,
            "timestamp": datetime.now().isoformat(),
            "event_data_hash": AuditTrail.generate_hash(event_data),
            "event_data_summary": str(event_data)[:100]
        }
    
    @staticmethod
    def create_workflow_audit(tenant_id: str, workflow_data: Dict,
                            events: List[Dict]) -> Dict:
        """Create complete workflow audit"""
        audit_data = {
            "workflow_id": f"WF_{tenant_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "tenant_id": tenant_id,
            "workflow_data": workflow_data,
            "events": events,
            "timestamp": datetime.now().isoformat()
        }
        
        audit_data["workflow_hash"] = AuditTrail.generate_hash(audit_data)
        return audit_data