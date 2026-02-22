"""
Temporal Engine - v4.1
Handles time-based simulation, component degradation, and multi-cycle workflows
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import math


class ComponentDegradationModel:
    """Models how vehicle components degrade over time"""
    
    # Degradation rates per day for different components
    DEGRADATION_RATES = {
        "brake_pad_mm": {
            "normal": 0.05,      # 0.05mm per day normal wear
            "heavy_use": 0.15,   # 0.15mm per day heavy use
            "critical": 0.25     # 0.25mm per day when already critical
        },
        "battery_voltage_v": {
            "normal": 0.01,      # 0.01V per day normal drain
            "heavy_use": 0.03,   # 0.03V per day heavy use
            "critical": 0.05     # 0.05V per day when failing
        },
        "coolant_temp_c": {
            "normal": 0.5,       # 0.5°C per day normal increase
            "heavy_use": 1.5,    # 1.5°C per day heavy use
            "critical": 3.0      # 3.0°C per day when overheating
        },
        "oil_pressure_bar": {
            "normal": 0.02,      # 0.02 bar per day normal decrease
            "heavy_use": 0.05,   # 0.05 bar per day heavy use
            "critical": 0.1      # 0.1 bar per day when failing
        }
    }
    
    # Critical thresholds
    THRESHOLDS = {
        "brake_pad_mm": {"critical": 2.0, "warning": 3.0},
        "battery_voltage_v": {"critical": 11.5, "warning": 11.8},
        "coolant_temp_c": {"critical": 110, "warning": 105},
        "oil_pressure_bar": {"critical": 2.0, "warning": 2.5}
    }
    
    @staticmethod
    def calculate_degradation(component: str, current_value: float, 
                            days_elapsed: int, scenario: str = "normal") -> float:
        """Calculate component value after time has passed"""
        
        if component not in ComponentDegradationModel.DEGRADATION_RATES:
            return current_value
        
        rates = ComponentDegradationModel.DEGRADATION_RATES[component]
        thresholds = ComponentDegradationModel.THRESHOLDS[component]
        
        # Determine degradation rate based on current state
        if component == "brake_pad_mm" or component == "oil_pressure_bar":
            # Decreasing values
            if current_value <= thresholds["critical"]:
                rate = rates["critical"]
            elif current_value <= thresholds["warning"]:
                rate = rates["heavy_use"]
            else:
                rate = rates.get(scenario, rates["normal"])
            
            new_value = current_value - (rate * days_elapsed)
            return max(0.0, new_value)  # Can't go below 0
        
        else:
            # Increasing values (battery drain, coolant temp)
            if component == "battery_voltage_v":
                if current_value <= thresholds["critical"]:
                    rate = rates["critical"]
                elif current_value <= thresholds["warning"]:
                    rate = rates["heavy_use"]
                else:
                    rate = rates.get(scenario, rates["normal"])
                
                new_value = current_value - (rate * days_elapsed)
                return max(10.0, new_value)  # Battery minimum
            
            else:  # coolant_temp_c
                if current_value >= thresholds["critical"]:
                    rate = rates["critical"]
                elif current_value >= thresholds["warning"]:
                    rate = rates["heavy_use"]
                else:
                    rate = rates.get(scenario, rates["normal"])
                
                new_value = current_value + (rate * days_elapsed)
                return min(130.0, new_value)  # Coolant maximum
    
    @staticmethod
    def get_degradation_rate(component: str, current_value: float) -> str:
        """Get current degradation rate category"""
        
        if component not in ComponentDegradationModel.THRESHOLDS:
            return "normal"
        
        thresholds = ComponentDegradationModel.THRESHOLDS[component]
        
        if component == "brake_pad_mm" or component == "oil_pressure_bar":
            if current_value <= thresholds["critical"]:
                return "critical"
            elif current_value <= thresholds["warning"]:
                return "heavy_use"
        else:
            if current_value >= thresholds["critical"]:
                return "critical"
            elif current_value >= thresholds["warning"]:
                return "heavy_use"
        
        return "normal"


class TemporalState:
    """Tracks state changes over time for a vehicle"""
    
    def __init__(self, vehicle_id: str, initial_telematics: Dict):
        self.vehicle_id = vehicle_id
        self.cycle_number = 0
        self.history = []
        
        # Store initial state
        self.add_snapshot(initial_telematics, "Initial contact")
    
    def add_snapshot(self, telematics: Dict, event: str):
        """Add a temporal snapshot"""
        
        snapshot = {
            "cycle": self.cycle_number,
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "telematics": telematics.copy(),
            "degradation_rates": {
                component: ComponentDegradationModel.get_degradation_rate(
                    component, telematics.get(component, 0)
                )
                for component in ComponentDegradationModel.THRESHOLDS.keys()
                if component in telematics
            }
        }
        
        self.history.append(snapshot)
    
    def get_degradation_comparison(self) -> Dict:
        """Compare current state with initial state"""
        
        if len(self.history) < 2:
            return {}
        
        initial = self.history[0]["telematics"]
        current = self.history[-1]["telematics"]
        
        comparison = {}
        for component in ComponentDegradationModel.THRESHOLDS.keys():
            if component in initial and component in current:
                initial_val = initial[component]
                current_val = current[component]
                change = current_val - initial_val
                change_pct = (change / initial_val * 100) if initial_val != 0 else 0
                
                comparison[component] = {
                    "initial": initial_val,
                    "current": current_val,
                    "change": change,
                    "change_pct": change_pct,
                    "worsened": (change < 0 and component in ["brake_pad_mm", "oil_pressure_bar"]) or
                               (change > 0 and component in ["coolant_temp_c"]) or
                               (change < 0 and component == "battery_voltage_v")
                }
        
        return comparison
    
    def increment_cycle(self):
        """Move to next workflow cycle"""
        self.cycle_number += 1


class TemporalSimulator:
    """Simulates time passage and generates fresh telematics data"""
    
    def __init__(self):
        self.temporal_states = {}  # vehicle_id -> TemporalState
    
    def initialize_vehicle(self, vehicle_id: str, initial_telematics: Dict):
        """Initialize temporal tracking for a vehicle"""
        
        self.temporal_states[vehicle_id] = TemporalState(vehicle_id, initial_telematics)
    
    def simulate_time_passage(self, vehicle_id: str, days_elapsed: int,
                            scenario: str = "normal") -> Dict:
        """
        Simulate time passage and return fresh telematics data
        This is the core of time-based simulation
        """
        
        if vehicle_id not in self.temporal_states:
            raise ValueError(f"Vehicle {vehicle_id} not initialized")
        
        state = self.temporal_states[vehicle_id]
        previous_telematics = state.history[-1]["telematics"]
        
        # Generate new telematics based on degradation
        new_telematics = previous_telematics.copy()
        
        # Apply degradation to each component
        for component in ComponentDegradationModel.THRESHOLDS.keys():
            if component in new_telematics:
                new_telematics[component] = ComponentDegradationModel.calculate_degradation(
                    component,
                    previous_telematics[component],
                    days_elapsed,
                    scenario
                )
        
        # Add realistic noise (±5%)
        for key in new_telematics:
            if isinstance(new_telematics[key], (int, float)) and key != "odo_km":
                noise = random.uniform(-0.05, 0.05)
                new_telematics[key] *= (1 + noise)
        
        # Increase odometer
        daily_km = random.randint(30, 80)
        new_telematics["odo_km"] += daily_km * days_elapsed
        
        # Update timestamp
        new_telematics["timestamp"] = (
            datetime.now() + timedelta(days=days_elapsed)
        ).isoformat()
        
        # Record snapshot
        state.add_snapshot(new_telematics, f"Day +{days_elapsed} simulation")
        
        return new_telematics
    
    def get_temporal_state(self, vehicle_id: str) -> Optional[TemporalState]:
        """Get temporal state for a vehicle"""
        return self.temporal_states.get(vehicle_id)
    
    def should_escalate(self, vehicle_id: str) -> Dict:
        """Determine if condition has worsened enough to escalate"""
        
        if vehicle_id not in self.temporal_states:
            return {"escalate": False}
        
        state = self.temporal_states[vehicle_id]
        comparison = state.get_degradation_comparison()
        
        # Check for significant worsening
        escalation_reasons = []
        
        for component, data in comparison.items():
            if data["worsened"]:
                # Check if crossed critical threshold
                thresholds = ComponentDegradationModel.THRESHOLDS[component]
                
                if component in ["brake_pad_mm", "oil_pressure_bar"]:
                    if data["current"] <= thresholds["critical"]:
                        escalation_reasons.append(
                            f"{component}: Now CRITICAL ({data['current']:.2f})"
                        )
                else:
                    if data["current"] >= thresholds["critical"]:
                        escalation_reasons.append(
                            f"{component}: Now CRITICAL ({data['current']:.2f})"
                        )
        
        return {
            "escalate": len(escalation_reasons) > 0,
            "reasons": escalation_reasons,
            "comparison": comparison
        }


class MultiCycleWorkflowManager:
    """Manages multi-cycle workflows with time delays"""
    
    def __init__(self):
        self.active_cycles = {}  # vehicle_id -> cycle_info
    
    def start_cycle(self, vehicle_id: str, cycle_number: int,
                   customer_response: str, reason: str):
        """Start a new workflow cycle"""
        
        self.active_cycles[vehicle_id] = {
            "cycle_number": cycle_number,
            "started_at": datetime.now(),
            "trigger": customer_response,
            "reason": reason,
            "status": "IN_PROGRESS"
        }
    
    def complete_cycle(self, vehicle_id: str, outcome: str):
        """Complete current cycle"""
        
        if vehicle_id in self.active_cycles:
            self.active_cycles[vehicle_id]["status"] = "COMPLETED"
            self.active_cycles[vehicle_id]["outcome"] = outcome
            self.active_cycles[vehicle_id]["completed_at"] = datetime.now()
    
    def get_cycle_info(self, vehicle_id: str) -> Optional[Dict]:
        """Get current cycle information"""
        return self.active_cycles.get(vehicle_id)