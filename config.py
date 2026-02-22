"""
Configuration Module - v4.0
Multi-tenant, event-driven autonomous agent system
"""

from typing import Dict, Optional
from autogen_ext.models.openai import OpenAIChatCompletionClient


class SystemConfig:
    """System-wide configuration for multi-tenant autonomous system"""
    
    # Model Configuration
    MODEL_NAME = "llama3:8b"
    OLLAMA_BASE_URL = "http://localhost:11434/v1"
    OLLAMA_API_KEY = "ollama"
    
    # Agent Parameters
    AGENT_TEMPERATURE = 0.1
    AGENT_MAX_TOKENS = 2000
    MASTER_AGENT_MAX_TOKENS = 3000
    
    # Workflow Configuration
    MAX_REPLANNING_ATTEMPTS = 3
    LOW_CONFIDENCE_THRESHOLD = 0.6
    CRITICAL_CONFIDENCE_THRESHOLD = 0.5
    MAX_WORKFLOW_STEPS = 15
    
    # Event-Driven Configuration
    EVENT_PROCESSING_TIMEOUT = 30  # seconds
    TENANT_ISOLATION_STRICT = True
    
    # Priority Thresholds
    CRITICAL_BRAKE_PAD_MM = 3.0
    CRITICAL_BATTERY_VOLTAGE = 11.5
    CRITICAL_COOLANT_TEMP = 110.0
    
    # Confidence Thresholds by Priority
    CONFIDENCE_THRESHOLDS = {
        "P0": 0.85,
        "P1": 0.75,
        "P2": 0.65,
        "P3": 0.50
    }
    
    # Critical Event Keywords
    CRITICAL_KEYWORDS = ["CRITICAL", "URGENT", "FAILURE", "EMERGENCY", "SEVERE", "SAFETY"]
    
    # Communication Channels Configuration
    COMMUNICATION_CHANNELS = {
        "EMAIL": {
            "enabled": True,
            "priority": ["P0", "P1", "P2", "P3"],
            "max_retry": 3
        },
        "WHATSAPP": {
            "enabled": True,
            "priority": ["P0", "P1"],
            "max_retry": 2
        },
        "SMS": {
            "enabled": True,
            "priority": ["P0", "P1", "P2"],
            "max_retry": 2
        },
        "VOICE_CALL": {
            "enabled": True,
            "priority": ["P0"],
            "max_retry": 1
        }
    }
    
    # Customer Response Timeout
    CUSTOMER_RESPONSE_TIMEOUT_HOURS = {
        "P0": 2,   # 2 hours for critical
        "P1": 12,  # 12 hours for high
        "P2": 24,  # 24 hours for medium
        "P3": 48   # 48 hours for low
    }
    
    
    # Memory and Learning Configuration
    MEMORY_RETENTION_DAYS = 365
    LEARNING_UPDATE_THRESHOLD = 0.3  # Update memory if confidence delta > 0.3
    
    # ML Model Configuration (v4.2)
    ML_MODELS_DIR = "ml_models"
    ML_ENABLE_PREDICTIONS = True
    ML_CONFIDENCE_THRESHOLD = 0.6
    
    # Contact Timing Configuration
    WORK_HOURS_START = 9   # 9 AM
    WORK_HOURS_END = 17    # 5 PM
    WEEKEND_CONTACT_ALLOWED = True
    OPTIMAL_CONTACT_HOURS = [18, 19, 20]  # 6-8 PM
    
    # Voice AI Configuration (v4.3)
    VOICE_AI_CONFIG = {
        "stt_model": "openai/whisper-large-v3-turbo",  # Hugging Face
        "llm_model": "llama-3.1-70b-versatile",  # Groq
        "tts_model": "eleven_turbo_v2_5",
        "tts_voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel voice
        "max_response_words": 25,
        "enable_fillers": True,
        "latency_target_ms": 300,
        "webhook_base_url": "https://your-ngrok-url.ngrok-free.app"  # Use ngrok for local development
    }
    
    # Sentiment Configuration (v4.3)
    SENTIMENT_CONFIG = {
        "frustration_threshold": 0.7,
        "urgency_threshold": 0.8,
        "auto_escalate_to_voice": True,
        "objection_detection": True,
        "min_frustration_count": 2
    }
    
    # API Configuration (for real integrations)
    TWILIO_CONFIG = {
        "account_sid": "YOUR_TWILIO_SID",  # Set via environment
        "auth_token": "YOUR_TWILIO_TOKEN",
        "from_number": "+1234567890"
    }
    
    WHATSAPP_CONFIG = {
        "api_key": "YOUR_WHATSAPP_API_KEY",
        "from_number": "whatsapp:+1234567890"
    }
    
    EMAIL_CONFIG = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "from_email": "maintenance@example.com",
        "password": "YOUR_EMAIL_PASSWORD"
    }
    
    # Audit Configuration
    AUDIT_HASH_LENGTH = 16


class EventTypes:
    """Event types for event-driven orchestration"""
    
    # Agent Completion Events
    DATA_ANALYSIS_COMPLETED = "DATA_ANALYSIS_COMPLETED"
    DIAGNOSIS_UPDATED = "DIAGNOSIS_UPDATED"
    CUSTOMER_RESPONSE_RECEIVED = "CUSTOMER_RESPONSE_RECEIVED"
    
    # Threshold Events
    LOW_CONFIDENCE_DETECTED = "LOW_CONFIDENCE_DETECTED"
    HIGH_FAILURE_PROBABILITY = "HIGH_FAILURE_PROBABILITY"
    
    # Customer Events
    CUSTOMER_NON_RESPONSIVE = "CUSTOMER_NON_RESPONSIVE"
    CUSTOMER_DECLINED = "CUSTOMER_DECLINED"
    CUSTOMER_ACCEPTED = "CUSTOMER_ACCEPTED"
    
    # System Events
    SLA_VIOLATION_RISK = "SLA_VIOLATION_RISK"
    AGENT_EXECUTION_FAILURE = "AGENT_EXECUTION_FAILURE"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"
    
    # Replanning Events
    REPLANNING_TRIGGERED = "REPLANNING_TRIGGERED"
    REPLANNING_COMPLETED = "REPLANNING_COMPLETED"
    
    # Workflow Events
    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    WORKFLOW_ABORTED = "WORKFLOW_ABORTED"


class CommunicationChannel:
    """Communication channel types"""
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    SMS = "SMS"
    VOICE_CALL = "VOICE_CALL"


class LlamaModelClient:
    """Enhanced Ollama/Llama model client factory with role-specific configs"""
    
    @staticmethod
    def create_client(max_tokens: int = None, temperature: float = None):
        """Create OpenAI-compatible client for Ollama"""
        
        client = OpenAIChatCompletionClient(
            model=SystemConfig.MODEL_NAME,
            base_url=SystemConfig.OLLAMA_BASE_URL,
            api_key=SystemConfig.OLLAMA_API_KEY,
            model_capabilities={
                "vision": False,
                "function_calling": True,
                "json_output": True,
            },
            temperature=temperature or SystemConfig.AGENT_TEMPERATURE,
            max_tokens=max_tokens or SystemConfig.AGENT_MAX_TOKENS,
        )
        
        return client
    
    @staticmethod
    def create_master_orchestrator_client():
        """Create client for Master Orchestrator (event-driven)"""
        print("🦙 Configuring Master Orchestrator (Event-Driven)...")
        client = LlamaModelClient.create_client(
            max_tokens=SystemConfig.MASTER_AGENT_MAX_TOKENS,
            temperature=0.05  # Very low for consistent planning
        )
        print("✅ Master Orchestrator configured!")
        return client
    
    @staticmethod
    def create_specialist_client():
        """Create client for specialist agents"""
        print("🦙 Configuring Specialist Agents...")
        client = LlamaModelClient.create_client(
            max_tokens=SystemConfig.AGENT_MAX_TOKENS,
            temperature=SystemConfig.AGENT_TEMPERATURE
        )
        print("✅ Specialist Agents configured!")
        return client
    
    @staticmethod
    def create_customer_interpreter_client():
        """Create client for customer response interpreter"""
        print("🦙 Configuring Customer Response Interpreter...")
        client = LlamaModelClient.create_client(
            max_tokens=1500,
            temperature=0.1  # Low for consistent interpretation
        )
        print("✅ Customer Interpreter configured!")
        return client
    
    @staticmethod
    def create_learning_client():
        """Create client for learning and memory agent"""
        print("🦙 Configuring Learning & Memory Agent...")
        client = LlamaModelClient.create_client(
            max_tokens=2000,
            temperature=0.2  # Slightly higher for creative memory updates
        )
        print("✅ Learning Agent configured!")
        return client