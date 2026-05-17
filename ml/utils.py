"""
Utility functions for AI Agro Rover ML Systems
Common utilities for YOLO detection and irrigation model
"""

import cv2
import numpy as np
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Colors:
    """Color palette for visualization"""
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)
    YELLOW = (0, 255, 255)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

def draw_bbox(image, bbox, label, confidence, color=None):
    """
    Draw bounding box with label and confidence
    
    Args:
        image: Input image
        bbox: Bounding box coordinates [x1, y1, x2, y2]
        label: Class label
        confidence: Confidence score
        color: Box color (default based on class)
    """
    if color is None:
        color = Colors.GREEN if label == "crop" else Colors.RED
    
    x1, y1, x2, y2 = map(int, bbox)
    
    # Draw bounding box
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    
    # Draw label background
    label_text = f"{label}: {confidence:.2f}"
    label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
    cv2.rectangle(image, (x1, y1 - label_size[1] - 10), 
                (x1 + label_size[0], y1), color, -1)
    
    # Draw label text
    cv2.putText(image, label_text, (x1, y1 - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, Colors.WHITE, 2)

def calculate_fps(start_time, frame_count):
    """Calculate FPS based on start time and frame count"""
    elapsed = time.time() - start_time
    if elapsed > 0:
        return frame_count / elapsed
    return 0

def resize_frame(frame, target_size=(416, 416)):
    """Resize frame for YOLO processing"""
    return cv2.resize(frame, target_size)

def preprocess_frame(frame, target_size=(416, 416)):
    """Preprocess frame for YOLO inference"""
    # Resize
    resized = cv2.resize(frame, target_size)
    # Convert to RGB
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    # Normalize to 0-1
    normalized = rgb.astype(np.float32) / 255.0
    return normalized

def calculate_weed_density(detections, frame_area):
    """
    Calculate weed density from detections
    
    Args:
        detections: List of weed detections
        frame_area: Total frame area
    
    Returns:
        weed_density: Number of weeds per unit area
    """
    weed_count = sum(1 for det in detections if det['class'] == 'weed')
    density = weed_count / (frame_area / 10000)  # Per 100x100 area
    return density, weed_count

def get_time_of_day(hour):
    """Get time of day category from hour"""
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "night"

def validate_sensor_data(soil_moisture, temperature, humidity):
    """
    Validate sensor data ranges
    
    Args:
        soil_moisture: 0-100%
        temperature: -50 to 60°C
        humidity: 0-100%
    
    Returns:
        bool: True if data is valid
    """
    return (0 <= soil_moisture <= 100 and 
            -50 <= temperature <= 60 and 
            0 <= humidity <= 100)

def create_irrigation_dataset(size=1000):
    """
    Create synthetic irrigation dataset for training
    
    Returns:
        X: Feature matrix [soil_moisture, temperature, humidity, time_of_day, weed_density]
        y: Labels [0=LOW, 1=MEDIUM, 2=HIGH]
    """
    np.random.seed(42)
    
    # Generate realistic sensor data
    soil_moisture = np.random.uniform(10, 80, size)
    temperature = np.random.uniform(15, 40, size)
    humidity = np.random.uniform(20, 90, size)
    time_of_day = np.random.choice([0, 1, 2], size)  # 0=morning, 1=afternoon, 2=night
    weed_density = np.random.uniform(0, 10, size)
    
    # Create irrigation labels based on rules
    y = np.zeros(size, dtype=int)
    
    for i in range(size):
        # Rule-based irrigation decisions
        if soil_moisture[i] < 30 and temperature[i] > 28:
            y[i] = 2  # HIGH
        elif soil_moisture[i] < 40 and humidity[i] < 50:
            y[i] = 1  # MEDIUM
        else:
            y[i] = 0  # LOW
            
        # Adjust based on weed density
        if weed_density[i] > 5:
            y[i] = min(y[i] + 1, 2)  # Increase irrigation level
    
    X = np.column_stack([soil_moisture, temperature, humidity, time_of_day, weed_density])
    
    return X, y

class PerformanceMonitor:
    """Monitor ML model performance"""
    
    def __init__(self):
        self.frame_times = []
        self.detection_counts = []
        self.start_time = time.time()
    
    def add_frame_time(self, frame_time):
        self.frame_times.append(frame_time)
    
    def add_detection_count(self, count):
        self.detection_counts.append(count)
    
    def get_stats(self):
        if not self.frame_times:
            return {}
        
        return {
            'avg_frame_time': np.mean(self.frame_times),
            'fps': 1.0 / np.mean(self.frame_times) if np.mean(self.frame_times) > 0 else 0,
            'avg_detections': np.mean(self.detection_counts) if self.detection_counts else 0,
            'total_frames': len(self.frame_times),
            'uptime': time.time() - self.start_time
        }
