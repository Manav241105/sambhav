"""
Event-Driven Orchestration Engine - v5.0 AUTONOMOUS ORCHESTRATION
Complete workflow engine with time-based simulation, multi-cycle workflows,
autonomous scheduling, follow-up reanalysis, and booking confirmation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

from config import EventTypes, SystemConfig
from event_system import EventBus, TenantRegistry, Event, EventLogger
from models import MemoryStore
from communication_service import CommunicationService
from customer_interpreter import CustomerResponseInterpreter, WebhookHandler
from learning_agent import LearningAgent
from master_orchestrator import MasterOrchestrator
from customer_engagement import CustomerEngagementAgentV4
from specialist_agents import AgentFactoryV4, AgentExecutor

# Import ML components (v4.2)
from ml_models import MLModelManager
from ml_contact_timing_agent import ContactTimingAgent

# Import temporal engine
from temporal_engine import (
    TemporalSimulator,
    MultiCycleWorkflowManager,
    ComponentDegradationModel
)

# Import from v3.0
from data_generator import VehicleDataGenerator
from rule_engine import MaintenanceRuleEngine
from utils import DisplayFormatter, DataConverter

# Import autonomous orchestration agents (v5.0)
from scheduling_agent import SchedulingAgent
from followup_cycle_manager import FollowupCycleManager
from vehicle_reanalysis_engine import VehicleReanalysisEngine


class EventDrivenOrchestratorV41:
    """
    Advanced event-driven orchestration with:
    - Time-based simulation
    - Multi-cycle workflows
    - Component degradation tracking
    - Smart escalation
    - Temporal state tracking
    """
    
    def __init__(self, master_client, specialist_client, 
                 interpreter_client, learning_client):
        
        # Core components
        self.event_bus = EventBus()
        self.tenant_registry = TenantRegistry()
        self.event_logger = EventLogger()
        self.memory_store = MemoryStore()
        
        # Services
        self.communication_service = CommunicationService()
        self.data_generator = VehicleDataGenerator()
        self.rule_engine = MaintenanceRuleEngine()
        self.formatter = DisplayFormatter()
        self.data_converter = DataConverter()
        
        # NEW: Temporal components
        self.temporal_simulator = TemporalSimulator()
        self.cycle_manager = MultiCycleWorkflowManager()
        
        # AI Agents
        self.master_orchestrator = MasterOrchestrator(
            master_client, self.event_bus
        )
        
        self.specialist_agents = AgentFactoryV4.create_all_agents(specialist_client)
        
        self.customer_engagement = CustomerEngagementAgentV4(
            specialist_client,
            self.memory_store,
            self.communication_service
        )
        
        self.interpreter = CustomerResponseInterpreter(interpreter_client)
        self.learning_agent = LearningAgent(learning_client, self.memory_store)
        self.webhook_handler = WebhookHandler(self.interpreter, self.event_bus)

        # Agent executor
        self.agent_executor = AgentExecutor()

        # ML Components (v4.2)
        print("🤖 Initializing ML models...")
        self.ml_manager = MLModelManager(SystemConfig.ML_MODELS_DIR)

        # Contact timing agent
        self.contact_timing_agent = ContactTimingAgent(
            specialist_client,
            self.memory_store,
            self.ml_manager.contact_optimizer
        )

        # Autonomous Orchestration Agents (v5.0)
        self.scheduling_agent = SchedulingAgent()
        self.followup_cycle_manager = FollowupCycleManager()
        self.vehicle_reanalysis_engine = VehicleReanalysisEngine()
    
    async def run_workflow(self, vehicle_id: str, scenario: str = "normal",
                          enable_multi_cycle: bool = True) -> Dict:
        """Run complete workflow with multi-cycle support"""
        
        print(self.formatter.format_header(
            f"🤖 ADVANCED EVENT-DRIVEN MAINTENANCE CYCLE v4.1\n"
            f"Vehicle ID: {vehicle_id} | Scenario: {scenario.upper()}\n"
            f"Features: Time Simulation | Multi-Cycle | Smart Escalation"
        ))
        
        # Register tenant
        tenant_state = self.tenant_registry.register_tenant(vehicle_id)
        
        # CYCLE 1: Initial Contact
        print(self.formatter.format_subheader("🔄 CYCLE 1: Initial Contact"))
        
        result = await self._run_single_cycle(
            vehicle_id, scenario, tenant_state, cycle_number=1
        )
        
        if not enable_multi_cycle:
            return result
        
        # Check if multi-cycle needed
        if result.get('customer_response') == "DECLINED":
            
            # SIMULATE TIME PASSAGE
            days_elapsed = 2
            print(f"\n{'⏰'*40}")
            print(f"⏰ TIME SIMULATION: {days_elapsed} DAYS PASS")
            print(f"{'⏰'*40}\n")
            
            await asyncio.sleep(1)  # Dramatic pause
            
            # Generate fresh telematics data
            new_telematics = self.temporal_simulator.simulate_time_passage(
                vehicle_id, days_elapsed, scenario
            )
            
            # Show degradation
            self._display_degradation(vehicle_id, days_elapsed)
            
            # Check if should escalate
            escalation = self.temporal_simulator.should_escalate(vehicle_id)
            
            if escalation["escalate"]:
                print(f"\n{'🚨'*40}")
                print(f"🚨 CONDITION WORSENED - AUTO-ESCALATION TRIGGERED")
                print(f"{'🚨'*40}")
                for reason in escalation["reasons"]:
                    print(f"   ⚠️  {reason}")
                print()
                
                # CYCLE 2: Re-contact with urgency
                print(self.formatter.format_subheader("🔄 CYCLE 2: Emergency Re-contact"))
                
                result = await self._run_single_cycle(
                    vehicle_id, scenario, tenant_state, 
                    cycle_number=2,
                    override_telematics=new_telematics,
                    escalated=True
                )
            else:
                # CYCLE 2: Standard follow-up
                print(self.formatter.format_subheader("🔄 CYCLE 2: Follow-up Contact"))
                
                result = await self._run_single_cycle(
                    vehicle_id, scenario, tenant_state,
                    cycle_number=2,
                    override_telematics=new_telematics
                )
        
        return result
    
    async def _run_single_cycle(self, vehicle_id: str, scenario: str,
                               tenant_state, cycle_number: int,
                               override_telematics: Optional[Dict] = None,
                               escalated: bool = False) -> Dict:
        """Run a single workflow cycle"""
        
        # Start cycle
        self.cycle_manager.start_cycle(
            vehicle_id, cycle_number,
            "Initial" if cycle_number == 1 else "Re-contact",
            "Escalated" if escalated else "Standard"
        )
        
        # PHASE 0: Data Gathering
        data_bundle = await self._phase_0_data_gathering(
            vehicle_id, scenario, tenant_state,
            override_telematics, cycle_number
        )
        
        if data_bundle is None:
            return {"status": "failed", "reason": "UEBA alert"}
        
        telematics, vehicle, maintenance_history, customer, ueba = data_bundle
        
        # PHASE 1: Planning (Fresh plan each cycle)
        plan = await self._phase_1_planning(
            tenant_state, telematics, vehicle, cycle_number, escalated
        )
        
        # PHASE 2: Workflow Execution (Re-execute all agents)
        diagnosis = await self._phase_2_workflow_execution(
            tenant_state, plan, telematics, maintenance_history, cycle_number
        )
        
        # PHASE 3: Customer Engagement
        customer_response = await self._phase_3_customer_engagement(
            tenant_state, vehicle, customer, diagnosis, telematics,
            cycle_number, escalated, maintenance_history
        )
        
        # PHASE 4: Check if replanning needed
        if customer_response.get('customer_response') == "DECLINED" and cycle_number == 1:
            # Will trigger next cycle
            self.cycle_manager.complete_cycle(vehicle_id, "DECLINED_PENDING_CYCLE_2")
            return customer_response
        
        # PHASE 5: Final Decision & Work Order
        work_order = await self._phase_5_final_decision(
            tenant_state, telematics, vehicle, customer, diagnosis,
            customer_response, cycle_number
        )
        
        # PHASE 6: Learning
        await self._phase_6_learning_and_summary(
            tenant_state, vehicle_id, customer['customer_id'],
            work_order, customer_response, cycle_number
        )
        
        # Complete cycle
        self.cycle_manager.complete_cycle(vehicle_id, "COMPLETED")
        
        return {
            "status": "completed",
            "vehicle_id": vehicle_id,
            "cycle_number": cycle_number,
            "work_order": work_order,
            "customer_response": customer_response.get('customer_response')
        }
    
    async def _phase_0_data_gathering(self, vehicle_id: str, scenario: str,
                                     tenant_state, override_telematics: Optional[Dict],
                                     cycle_number: int) -> tuple:
        """PHASE 0: Data Gathering with temporal support"""
        
        """PHASE 0: Data Gathering with temporal support"""
        
        # print header moved to single location

        
        if override_telematics:
            # Use fresh telematics from temporal simulation
            telematics = override_telematics
            print(self.formatter.format_metric("Data Source", "TEMPORAL SIMULATION (Fresh Data)"))
        else:
            # Initial data generation
            telematics = self.data_generator.generate_telematics_timeseries(vehicle_id, scenario)
            # Initialize temporal tracking
            self.temporal_simulator.initialize_vehicle(vehicle_id, telematics)
            print(self.formatter.format_metric("Data Source", "REAL-TIME TELEMATICS"))
        
        vehicle = self.data_generator.generate_vehicle_master(vehicle_id)
        maintenance_history = self.data_generator.generate_maintenance_history(vehicle_id)
        customer = self.data_generator.generate_customer_profile(vehicle["customer_id"])
        ueba = self.data_generator.generate_ueba_status()
        
        print(self.formatter.format_metric("Vehicle", f"{vehicle['make']} {vehicle['model']} ({vehicle['year']})"))
        print(self.formatter.format_metric("Customer", customer['name']))
        print(self.formatter.format_metric("Odometer", f"{telematics['odo_km']:,} km"))
        print(self.formatter.format_metric("Brake Pad", f"{telematics['brake_pad_mm']:.2f} mm"))
        print(self.formatter.format_metric("Battery", f"{telematics['battery_voltage_v']:.2f} V"))
        print(self.formatter.format_metric("Coolant", f"{telematics['coolant_temp_c']:.1f}°C"))
        
        if ueba.get("alert", False):
            print(self.formatter.format_warning(f"UEBA ALERT: {ueba.get('message')}"))
            return None
        
        return telematics, vehicle, maintenance_history, customer, ueba
    
    def _display_degradation(self, vehicle_id: str, days_elapsed: int):
        """Display component degradation comparison"""
        
        state = self.temporal_simulator.get_temporal_state(vehicle_id)
        if not state:
            return
        
        comparison = state.get_degradation_comparison()
        
        print(self.formatter.format_subheader(
            f"📉 COMPONENT DEGRADATION ANALYSIS ({days_elapsed} days)"
        ))
        
        for component, data in comparison.items():
            component_name = component.replace('_', ' ').title()
            
            initial = data['initial']
            current = data['current']
            change = data['change']
            worsened = data['worsened']
            
            status = "🔴 WORSENED" if worsened else "🟢 STABLE"
            
            print(f"\n{component_name}:")
            print(f"   Day 0: {initial:.2f}")
            print(f"   Day {days_elapsed}: {current:.2f}")
            print(f"   Change: {change:+.2f} ({data['change_pct']:+.1f}%)")
            print(f"   Status: {status}")
    
    async def _phase_1_planning(self, tenant_state, telematics: Dict,
                               vehicle: Dict, cycle_number: int,
                               escalated: bool = False) -> Dict:
        """PHASE 1: Master Orchestrator Planning"""
        
        print(self.formatter.format_subheader(
            f"🧠 PHASE 1: Planning - Cycle {cycle_number} "
            f"{'(ESCALATED)' if escalated else ''}"
        ))
        
        plan = await self.master_orchestrator.create_initial_plan(
            tenant_state, telematics, vehicle
        )
        
        # Override strategy if escalated
        if escalated:
            plan['strategy'] = 'expedited'
            plan['risk_level'] = 'critical'
        
        print(self.formatter.format_metric("Strategy", plan.get('strategy', 'standard').upper()))
        print(self.formatter.format_metric("Risk Level", plan.get('risk_level', 'unknown').upper()))
        print(self.formatter.format_metric("Cycle", cycle_number))
        
        return plan
    
    async def _phase_2_workflow_execution(self, tenant_state, plan: Dict,
                                         telematics: Dict,
                                         maintenance_history: List[Dict],
                                         cycle_number: int) -> Dict:
        """PHASE 2: Workflow Execution - Fresh analysis each cycle"""
        
        print(self.formatter.format_subheader(
            f"⚙️ PHASE 2: Workflow Execution (Cycle {cycle_number})"
        ))
        
        # ALWAYS re-execute agents with fresh data
        print(f"\n{'='*80}")
        print(f"STEP 1: Data_Analysis_Agent (Fresh Analysis)")
        print(f"{'='*80}")
        
        analysis_output = await self._execute_data_analysis(telematics, maintenance_history)
        print(f"✓ Fresh analysis completed")
        
        print(f"\n{'='*80}")
        print(f"STEP 2: Diagnosis_Agent (Fresh Diagnosis)")
        print(f"{'='*80}")
        
        diagnosis = await self._execute_diagnosis(telematics, maintenance_history)
        print(f"✓ Fresh diagnosis completed")
        
        return diagnosis
    
    async def _execute_data_analysis(self, telematics: Dict,
                                     maintenance_history: List[Dict]) -> Dict:
        """Execute data analysis agent"""
        
        prompt = f"""Analyze vehicle data:

TELEMATICS:
- Brake Pads: {telematics.get('brake_pad_mm'):.2f}mm
- Battery: {telematics.get('battery_voltage_v'):.2f}V
- Coolant: {telematics.get('coolant_temp_c'):.1f}°C
- Oil Pressure: {telematics.get('oil_pressure_bar', 3.0):.2f} bar
- Odometer: {telematics.get('odo_km'):,}km

MAINTENANCE HISTORY: {len(maintenance_history)} events

Provide health assessment. JSON only."""
        
        # Dynamic fallback based on readings
        brake_health = 0.9 if telematics.get('brake_pad_mm', 5) > 4 else 0.5
        battery_health = 0.9 if telematics.get('battery_voltage_v', 12) > 12 else 0.5
        overall_health = min(brake_health, battery_health)
        
        fallback = {
            "health_score": overall_health,
            "detected_anomalies": self._detect_anomalies(telematics),
            "service_demand_forecast": self._forecast_demand(telematics),
            "confidence": 0.75,
            "data_coverage": 0.95,
            "data_quality_notes": "Real-time data complete",
            "critical_alerts": self._get_critical_alerts(telematics),
            "trend_analysis": "Monitoring required"
        }
        
        output = await self.agent_executor.execute_agent(
            self.specialist_agents["Data_Analysis_Agent"],
            prompt,
            fallback
        )
        
        # Display output
        print(self.formatter.format_metric("Health Score", f"{output.get('health_score', 0.0):.2f}"))
        print(self.formatter.format_metric("Forecast", output.get('service_demand_forecast', 'UNKNOWN')))
        print(self.formatter.format_metric("Confidence", f"{output.get('confidence', 0.0):.2f}"))
        
        anomalies = output.get('detected_anomalies', [])
        if anomalies:
            print(self.formatter.format_warning(f"Anomalies: {', '.join(anomalies[:2])}"))
        
        return output
    
    def _detect_anomalies(self, telematics: Dict) -> List[str]:
        """Detect anomalies in telematics"""
        anomalies = []
        
        if telematics.get('brake_pad_mm', 5) < 3:
            anomalies.append("Critical brake wear")
        elif telematics.get('brake_pad_mm', 5) < 5:
            anomalies.append("Brake wear detected")
        
        if telematics.get('battery_voltage_v', 12) < 11.5:
            anomalies.append("Critical battery drain")
        elif telematics.get('battery_voltage_v', 12) < 11.8:
            anomalies.append("Battery degradation")
        
        if telematics.get('coolant_temp_c', 90) > 110:
            anomalies.append("Critical overheating")
        elif telematics.get('coolant_temp_c', 90) > 105:
            anomalies.append("Elevated coolant temperature")
        
        return anomalies or ["Normal operation"]
    
    def _forecast_demand(self, telematics: Dict) -> str:
        """Forecast service demand"""
        critical_count = 0
        
        if telematics.get('brake_pad_mm', 5) < 3:
            critical_count += 1
        if telematics.get('battery_voltage_v', 12) < 11.5:
            critical_count += 1
        if telematics.get('coolant_temp_c', 90) > 110:
            critical_count += 1
        
        if critical_count >= 2:
            return "CRITICAL"
        elif critical_count == 1:
            return "HIGH"
        
        warning_count = 0
        if telematics.get('brake_pad_mm', 5) < 5:
            warning_count += 1
        if telematics.get('battery_voltage_v', 12) < 11.8:
            warning_count += 1
        
        if warning_count >= 1:
            return "MEDIUM"
        
        return "LOW"
    
    def _get_critical_alerts(self, telematics: Dict) -> List[str]:
        """Get critical alerts"""
        alerts = []
        
        if telematics.get('brake_pad_mm', 5) < 2:
            alerts.append("IMMEDIATE brake replacement required")
        if telematics.get('battery_voltage_v', 12) < 11.2:
            alerts.append("Battery failure imminent")
        if telematics.get('coolant_temp_c', 90) > 115:
            alerts.append("Engine damage risk")
        
        return alerts
    
    async def _execute_diagnosis(self, telematics: Dict,
                                 maintenance_history: List[Dict]) -> Dict:
        """Execute diagnosis agent"""
        
        prompt = f"""Diagnose failures:

READINGS:
- Brake Pads: {telematics.get('brake_pad_mm'):.2f}mm (Critical: <3mm)
- Battery: {telematics.get('battery_voltage_v'):.2f}V (Critical: <11.5V)
- Coolant: {telematics.get('coolant_temp_c'):.1f}°C (Critical: >110°C)
- Mileage: {telematics.get('odo_km'):,}km

HISTORY: {len(maintenance_history)} events

Predict failures. JSON only."""
        
        # Dynamic fallback
        brake_val = telematics.get('brake_pad_mm', 5)
        battery_val = telematics.get('battery_voltage_v', 12)
        coolant_val = telematics.get('coolant_temp_c', 90)
        
        if brake_val < 3:
            component = "Brake Pads"
            failure_prob = 0.85
            rul = max(3, int((brake_val - 1.5) * 5))
            severity = "CRITICAL"
        elif battery_val < 11.5:
            component = "Battery"
            failure_prob = 0.80
            rul = max(5, int((battery_val - 10.5) * 10))
            severity = "HIGH"
        elif coolant_val > 110:
            component = "Cooling System"
            failure_prob = 0.75
            rul = max(7, int((120 - coolant_val) * 2))
            severity = "HIGH"
        else:
            component = "Brake Pads"
            failure_prob = 0.40
            rul = max(20, int(brake_val * 10))
            severity = "MEDIUM"
        
        fallback = {
            "failure_probability": failure_prob,
            "rul_days": rul,
            "affected_component": component,
            "severity": severity,
            "recurring_defect": False,
            "confidence": 0.80,
            "diagnostic_reasoning": f"{component} approaching critical threshold",
            "recommended_action": f"Replace {component}",
            "failure_mode": "Gradual degradation",
            "secondary_risks": []
        }
        
        # Get ML prediction if enabled
        ml_prediction = None
        if SystemConfig.ML_ENABLE_PREDICTIONS:
            ml_prediction = self.ml_manager.predict_failure(telematics, maintenance_history)
            print(f"\n🤖 ML PREDICTION:")
            print(self.formatter.format_metric("  ML Model", ml_prediction.get('ml_model', 'N/A')))
            print(self.formatter.format_metric("  Failure Prob", f"{ml_prediction.get('failure_probability', 0.0):.1%}"))
            print(self.formatter.format_metric("  RUL", f"{ml_prediction.get('rul_days', 0)} days"))
            print(self.formatter.format_metric("  Confidence", f"{ml_prediction.get('confidence', 0.0):.2f}"))
        
        output = await self.agent_executor.execute_agent(
            self.specialist_agents["Diagnosis_Agent"],
            prompt,
            fallback
        )
        
        # Merge ML prediction if available and agent used fallback
        if ml_prediction and output.get('ml_model') != 'rule_based_fallback':
            # Agent provided good output, optionally blend with ML
            pass
        elif ml_prediction:
            # Use ML prediction
            output = ml_prediction
        
        # Display output
        print(f"\n✓ FINAL DIAGNOSIS:")
        print(self.formatter.format_metric("Component", output.get('affected_component', 'Unknown')))
        print(self.formatter.format_metric("Failure Prob", f"{output.get('failure_probability', 0.0):.1%}"))
        print(self.formatter.format_metric("RUL", f"{output.get('rul_days', 0)} days"))
        print(self.formatter.format_metric("Severity", output.get('severity', 'UNKNOWN')))
        
        return output
    
    async def _phase_3_customer_engagement(self, tenant_state, vehicle: Dict,
                                          customer: Dict, diagnosis: Dict,
                                          telematics: Dict, cycle_number: int,
                                          escalated: bool = False,
                                          maintenance_history: list = None) -> Dict:
        """PHASE 3: Customer Engagement"""
        
        print(self.formatter.format_subheader(
            f"📧 PHASE 3: Customer Engagement (Cycle {cycle_number})"
        ))
        
        # Determine priority
        priority = self._assign_priority(diagnosis, telematics)
        
        # Override priority if escalated
        if escalated:
            priority = "P0"
        
        # Get optimal contact timing (v4.2)
        if SystemConfig.ML_ENABLE_PREDICTIONS:
            print(f"\n{'='*80}")
            print(f"STEP: Contact_Timing_Optimization")
            print(f"{'='*80}")
            
            timing_result = await self.contact_timing_agent.determine_optimal_timing(
                customer['customer_id'], priority, diagnosis
            )
            
            print(f"✓ Optimal Time: {timing_result.get('optimal_contact_time', 'N/A')}")
            print(f"✓ Should Wait: {timing_result.get('should_wait', False)}")
            print(f"✓ Reasoning: {timing_result.get('reasoning', 'N/A')[:60]}...")
            
            if timing_result.get('should_wait') and priority not in ["P0", "P1"]:
                print(f"   ℹ️  Optimal to wait {timing_result.get('wait_hours', 0):.1f} hours")
        
        print(f"\n{'='*80}")
        print(f"STEP: Customer_Engagement_Agent {'(ESCALATED)' if escalated else ''}")
        print(f"{'='*80}")
        
        # Get degradation info if multi-cycle
        degradation_info = None
        days_elapsed = 0
        reanalysis_result = None
        if cycle_number > 1:
            state = self.temporal_simulator.get_temporal_state(tenant_state.tenant_id)
            if state:
                degradation_info = state.get_degradation_comparison()
                days_elapsed = 2  # Default interval

            # ── v5.0: Run vehicle reanalysis before follow-up contact ──────────
            component = diagnosis.get('affected_component', 'Component')
            vehicle_id = tenant_state.tenant_id
            print(f"\n{'='*80}")
            print(f"STEP: Vehicle_Reanalysis_Engine (Pre-Follow-Up)")
            print(f"{'='*80}")
            reanalysis_result = self.vehicle_reanalysis_engine.run_reanalysis(
                vehicle_id, component, telematics, diagnosis
            )
            print(f"✓ Reanalysis complete: {reanalysis_result.condition_delta.upper()} "
                  f"({reanalysis_result.urgency_level})")
            print(f"✓ Tone directive: {reanalysis_result.tone_directive}")

        # Execute customer engagement
        result = await self.customer_engagement.engage_customer(
            tenant_id=tenant_state.tenant_id,
            customer_id=customer['customer_id'],
            customer_data=customer,
            diagnosis=diagnosis,
            priority=priority,
            vehicle=vehicle,
            cycle_number=cycle_number,
            escalated=escalated,
            days_elapsed=days_elapsed,
            degradation_info=degradation_info,
            maintenance_history=maintenance_history,
            telematics=telematics,
            reanalysis_result=reanalysis_result
        )
        
        # Simulate customer response
        import random
        
        if cycle_number == 1:
            # First cycle - may decline
            if priority == "P0":
                customer_response_type = "ACCEPTED"
            else:
                customer_response_type = random.choice(
                    ["ACCEPTED", "DECLINED", "REQUESTED_RESCHEDULE"]
                )
        else:
            # Second cycle - more likely to accept after escalation
            if escalated:
                customer_response_type = "ACCEPTED"  # Convinced by urgency
            else:
                customer_response_type = random.choice(
                    ["ACCEPTED", "REQUESTED_RESCHEDULE"]
                )
        
        response_time_hours = random.uniform(1.0, 24.0)
        
        print(f"✓ Channel Used: {result.get('channel_used', 'UNKNOWN')}")
        print(f"✓ Customer Response: {customer_response_type}")
        print(f"✓ Response Time: {response_time_hours:.1f}h")
        
        result['customer_response'] = customer_response_type
        result['response_time_hours'] = response_time_hours
        
        return result
    
    async def _phase_5_final_decision(self, tenant_state, telematics: Dict,
                                     vehicle: Dict, customer: Dict,
                                     diagnosis: Dict, customer_response: Dict,
                                     cycle_number: int) -> Dict:
        """PHASE 5: Final Decision & Work Order"""
        
        print(self.formatter.format_subheader(
            f"🎯 PHASE 5: Final Decision (Cycle {cycle_number})"
        ))
        
        priority = self._assign_priority(diagnosis, telematics)
        component = diagnosis.get('affected_component', 'Component')
        rul_days = diagnosis.get('rul_days', 30)
        failure_prob = diagnosis.get('failure_probability', 0.5)
        
        print(f"\n📋 MAINTENANCE RECOMMENDATION:")
        print(self.formatter.format_metric("  Component", component))
        print(self.formatter.format_metric("  Priority", priority))
        print(self.formatter.format_metric("  Failure Prob", f"{failure_prob:.1%}"))
        print(self.formatter.format_metric("  RUL", f"{rul_days} days"))
        print(self.formatter.format_metric("  Cycle", cycle_number))
        
        # Generate work order
        service_window = self.rule_engine.calculate_service_window(priority, rul_days)
        scheduled_date = (datetime.now() + timedelta(days=service_window)).strftime("%Y-%m-%d")
        
        work_order = {
            "work_order_id": f"WO{datetime.now().strftime('%Y%m%d')}{tenant_state.tenant_id[-3:]}",
            "vehicle_id": tenant_state.tenant_id,
            "customer_id": customer['customer_id'],
            "service_type": f"{component} Maintenance",
            "priority": priority,
            "scheduled_date": scheduled_date,
            "cycle_number": cycle_number,
            "status": "SCHEDULED",
            "created_at": datetime.now().isoformat()
        }
        
        print(f"\n📄 WORK ORDER: {work_order['work_order_id']}")
        print(self.formatter.format_metric("  Scheduled", scheduled_date))
        print(self.formatter.format_metric("  Status", "SCHEDULED"))
        
        return work_order
    
    async def _phase_6_learning_and_summary(self, tenant_state, vehicle_id: str,
                                           customer_id: str, work_order: Dict,
                                           customer_response: Dict, cycle_number: int):
        """PHASE 6: Learning & Summary"""
        
        print(self.formatter.format_subheader(
            f"🧠 PHASE 6: Learning (Cycle {cycle_number})"
        ))
        
        workflow_outcome = {
            "final_customer_response": customer_response.get('customer_response', 'ACCEPTED'),
            "communication_channel": customer_response.get('channel_used', 'EMAIL'),
            "response_time_hours": customer_response.get('response_time_hours', 24.0),
            "confidence_scores": [0.85, 0.90],
            "replanning_count": cycle_number - 1,
            "affected_component": "Brake Pads",
            "cycle_count": cycle_number
        }
        
        await self.learning_agent.update_memory(
            tenant_id=vehicle_id,
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            workflow_outcome=workflow_outcome
        )
        
        print(f"✓ Memory updated with cycle {cycle_number} data")
        
        if cycle_number > 1:
            print(f"✓ Multi-cycle workflow completed successfully")
    
    def _assign_priority(self, diagnosis: Dict, telematics: Dict) -> str:
        """Assign priority using rule engine"""
        failure_prob = self.data_converter.safe_float(diagnosis.get('failure_probability', 0.5))
        rul_days = self.data_converter.safe_int(diagnosis.get('rul_days', 30))
        severity = diagnosis.get('severity', 'MEDIUM')
        recurring = self.data_converter.safe_bool(diagnosis.get('recurring_defect', False))
        brake_pad = self.data_converter.safe_float(telematics.get('brake_pad_mm', 5.0))
        battery = self.data_converter.safe_float(telematics.get('battery_voltage_v', 12.5))
        coolant = self.data_converter.safe_float(telematics.get('coolant_temp_c', 90.0))
        
        return self.rule_engine.assign_priority(
            failure_prob, rul_days, severity, recurring, brake_pad, battery, coolant
        )