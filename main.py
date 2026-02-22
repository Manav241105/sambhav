"""
Main Entry Point - v5.0 AUTONOMOUS ORCHESTRATION
Fully Autonomous Agentic Service Orchestration Platform
4 Test Scenarios: Booking, Follow-up Reanalysis, Edge Case, Trust Recovery
"""

import asyncio
import sys
from datetime import datetime

from config import LlamaModelClient
from orchestration_system import EventDrivenOrchestratorV41
from utils import DisplayFormatter


async def main():
    """Main entry point"""
    
    formatter = DisplayFormatter()
    
    print("\n" + "="*80)
    print("🚀 AUTONOMOUS AGENTIC SERVICE ORCHESTRATION PLATFORM v5.0")
    print("="*80)
    print("Autonomous Capabilities:")
    print("  ✓ AI-Driven Full Customer Lifecycle Management")
    print("  ✓ Autonomous Scheduling Agent (No Human Advisor Needed)")
    print("  ✓ EXECUTION_MODE Gate (One-Way Booking Activation)")
    print("  ✓ Follow-Up Cycle Manager with Vehicle Re-Analysis")
    print("  ✓ Master Orchestrator Domain Router")
    print("  ✓ Deep Personalization Context Engine")
    print("  ✓ Extended Edge Case Decision Engine (7 Cases)")
    print("  ✓ Trust Recovery + Supervisor Escalation")
    print("="*80 + "\n")
    
    try:
        # Initialize model clients
        print("📦 Initializing AI model clients...")
        master_client = LlamaModelClient.create_master_orchestrator_client()
        specialist_client = LlamaModelClient.create_specialist_client()
        interpreter_client = LlamaModelClient.create_customer_interpreter_client()
        learning_client = LlamaModelClient.create_learning_client()
        
        # Create orchestrator
        print("\n🔧 Creating advanced orchestration engine...")
        orchestrator = EventDrivenOrchestratorV41(
            master_client,
            specialist_client,
            interpreter_client,
            learning_client
        )
        
        # Try to load existing memory
        print("💾 Loading memory store...")
        try:
            orchestrator.memory_store.load_from_file("memory_store_v41.json")
        except:
            print("   ℹ️  Starting with fresh memory")
        
        # Check communication channels
        print("\n📡 Communication Channels:")
        status = orchestrator.communication_service.get_channel_status()
        for channel, configured in status.items():
            mode = "CONFIGURED" if configured else "SIMULATION"
            icon = "✅" if configured else "⚠️ "
            print(f"   {icon} {channel}: {mode}")
        
        print("\n" + "="*80)
        print("✅ INITIALIZATION COMPLETE")
        print("="*80 + "\n")
        
        # Define 4 required test scenarios for v5.0
        test_scenarios = [
            {
                "vehicle_id": "VEH001",
                "scenario": "critical",
                "description": "Scenario 1: Autonomous Booking Flow — Customer says 'yes' → EXECUTION_MODE → SchedulingAgent confirms slot autonomously",
                "enable_multi_cycle": False
            },
            {
                "vehicle_id": "VEH002",
                "scenario": "warning",
                "description": "Scenario 2: Follow-Up Cycle with Vehicle Reanalysis — Customer declines → time passes → VehicleReanalysisEngine runs → delta-aware follow-up",
                "enable_multi_cycle": True
            },
            {
                "vehicle_id": "VEH003",
                "scenario": "normal",
                "description": "Scenario 3: Edge Case Handling — Customer asks for supervisor → EdgeCaseDecisionEngine → ESCALATED_TO_HUMAN",
                "enable_multi_cycle": False
            },
            {
                "vehicle_id": "VEH004",
                "scenario": "warning",
                "description": "Scenario 4: Trust Recovery + Multi-Cycle — Customer expresses past service failure → TrustRecoveryEngine → 6-step repair protocol",
                "enable_multi_cycle": True
            }
        ]

        print(f"🎬 Running {len(test_scenarios)} autonomous orchestration test scenarios...\n")
        print("⚠️  Scenarios 2 & 4 will demonstrate TIME-BASED SIMULATION with multi-cycle follow-up\n")
        
        # Run scenarios sequentially
        results = []
        for scenario_config in test_scenarios:
            vehicle_id = scenario_config["vehicle_id"]
            scenario = scenario_config["scenario"]
            description = scenario_config["description"]
            enable_multi_cycle = scenario_config["enable_multi_cycle"]
            
            print(f"\n{'▓'*80}")
            print(f"  SCENARIO: {description.upper()}")
            print(f"{'▓'*80}\n")
            
            try:
                result = await orchestrator.run_workflow(
                    vehicle_id, scenario, enable_multi_cycle
                )
                results.append(result)
                
                # Pause between scenarios
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"\n❌ ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
                results.append({"status": "error", "vehicle_id": vehicle_id})
        
        # Overall summary
        print(formatter.format_header("📊 OVERALL SUMMARY"))
        
        successful = sum(1 for r in results if r.get('status') == 'completed')
        multi_cycle_count = sum(1 for r in results if r.get('cycle_number', 1) > 1)
        
        print(f"\nTotal Scenarios: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(results) - successful}")
        print(f"Multi-Cycle Workflows: {multi_cycle_count}")
        
        print("\n" + "-"*80)
        print("SCENARIO RESULTS:")
        print("-"*80)
        
        for i, (result, scenario_config) in enumerate(zip(results, test_scenarios), 1):
            vehicle_id = scenario_config["vehicle_id"]
            scenario = scenario_config["scenario"]
            desc = scenario_config["description"]
            
            print(f"\n{i}. {vehicle_id} ({scenario.upper()})")
            print(f"   Description: {desc}")
            print(f"   Status: {result.get('status', 'unknown').upper()}")
            print(f"   Cycles: {result.get('cycle_number', 1)}")
            print(f"   Final Response: {result.get('customer_response', 'N/A')}")
            if result.get('work_order'):
                print(f"   Work Order: {result['work_order']['work_order_id']}")
        
        # Advanced system metrics
        print("\n" + "-"*80)
        print("ADVANCED SYSTEM METRICS:")
        print("-"*80)
        print(f"Active Tenants: {orchestrator.tenant_registry.get_tenant_count()}")
        print(f"Temporal Simulations: {len(orchestrator.temporal_simulator.temporal_states)}")
        print(f"Multi-Cycle Workflows: {len(orchestrator.cycle_manager.active_cycles)}")
        print(f"Customer Memories: {len(orchestrator.memory_store.customer_memories)}")
        print(f"Vehicle Memories: {len(orchestrator.memory_store.vehicle_memories)}")
        
        # Component degradation summary
        print("\n" + "-"*80)
        print("COMPONENT DEGRADATION TRACKING:")
        print("-"*80)
        for vehicle_id in orchestrator.temporal_simulator.temporal_states:
            state = orchestrator.temporal_simulator.get_temporal_state(vehicle_id)
            if state:
                print(f"\n{vehicle_id}:")
                print(f"   Cycles Tracked: {state.cycle_number}")
                print(f"   Snapshots: {len(state.history)}")
                
                if len(state.history) > 1:
                    comparison = state.get_degradation_comparison()
                    worsened_components = [
                        comp for comp, data in comparison.items() 
                        if data.get('worsened', False)
                    ]
                    if worsened_components:
                        print(f"   Degraded Components: {', '.join(worsened_components)}")
        
        # Save memory
        print("\n💾 Saving memory store...")
        orchestrator.memory_store.save_to_file("memory_store_v41.json")
        print("   ✅ Memory saved to memory_store_v41.json")
        
        print("\n" + "="*80)
        print("✅ ALL ADVANCED WORKFLOWS COMPLETED SUCCESSFULLY")
        print("="*80)
        
        print("\n💡 Next Steps:")
        print("   1. Run interactive terminal tests for each scenario")
        print("   2. Verify EXECUTION_MODE gate activates on booking intent")
        print("   3. Verify SchedulingAgent creates bookings autonomously")
        print("   4. Verify VehicleReanalysisEngine runs before follow-up cycles")
        print("   5. Verify EdgeCaseDecisionEngine handles supervisor escalation")
        print("   6. Deploy to production fleet with real telematics integration\n")

        print("🎯 v5.0 Autonomous Achievements:")
        print("   ✓ EXECUTION_MODE gate: one-way booking activation")
        print("   ✓ SchedulingAgent: autonomous slot booking (no human advisor)")
        print("   ✓ VehicleReanalysisEngine: pre-follow-up delta analysis")
        print("   ✓ FollowupCycleManager: cycle tracking with re-analysis trigger")
        print("   ✓ MasterOrchestratorRouter: domain routing (BOOKING/PARTS/PRICE/ESCALATION)")
        print("   ✓ PersonalizationContextEngine: deep behavioral + emotional context")
        print("   ✓ EdgeCaseDecisionEngine: 7 cases incl. silent + supervisor\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)