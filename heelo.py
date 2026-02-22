"""
Automotive Predictive Maintenance with Local Llama + AutoGen 0.7.5
No API required - runs completely offline!
"""

import json
from datetime import datetime, timedelta
import numpy as np
import asyncio

# ===================== AUTOGEN 0.7.5+ =====================
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

# LangChain imports removed - not needed for AutoGen 0.7.5

# ======================================================================
# PART 1: LOCAL LLAMA CONFIG
# ======================================================================

class LocalLlamaConfig:
    """Configuration for running Llama models locally"""

    def __init__(self, model_name="llama3:8b"):
        self.model_name = model_name

    def get_autogen_model_client(self):
        """Get model client for AutoGen 0.7.5"""
        print(f"🦙 Configuring {self.model_name}...")
        
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
        
        print("✅ Llama model configured successfully!")
        return client

# ======================================================================
# PART 2: SYNTHETIC VEHICLE DATA
# ======================================================================

class VehicleDataGenerator:
    def _generate_diagnostic_codes(self):
        """Helper to generate diagnostic codes"""
        codes_options = [
            [],
            ["P0420"],
            ["P0171"],
            ["P0300"]
        ]
        probabilities = [0.7, 0.1, 0.1, 0.1]
        idx = np.random.choice(len(codes_options), p=probabilities)
        return codes_options[idx]
    
    def generate_vehicle_data(self, vehicle_id="VEH001"):
        return {
            "vehicle_id": vehicle_id,
            "timestamp": datetime.now().isoformat(),
            "mileage": np.random.randint(50_000, 150_000),
            "engine_temp": round(np.random.uniform(85, 110), 1),
            "oil_pressure": round(np.random.uniform(25, 55), 1),
            "brake_wear_percent": round(np.random.uniform(30, 95), 1),
            "battery_voltage": round(np.random.uniform(11.0, 14.5), 2),
            "tire_pressure_fl": round(np.random.uniform(28, 35), 1),
            "tire_pressure_fr": round(np.random.uniform(28, 35), 1),
            "tire_pressure_rl": round(np.random.uniform(28, 35), 1),
            "tire_pressure_rr": round(np.random.uniform(28, 35), 1),
            "coolant_level": round(np.random.uniform(60, 100), 1),
            "diagnostic_codes": self._generate_diagnostic_codes(),
            "vehicle_age_months": np.random.randint(12, 120),
            "driving_style": np.random.choice(
                ["aggressive", "normal", "gentle"]
            ),
            "climate": np.random.choice(["hot", "moderate", "cold"]),
        }

    def generate_maintenance_history(self, vehicle_id="VEH001"):
        history = []
        for _ in range(np.random.randint(3, 8)):
            days_ago = np.random.randint(30, 1000)
            history.append(
                {
                    "date": (
                        datetime.now() - timedelta(days=days_ago)
                    ).strftime("%Y-%m-%d"),
                    "service_type": np.random.choice(
                        [
                            "Oil Change",
                            "Brake Service",
                            "Battery Replacement",
                            "Tire Rotation",
                            "Engine Diagnostics",
                        ]
                    ),
                    "cost": int(np.random.randint(500, 15000)),
                    "mileage_at_service": int(
                        np.random.randint(10_000, 140_000)
                    ),
                }
            )
        return sorted(history, key=lambda x: x["date"], reverse=True)

    def get_rca_capa_knowledge(self):
        return """
RCA/CAPA Knowledge Base:

1. BRAKE PAD DEFECT (RCA001)
   - Premature wear <30k km
   - Root cause: Supplier B material

2. BATTERY DEFECT (RCA002)
   - Voltage drop in hot climate
   - Root cause: Poor sealing

3. OXYGEN SENSOR (RCA003)
   - P0420 catalyst efficiency
   - Root cause: Heat drift
"""

# ======================================================================
# PART 3: AUTOGEN 0.7.5 MULTI-AGENT SYSTEM
# ======================================================================

class AutoGenMaintenanceSystem:
    def __init__(self, model_client):
        self.model_client = model_client
        self.data_generator = VehicleDataGenerator()
        self.setup_agents()

    def setup_agents(self):
        """Setup agents for AutoGen 0.7.5"""
        
        self.data_analyst = AssistantAgent(
            name="Data_Analyst",
            model_client=self.model_client,
            system_message="You are a vehicle data analyst. Analyze telemetry data and calculate overall vehicle health score (0-100). Focus on critical metrics like engine temp, oil pressure, brake wear, and battery voltage.",
        )

        self.diagnostician = AssistantAgent(
            name="Diagnostician",
            model_client=self.model_client,
            system_message="You are a diagnostic specialist. Based on the data analysis, predict potential component failures and their severity (LOW/MEDIUM/HIGH/CRITICAL). Explain which parts need attention.",
        )

        self.quality_analyst = AssistantAgent(
            name="Quality_Analyst",
            model_client=self.model_client,
            system_message="You are a quality engineer. Match identified failures with known RCA/CAPA records. Determine if this is a known defect pattern.",
        )

        self.customer_advisor = AssistantAgent(
            name="Customer_Advisor",
            model_client=self.model_client,
            system_message="You are a customer service advisor. Translate technical findings into simple, friendly language for the vehicle owner. Avoid jargon.",
        )

        self.scheduler = AssistantAgent(
            name="Scheduler",
            model_client=self.model_client,
            system_message="You are a service scheduler. Based on severity, recommend appointment timing (URGENT: within 3 days, SOON: within 2 weeks, ROUTINE: within 30 days).",
        )

    async def run_predictive_maintenance(self, vehicle_id, customer_name):
        """Run the predictive maintenance analysis"""
        
        vehicle_data = self.data_generator.generate_vehicle_data(vehicle_id)
        history = self.data_generator.generate_maintenance_history(vehicle_id)
        rca = self.data_generator.get_rca_capa_knowledge()

        context = f"""
VEHICLE PREDICTIVE MAINTENANCE REQUEST
Customer: {customer_name}
Vehicle ID: {vehicle_id}

=== CURRENT VEHICLE DATA ===
{json.dumps(vehicle_data, indent=2)}

=== MAINTENANCE HISTORY ===
{json.dumps(history, indent=2)}

=== RCA/CAPA KNOWLEDGE BASE ===
{rca}

TASK: Perform a comprehensive predictive maintenance analysis following this workflow:
1. Data_Analyst: Analyze the data and provide health score
2. Diagnostician: Identify potential failures and severity
3. Quality_Analyst: Match with RCA/CAPA records
4. Customer_Advisor: Create customer-friendly explanation
5. Scheduler: Recommend appointment timing

Each agent should provide clear, concise analysis in their domain.
"""

        # Create team with RoundRobin chat
        team = RoundRobinGroupChat(
            [
                self.data_analyst,
                self.diagnostician,
                self.quality_analyst,
                self.customer_advisor,
                self.scheduler,
            ],
            max_turns=10,
        )

        print("\n" + "="*70)
        print("🚗 STARTING PREDICTIVE MAINTENANCE ANALYSIS")
        print("="*70 + "\n")

        # Run the team
        stream = team.run_stream(task=context)
        
        async for message in stream:
            if hasattr(message, 'content'):
                print(f"\n[{message.source}]: {message.content}\n")
            print("-" * 70)

        print("\n" + "="*70)
        print("✅ ANALYSIS COMPLETE")
        print("="*70 + "\n")

# ======================================================================
# PART 4: MAIN
# ======================================================================

async def main():
    print("\n" + "="*70)
    print("AUTOMOTIVE PREDICTIVE MAINTENANCE (LOCAL LLM)")
    print("="*70)
    print("\n1. AutoGen 0.7.5 (Multi-agent)")
    print("2. LangGraph (Coming soon)")

    choice = input("\nEnter choice (1/2): ").strip()

    if choice == "1":
        print("\n🔧 Initializing AutoGen 0.7.5 system...")
        
        llama = LocalLlamaConfig()
        model_client = llama.get_autogen_model_client()
        
        system = AutoGenMaintenanceSystem(model_client)
        
        await system.run_predictive_maintenance(
            "VEH001", "Rajesh Kumar"
        )
    else:
        print("\n⏳ LangGraph implementation coming soon...")

if __name__ == "__main__":
    asyncio.run(main())