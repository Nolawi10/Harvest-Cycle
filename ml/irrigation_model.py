"""
Smart Irrigation Decision Model
Multi-parameter irrigation decision system with rule-based and ML approaches
"""

import numpy as np
import sys
from pathlib import Path
import pickle
import logging
from datetime import datetime
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ml.utils import logger, get_time_of_day, validate_sensor_data, create_irrigation_dataset

class IrrigationDecisionEngine:
    """Smart irrigation decision system"""
    
    def __init__(self, model_type='rule_based'):
        """
        Initialize irrigation decision engine
        
        Args:
            model_type: 'rule_based', 'decision_tree', or 'random_forest'
        """
        self.model_type = model_type
        self.model = None
        self.is_trained = False
        self.feature_names = ['soil_moisture', 'temperature', 'humidity', 'time_of_day', 'weed_density']
        self.class_names = ['LOW', 'MEDIUM', 'HIGH']
        
        # Decision thresholds for rule-based system
        self.thresholds = {
            'low_moisture': 30,
            'high_temp': 28,
            'medium_moisture': 40,
            'low_humidity': 50,
            'high_weed_density': 5
        }
        
        logger.info(f"Initialized irrigation engine: {model_type}")
    
    def _rule_based_decision(self, soil_moisture, temperature, humidity, time_of_day, weed_density):
        """
        Rule-based irrigation decision
        
        Args:
            soil_moisture: 0-100%
            temperature: °C
            humidity: 0-100%
            time_of_day: morning/afternoon/night
            weed_density: weeds per unit area
        
        Returns:
            decision: irrigation level (0=LOW, 1=MEDIUM, 2=HIGH)
            reasoning: explanation of decision
        """
        reasoning = []
        decision = 0  # Default to LOW
        
        # Primary moisture and temperature rule
        if soil_moisture < self.thresholds['low_moisture'] and temperature > self.thresholds['high_temp']:
            decision = 2  # HIGH
            reasoning.append(f"Low moisture ({soil_moisture:.1f}%) + high temperature ({temperature:.1f}°C) → High irrigation")
        elif soil_moisture < self.thresholds['medium_moisture'] and humidity < self.thresholds['low_humidity']:
            decision = max(decision, 1)  # MEDIUM
            reasoning.append(f"Low moisture ({soil_moisture:.1f}%) + low humidity ({humidity:.1f}%) → Medium irrigation")
        
        # Time-based adjustments
        if time_of_day == "afternoon":
            reasoning.append("Afternoon heat - increasing irrigation")
            decision = min(decision + 1, 2)
        elif time_of_day == "night":
            reasoning.append("Night time - reducing irrigation")
            decision = max(decision - 1, 0)
        
        # Weed density adjustment
        if weed_density > self.thresholds['high_weed_density']:
            reasoning.append(f"High weed density ({weed_density:.1f}) - adjusting irrigation")
            decision = min(decision + 1, 2)
        
        # Ensure minimum irrigation for very dry soil
        if soil_moisture < 20:
            decision = 2
            reasoning.append("Very dry soil - High irrigation required")
        
        return decision, " | ".join(reasoning) if reasoning else "Normal conditions - Low irrigation"
    
    def train_ml_model(self, dataset_size=1000):
        """
        Train ML model (Decision Tree or Random Forest)
        
        Args:
            dataset_size: Size of synthetic dataset
        """
        logger.info(f"Training {self.model_type} model...")
        
        # Generate synthetic dataset
        X, y = create_irrigation_dataset(dataset_size)
        
        # Split dataset
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Choose model based on type
        if self.model_type == 'decision_tree':
            self.model = DecisionTreeClassifier(
                max_depth=5, 
                min_samples_split=10,
                random_state=42
            )
        elif self.model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=50,
                max_depth=5,
                min_samples_split=10,
                random_state=42
            )
        else:
            logger.error(f"Unknown model type: {self.model_type}")
            return False
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Model trained with accuracy: {accuracy:.3f}")
        logger.info("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=self.class_names))
        
        self.is_trained = True
        return True
    
    def predict_irrigation(self, soil_moisture, temperature, humidity, crop_type="general"):
        """
        Predict irrigation level
        
        Args:
            soil_moisture: 0-100%
            temperature: °C
            humidity: 0-100%
            crop_type: Type of crop (for future extension)
        
        Returns:
            dict: Complete irrigation decision with reasoning
        """
        # Validate input
        if not validate_sensor_data(soil_moisture, temperature, humidity):
            return {
                'error': 'Invalid sensor data',
                'soil_moisture': soil_moisture,
                'temperature': temperature,
                'humidity': humidity
            }
        
        # Get current time of day
        current_hour = datetime.now().hour
        time_of_day = get_time_of_day(current_hour)
        
        # Get weed density (would come from YOLO detection)
        weed_density = 0  # Default, will be updated from YOLO
        
        # Make decision
        if self.model_type == 'rule_based' or not self.is_trained:
            decision, reasoning = self._rule_based_decision(
                soil_moisture, temperature, humidity, time_of_day, weed_density
            )
        else:
            # Use ML model
            features = np.array([[soil_moisture, temperature, humidity, 
                              ['morning', 'afternoon', 'night'].index(time_of_day), 
                              weed_density]])
            decision = self.model.predict(features)[0]
            reasoning = f"ML model prediction based on current conditions"
        
        # Create result dictionary
        result = {
            'irrigation_level': self.class_names[decision],
            'irrigation_code': decision,  # 0=LOW, 1=MEDIUM, 2=HIGH
            'reasoning': reasoning,
            'sensor_data': {
                'soil_moisture': soil_moisture,
                'temperature': temperature,
                'humidity': humidity,
                'time_of_day': time_of_day,
                'weed_density': weed_density,
                'crop_type': crop_type
            },
            'timestamp': datetime.now().isoformat(),
            'model_type': self.model_type
        }
        
        return result
    
    def update_weed_density(self, weed_density):
        """
        Update weed density from YOLO detection
        
        Args:
            weed_density: Current weed density
        """
        # This would be called from the YOLO detection system
        logger.info(f"Updated weed density: {weed_density:.2f}")
    
    def save_model(self, filepath="models/irrigation_model.pkl"):
        """Save trained model"""
        if self.is_trained and self.model:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model, filepath)
            logger.info(f"Model saved to {filepath}")
            return True
        return False
    
    def load_model(self, filepath="models/irrigation_model.pkl"):
        """Load trained model"""
        if Path(filepath).exists():
            self.model = joblib.load(filepath)
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")
            return True
        return False
    
    def get_feature_importance(self):
        """Get feature importance from trained model"""
        if not self.is_trained or self.model is None:
            return None
        
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
            return dict(zip(self.feature_names, importance))
        return None
    
    def simulate_conditions(self, hours=24):
        """
        Simulate irrigation decisions over time
        
        Args:
            hours: Number of hours to simulate
        """
        logger.info(f"Simulating {hours} hours of irrigation decisions...")
        
        results = []
        base_time = datetime.now().replace(hour=0, minute=0, second=0)
        
        for hour in range(hours):
            # Simulate sensor data with daily patterns
            temp = 25 + 10 * np.sin(2 * np.pi * hour / 24) + np.random.normal(0, 2)
            humidity = 60 - 20 * np.sin(2 * np.pi * hour / 24) + np.random.normal(0, 5)
            soil_moisture = max(10, 50 - 0.5 * hour + np.random.normal(0, 5))
            
            # Get prediction
            prediction = self.predict_irrigation(soil_moisture, temp, humidity)
            
            results.append({
                'hour': hour,
                'time': base_time.replace(hour=hour).strftime('%H:%M'),
                'temperature': temp,
                'humidity': humidity,
                'soil_moisture': soil_moisture,
                'irrigation_level': prediction['irrigation_level'],
                'reasoning': prediction['reasoning']
            })
        
        return results

class SmartIrrigationController:
    """Complete irrigation control system"""
    
    def __init__(self, model_type='rule_based'):
        self.engine = IrrigationDecisionEngine(model_type)
        self.irrigation_history = []
        self.current_state = {
            'irrigation_active': False,
            'current_level': 'LOW',
            'last_change': datetime.now()
        }
    
    def update_sensors(self, soil_moisture, temperature, humidity):
        """Update sensor readings and make irrigation decision"""
        decision = self.engine.predict_irrigation(soil_moisture, temperature, humidity)
        
        # Update current state
        old_level = self.current_state['current_level']
        self.current_state['current_level'] = decision['irrigation_level']
        self.current_state['last_change'] = datetime.now()
        
        # Log decision
        log_entry = {
            'timestamp': decision['timestamp'],
            'old_level': old_level,
            'new_level': decision['irrigation_level'],
            'reasoning': decision['reasoning'],
            'sensor_data': decision['sensor_data']
        }
        self.irrigation_history.append(log_entry)
        
        # Control irrigation (simulated)
        self._control_irrigation(decision['irrigation_code'])
        
        return decision
    
    def _control_irrigation(self, irrigation_code):
        """Control physical irrigation system"""
        # This would interface with actual hardware
        if irrigation_code == 0:  # LOW
            self.current_state['irrigation_active'] = False
            logger.info("Irrigation: LOW (OFF)")
        elif irrigation_code == 1:  # MEDIUM
            self.current_state['irrigation_active'] = True
            logger.info("Irrigation: MEDIUM (50% flow)")
        elif irrigation_code == 2:  # HIGH
            self.current_state['irrigation_active'] = True
            logger.info("Irrigation: HIGH (100% flow)")
    
    def get_status(self):
        """Get current irrigation system status"""
        return {
            'current_state': self.current_state,
            'recent_decisions': self.irrigation_history[-5:],  # Last 5 decisions
            'model_type': self.engine.model_type,
            'total_decisions': len(self.irrigation_history)
        }

def main():
    """Main function for testing irrigation model"""
    logger.info("Smart Irrigation System Test")
    logger.info("=" * 40)
    
    # Test different model types
    for model_type in ['rule_based', 'decision_tree', 'random_forest']:
        logger.info(f"\nTesting {model_type} model:")
        
        # Initialize engine
        engine = IrrigationDecisionEngine(model_type)
        
        # Train ML models
        if model_type != 'rule_based':
            engine.train_ml_model(dataset_size=500)
        
        # Test with sample conditions
        test_conditions = [
            (25, 35, 40),  # Normal
            (20, 30, 30),  # Dry
            (15, 40, 25),  # Very dry, hot
            (60, 20, 80),  # Wet, cool
        ]
        
        for soil, temp, humid in test_conditions:
            result = engine.predict_irrigation(soil, temp, humid)
            logger.info(f"  Soil: {soil}%, Temp: {temp}°C, Humid: {humid}%")
            logger.info(f"  → {result['irrigation_level']}: {result['reasoning']}")
        
        # Save ML models
        if model_type != 'rule_based':
            engine.save_model(f"models/irrigation_{model_type}.pkl")
    
    # Test complete controller
    logger.info("\nTesting Smart Irrigation Controller:")
    controller = SmartIrrigationController('decision_tree')
    controller.engine.train_ml_model()
    
    # Simulate sensor updates
    for i in range(5):
        soil = 30 + np.random.normal(0, 10)
        temp = 25 + np.random.normal(0, 5)
        humid = 60 + np.random.normal(0, 10)
        
        decision = controller.update_sensors(soil, temp, humid)
        logger.info(f"Update {i+1}: {decision['irrigation_level']} - {decision['reasoning']}")

if __name__ == "__main__":
    main()
