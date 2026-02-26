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

    # ── 7-day telematics history (Phase 1) ────────────────────────────────────

    def generate_telematics_history(self, vehicle_id: str,
                                    scenario: str = "normal",
                                    days: int = 7) -> List[Dict]:
        """
        Generate *days* daily telematics snapshots with a realistic degradation
        curve.  Critical vehicles degrade faster; normal vehicles stay stable.

        Returns a list ordered from oldest → newest.
        """
        scenario_ranges = self.SCENARIOS.get(scenario, self.SCENARIOS["normal"])

        # Seed from vehicle_id so repeated calls produce the same curve
        seed = int("".join(c for c in vehicle_id if c.isdigit()) or "0") * 131
        rng = random.Random(seed)

        # Base values (start of the window)
        brake_base = rng.uniform(*scenario_ranges["brake_pad_mm"])
        batt_base = rng.uniform(*scenario_ranges["battery_voltage_v"])
        cool_base = rng.uniform(*scenario_ranges["coolant_temp_c"])
        oil_base = rng.uniform(*scenario_ranges["oil_pressure_bar"])

        # Per-day degradation rates
        degrade = {
            "normal":   {"brake": 0.01, "batt": 0.005, "cool": 0.1,  "oil": 0.005},
            "warning":  {"brake": 0.05, "batt": 0.02,  "cool": 0.3,  "oil": 0.015},
            "critical": {"brake": 0.12, "batt": 0.04,  "cool": 0.6,  "oil": 0.03},
        }.get(scenario, {"brake": 0.01, "batt": 0.005, "cool": 0.1, "oil": 0.005})

        vehicle_num = int(vehicle_id.replace("VEH", "").replace("VEH-", ""))
        base_odo = 50000 + (vehicle_num * 10000)

        history: List[Dict] = []
        now = datetime.now()

        for day_offset in range(days, 0, -1):
            ts = now - timedelta(days=day_offset)
            day_idx = days - day_offset  # 0 = oldest

            # Apply degradation with small random noise
            brake = max(0.5, brake_base - degrade["brake"] * day_idx + rng.gauss(0, 0.02))
            batt = max(10.5, batt_base - degrade["batt"] * day_idx + rng.gauss(0, 0.01))
            cool = cool_base + degrade["cool"] * day_idx + rng.gauss(0, 0.3)
            oil = max(1.0, oil_base - degrade["oil"] * day_idx + rng.gauss(0, 0.01))

            # Compute a simple health score for the day
            health = self._compute_health(brake, batt, cool, oil)

            history.append({
                "vehicle_id": vehicle_id,
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "day_label": ts.strftime("%a %d %b"),
                "odo_km": base_odo + rng.randint(0, 20000) + day_idx * rng.randint(30, 80),
                "brake_pad_mm": round(brake, 2),
                "battery_voltage_v": round(batt, 2),
                "coolant_temp_c": round(cool, 1),
                "oil_pressure_bar": round(oil, 2),
                "tire_pressure_psi": {
                    "fl": round(rng.uniform(30, 35), 1),
                    "fr": round(rng.uniform(30, 35), 1),
                    "rl": round(rng.uniform(30, 35), 1),
                    "rr": round(rng.uniform(30, 35), 1),
                },
                "engine_rpm": rng.randint(800, 3000),
                "speed_kmh": rng.randint(0, 80),
                "health_score": round(health, 2),
            })

        return history

    @staticmethod
    def _compute_health(brake: float, batt: float, cool: float, oil: float) -> float:
        """
        Simple deterministic health score in [0, 1] from the four core metrics.
        Thresholds aligned with DataAnalysisAgentV4 system message.
        """
        score = 1.0

        # Brake pads: <3mm critical, <5mm warning
        if brake < 3.0:
            score -= 0.35
        elif brake < 5.0:
            score -= 0.15

        # Battery: <11.5V critical, <11.8V warning
        if batt < 11.5:
            score -= 0.30
        elif batt < 11.8:
            score -= 0.12

        # Coolant: >110°C critical, >105°C warning
        if cool > 110:
            score -= 0.25
        elif cool > 105:
            score -= 0.10

        # Oil: <2.0 critical, <2.5 warning
        if oil < 2.0:
            score -= 0.20
        elif oil < 2.5:
            score -= 0.08

        return max(0.0, min(1.0, score))