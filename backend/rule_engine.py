"""
Rule Engine Module
Deterministic decision system for priority assignment and escalation
"""

from typing import Dict
from config import SystemConfig


class MaintenanceRuleEngine:
    """
    Deterministic rule-based decision system
    Ensures consistent, auditable decisions
    """
    
    def __init__(self):
        self.config = SystemConfig()
    
    def assign_priority(self, 
                       failure_probability: float,
                       rul_days: int,
                       severity: str,
                       recurring_defect: bool,
                       brake_pad_mm: float,
                       battery_voltage: float,
                       coolant_temp: float = None) -> str:
        """
        Assign maintenance priority based on multiple factors
        
        Priority Levels:
        - P0: Critical - Immediate action required (< 24 hours)
        - P1: High - Urgent attention needed (< 7 days)
        - P2: Medium - Schedule soon (< 30 days)
        - P3: Low - Routine maintenance
        
        Returns: Priority code (P0, P1, P2, P3)
        """
        
        # P0: Critical conditions
        if brake_pad_mm < self.config.CRITICAL_BRAKE_PAD_MM:
            return "P0"
        
        if battery_voltage < self.config.CRITICAL_BATTERY_VOLTAGE:
            return "P0"
        
        if coolant_temp and coolant_temp > self.config.CRITICAL_COOLANT_TEMP:
            return "P0"
        
        if severity == "HIGH" or severity == "CRITICAL":
            return "P0"
        
        if recurring_defect and severity == "MEDIUM":
            return "P0"
        
        if rul_days <= 3:
            return "P0"
        
        # P1: High priority
        if failure_probability > 0.7:
            return "P1"
        
        if rul_days <= 7:
            return "P1"
        
        if brake_pad_mm < 4.0:
            return "P1"
        
        if battery_voltage < 11.8:
            return "P1"
        
        # P2: Medium priority
        if failure_probability > 0.4:
            return "P2"
        
        if rul_days <= 30:
            return "P2"
        
        if brake_pad_mm < 6.0:
            return "P2"
        
        # P3: Low priority (routine)
        return "P3"
    
    def determine_escalation(self, 
                           priority: str,
                           customer_response: str,
                           recurring_defect: bool,
                           failure_probability: float = 0.0) -> bool:
        """
        Determine if case should be escalated to supervisor
        
        Escalation Criteria:
        - P0 priority (always escalate critical cases)
        - P1 priority with customer decline
        - Recurring defect with customer decline
        - High failure probability with customer decline
        
        Returns: Boolean indicating escalation requirement
        """
        
        # Always escalate critical priority
        if priority == "P0":
            return True
        
        # Escalate P1 declined cases
        if priority == "P1" and customer_response == "DECLINED":
            return True
        
        # Escalate recurring defects if declined
        if recurring_defect and customer_response == "DECLINED":
            return True
        
        # Escalate high failure probability if declined
        if failure_probability > 0.7 and customer_response == "DECLINED":
            return True
        
        return False
    
    def calculate_confidence_threshold(self, priority: str) -> float:
        """
        Get minimum confidence threshold for given priority
        Higher priority requires higher confidence
        
        Returns: Confidence threshold (0.0 - 1.0)
        """
        return self.config.CONFIDENCE_THRESHOLDS.get(priority, 0.60)
    
    def determine_service_urgency(self, priority: str, rul_days: int) -> str:
        """
        Determine urgency level for service scheduling
        
        Returns: Urgency level string
        """
        if priority == "P0":
            return "EMERGENCY"
        elif priority == "P1":
            return "URGENT"
        elif priority == "P2" and rul_days <= 14:
            return "SCHEDULED_SOON"
        else:
            return "ROUTINE"
    
    def calculate_service_window(self, priority: str, rul_days: int) -> int:
        """
        Calculate recommended service window in days
        
        Returns: Number of days until service should be completed
        """
        if priority == "P0":
            return min(1, rul_days // 4)
        elif priority == "P1":
            return min(7, rul_days // 2)
        elif priority == "P2":
            return min(30, rul_days // 2)
        else:
            return min(90, rul_days)
    
    def assess_risk_level(self,
                         failure_probability: float,
                         severity: str,
                         rul_days: int) -> str:
        """
        Assess overall risk level
        
        Returns: Risk level (CRITICAL, HIGH, MEDIUM, LOW)
        """
        if failure_probability > 0.8 or severity == "CRITICAL" or rul_days <= 3:
            return "CRITICAL"
        elif failure_probability > 0.6 or severity == "HIGH" or rul_days <= 7:
            return "HIGH"
        elif failure_probability > 0.3 or severity == "MEDIUM" or rul_days <= 30:
            return "MEDIUM"
        else:
            return "LOW"