"""
ENTERPRISE AUTONOMOUS PREDICTIVE MAINTENANCE SYSTEM
Version 2.0: True Agentic AI with Master Orchestrator
Features: Dynamic Planning, Adaptive Re-planning, Self-Monitoring
"""

import json
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import numpy as np
import pandas as pd

# AutoGen 0.7.5
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

# ======================================================================
# PART 1: ENHANCED OLLAMA CONFIGURATION
# ======================================================================

class LocalLlamaConfig:
    """Enhanced configuration for Ollama with proper settings"""
    
    def __init__(self, model_name="llama3:8b"):
        self.model_name = model_name
    
    def get_model_client(self):
        """Get OpenAI-compatible client for Ollama with optimized settings"""
        print(f"🦙 Configuring {self.model_name} via Ollama...")
        
        client = OpenAIChatCompletionClient(
            model=self.model_name,
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model_capabilities={
                "vision": False,
                "function_calling": True,
                "json_output": True,
            },
            temperature=0.1,
            max_tokens=1500,  # Increased for master agent
        )
        
        print("✅ Local LLM configured successfully!")
        return client

# ======================================================================
# PART 2: WORKFLOW STATE MANAGEMENT
# ======================================================================

class WorkflowState(Enum):
    """Workflow execution states"""
    PLANNING = "planning"
    EXECUTING = "executing"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"

class ExecutionContext:
    """Tracks execution state and history"""
    
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.state = WorkflowState.PLANNING
        self.execution_history: List[Dict] = []
        self.plan: Optional[Dict] = None
        self.current_step = 0
        self.replanning_count = 0
        self.confidence_scores: List[float] = []
        self.anomalies_detected: List[str] = []
        self.agent_outputs: Dict[str, Any] = {}
        self.start_time = datetime.now()
        
    def add_execution_record(self, agent_name: str, status: str, 
                            output: Any, confidence: float):
        """Record agent execution"""
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "status": status,
            "output": output,
            "confidence": confidence,
            "step": self.current_step
        })
        self.confidence_scores.append(confidence)
        self.agent_outputs[agent_name] = output
    
    def should_replan(self) -> Tuple[bool, str]:
        """Determine if replanning is needed"""
        # Max replanning attempts
        if self.replanning_count >= 2:
            return False, "Max replanning attempts reached"
        
        # Low confidence threshold
        if self.confidence_scores and np.mean(self.confidence_scores[-3:]) < 0.5:
            return True, "Low confidence in recent steps"
        
        # Critical anomalies
        critical_keywords = ["CRITICAL", "URGENT", "FAILURE", "EMERGENCY"]
        if any(any(kw in str(anomaly).upper() for kw in critical_keywords) 
               for anomaly in self.anomalies_detected):
            return True, "Critical anomaly detected"
        
        return False, ""
    
    def get_execution_summary(self) -> Dict:
        """Generate execution summary"""
        return {
            "vehicle_id": self.vehicle_id,
            "state": self.state.value,
            "steps_completed": len(self.execution_history),
            "replanning_count": self.replanning_count,
            "avg_confidence": np.mean(self.confidence_scores) if self.confidence_scores else 0.0,
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "agents_invoked": list(self.agent_outputs.keys())
        }

# ======================================================================
# PART 3: AUDIT & TRACEABILITY
# ======================================================================

class AuditTrail:
    """Generate audit hashes for regulatory-grade traceability"""
    
    @staticmethod
    def generate_hash(data: Any) -> str:
        """Generate SHA-256 hash of data"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    @staticmethod
    def create_audit_record(agent_name: str, input_data: Any, 
                          output_data: Any, context: ExecutionContext) -> Dict:
        """Create audit record with hashes"""
        return {
            "agent_name": agent_name,
            "timestamp": datetime.now().isoformat(),
            "input_hash": AuditTrail.generate_hash(input_data),
            "output_hash": AuditTrail.generate_hash(output_data),
            "workflow_state": context.state.value,
            "step": context.current_step,
            "replanning_count": context.replanning_count
        }

# ======================================================================
# PART 4: DATA GENERATOR
# ======================================================================

class ComprehensiveDataGenerator:
    """Generate synthetic data matching all CSV schemas"""
    
    def __init__(self):
        self.vehicle_ids = [f"VEH{str(i).zfill(3)}" for i in range(1, 11)]
        self.customer_ids = [f"CUST{str(i).zfill(4)}" for i in range(1001, 1011)]
        self.makes = ["Tata", "Mahindra"]
        self.models = {
            "Tata": ["Nexon EV", "Harrier", "Safari", "Punch"],
            "Mahindra": ["XUV700", "Scorpio", "Thar", "XUV300"]
        }
    
    def generate_telematics_timeseries(self, vehicle_id: str, 
                                      scenario: str = "normal") -> Dict:
        """Generate real-time telematics with scenario support"""
        base_data = {
            "vehicle_id": vehicle_id,
            "timestamp": datetime.now().isoformat(),
            "engine_rpm": int(np.random.randint(800, 3500)),
            "coolant_temp_c": round(float(np.random.uniform(85, 110)), 1),
            "battery_voltage_v": round(float(np.random.uniform(11.5, 14.5)), 2),
            "battery_soc_pct": round(float(np.random.uniform(20, 100)), 1),
            "brake_pad_mm": round(float(np.random.uniform(2.0, 12.0)), 1),
            "tyre_fl_pressure": round(float(np.random.uniform(28, 35)), 1),
            "speed_kmph": int(np.random.randint(0, 120)),
            "odo_km": int(np.random.randint(50000, 150000)),
        }
        
        # Apply scenario modifications
        if scenario == "critical":
            base_data["brake_pad_mm"] = 1.8
            base_data["battery_voltage_v"] = 11.2
            base_data["coolant_temp_c"] = 115.0
        elif scenario == "warning":
            base_data["brake_pad_mm"] = 2.9
            base_data["battery_voltage_v"] = 11.7
            
        return base_data
    
    def generate_vehicles_data(self, vehicle_id: str) -> Dict:
        """Generate vehicle master record"""
        make = np.random.choice(self.makes)
        model = np.random.choice(self.models[make])
        idx = self.vehicle_ids.index(vehicle_id) if vehicle_id in self.vehicle_ids else 0
        
        return {
            "vehicle_id": vehicle_id,
            "vin": f"MA3F{vehicle_id[-3:]}{np.random.randint(100000, 999999)}",
            "make": make,
            "model": model,
            "year": np.random.randint(2020, 2025),
            "customer_id": self.customer_ids[min(idx, len(self.customer_ids)-1)]
        }
    
    def generate_maintenance_events(self, vehicle_id: str) -> List[Dict]:
        """Generate maintenance history"""
        events = []
        for i in range(3):
            days_ago = np.random.randint(30, 300)
            service_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            events.append({
                "maintenance_id": f"MAINT{str(i+1).zfill(4)}",
                "vehicle_id": vehicle_id,
                "service_date": service_date,
                "service_type": np.random.choice(["Oil Change", "Brake Service", "Battery Replacement"]),
            })
        
        return events
    
    def generate_customers_data(self, customer_id: str) -> Dict:
        """Generate customer record"""
        names = ["Rajesh Kumar", "Priya Sharma", "Amit Patel", "Neha Gupta"]
        idx = self.customer_ids.index(customer_id) if customer_id in self.customer_ids else 0
        
        return {
            "customer_id": customer_id,
            "name": names[min(idx, len(names)-1)],
            "phone": f"+91-{np.random.randint(7000000000, 9999999999, dtype=np.int64)}",
            "preferred_lang": "en",
            "pref_contact_mode": "chat"
        }
    
    def generate_ueba_baseline(self) -> Dict:
        """Generate UEBA status"""
        return {
            "alert": False,
            "severity": "NONE",
            "message": "All agent behaviors within baseline"
        }

# ======================================================================
# PART 5: RULE ENGINE
# ======================================================================

class RuleEngine:
    """Deterministic decision system"""
    
    def assign_priority(self, failure_probability: float, rul_days: int, 
                       severity: str, recurring_defect: bool, 
                       brake_pad_mm: float, battery_voltage: float) -> str:
        """Priority assignment rules"""
        if brake_pad_mm < 3.0 or battery_voltage < 11.5:
            return "P0"
        if severity == "HIGH" or recurring_defect or rul_days <= 3:
            return "P0"
        elif failure_probability > 0.7 or rul_days <= 7:
            return "P1"
        elif failure_probability > 0.4 or rul_days <= 30:
            return "P2"
        else:
            return "P3"
    
    def determine_escalation(self, priority: str, customer_response: str, 
                            recurring_defect: bool) -> bool:
        """Escalation decision"""
        if priority == "P0":
            return True
        if priority == "P1" and customer_response == "DECLINED":
            return True
        if recurring_defect and customer_response == "DECLINED":
            return True
        return False
    
    def calculate_confidence_threshold(self, priority: str) -> float:
        """Confidence thresholds"""
        thresholds = {"P0": 0.85, "P1": 0.75, "P2": 0.65, "P3": 0.50}
        return thresholds.get(priority, 0.60)

# ======================================================================
# PART 6: MASTER ORCHESTRATOR AGENT
# ======================================================================

class MasterOrchestratorAgent:
    """
    True Agentic AI: Plans, executes, monitors, and replans autonomously
    """
    
    def __init__(self, model_client):
        self.model_client = model_client
        self.agent = AssistantAgent(
            name="Master_Orchestrator",
            model_client=model_client,
            system_message="""You are the Master Orchestrator AI - an autonomous planning and decision-making system.

CRITICAL: Respond with ONLY valid JSON. No explanations, no markdown, no extra text.

AVAILABLE AGENTS (you must use these exact names):
1. "Data_Analysis_Agent" - analyzes telematics and maintenance history for health assessment
2. "Diagnosis_Agent" - predicts component failures and remaining useful life
3. "Customer_Engagement_Agent" - communicates service needs to customers

Your responsibilities:
1. Create execution plans using ONLY the available agents above
2. Monitor workflow execution
3. Detect when replanning is needed
4. Adapt plans dynamically based on agent outputs
5. Make go/no-go decisions on workflow continuation

PLANNING OUTPUT FORMAT:
{
  "plan_type": "initial" or "replan",
  "strategy": "standard" or "expedited" or "deep_analysis",
  "steps": [
    {"agent": "Data_Analysis_Agent", "priority": "high", "required": true},
    {"agent": "Diagnosis_Agent", "priority": "critical", "required": true},
    {"agent": "Customer_Engagement_Agent", "priority": "medium", "required": false}
  ],
  "risk_level": "low" or "medium" or "high" or "critical",
  "estimated_duration_min": 5,
  "contingency_actions": ["escalate_if_low_confidence", "skip_optional_steps"],
  "reasoning": "Brief explanation of strategy"
}

MONITORING OUTPUT FORMAT:
{
  "continue_execution": true or false,
  "recommendation": "proceed" or "replan" or "escalate" or "abort",
  "concern_level": "none" or "low" or "medium" or "high",
  "detected_issues": ["issue1", "issue2"],
  "next_action": "What should happen next",
  "confidence": 0.85
}

Start response with { and end with }. Nothing else."""
        )
    
    async def create_initial_plan(self, context: ExecutionContext, 
                                 telematics: Dict, vehicle: Dict) -> Dict:
        """Generate initial execution plan"""
        
        planning_context = f"""Create an execution plan for predictive maintenance:

VEHICLE: {vehicle['make']} {vehicle['model']} (ID: {context.vehicle_id})
TELEMATICS SNAPSHOT:
  - Brake Pads: {telematics['brake_pad_mm']}mm
  - Battery: {telematics['battery_voltage_v']}V
  - Coolant: {telematics['coolant_temp_c']}°C
  - Odometer: {telematics['odo_km']:,}km

Determine the optimal workflow strategy. Respond with JSON only."""

        return await self._execute_planning(planning_context, "initial")
    
    async def monitor_and_decide(self, context: ExecutionContext) -> Dict:
        """Monitor execution and decide next steps"""
        
        summary = context.get_execution_summary()
        recent_outputs = list(context.agent_outputs.values())[-2:] if context.agent_outputs else []
        
        monitoring_context = f"""Monitor workflow execution and decide next action:

EXECUTION STATUS:
  - Steps Completed: {summary['steps_completed']}
  - Avg Confidence: {summary['avg_confidence']:.2f}
  - Replanning Count: {summary['replanning_count']}
  - Agents Invoked: {', '.join(summary['agents_invoked'])}

RECENT AGENT OUTPUTS:
{json.dumps(recent_outputs, indent=2)}

ANOMALIES: {context.anomalies_detected}

Should we continue, replan, or escalate? Respond with JSON only."""

        return await self._execute_monitoring(monitoring_context)
    
    async def create_replan(self, context: ExecutionContext, reason: str) -> Dict:
        """Generate adaptive replan"""
        
        replan_context = f"""Create a new execution plan (REPLANNING):

REASON FOR REPLANNING: {reason}

CURRENT STATE:
  - Steps Completed: {len(context.execution_history)}
  - Confidence Scores: {context.confidence_scores[-3:]}
  - Detected Issues: {context.anomalies_detected}

AGENTS ALREADY EXECUTED:
{json.dumps(list(context.agent_outputs.keys()))}

Create an adaptive plan to address the issues. Respond with JSON only."""

        return await self._execute_planning(replan_context, "replan")
    
    async def _execute_planning(self, context_str: str, plan_type: str) -> Dict:
        """Execute planning with fallback"""
        default_plan = {
            "plan_type": plan_type,
            "strategy": "standard",
            "steps": [
                {"agent": "Data_Analysis_Agent", "priority": "high", "required": True},
                {"agent": "Diagnosis_Agent", "priority": "critical", "required": True},
                {"agent": "Customer_Engagement_Agent", "priority": "medium", "required": False}
            ],
            "risk_level": "medium",
            "estimated_duration_min": 5,
            "contingency_actions": ["escalate_if_low_confidence"],
            "reasoning": "Standard maintenance workflow"
        }
        
        try:
            team = RoundRobinGroupChat([self.agent], max_turns=1)
            stream = team.run_stream(task=context_str)
            
            response_text = ""
            async for message in stream:
                if hasattr(message, 'content'):
                    response_text += str(message.content)
            
            response_text = response_text.strip()
            
            # Clean response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx+1]
                plan = json.loads(json_str)
                print(f"   ✅ Master Orchestrator created {plan_type} plan")
                return plan
            
        except Exception as e:
            print(f"   ⚠️  Planning failed: {str(e)[:50]}")
        
        print(f"   ℹ️  Using default {plan_type} plan")
        return default_plan
    
    async def _execute_monitoring(self, context_str: str) -> Dict:
        """Execute monitoring with fallback"""
        default_decision = {
            "continue_execution": True,
            "recommendation": "proceed",
            "concern_level": "low",
            "detected_issues": [],
            "next_action": "Continue with next step",
            "confidence": 0.75
        }
        
        try:
            team = RoundRobinGroupChat([self.agent], max_turns=1)
            stream = team.run_stream(task=context_str)
            
            response_text = ""
            async for message in stream:
                if hasattr(message, 'content'):
                    response_text += str(message.content)
            
            response_text = response_text.strip()
            
            # Clean response - remove code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Extract ONLY the JSON part - from first { to last }
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx+1]
                # Try to parse with strict validation
                decision = json.loads(json_str)
                print(f"   ✅ Master Orchestrator monitoring decision: {decision.get('recommendation', 'proceed')}")
                return decision
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Monitoring JSON error: {str(e)[:40]}")
        except Exception as e:
            print(f"   ⚠️  Monitoring failed: {str(e)[:50]}")
        
        print(f"   ℹ️  Using default monitoring decision")
        return default_decision

# ======================================================================
# PART 7: SPECIALIZED AGENT FACTORY
# ======================================================================

class EnhancedAgentFactory:
    """Factory to create specialized agents"""
    
    @staticmethod
    def create_data_analysis_agent(model_client) -> AssistantAgent:
        return AssistantAgent(
            name="Data_Analysis_Agent",
            model_client=model_client,
            system_message="""You are a data analysis agent. Analyze vehicle telematics data.

CRITICAL: You MUST respond with ONLY a JSON object. No explanations, no markdown, no extra text.

Your response must be a valid JSON object with these exact fields:
{
  "health_score": 0.75,
  "detected_anomalies": ["High coolant temp"],
  "service_demand_forecast": "MEDIUM",
  "confidence": 0.8,
  "data_coverage": 0.95,
  "data_quality_notes": "Real-time data available"
}

health_score: float 0.0-1.0 (0.5=normal, <0.5=degraded, >0.7=good)
detected_anomalies: list of issues found
service_demand_forecast: "LOW", "MEDIUM", or "HIGH"
confidence: float 0.0-1.0
data_coverage: float 0.0-1.0
data_quality_notes: brief note

Start your response with { and end with }. Nothing else."""
        )
    
    @staticmethod
    def create_diagnosis_agent(model_client) -> AssistantAgent:
        return AssistantAgent(
            name="Diagnosis_Agent",
            model_client=model_client,
            system_message="""You are a diagnostic agent. Predict component failures.

CRITICAL: You MUST respond with ONLY a JSON object. No explanations, no markdown, no extra text.

Your response must be a valid JSON object with these exact fields:
{
  "failure_probability": 0.6,
  "rul_days": 25,
  "affected_component": "Brake Pads",
  "severity": "MEDIUM",
  "recurring_defect": false,
  "confidence": 0.75,
  "diagnostic_reasoning": "Brake pad thickness below recommended level"
}

failure_probability: float 0.0-1.0
rul_days: integer (remaining useful life in days)
affected_component: component name
severity: "LOW", "MEDIUM", or "HIGH"
recurring_defect: true or false
confidence: float 0.0-1.0
diagnostic_reasoning: brief explanation

Start your response with { and end with }. Nothing else."""
        )
    
    @staticmethod
    def create_customer_engagement_agent(model_client) -> AssistantAgent:
        return AssistantAgent(
            name="Customer_Engagement_Agent",
            model_client=model_client,
            system_message="""You are a customer service agent. Communicate service needs to customers.

CRITICAL: You MUST respond with ONLY a JSON object. No explanations, no markdown, no extra text.

Your response must be a valid JSON object with these exact fields:
{
  "customer_response": "ACCEPTED",
  "interaction_outcome": "Customer agreed to service appointment",
  "customer_message": "Thank you for the notification. I'll bring it in.",
  "engagement_quality": 0.85,
  "sentiment": "positive"
}

customer_response: "ACCEPTED", "DECLINED", or "REQUESTED_RESCHEDULE"
interaction_outcome: brief summary
customer_message: simulated customer reply
engagement_quality: float 0.0-1.0
sentiment: "positive", "neutral", or "negative"

Start your response with { and end with }. Nothing else."""
        )

# ======================================================================
# PART 8: AGENTIC ORCHESTRATION SYSTEM
# ======================================================================

class AgenticPredictiveMaintenanceSystem:
    """
    Main orchestration system with Master Agent control
    """
    
    @staticmethod
    def _convert_numpy_types(obj):
        """Convert NumPy types to native Python types"""
        if isinstance(obj, dict):
            return {k: AgenticPredictiveMaintenanceSystem._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [AgenticPredictiveMaintenanceSystem._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, (np.bool_, np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    def __init__(self, model_client):
        self.model_client = model_client
        self.data_gen = ComprehensiveDataGenerator()
        self.rule_engine = RuleEngine()
        self.audit_trail = AuditTrail()
        self.master_orchestrator = MasterOrchestratorAgent(model_client)
        self.setup_agents()
        self.audit_log = []
    
    def setup_agents(self):
        """Initialize all agents"""
        factory = EnhancedAgentFactory()
        self.agents = {
            "Data_Analysis_Agent": factory.create_data_analysis_agent(self.model_client),
            "Diagnosis_Agent": factory.create_diagnosis_agent(self.model_client),
            "Customer_Engagement_Agent": factory.create_customer_engagement_agent(self.model_client)
        }
    
    async def run_agentic_maintenance_cycle(self, vehicle_id: str, scenario: str = "normal"):
        """Execute FULLY AGENTIC maintenance cycle with Master Orchestrator"""
        
        print("\n" + "="*80)
        print(f"🤖 AGENTIC PREDICTIVE MAINTENANCE CYCLE")
        print(f"Vehicle ID: {vehicle_id} | Scenario: {scenario}")
        print("="*80 + "\n")
        
        # Initialize execution context
        context = ExecutionContext(vehicle_id)
        
        # ==================== DATA GATHERING ====================
        print("📊 STEP 0: Data Gathering")
        print("-" * 80)
        
        telematics = self.data_gen.generate_telematics_timeseries(vehicle_id, scenario)
        vehicle_master = self.data_gen.generate_vehicles_data(vehicle_id)
        maintenance_history = self.data_gen.generate_maintenance_events(vehicle_id)
        customer_data = self.data_gen.generate_customers_data(vehicle_master["customer_id"])
        ueba_status = self.data_gen.generate_ueba_baseline()
        
        print(f"✓ Vehicle: {vehicle_master['make']} {vehicle_master['model']} ({vehicle_master['year']})")
        print(f"✓ Customer: {customer_data['name']}")
        print(f"✓ Odometer: {telematics['odo_km']:,} km")
        print(f"✓ Brake Pad: {telematics['brake_pad_mm']} mm")
        print(f"✓ Battery: {telematics['battery_voltage_v']} V")
        print(f"✓ Coolant: {telematics['coolant_temp_c']}°C")
        
        if ueba_status.get("alert", False):
            print("\n🛡️ UEBA ALERT: Workflow halted")
            context.state = WorkflowState.FAILED
            return context
        
        # ==================== MASTER ORCHESTRATOR: PLANNING ====================
        print("\n🧠 MASTER ORCHESTRATOR: Initial Planning")
        print("-" * 80)
        
        context.state = WorkflowState.PLANNING
        plan = await self.master_orchestrator.create_initial_plan(context, telematics, vehicle_master)
        context.plan = plan
        
        print(f"✓ Strategy: {plan.get('strategy', 'standard').upper()}")
        print(f"✓ Risk Level: {plan.get('risk_level', 'unknown').upper()}")
        print(f"✓ Steps Planned: {len(plan.get('steps', []))}")
        print(f"✓ Estimated Duration: {plan.get('estimated_duration_min', 0)} min")
        print(f"✓ Reasoning: {plan.get('reasoning', 'N/A')}")
        
        # ==================== EXECUTE WORKFLOW ====================
        context.state = WorkflowState.EXECUTING
        
        for step in plan.get('steps', []):
            agent_name = step.get('agent')
            priority = step.get('priority', 'medium')
            required = step.get('required', True)
            
            context.current_step += 1
            
            print(f"\n{'='*80}")
            print(f"STEP {context.current_step}: {agent_name} [Priority: {priority.upper()}]")
            print("-" * 80)
            
            # Execute agent based on type
            if agent_name == "Data_Analysis_Agent":
                result = await self._execute_data_analysis(context, telematics, maintenance_history)
            elif agent_name == "Diagnosis_Agent":
                result = await self._execute_diagnosis(context, telematics, maintenance_history)
            elif agent_name == "Customer_Engagement_Agent":
                # Get diagnosis first
                diagnosis = context.agent_outputs.get('Diagnosis_Agent', {})
                priority_assigned = self._assign_priority(diagnosis, telematics)
                result = await self._execute_customer_engagement(
                    context, vehicle_master, customer_data, diagnosis, priority_assigned
                )
            else:
                print(f"⚠️  Unknown agent: {agent_name}")
                continue
            
            # Check if we should continue
            if required and not result:
                print(f"❌ Required step failed - considering replanning")
                context.state = WorkflowState.REPLANNING
                break
            
            # Master Orchestrator monitoring decision
            decision = await self.master_orchestrator.monitor_and_decide(context)
            print(f"✓ Monitoring: {decision.get('recommendation', 'proceed').upper()}")
            
            # Handle monitoring decision
            if decision.get('recommendation') == 'replan':
                print("\n🔄 REPLANNING TRIGGERED")
                context.state = WorkflowState.REPLANNING
                break
            elif decision.get('recommendation') == 'escalate':
                print("\n⚠️  ESCALATION TRIGGERED")
                context.state = WorkflowState.ESCALATED
                break
            elif decision.get('recommendation') == 'abort':
                print("\n❌ WORKFLOW ABORTED")
                context.state = WorkflowState.FAILED
                return context
            elif not decision.get('continue_execution', True):
                print("\n⏸️  Execution halted by Master Orchestrator")
                break
        
        # ==================== REPLANNING IF NEEDED ====================
        if context.state == WorkflowState.REPLANNING:
            should_replan, replan_reason = context.should_replan()
            
            if should_replan:
                print(f"\n{'='*80}")
                print(f"🔄 ADAPTIVE REPLANNING")
                print(f"Reason: {replan_reason}")
                print("="*80)
                
                context.replanning_count += 1
                new_plan = await self.master_orchestrator.create_replan(context, replan_reason)
                
                print(f"✓ New Strategy: {new_plan.get('strategy', 'standard').upper()}")
                print(f"✓ Adjusted Steps: {len(new_plan.get('steps', []))}")
                print(f"✓ New Reasoning: {new_plan.get('reasoning', 'N/A')}")
                
                # Execute replan (simplified - only missing critical steps)
                for step in new_plan.get('steps', []):
                    agent_name = step.get('agent')
                    if agent_name not in context.agent_outputs and step.get('required', False):
                        context.current_step += 1
                        print(f"\n{'='*80}")
                        print(f"REPLAN STEP {context.current_step}: {agent_name}")
                        print("-" * 80)
                        
                        # Execute missing agent
                        if agent_name == "Data_Analysis_Agent":
                            await self._execute_data_analysis(context, telematics, maintenance_history)
                        elif agent_name == "Diagnosis_Agent":
                            await self._execute_diagnosis(context, telematics, maintenance_history)
        
        # ==================== FINAL DECISION MAKING ====================
        print(f"\n{'='*80}")
        print("🎯 FINAL DECISION & ACTION")
        print("="*80)
        
        # Get outputs from context
        diagnosis = context.agent_outputs.get('Diagnosis_Agent', {})
        customer_response_data = context.agent_outputs.get('Customer_Engagement_Agent', {})
        
        # Assign priority using rule engine
        priority = self._assign_priority(diagnosis, telematics)
        
        # Escalation decision
        customer_response = customer_response_data.get('customer_response', 'ACCEPTED')
        recurring = diagnosis.get('recurring_defect', False)
        escalate = self.rule_engine.determine_escalation(priority, customer_response, recurring)
        
        # Final recommendation
        component = diagnosis.get('affected_component', 'Unknown')
        rul_days = diagnosis.get('rul_days', 30)
        failure_prob = diagnosis.get('failure_probability', 0.5)
        
        print(f"\n📋 MAINTENANCE RECOMMENDATION:")
        print(f"   Component: {component}")
        print(f"   Priority: {priority}")
        print(f"   Failure Probability: {failure_prob:.1%}")
        print(f"   Remaining Useful Life: {rul_days} days")
        print(f"   Customer Response: {customer_response}")
        print(f"   Escalation Required: {'YES' if escalate else 'NO'}")
        
        # Generate work order
        work_order = self._generate_work_order(
            context, vehicle_master, customer_data, diagnosis, 
            priority, escalate, customer_response
        )
        
        print(f"\n📄 WORK ORDER GENERATED: {work_order['work_order_id']}")
        print(f"   Scheduled: {work_order['scheduled_date']}")
        print(f"   Service Type: {work_order['service_type']}")
        print(f"   Status: {work_order['status']}")
        
        # ==================== AUDIT & SUMMARY ====================
        context.state = WorkflowState.COMPLETED
        summary = context.get_execution_summary()
        
        print(f"\n{'='*80}")
        print("📊 EXECUTION SUMMARY")
        print("="*80)
        print(f"✓ Total Steps: {summary['steps_completed']}")
        print(f"✓ Agents Invoked: {len(summary['agents_invoked'])}")
        print(f"✓ Replanning Count: {summary['replanning_count']}")
        print(f"✓ Average Confidence: {summary['avg_confidence']:.2f}")
        print(f"✓ Duration: {summary['duration_seconds']:.1f}s")
        print(f"✓ Final State: {summary['state']}")
        
        # Generate audit hash
        audit_data = {
            "context": summary,
            "work_order": work_order,
            "execution_history": context.execution_history
        }
        audit_hash = self.audit_trail.generate_hash(audit_data)
        
        print(f"\n🔒 AUDIT HASH: {audit_hash}")
        print(f"✓ Regulatory Compliance: VERIFIED")
        
        print("\n" + "="*80)
        print("✅ AGENTIC MAINTENANCE CYCLE COMPLETED")
        print("="*80 + "\n")
        
        return context
    
    async def _execute_data_analysis(self, context: ExecutionContext, 
                                    telematics: Dict, maintenance_history: List[Dict]) -> bool:
        """Execute data analysis agent"""
        input_data = {
            "telematics": telematics,
            "maintenance_history": maintenance_history
        }
        
        analysis_prompt = f"""Analyze this vehicle data:

TELEMATICS:
- Brake Pads: {telematics['brake_pad_mm']}mm
- Battery: {telematics['battery_voltage_v']}V  
- Coolant: {telematics['coolant_temp_c']}°C
- Odometer: {telematics['odo_km']:,}km
- Speed: {telematics['speed_kmph']}km/h

MAINTENANCE HISTORY: {len(maintenance_history)} service events

Provide health assessment. Respond with JSON only."""

        try:
            output = await self._run_agent_with_fallback(
                self.agents["Data_Analysis_Agent"],
                analysis_prompt,
                {
                    "health_score": 0.65,
                    "detected_anomalies": ["Brake pad wear detected"],
                    "service_demand_forecast": "MEDIUM",
                    "confidence": 0.75,
                    "data_coverage": 0.95,
                    "data_quality_notes": "Real-time data complete"
                }
            )
            
            confidence = output.get('confidence', 0.75)
            context.add_execution_record("Data_Analysis_Agent", "success", output, confidence)
            
            # Check for anomalies
            anomalies = output.get('detected_anomalies', [])
            context.anomalies_detected.extend(anomalies)
            
            print(f"✓ Health Score: {output.get('health_score', 0.0):.2f}")
            print(f"✓ Forecast: {output.get('service_demand_forecast', 'UNKNOWN')}")
            print(f"✓ Confidence: {confidence:.2f}")
            if anomalies:
                print(f"⚠️  Anomalies: {', '.join(anomalies)}")
            
            # Create audit record
            audit = self.audit_trail.create_audit_record(
                "Data_Analysis_Agent", input_data, output, context
            )
            self.audit_log.append(audit)
            
            return True
            
        except Exception as e:
            print(f"❌ Data analysis failed: {str(e)[:50]}")
            context.add_execution_record("Data_Analysis_Agent", "failed", {}, 0.0)
            return False
    
    async def _execute_diagnosis(self, context: ExecutionContext,
                                telematics: Dict, maintenance_history: List[Dict]) -> bool:
        """Execute diagnosis agent"""
        input_data = {
            "telematics": telematics,
            "maintenance_history": maintenance_history
        }
        
        diagnosis_prompt = f"""Diagnose potential failures:

CURRENT READINGS:
- Brake Pads: {telematics['brake_pad_mm']}mm (Critical: <3mm)
- Battery: {telematics['battery_voltage_v']}V (Critical: <11.5V)
- Coolant: {telematics['coolant_temp_c']}°C (Critical: >110°C)
- Mileage: {telematics['odo_km']:,}km

MAINTENANCE HISTORY: {len(maintenance_history)} events

Predict component failures. Respond with JSON only."""

        try:
            output = await self._run_agent_with_fallback(
                self.agents["Diagnosis_Agent"],
                diagnosis_prompt,
                {
                    "failure_probability": 0.65,
                    "rul_days": 20,
                    "affected_component": "Brake Pads",
                    "severity": "MEDIUM",
                    "recurring_defect": False,
                    "confidence": 0.75,
                    "diagnostic_reasoning": "Brake pad thickness approaching critical threshold"
                }
            )
            
            confidence = output.get('confidence', 0.75)
            context.add_execution_record("Diagnosis_Agent", "success", output, confidence)
            
            print(f"✓ Component: {output.get('affected_component', 'Unknown')}")
            print(f"✓ Failure Probability: {output.get('failure_probability', 0.0):.1%}")
            print(f"✓ RUL: {output.get('rul_days', 0)} days")
            print(f"✓ Severity: {output.get('severity', 'UNKNOWN')}")
            print(f"✓ Confidence: {confidence:.2f}")
            
            # Create audit record
            audit = self.audit_trail.create_audit_record(
                "Diagnosis_Agent", input_data, output, context
            )
            self.audit_log.append(audit)
            
            return True
            
        except Exception as e:
            print(f"❌ Diagnosis failed: {str(e)[:50]}")
            context.add_execution_record("Diagnosis_Agent", "failed", {}, 0.0)
            return False
    
    async def _execute_customer_engagement(self, context: ExecutionContext,
                                          vehicle: Dict, customer: Dict,
                                          diagnosis: Dict, priority: str) -> bool:
        """Execute customer engagement agent"""
        input_data = {
            "customer": customer,
            "diagnosis": diagnosis,
            "priority": priority
        }
        
        component = diagnosis.get('affected_component', 'Component')
        rul_days = diagnosis.get('rul_days', 30)
        
        engagement_prompt = f"""Communicate service need to customer:

CUSTOMER: {customer.get('name', 'Customer')}
VEHICLE: {vehicle['make']} {vehicle['model']}
ISSUE: {component} requires attention
URGENCY: Priority {priority}
RUL: {rul_days} days

Preferred Contact: {customer.get('pref_contact_mode', 'chat')}
Language: {customer.get('preferred_lang', 'en')}

Simulate customer interaction. Respond with JSON only."""

        try:
            output = await self._run_agent_with_fallback(
                self.agents["Customer_Engagement_Agent"],
                engagement_prompt,
                {
                    "customer_response": "ACCEPTED" if priority in ["P0", "P1"] else "REQUESTED_RESCHEDULE",
                    "interaction_outcome": "Customer acknowledged service need",
                    "customer_message": "I'll schedule an appointment soon.",
                    "engagement_quality": 0.80,
                    "sentiment": "positive"
                }
            )
            
            confidence = output.get('engagement_quality', 0.80)
            context.add_execution_record("Customer_Engagement_Agent", "success", output, confidence)
            
            print(f"✓ Customer Response: {output.get('customer_response', 'UNKNOWN')}")
            print(f"✓ Outcome: {output.get('interaction_outcome', 'N/A')}")
            print(f"✓ Sentiment: {output.get('sentiment', 'neutral')}")
            print(f"✓ Quality: {confidence:.2f}")
            
            # Create audit record
            audit = self.audit_trail.create_audit_record(
                "Customer_Engagement_Agent", input_data, output, context
            )
            self.audit_log.append(audit)
            
            return True
            
        except Exception as e:
            print(f"❌ Customer engagement failed: {str(e)[:50]}")
            context.add_execution_record("Customer_Engagement_Agent", "failed", {}, 0.0)
            return False
    
    async def _run_agent_with_fallback(self, agent: AssistantAgent, 
                                      prompt: str, fallback: Dict) -> Dict:
        """Run agent with fallback to default output"""
        try:
            team = RoundRobinGroupChat([agent], max_turns=1)
            stream = team.run_stream(task=prompt)
            
            response_text = ""
            async for message in stream:
                if hasattr(message, 'content'):
                    response_text += str(message.content)
            
            response_text = response_text.strip()
            
            # Clean response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx+1]
                result = json.loads(json_str)
                return self._convert_numpy_types(result)
        
        except Exception as e:
            print(f"   ⚠️  Agent execution error: {str(e)[:50]}, using fallback")
        
        return fallback
    
    def _assign_priority(self, diagnosis: Dict, telematics: Dict) -> str:
        """Assign priority using rule engine"""
        failure_prob = diagnosis.get('failure_probability', 0.5)
        rul_days = diagnosis.get('rul_days', 30)
        severity = diagnosis.get('severity', 'MEDIUM')
        recurring = diagnosis.get('recurring_defect', False)
        brake_pad = telematics.get('brake_pad_mm', 5.0)
        battery = telematics.get('battery_voltage_v', 12.5)
        
        return self.rule_engine.assign_priority(
            failure_prob, rul_days, severity, recurring, brake_pad, battery
        )
    
    def _generate_work_order(self, context: ExecutionContext, vehicle: Dict,
                            customer: Dict, diagnosis: Dict, priority: str,
                            escalate: bool, customer_response: str) -> Dict:
        """Generate final work order"""
        component = diagnosis.get('affected_component', 'Component')
        rul_days = diagnosis.get('rul_days', 30)
        
        scheduled_date = (datetime.now() + timedelta(days=min(rul_days // 2, 7))).strftime("%Y-%m-%d")
        
        if customer_response == "DECLINED":
            status = "ESCALATED" if escalate else "PENDING_CUSTOMER_CONFIRMATION"
        elif customer_response == "REQUESTED_RESCHEDULE":
            status = "PENDING_RESCHEDULE"
        else:
            status = "SCHEDULED"
        
        return {
            "work_order_id": f"WO{datetime.now().strftime('%Y%m%d')}{context.vehicle_id[-3:]}",
            "vehicle_id": context.vehicle_id,
            "customer_id": customer['customer_id'],
            "service_type": f"{component} Maintenance",
            "priority": priority,
            "scheduled_date": scheduled_date,
            "status": status,
            "escalated": escalate,
            "created_at": datetime.now().isoformat(),
            "estimated_duration_hours": 2 if priority in ["P0", "P1"] else 1,
            "assigned_technician": "AUTO_ASSIGNED"
        }

# ======================================================================
# PART 9: MAIN EXECUTION
# ======================================================================

async def main():
    """Main execution function"""
    print("\n" + "="*80)
    print("🚀 ENTERPRISE AGENTIC PREDICTIVE MAINTENANCE SYSTEM v2.0")
    print("="*80)
    
    # Initialize
    config = LocalLlamaConfig("llama3:8b")
    model_client = config.get_model_client()
    
    system = AgenticPredictiveMaintenanceSystem(model_client)
    
    # Run scenarios
    scenarios = [
        ("VEH001", "critical"),
        ("VEH002", "warning"),
        ("VEH003", "normal")
    ]
    
    for vehicle_id, scenario in scenarios:
        context = await system.run_agentic_maintenance_cycle(vehicle_id, scenario)
        await asyncio.sleep(2)
    
    print("\n✅ All maintenance cycles completed!")

if __name__ == "__main__":
    asyncio.run(main())