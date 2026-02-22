"""
ENTERPRISE AUTONOMOUS PREDICTIVE MAINTENANCE SYSTEM
Architecture: Deterministic Rule Engine + LLM Advisory Agents
Compliance: Global System Contract (Non-Negotiable)
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import numpy as np
import pandas as pd

# AutoGen 0.7.5
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

# ======================================================================
# PART 1: OLLAMA LOCAL LLM CONFIGURATION
# ======================================================================

class LocalLlamaConfig:
    """Configuration for running Llama models locally via Ollama"""
    
    def __init__(self, model_name="llama3:8b"):
        self.model_name = model_name
    
    def get_model_client(self):
        """Get OpenAI-compatible client for Ollama"""
        print(f"🦙 Configuring {self.model_name} via Ollama...")
        
        client = OpenAIChatCompletionClient(
            model=self.model_name,
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model_capabilities={
                "vision": False,
                "function_calling": True,
                "json_output": True,
            }
        )
        
        print("✅ Local LLM configured successfully!")
        return client

# ======================================================================
# PART 2: DATA LAYER (SYNTHETIC DATA GENERATORS)
# ======================================================================

class DataGenerator:
    """Generate synthetic automotive data matching schema"""
    
    def generate_telematics_data(self, vehicle_id: str) -> Dict:
        """Generate current telematics snapshot"""
        return {
            "vehicle_id": vehicle_id,
            "timestamp": datetime.now().isoformat(),
            "mileage_km": int(np.random.randint(50_000, 150_000)),
            "engine_temp_c": round(float(np.random.uniform(85, 110)), 1),
            "oil_pressure_psi": round(float(np.random.uniform(25, 55)), 1),
            "brake_wear_percent": round(float(np.random.uniform(30, 95)), 1),
            "battery_voltage_v": round(float(np.random.uniform(11.5, 14.5)), 2),
            "coolant_level_percent": round(float(np.random.uniform(60, 100)), 1),
            "tire_pressure_fl_psi": round(float(np.random.uniform(28, 35)), 1),
            "tire_pressure_fr_psi": round(float(np.random.uniform(28, 35)), 1),
            "tire_pressure_rl_psi": round(float(np.random.uniform(28, 35)), 1),
            "tire_pressure_rr_psi": round(float(np.random.uniform(28, 35)), 1),
        }
    
    def generate_vehicle_metadata(self, vehicle_id: str) -> Dict:
        """Generate vehicle master data"""
        return {
            "vehicle_id": vehicle_id,
            "vin": f"VIN{vehicle_id[-3:]}2024",
            "make": "Tata",
            "model": np.random.choice(["Nexon EV", "Harrier", "Safari"]),
            "year": np.random.randint(2020, 2025),
            "age_months": np.random.randint(12, 60),
            "total_mileage_km": np.random.randint(50_000, 150_000),
            "customer_id": f"CUST{np.random.randint(1000, 9999)}",
        }
    
    def generate_maintenance_history(self, vehicle_id: str) -> List[Dict]:
        """Generate past maintenance records"""
        history = []
        for _ in range(np.random.randint(2, 6)):
            days_ago = np.random.randint(30, 800)
            history.append({
                "vehicle_id": vehicle_id,
                "date": (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
                "service_type": np.random.choice([
                    "Oil Change",
                    "Brake Service",
                    "Battery Replacement",
                    "Tire Rotation",
                    "Engine Diagnostics"
                ]),
                "cost_inr": int(np.random.randint(2000, 25000)),
                "mileage_at_service_km": int(np.random.randint(10_000, 140_000)),
            })
        return sorted(history, key=lambda x: x["date"], reverse=True)
    
    def generate_dtc_events(self, vehicle_id: str) -> List[Dict]:
        """Generate diagnostic trouble codes"""
        codes = []
        if np.random.random() < 0.3:  # 30% chance of having DTCs
            for code in np.random.choice(["P0420", "P0171", "P0300", "P0101"], 
                                         size=np.random.randint(1, 3), 
                                         replace=False):
                codes.append({
                    "vehicle_id": vehicle_id,
                    "dtc_code": code,
                    "timestamp": (datetime.now() - timedelta(days=np.random.randint(1, 30))).isoformat(),
                    "description": self._get_dtc_description(code)
                })
        return codes
    
    def _get_dtc_description(self, code: str) -> str:
        descriptions = {
            "P0420": "Catalyst System Efficiency Below Threshold",
            "P0171": "System Too Lean (Bank 1)",
            "P0300": "Random/Multiple Cylinder Misfire Detected",
            "P0101": "Mass Air Flow Circuit Range/Performance"
        }
        return descriptions.get(code, "Unknown DTC")
    
    def generate_rca_capa_records(self) -> List[Dict]:
        """Generate RCA/CAPA knowledge base"""
        return [
            {
                "rca_id": "RCA001",
                "component": "Brake Pads",
                "root_cause": "Supplier B material compound degrades prematurely in high-temp regions",
                "affected_models": ["Nexon EV", "Harrier"],
                "capa_action": "Switch to Supplier A material; retrofit existing vehicles",
                "defect_pattern": "Brake wear >80% before 30,000 km"
            },
            {
                "rca_id": "RCA002",
                "component": "Battery",
                "root_cause": "Poor sealing allows moisture ingress in hot/humid climates",
                "affected_models": ["Safari", "Harrier"],
                "capa_action": "Improved gasket design; inspection protocol for existing fleet",
                "defect_pattern": "Voltage drop <12.0V in vehicles <2 years old"
            },
            {
                "rca_id": "RCA003",
                "component": "Oxygen Sensor",
                "root_cause": "Sensor drift due to thermal cycling beyond design limits",
                "affected_models": ["Nexon EV"],
                "capa_action": "Updated sensor specification; extended warranty program",
                "defect_pattern": "P0420 DTC with <50,000 km"
            }
        ]
    
    def generate_ueba_baseline(self) -> Dict:
        """Generate UEBA baseline (no alerts for demo)"""
        return {
            "alert": False,
            "severity": "NONE",
            "message": "All agent behaviors within baseline parameters"
        }

# ======================================================================
# PART 3: DETERMINISTIC RULE ENGINE (FINAL DECISION AUTHORITY)
# ======================================================================

class RuleEngine:
    """
    Deterministic decision system - FINAL AUTHORITY
    Processes LLM agent recommendations and makes binding decisions
    """
    
    def assign_priority(self, failure_probability: float, rul_days: int, 
                       severity: str, recurring_defect: bool) -> str:
        """
        P0 = CRITICAL: Immediate safety risk or imminent failure
        P1 = HIGH: Failure likely within 7 days
        P2 = MEDIUM: Failure likely within 30 days
        P3 = LOW: Routine maintenance
        """
        if severity == "HIGH" or recurring_defect or rul_days <= 3:
            return "P0"
        elif failure_probability > 0.7 or rul_days <= 7:
            return "P1"
        elif failure_probability > 0.4 or rul_days <= 30:
            return "P2"
        else:
            return "P3"
    
    def determine_escalation(self, priority: str, customer_response: str) -> bool:
        """Decide if issue requires management escalation"""
        if priority in ["P0", "P1"]:
            return True
        if priority == "P2" and customer_response == "DECLINED":
            return True
        return False
    
    def approve_scheduling(self, priority: str, customer_response: str, 
                          ueba_alert: bool) -> bool:
        """Final approval for scheduling"""
        if ueba_alert:
            return False
        if customer_response != "ACCEPTED":
            return False
        if priority in ["P0", "P1", "P2"]:
            return True
        return False

# ======================================================================
# PART 4: AGENT DEFINITIONS (ADVISORY ONLY)
# ======================================================================

class AgentFactory:
    """Factory to create specialized advisory agents"""
    
    @staticmethod
    def create_master_agent(model_client) -> AssistantAgent:
        return AssistantAgent(
            name="Master_Agent",
            model_client=model_client,
            system_message="""MASTER AGENT — ORCHESTRATION & REASONING ONLY

YOU ARE: A planning and reasoning agent. You are NOT a decision-maker.

BUSINESS CONTEXT:
Indian automotive OEM predictive maintenance system.

YOU DO NOT:
- Assign priority (P0–P3)
- Decide escalation
- Schedule appointments
- Override UEBA
- Modify data

YOU ARE RESPONSIBLE FOR:
1. Maintaining holistic understanding of vehicle state
2. Interpreting analytical outputs from Worker Agents
3. Explaining WHY risks exist and WHAT actions may be needed
4. Proposing candidate execution steps (non-binding)
5. Detecting potential recurring defects

OUTPUT FORMAT — STRICT JSON:
{
  "risk_summary": "string",
  "key_observations": ["string"],
  "suggested_next_agents": ["agent_name"],
  "manufacturing_review_recommended": true|false,
  "replan_trigger_conditions": "string"
}

CRITICAL: Only output valid JSON. No markdown, no prose."""
        )
    
    @staticmethod
    def create_data_analysis_agent(model_client) -> AssistantAgent:
        return AssistantAgent(
            name="Data_Analysis_Agent",
            model_client=model_client,
            system_message="""DATA ANALYSIS AGENT

ROLE: Analyze telematics and maintenance history to detect degradation.

YOU MUST:
1. Detect abnormal trends
2. Compute normalized health indicators
3. Forecast service demand likelihood

YOU MUST NOT:
- Assign priority
- Predict component failures
- Contact customers
- Reference other agents

OUTPUT FORMAT — JSON ONLY:
{
  "health_score": 0.0,
  "detected_anomalies": ["string"],
  "service_demand_forecast": "LOW|MEDIUM|HIGH"
}"""
        )
    
    @staticmethod
    def create_diagnosis_agent(model_client) -> AssistantAgent:
        return AssistantAgent(
            name="Diagnosis_Agent",
            model_client=model_client,
            system_message="""DIAGNOSIS AGENT

ROLE: Provide probabilistic diagnostics and failure predictions.

YOU MUST:
1. Estimate component-level failure probability
2. Estimate Remaining Useful Life (RUL) in days
3. Determine technical severity
4. Identify recurring defect patterns

YOU MUST NOT:
- Assign priority
- Decide escalation
- Schedule services
- Reference other agents

OUTPUT FORMAT — JSON ONLY:
{
  "failure_probability": 0.0,
  "rul_days": 0,
  "affected_component": "string",
  "severity": "LOW|MEDIUM|HIGH",
  "recurring_defect": true|false
}"""
        )
    
    @staticmethod
    def create_customer_engagement_agent(model_client) -> AssistantAgent:
        return AssistantAgent(
            name="Customer_Engagement_Agent",
            model_client=model_client,
            system_message="""CUSTOMER ENGAGEMENT AGENT

ROLE: Explain predicted issues and capture customer intent.

YOU MUST:
1. Explain vehicle condition in simple, reassuring language
2. Recommend proactive service
3. Capture customer decision

YOU MUST NOT:
- Schedule appointments
- Decide urgency or priority
- Reference other agents

OUTPUT FORMAT — JSON ONLY:
{
  "customer_response": "ACCEPTED|DECLINED|REQUESTED_RESCHEDULE",
  "interaction_outcome": "string"
}"""
        )
    
    @staticmethod
    def create_manufacturing_insights_agent(model_client) -> AssistantAgent:
        return AssistantAgent(
            name="Manufacturing_Insights_Agent",
            model_client=model_client,
            system_message="""MANUFACTURING QUALITY INSIGHTS AGENT

ROLE: Generate RCA/CAPA-driven insights for manufacturing teams.

YOU MUST:
1. Correlate failures with known defect patterns
2. Summarize root causes
3. Recommend preventive/corrective actions

YOU MUST NOT:
- Contact customers
- Schedule services
- Reference other agents

OUTPUT FORMAT — JSON ONLY:
{
  "capa_reference": "string",
  "root_cause_summary": "string",
  "preventive_action": "string"
}"""
        )

# ======================================================================
# PART 5: ORCHESTRATION SYSTEM
# ======================================================================

class PredictiveMaintenanceSystem:
    """Main orchestration system combining Rule Engine + LLM Agents"""
    
    def __init__(self, model_client):
        self.model_client = model_client
        self.data_gen = DataGenerator()
        self.rule_engine = RuleEngine()
        self.setup_agents()
    
    def setup_agents(self):
        """Initialize all advisory agents"""
        factory = AgentFactory()
        self.master_agent = factory.create_master_agent(self.model_client)
        self.data_agent = factory.create_data_analysis_agent(self.model_client)
        self.diagnosis_agent = factory.create_diagnosis_agent(self.model_client)
        self.customer_agent = factory.create_customer_engagement_agent(self.model_client)
        self.mfg_agent = factory.create_manufacturing_insights_agent(self.model_client)
    
    async def run_maintenance_cycle(self, vehicle_id: str, customer_name: str):
        """Execute complete maintenance prediction cycle"""
        
        print("\n" + "="*70)
        print(f"🚗 PREDICTIVE MAINTENANCE CYCLE: {vehicle_id}")
        print(f"👤 Customer: {customer_name}")
        print("="*70 + "\n")
        
        # Step 1: Gather data
        print("📊 Step 1: Gathering vehicle data...")
        vehicle_data = self.data_gen.generate_vehicle_metadata(vehicle_id)
        telematics = self.data_gen.generate_telematics_data(vehicle_id)
        maintenance_history = self.data_gen.generate_maintenance_history(vehicle_id)
        dtc_events = self.data_gen.generate_dtc_events(vehicle_id)
        rca_capa = self.data_gen.generate_rca_capa_records()
        ueba_status = self.data_gen.generate_ueba_baseline()
        
        print(f"   ✓ Vehicle: {vehicle_data['make']} {vehicle_data['model']} ({vehicle_data['year']})")
        print(f"   ✓ Mileage: {telematics['mileage_km']:,} km")
        print(f"   ✓ DTCs: {len(dtc_events)} active codes")
        print(f"   ✓ UEBA: {ueba_status['message']}")
        
        # Step 2: Data Analysis (LLM Advisory)
        print("\n🔍 Step 2: Running data analysis agent...")
        data_context = self._build_data_analysis_context(telematics, maintenance_history)
        data_analysis = await self._run_agent_analysis(self.data_agent, data_context)
        
        # Step 3: Diagnosis (LLM Advisory)
        print("\n🩺 Step 3: Running diagnosis agent...")
        diagnosis_context = self._build_diagnosis_context(
            telematics, dtc_events, maintenance_history, rca_capa
        )
        diagnosis_result = await self._run_agent_analysis(self.diagnosis_agent, diagnosis_context)
        
        # Step 4: RULE ENGINE DECISION (Deterministic)
        print("\n⚖️  Step 4: Rule Engine processing (deterministic)...")
        priority = self.rule_engine.assign_priority(
            failure_probability=diagnosis_result.get("failure_probability", 0.5),
            rul_days=diagnosis_result.get("rul_days", 30),
            severity=diagnosis_result.get("severity", "MEDIUM"),
            recurring_defect=diagnosis_result.get("recurring_defect", False)
        )
        print(f"   ✓ PRIORITY ASSIGNED: {priority}")
        
        # Step 5: Customer Engagement (LLM Advisory)
        print("\n💬 Step 5: Running customer engagement agent...")
        customer_context = self._build_customer_context(
            vehicle_data, diagnosis_result, priority
        )
        customer_response = await self._run_agent_analysis(self.customer_agent, customer_context)
        
        # Step 6: RULE ENGINE DECISION (Escalation)
        print("\n⚖️  Step 6: Rule Engine determining escalation...")
        escalation_needed = self.rule_engine.determine_escalation(
            priority, customer_response.get("customer_response", "DECLINED")
        )
        print(f"   ✓ ESCALATION: {'YES' if escalation_needed else 'NO'}")
        
        # Step 7: Manufacturing Insights (if recurring defect)
        if diagnosis_result.get("recurring_defect", False):
            print("\n🏭 Step 7: Running manufacturing insights agent...")
            mfg_context = self._build_manufacturing_context(diagnosis_result, rca_capa)
            mfg_insights = await self._run_agent_analysis(self.mfg_agent, mfg_context)
        
        # Step 8: Final Summary
        print("\n" + "="*70)
        print("📋 FINAL MAINTENANCE RECOMMENDATION")
        print("="*70)
        print(f"Vehicle: {vehicle_id}")
        print(f"Component: {diagnosis_result.get('affected_component', 'Unknown')}")
        print(f"Priority: {priority}")
        print(f"Severity: {diagnosis_result.get('severity', 'UNKNOWN')}")
        print(f"RUL: {diagnosis_result.get('rul_days', 0)} days")
        print(f"Customer Response: {customer_response.get('customer_response', 'PENDING')}")
        print(f"Escalation Required: {'YES' if escalation_needed else 'NO'}")
        print("="*70 + "\n")
    
    def _build_data_analysis_context(self, telematics: Dict, history: List[Dict]) -> str:
        return f"""Analyze this vehicle data:

CURRENT TELEMATICS:
{json.dumps(telematics, indent=2)}

MAINTENANCE HISTORY (last 3 records):
{json.dumps(history[:3], indent=2)}

Provide health score and anomaly detection in JSON format only."""
    
    def _build_diagnosis_context(self, telematics: Dict, dtc: List[Dict], 
                                 history: List[Dict], rca: List[Dict]) -> str:
        return f"""Diagnose potential failures:

TELEMATICS:
{json.dumps(telematics, indent=2)}

DIAGNOSTIC CODES:
{json.dumps(dtc, indent=2)}

MAINTENANCE HISTORY:
{json.dumps(history[:3], indent=2)}

RCA/CAPA RECORDS:
{json.dumps(rca, indent=2)}

Provide failure prediction in JSON format only."""
    
    def _build_customer_context(self, vehicle: Dict, diagnosis: Dict, priority: str) -> str:
        return f"""Create customer communication:

VEHICLE: {vehicle['make']} {vehicle['model']}
ISSUE: {diagnosis.get('affected_component', 'Component')} needs attention
SEVERITY: {diagnosis.get('severity', 'MEDIUM')}
URGENCY: {priority}

Explain to customer in simple terms and capture their response in JSON."""
    
    def _build_manufacturing_context(self, diagnosis: Dict, rca: List[Dict]) -> str:
        return f"""Generate manufacturing insights:

DIAGNOSED ISSUE:
{json.dumps(diagnosis, indent=2)}

KNOWN RCA/CAPA:
{json.dumps(rca, indent=2)}

Provide quality insights in JSON format only."""
    
    async def _run_agent_analysis(self, agent: AssistantAgent, context: str) -> Dict:
        """Run single agent and extract JSON response"""
        try:
            # Create a simple chat to get response
            team = RoundRobinGroupChat([agent], max_turns=1)
            stream = team.run_stream(task=context)
            
            response_text = ""
            async for message in stream:
                if hasattr(message, 'content'):
                    response_text += str(message.content)
            
            # Try to extract JSON from response
            response_text = response_text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            return json.loads(response_text)
        except Exception as e:
            print(f"   ⚠️  Agent response parsing error: {e}")
            return {}

# ======================================================================
# PART 6: MAIN EXECUTION
# ======================================================================

async def main():
    print("\n" + "="*70)
    print("ENTERPRISE AUTONOMOUS PREDICTIVE MAINTENANCE SYSTEM")
    print("Architecture: Rule Engine + LLM Advisory Agents")
    print("="*70)
    
    # Initialize local LLM
    llama_config = LocalLlamaConfig(model_name="llama3:8b")
    model_client = llama_config.get_model_client()
    
    # Initialize system
    system = PredictiveMaintenanceSystem(model_client)
    
    # Run maintenance cycle
    await system.run_maintenance_cycle(
        vehicle_id="VEH001",
        customer_name="Rajesh Kumar"
    )
    
    print("✅ Maintenance cycle complete!")

if __name__ == "__main__":
    asyncio.run(main())