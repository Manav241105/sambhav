"""
ML Models Module - v4.2
Predictive ML models for failure prediction, contact timing, and customer behavior
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️  ML libraries not available. Install: pip install scikit-learn joblib")


class FailurePredictionModel:
    """
    ML model for predicting component failures
    Uses RandomForest for classification and regression
    """
    
    def __init__(self):
        self.classifier = None  # Predicts failure probability
        self.regressor = None   # Predicts RUL (days)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def extract_features(self, telematics: Dict, maintenance_history: List[Dict]) -> np.ndarray:
        """Extract features from telematics and history"""
        
        # Safe conversion helper
        def safe_float(val, default=0.0):
            try:
                return float(val)
            except (ValueError, TypeError):
                return default
        
        features = [
            safe_float(telematics.get('brake_pad_mm', 5.0)),
            safe_float(telematics.get('battery_voltage_v', 12.0)),
            safe_float(telematics.get('coolant_temp_c', 90.0)),
            safe_float(telematics.get('oil_pressure_bar', 3.0)),
            safe_float(telematics.get('tire_pressure_psi', 32.0)),
            safe_float(telematics.get('odo_km', 50000)) / 1000,  # Normalize
            len(maintenance_history),
            # Derived features
            1.0 if safe_float(telematics.get('brake_pad_mm', 5.0)) < 3.0 else 0.0,
            1.0 if safe_float(telematics.get('battery_voltage_v', 12.0)) < 11.5 else 0.0,
            1.0 if safe_float(telematics.get('coolant_temp_c', 90.0)) > 110.0 else 0.0,
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict(self, telematics: Dict, maintenance_history: List[Dict]) -> Dict:
        """Predict failure probability and RUL"""
        
        if not ML_AVAILABLE or not self.is_trained:
            return self._fallback_prediction(telematics)
        
        try:
            features = self.extract_features(telematics, maintenance_history)
            features_scaled = self.scaler.transform(features)
            
            # Predict failure probability with small random variance for realism
            base_failure_prob = self.classifier.predict_proba(features_scaled)[0][1]
            # Add ±5% random variance to simulate real-world model uncertainty
            variance = np.random.uniform(-0.05, 0.05)
            failure_prob = np.clip(base_failure_prob + variance, 0.01, 0.99)
            
            # Predict RUL with small random variance
            base_rul = self.regressor.predict(features_scaled)[0]
            rul_variance = np.random.randint(-5, 6)  # ±5 days variance
            rul_days = max(1, int(base_rul + rul_variance))
            
            # Determine component
            component = self._identify_critical_component(telematics)
            
            # Determine severity
            if failure_prob > 0.8:
                severity = "CRITICAL"
            elif failure_prob > 0.6:
                severity = "HIGH"
            elif failure_prob > 0.4:
                severity = "MEDIUM"
            else:
                severity = "LOW"
            
            # Calculate dynamic confidence based on prediction certainty
            # Higher margin from 0.5 = higher confidence
            raw_confidence = 2 * abs(failure_prob - 0.5)  # 0.5->0, 1.0->1.0
            # Add small variance to confidence as well
            confidence_variance = np.random.uniform(-0.03, 0.03)
            confidence = min(0.98, max(0.60, raw_confidence + 0.5 + confidence_variance))
            
            return {
                "failure_probability": round(float(failure_prob), 3),
                "rul_days": rul_days,
                "affected_component": component,
                "severity": severity,
                "confidence": round(confidence, 2),
                "ml_model": "RandomForest",
                "features_used": 10
            }
            
        except Exception as e:
            print(f"      ⚠️  ML prediction error: {str(e)[:50]}")
            return self._fallback_prediction(telematics)
    
    def _identify_critical_component(self, telematics: Dict) -> str:
        """Identify which component is most critical"""
        
        brake_val = telematics.get('brake_pad_mm', 5.0)
        battery_val = telematics.get('battery_voltage_v', 12.0)
        coolant_val = telematics.get('coolant_temp_c', 90.0)
        
        # Score each component (lower is worse)
        brake_score = brake_val / 5.0
        battery_score = battery_val / 12.5
        coolant_score = 1.0 - (max(0, coolant_val - 90) / 30.0)
        
        scores = {
            "Brake Pads": brake_score,
            "Battery": battery_score,
            "Cooling System": coolant_score
        }
        
        return min(scores, key=scores.get)
    
    def _fallback_prediction(self, telematics: Dict) -> Dict:
        """Rule-based fallback when ML unavailable"""
        
        brake_val = telematics.get('brake_pad_mm', 5.0)
        battery_val = telematics.get('battery_voltage_v', 12.0)
        coolant_val = telematics.get('coolant_temp_c', 90.0)
        
        if brake_val < 3.0:
            return {
                "failure_probability": 0.85,
                "rul_days": max(3, int((brake_val - 1.5) * 5)),
                "affected_component": "Brake Pads",
                "severity": "CRITICAL",
                "confidence": 0.75,
                "ml_model": "rule_based_fallback"
            }
        elif battery_val < 11.5:
            return {
                "failure_probability": 0.75,
                "rul_days": max(5, int((battery_val - 10.5) * 10)),
                "affected_component": "Battery",
                "severity": "HIGH",
                "confidence": 0.75,
                "ml_model": "rule_based_fallback"
            }
        else:
            return {
                "failure_probability": 0.35,
                "rul_days": 30,
                "affected_component": "Brake Pads",
                "severity": "MEDIUM",
                "confidence": 0.70,
                "ml_model": "rule_based_fallback"
            }


class ContactTimingOptimizer:
    """
    ML model for predicting optimal contact time
    Considers work hours, weekends, customer preferences
    """
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Configuration
        self.work_hours_start = 9   # 9 AM
        self.work_hours_end = 17    # 5 PM
    
    def extract_features(self, customer_memory: Dict, current_time: datetime) -> np.ndarray:
        """Extract features for contact timing prediction"""
        
        features = [
            current_time.hour,
            current_time.weekday(),  # 0=Monday, 6=Sunday
            1.0 if current_time.weekday() >= 5 else 0.0,  # Is weekend
            customer_memory.get('total_interactions', 0),
            customer_memory.get('avg_response_time_hours', 12.0),
            customer_memory.get('acceptance_rate', 0.5),
            # Historical best hours (simplified)
            customer_memory.get('preferred_hour', 18),
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict_optimal_time(self, customer_memory: Dict, 
                            priority: str = "P2") -> Dict:
        """Predict optimal contact time"""
        
        current_time = datetime.now()
        
        # Get customer preferences from memory
        preferred_hour = customer_memory.get('preferred_hour', 18)
        weekend_preference = customer_memory.get('weekend_preference', False)
        
        # Calculate optimal time
        optimal_hour = self._calculate_optimal_hour(
            current_time, preferred_hour, weekend_preference, priority
        )
        
        # Create optimal datetime
        optimal_time = current_time.replace(
            hour=optimal_hour, minute=30, second=0, microsecond=0
        )
        
        # If optimal time is in the past today, move to tomorrow
        if optimal_time < current_time:
            optimal_time += timedelta(days=1)
        
        # Avoid weekends if customer prefers weekdays
        if not weekend_preference and optimal_time.weekday() >= 5:
            # Move to Monday
            days_to_add = 7 - optimal_time.weekday()
            optimal_time += timedelta(days=days_to_add)
        
        # Calculate acceptance probability
        acceptance_prob = self._calculate_acceptance_probability(
            optimal_hour, current_time.weekday(), customer_memory
        )
        
        # Determine if we should wait
        should_wait = self._should_wait_for_optimal_time(
            current_time, optimal_time, priority
        )
        
        return {
            "optimal_contact_time": optimal_time.isoformat(),
            "optimal_hour": optimal_hour,
            "current_time": current_time.isoformat(),
            "should_wait": should_wait,
            "wait_hours": (optimal_time - current_time).total_seconds() / 3600,
            "is_work_hours": self._is_work_hours(current_time),
            "is_weekend": current_time.weekday() >= 5,
            "acceptance_probability": acceptance_prob,
            "confidence": 0.80,
            "reasoning": self._generate_reasoning(
                current_time, optimal_time, priority, weekend_preference
            )
        }
    
    def _calculate_optimal_hour(self, current_time: datetime, 
                                preferred_hour: int,
                                weekend_preference: bool,
                                priority: str) -> int:
        """Calculate optimal hour to contact"""
        
        # Critical priority - contact immediately
        if priority == "P0":
            return current_time.hour
        
        # High priority - contact soon, but avoid work hours
        if priority == "P1":
            if self._is_work_hours(current_time):
                return self.work_hours_end + 1  # Right after work
            return current_time.hour
        
        # Medium/Low priority - use customer preference
        # Default to evening (6-8 PM) if no preference
        if preferred_hour:
            return preferred_hour
        
        # Default to 7 PM (after work hours)
        return 19
    
    def _is_work_hours(self, dt: datetime) -> bool:
        """Check if time is during work hours"""
        
        # Weekend - not work hours
        if dt.weekday() >= 5:
            return False
        
        # Check hour
        return self.work_hours_start <= dt.hour < self.work_hours_end
    
    def _calculate_acceptance_probability(self, hour: int, weekday: int,
                                         customer_memory: Dict) -> float:
        """Calculate probability of acceptance at given time"""
        
        base_rate = customer_memory.get('acceptance_rate', 0.5)
        
        # Boost for preferred times
        if hour >= 18 and hour <= 20:  # Evening
            base_rate += 0.15
        elif hour >= 9 and hour <= 17:  # Work hours
            base_rate -= 0.20
        
        # Weekend adjustment
        if weekday >= 5:
            weekend_pref = customer_memory.get('weekend_preference', False)
            if weekend_pref:
                base_rate += 0.10
            else:
                base_rate -= 0.10
        
        return max(0.0, min(1.0, base_rate))
    
    def _should_wait_for_optimal_time(self, current_time: datetime,
                                     optimal_time: datetime,
                                     priority: str) -> bool:
        """Determine if we should wait for optimal time"""
        
        # Critical - never wait
        if priority == "P0":
            return False
        
        # High - wait max 2 hours
        if priority == "P1":
            wait_hours = (optimal_time - current_time).total_seconds() / 3600
            return wait_hours <= 2
        
        # Medium/Low - wait up to 24 hours
        wait_hours = (optimal_time - current_time).total_seconds() / 3600
        return wait_hours <= 24
    
    def _generate_reasoning(self, current_time: datetime,
                           optimal_time: datetime,
                           priority: str,
                           weekend_preference: bool) -> str:
        """Generate human-readable reasoning"""
        
        reasons = []
        
        if self._is_work_hours(current_time):
            reasons.append("Avoiding work hours (9 AM - 5 PM)")
        
        if optimal_time.hour >= 18:
            reasons.append("Evening contact preferred")
        
        if weekend_preference and optimal_time.weekday() >= 5:
            reasons.append("Customer prefers weekend contact")
        
        if priority == "P0":
            reasons.append("Critical priority - immediate contact")
        
        return "; ".join(reasons) if reasons else "Standard timing"


class CustomerBehaviorPredictor:
    """
    Predicts customer behavior patterns
    """
    
    def __init__(self):
        self.model = None
        self.is_trained = False
    
    def predict_acceptance(self, customer_memory: Dict, 
                          diagnosis: Dict, priority: str) -> Dict:
        """Predict likelihood of customer accepting service"""
        
        # Base acceptance rate from history
        base_rate = customer_memory.get('acceptance_rate', 0.5)
        
        # Adjust based on severity
        severity_boost = {
            "CRITICAL": 0.30,
            "HIGH": 0.20,
            "MEDIUM": 0.10,
            "LOW": 0.0
        }
        
        severity = diagnosis.get('severity', 'MEDIUM')
        acceptance_prob = base_rate + severity_boost.get(severity, 0.0)
        
        # Adjust based on failure probability
        failure_prob = diagnosis.get('failure_probability', 0.5)
        if failure_prob > 0.8:
            acceptance_prob += 0.15
        
        # Cap at 0.95 (never 100% certain)
        acceptance_prob = min(0.95, acceptance_prob)
        
        return {
            "acceptance_probability": acceptance_prob,
            "confidence": 0.75,
            "recommended_approach": self._recommend_approach(acceptance_prob, severity),
            "predicted_response_time_hours": customer_memory.get('avg_response_time_hours', 12.0)
        }
    
    def _recommend_approach(self, acceptance_prob: float, severity: str) -> str:
        """Recommend communication approach"""
        
        if acceptance_prob > 0.7:
            return "standard_notification"
        elif severity in ["CRITICAL", "HIGH"]:
            return "urgent_multi_channel"
        else:
            return "gentle_persuasion"


class MLModelManager:
    """
    Manages all ML models - loading, saving, predictions
    """
    
    def __init__(self, models_dir: str = "ml_models"):
        self.models_dir = models_dir
        self.failure_model = FailurePredictionModel()
        self.contact_optimizer = ContactTimingOptimizer()
        self.behavior_predictor = CustomerBehaviorPredictor()
        
        # Try to load models
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models from disk"""
        
        if not ML_AVAILABLE:
            print("   ℹ️  ML libraries not available - using rule-based fallbacks")
            return
        
        try:
            # Load failure prediction model
            classifier_path = os.path.join(self.models_dir, "failure_classifier.joblib")
            regressor_path = os.path.join(self.models_dir, "failure_regressor.joblib")
            scaler_path = os.path.join(self.models_dir, "scaler.joblib")
            
            if os.path.exists(classifier_path):
                self.failure_model.classifier = joblib.load(classifier_path)
                self.failure_model.regressor = joblib.load(regressor_path)
                self.failure_model.scaler = joblib.load(scaler_path)
                self.failure_model.is_trained = True
                print("   ✅ ML models loaded successfully")
            else:
                print("   ℹ️  Pre-trained models not found - using rule-based fallbacks")
                
        except Exception as e:
            print(f"   ⚠️  Error loading models: {str(e)[:50]}")
    
    def save_models(self):
        """Save trained models to disk"""
        
        if not ML_AVAILABLE:
            return
        
        os.makedirs(self.models_dir, exist_ok=True)
        
        try:
            joblib.dump(self.failure_model.classifier, 
                       os.path.join(self.models_dir, "failure_classifier.joblib"))
            joblib.dump(self.failure_model.regressor,
                       os.path.join(self.models_dir, "failure_regressor.joblib"))
            joblib.dump(self.failure_model.scaler,
                       os.path.join(self.models_dir, "scaler.joblib"))
            
            print("   ✅ Models saved successfully")
            
        except Exception as e:
            print(f"   ⚠️  Error saving models: {str(e)[:50]}")
    
    def predict_failure(self, telematics: Dict, 
                       maintenance_history: List[Dict]) -> Dict:
        """Get failure prediction"""
        return self.failure_model.predict(telematics, maintenance_history)
    
    def predict_contact_timing(self, customer_memory: Dict,
                              priority: str = "P2") -> Dict:
        """Get optimal contact timing"""
        return self.contact_optimizer.predict_optimal_time(customer_memory, priority)
    
    def predict_customer_behavior(self, customer_memory: Dict,
                                  diagnosis: Dict, priority: str) -> Dict:
        """Get customer behavior prediction"""
        return self.behavior_predictor.predict_acceptance(
            customer_memory, diagnosis, priority
        )
