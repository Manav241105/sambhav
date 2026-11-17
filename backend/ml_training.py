"""
ML Training Pipeline - v4.2
Trains predictive models on synthetic data
"""

import os
import numpy as np
import argparse
from typing import Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, mean_absolute_error
    from sklearn.preprocessing import StandardScaler
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("❌ ML libraries not installed!")
    print("Install with: pip install scikit-learn joblib")
    exit(1)


class SyntheticDataGenerator:
    """Generate synthetic training data"""
    
    @staticmethod
    def generate_failure_data(n_samples: int = 10000) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate synthetic data for failure prediction
        
        Returns:
            X: Features (telematics + history)
            y_class: Binary labels (0=no failure, 1=failure)
            y_reg: RUL in days
        """
        
        np.random.seed(42)
        
        # Features
        brake_pad = np.random.uniform(1.0, 8.0, n_samples)
        battery = np.random.uniform(10.5, 13.0, n_samples)
        coolant = np.random.uniform(85.0, 120.0, n_samples)
        oil_pressure = np.random.uniform(2.0, 4.5, n_samples)
        tire_pressure = np.random.uniform(28.0, 36.0, n_samples)
        odometer = np.random.uniform(10.0, 200.0, n_samples)  # In thousands
        maintenance_count = np.random.randint(0, 20, n_samples)
        
        # Derived features
        brake_critical = (brake_pad < 3.0).astype(float)
        battery_critical = (battery < 11.5).astype(float)
        coolant_critical = (coolant > 110.0).astype(float)
        
        # Combine features
        X = np.column_stack([
            brake_pad, battery, coolant, oil_pressure, tire_pressure,
            odometer, maintenance_count,
            brake_critical, battery_critical, coolant_critical
        ])
        
        # Generate labels based on features
        y_class = np.zeros(n_samples)
        y_reg = np.zeros(n_samples)
        
        for i in range(n_samples):
            # Failure probability based on conditions
            failure_score = 0
            
            if brake_pad[i] < 2.5:
                failure_score += 0.5
            elif brake_pad[i] < 3.5:
                failure_score += 0.3
            
            if battery[i] < 11.2:
                failure_score += 0.4
            elif battery[i] < 11.8:
                failure_score += 0.2
            
            if coolant[i] > 115:
                failure_score += 0.4
            elif coolant[i] > 105:
                failure_score += 0.2
            
            # Add some randomness
            failure_score += np.random.uniform(-0.1, 0.1)
            
            # Binary classification
            y_class[i] = 1 if failure_score > 0.5 else 0
            
            # RUL regression (days)
            if y_class[i] == 1:
                # Critical - short RUL
                y_reg[i] = max(1, int(brake_pad[i] * 5 + np.random.uniform(-5, 5)))
            else:
                # Normal - longer RUL
                y_reg[i] = max(10, int(brake_pad[i] * 10 + np.random.uniform(-10, 10)))
        
        return X, y_class, y_reg


class MLTrainer:
    """Train ML models"""
    
    def __init__(self, output_dir: str = "ml_models"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def train_failure_models(self, n_samples: int = 10000):
        """Train failure prediction models"""
        
        print("\n" + "="*80)
        print("🤖 TRAINING FAILURE PREDICTION MODELS")
        print("="*80)
        
        # Generate data
        print(f"\n📊 Generating {n_samples:,} synthetic samples...")
        X, y_class, y_reg = SyntheticDataGenerator.generate_failure_data(n_samples)
        
        # Split data
        X_train, X_test, y_class_train, y_class_test, y_reg_train, y_reg_test = train_test_split(
            X, y_class, y_reg, test_size=0.2, random_state=42
        )
        
        print(f"   ✓ Training samples: {len(X_train):,}")
        print(f"   ✓ Test samples: {len(X_test):,}")
        
        # Scale features
        print("\n🔧 Scaling features...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train classifier (failure probability)
        print("\n🌲 Training Failure Classifier (RandomForest)...")
        classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        classifier.fit(X_train_scaled, y_class_train)
        
        # Evaluate classifier
        y_pred_class = classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_class_test, y_pred_class)
        precision = precision_score(y_class_test, y_pred_class, zero_division=0)
        recall = recall_score(y_class_test, y_pred_class, zero_division=0)
        
        print(f"   ✅ Accuracy:  {accuracy:.3f}")
        print(f"   ✅ Precision: {precision:.3f}")
        print(f"   ✅ Recall:    {recall:.3f}")
        
        # Train regressor (RUL prediction)
        print("\n🌲 Training RUL Regressor (RandomForest)...")
        regressor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        regressor.fit(X_train_scaled, y_reg_train)
        
        # Evaluate regressor
        y_pred_reg = regressor.predict(X_test_scaled)
        mae = mean_absolute_error(y_reg_test, y_pred_reg)
        
        print(f"   ✅ Mean Absolute Error: {mae:.2f} days")
        
        # Save models
        print("\n💾 Saving models...")
        joblib.dump(classifier, os.path.join(self.output_dir, "failure_classifier.joblib"))
        joblib.dump(regressor, os.path.join(self.output_dir, "failure_regressor.joblib"))
        joblib.dump(scaler, os.path.join(self.output_dir, "scaler.joblib"))
        
        print(f"   ✅ Models saved to {self.output_dir}/")
        
        # Feature importance
        print("\n📊 Feature Importance (Top 5):")
        feature_names = [
            "brake_pad_mm", "battery_v", "coolant_c", "oil_bar", "tire_psi",
            "odo_km", "maint_count", "brake_crit", "battery_crit", "coolant_crit"
        ]
        importances = classifier.feature_importances_
        indices = np.argsort(importances)[::-1][:5]
        
        for i, idx in enumerate(indices, 1):
            print(f"   {i}. {feature_names[idx]}: {importances[idx]:.3f}")
        
        return {
            "classifier_accuracy": accuracy,
            "classifier_precision": precision,
            "classifier_recall": recall,
            "regressor_mae": mae
        }


def main():
    """Main training pipeline"""
    
    parser = argparse.ArgumentParser(description="Train ML models for predictive maintenance")
    parser.add_argument("--samples", type=int, default=10000, help="Number of training samples")
    parser.add_argument("--output", type=str, default="ml_models", help="Output directory")
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🚀 ML MODEL TRAINING PIPELINE v4.2")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"   Samples: {args.samples:,}")
    print(f"   Output:  {args.output}")
    
    # Check ML availability
    if not ML_AVAILABLE:
        print("\n❌ ML libraries not available!")
        return
    
    # Train models
    trainer = MLTrainer(args.output)
    metrics = trainer.train_failure_models(args.samples)
    
    # Summary
    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE")
    print("="*80)
    print(f"\n📊 Final Metrics:")
    print(f"   Classifier Accuracy:  {metrics['classifier_accuracy']:.3f}")
    print(f"   Classifier Precision: {metrics['classifier_precision']:.3f}")
    print(f"   Classifier Recall:    {metrics['classifier_recall']:.3f}")
    print(f"   Regressor MAE:        {metrics['regressor_mae']:.2f} days")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Models are saved in '{args.output}/' directory")
    print(f"   2. Run 'python main.py' to use ML-enhanced predictions")
    print(f"   3. System will automatically load models on startup\n")


if __name__ == "__main__":
    main()
