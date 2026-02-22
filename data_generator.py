"""
Enhanced Data Generator - v4.1
Supports time-based scenarios and realistic degradation
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List


class VehicleDataGenerator:
    """Generate realistic vehicle data with scenario support"""
    
    # Scenario configurations
    SCENARIOS = {
        "normal": {
            "brake_pad_mm": (4.0, 6.0),
            "battery_voltage_v": (12.0, 12.8),
            "coolant_temp_c": (85.0, 95.0),
            "oil_pressure_bar": (3.0, 4.0)
        },
        "warning": {
            "brake_pad_mm": (3.0, 4.5),
            "battery_voltage_v": (11.8, 12.0),
            "coolant_temp_c": (95.0, 105.0),
            "oil_pressure_bar": (2.5, 3.0)
        },
        "critical": {
            "brake_pad_mm": (1.5, 3.0),
            "battery_voltage_v": (11.2, 11.7),
            "coolant_temp_c": (105.0, 115.0),
            "oil_pressure_bar": (2.0, 2.5)
        }
    }
    
    def generate_telematics_timeseries(self, vehicle_id: str, 
                                      scenario: str = "normal") -> Dict:
        """Generate telematics data based on scenario"""
        
        scenario_ranges = self.SCENARIOS.get(scenario, self.SCENARIOS["normal"])
        
        # Generate random values within scenario ranges
        brake_pad = random.uniform(*scenario_ranges["brake_pad_mm"])
        battery = random.uniform(*scenario_ranges["battery_voltage_v"])
        coolant = random.uniform(*scenario_ranges["coolant_temp_c"])
        oil_pressure = random.uniform(*scenario_ranges["oil_pressure_bar"])
        
        # Base odometer on vehicle ID
        vehicle_num = int(vehicle_id.replace("VEH", "").replace("VEH-", ""))
        base_odo = 50000 + (vehicle_num * 10000)
        odometer = base_odo + random.randint(0, 20000)
        
        return {
            "vehicle_id": vehicle_id,
            "timestamp": datetime.now().isoformat(),
            "odo_km": odometer,
            "brake_pad_mm": round(brake_pad, 2),
            "battery_voltage_v": round(battery, 2),
            "coolant_temp_c": round(coolant, 1),
            "oil_pressure_bar": round(oil_pressure, 2),
            "tire_pressure_psi": {
                "fl": round(random.uniform(30, 35), 1),
                "fr": round(random.uniform(30, 35), 1),
                "rl": round(random.uniform(30, 35), 1),
                "rr": round(random.uniform(30, 35), 1)
            },
            "engine_rpm": random.randint(800, 3000),
            "speed_kmh": random.randint(0, 80)
        }
    
    def generate_vehicle_master(self, vehicle_id: str) -> Dict:
        """Generate vehicle master data"""
        
        vehicles = [
            {"make": "Toyota", "model": "Camry", "year": 2020},
            {"make": "Honda", "model": "Accord", "year": 2019},
            {"make": "Ford", "model": "F-150", "year": 2021},
            {"make": "Tesla", "model": "Model 3", "year": 2022},
            {"make": "BMW", "model": "X5", "year": 2020}
        ]
        
        vehicle_num = int(vehicle_id.replace("VEH", "").replace("VEH-", "")) % len(vehicles)
        vehicle_data = vehicles[vehicle_num]
        
        return {
            "vehicle_id": vehicle_id,
            "vin": f"1HGCM82633A{vehicle_id[-6:]}",
            "customer_id": f"CUST{vehicle_id[-3:]}",
            "make": vehicle_data["make"],
            "model": vehicle_data["model"],
            "year": vehicle_data["year"],
            "engine_type": "Gasoline" if vehicle_data["make"] != "Tesla" else "Electric",
            "transmission": "Automatic",
            "last_service_date": (datetime.now() - timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d")
        }
    
    def generate_maintenance_history(self, vehicle_id: str) -> List[Dict]:
        """Generate maintenance history"""
        
        history = []
        num_events = random.randint(3, 8)
        
        service_types = [
            "Oil Change",
            "Tire Rotation",
            "Brake Inspection",
            "Battery Check",
            "Filter Replacement",
            "Fluid Top-up"
        ]
        
        for i in range(num_events):
            days_ago = random.randint(30 + (i * 30), 60 + (i * 30))
            
            history.append({
                "service_id": f"SVC{vehicle_id[-3:]}{i:03d}",
                "vehicle_id": vehicle_id,
                "service_date": (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
                "service_type": random.choice(service_types),
                "mileage_km": random.randint(40000, 80000),
                "cost_usd": round(random.uniform(50, 500), 2),
                "parts_replaced": random.choice([[], ["Filter"], ["Brake Pads"], ["Battery"]]),
                "technician_notes": "Service completed successfully"
            })
        
        return sorted(history, key=lambda x: x["service_date"], reverse=True)
    
    def generate_customer_profile(self, customer_id: str) -> Dict:
        """Generate customer profile"""
        
        names = [
            "John Smith",
            "Sarah Johnson",
            "Michael Brown",
            "Emily Davis",
            "David Wilson"
        ]
        
        customer_num = int(customer_id.replace("CUST", "")) % len(names)
        
        return {
            "customer_id": customer_id,
            "name": names[customer_num],
            "email": f"{names[customer_num].lower().replace(' ', '.')}@email.com",
            "phone": f"+1-555-{random.randint(1000, 9999)}",
            "address": f"{random.randint(100, 999)} Main St, City, State",
            "preferred_contact_method": random.choice(["EMAIL", "SMS", "PHONE"]),
            "preferred_contact_time": random.choice(["MORNING", "AFTERNOON", "EVENING"]),
            "loyalty_tier": random.choice(["BRONZE", "SILVER", "GOLD"]),
            "total_vehicles": random.randint(1, 3),
            "customer_since": (datetime.now() - timedelta(days=random.randint(365, 1825))).strftime("%Y-%m-%d")
        }
    
    def generate_ueba_status(self) -> Dict:
        """Generate UEBA (User Entity Behavior Analytics) status"""
        
        # 95% normal, 5% alert
        has_alert = random.random() < 0.05
        
        if has_alert:
            alert_types = [
                "Unusual access pattern detected",
                "Potential fraudulent activity",
                "Multiple failed authentication attempts"
            ]
            
            return {
                "alert": True,
                "message": random.choice(alert_types),
                "risk_score": random.uniform(0.7, 0.95),
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "alert": False,
            "risk_score": random.uniform(0.0, 0.3),
            "timestamp": datetime.now().isoformat()
        }