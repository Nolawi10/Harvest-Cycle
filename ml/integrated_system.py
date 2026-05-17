"""
Integrated AI Agro Rover System
Combines YOLO weed detection with smart irrigation decisions
"""

import cv2
import numpy as np
import time
import threading
import queue
from pathlib import Path
from datetime import datetime
import json
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ml.detect import WeedDetector, ESP32StreamDetector
from ml.irrigation_model import SmartIrrigationController
from ml.utils import logger, calculate_weed_density, PerformanceMonitor

class IntegratedAgroRover:
    """Complete AI Agro Rover system with detection and irrigation"""
    
    def __init__(self, model_path="runs/detect/train/weights/best.pt", 
                 esp32_ip="192.168.1.5", irrigation_model='decision_tree'):
        """
        Initialize integrated system
        
        Args:
            model_path: Path to YOLO model
            esp32_ip: ESP32-CAM IP address
            irrigation_model: Type of irrigation model
        """
        self.esp32_ip = esp32_ip
        self.stream_url = f"http://{esp32_ip}/stream"
        
        # Initialize weed detector
        self.weed_detector = WeedDetector(model_path)
        
        # Initialize irrigation controller
        self.irrigation_controller = SmartIrrigationController(irrigation_model)
        self.irrigation_controller.engine.train_ml_model(500)
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        
        # Data queues for inter-thread communication
        self.detection_queue = queue.Queue(maxsize=10)
        self.irrigation_queue = queue.Queue(maxsize=10)
        
        # System state
        self.running = False
        self.current_weed_density = 0
        self.last_irrigation_update = time.time()
        
        logger.info("Integrated AI Agro Rover System initialized")
    
    def process_detections(self, detections, frame_area):
        """
        Process YOLO detections and update irrigation system
        
        Args:
            detections: List of weed/crop detections
            frame_area: Total frame area for density calculation
        """
        if not detections:
            return
        
        # Calculate weed density
        weed_density, weed_count = calculate_weed_density(detections, frame_area)
        self.current_weed_density = weed_density
        
        # Update irrigation system with weed density
        self.irrigation_controller.engine.update_weed_density(weed_density)
        
        # Log detection summary
        crop_count = sum(1 for det in detections if det['class'] == 'crop')
        logger.info(f"Detections: {weed_count} weeds, {crop_count} crops, density: {weed_density:.2f}")
        
        # Add to queue for processing
        detection_summary = {
            'timestamp': datetime.now().isoformat(),
            'weed_count': weed_count,
            'crop_count': crop_count,
            'weed_density': weed_density,
            'total_detections': len(detections)
        }
        
        try:
            self.detection_queue.put_nowait(detection_summary)
        except queue.Full:
            # Remove old data and add new
            try:
                self.detection_queue.get_nowait()
                self.detection_queue.put_nowait(detection_summary)
            except queue.Empty:
                pass
    
    def simulate_sensor_data(self):
        """
        Simulate sensor data for irrigation decisions
        In real system, this would read from actual sensors
        """
        # Simulate realistic sensor data with some variation
        base_moisture = 40
        base_temp = 25
        base_humidity = 60
        
        # Add time-based variations
        hour = datetime.now().hour
        temp_variation = 5 * np.sin(2 * np.pi * hour / 24)
        humidity_variation = -15 * np.sin(2 * np.pi * hour / 24)
        
        # Add random noise
        moisture = base_moisture + np.random.normal(0, 5)
        temperature = base_temp + temp_variation + np.random.normal(0, 2)
        humidity = base_humidity + humidity_variation + np.random.normal(0, 5)
        
        # Ensure valid ranges
        moisture = np.clip(moisture, 0, 100)
        temperature = np.clip(temperature, -10, 50)
        humidity = np.clip(humidity, 0, 100)
        
        return moisture, temperature, humidity
    
    def update_irrigation_system(self):
        """Update irrigation system based on current conditions"""
        # Get simulated sensor data
        soil_moisture, temperature, humidity = self.simulate_sensor_data()
        
        # Make irrigation decision
        decision = self.irrigation_controller.update_sensors(
            soil_moisture, temperature, humidity
        )
        
        # Add to irrigation queue
        try:
            self.irrigation_queue.put_nowait(decision)
        except queue.Full:
            try:
                self.irrigation_queue.get_nowait()
                self.irrigation_queue.put_nowait(decision)
            except queue.Empty:
                pass
        
        return decision
    
    def draw_system_overlay(self, frame, detections, irrigation_decision):
        """
        Draw comprehensive system overlay on frame
        
        Args:
            frame: Input frame
            detections: Current detections
            irrigation_decision: Current irrigation decision
        """
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Semi-transparent background for info panel
        panel_height = 120
        panel = np.zeros((panel_height, w, 3), dtype=np.uint8)
        panel[:] = (20, 20, 20)  # Dark background
        
        # Place panel at bottom
        overlay[h-panel_height:h, :] = panel
        
        # Draw system information
        y_offset = h - panel_height + 20
        
        # Irrigation status
        irrigation_level = irrigation_decision['irrigation_level']
        color = (0, 255, 0) if irrigation_level == 'LOW' else (0, 255, 255) if irrigation_level == 'MEDIUM' else (0, 0, 255)
        
        cv2.putText(overlay, f"Irrigation: {irrigation_level}", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Weed density
        cv2.putText(overlay, f"Weed Density: {self.current_weed_density:.2f}", 
                   (10, y_offset + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Detection counts
        weed_count = sum(1 for det in detections if det['class'] == 'weed')
        crop_count = sum(1 for det in detections if det['class'] == 'crop')
        cv2.putText(overlay, f"Weeds: {weed_count} | Crops: {crop_count}", 
                   (10, y_offset + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Performance stats
        stats = self.performance_monitor.get_stats()
        fps = stats.get('fps', 0)
        cv2.putText(overlay, f"FPS: {fps:.1f}", 
                   (w - 100, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Reasoning
        reasoning = irrigation_decision['reasoning'][:60] + "..." if len(irrigation_decision['reasoning']) > 60 else irrigation_decision['reasoning']
        cv2.putText(overlay, reasoning, 
                   (10, y_offset + 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        return overlay
    
    def run_integrated_system(self, source="0", skip_frames=2):
        """
        Run complete integrated system
        
        Args:
            source: Video source (webcam, ESP32 URL, etc.)
            skip_frames: Frames to skip for performance
        """
        logger.info("Starting Integrated AI Agro Rover System")
        
        # Initialize video capture
        if isinstance(source, str) and source.startswith('http'):
            cap = cv2.VideoCapture(source)
            logger.info(f"Connecting to ESP32-CAM at {source}")
        else:
            cap = cv2.VideoCapture(int(source))
            logger.info("Using webcam")
        
        if not cap.isOpened():
            logger.error("Failed to open video source")
            return
        
        # Configure capture
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        frame_count = 0
        start_time = time.time()
        last_irrigation_update = time.time()
        current_irrigation_decision = {'irrigation_level': 'LOW', 'reasoning': 'Initializing...'}
        
        self.running = True
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame")
                    break
                
                frame_count += 1
                frame_start = time.time()
                
                # Skip frames for performance
                if frame_count % (skip_frames + 1) != 0:
                    continue
                
                # Resize frame for performance
                frame = cv2.resize(frame, (640, 480))
                frame_area = frame.shape[0] * frame.shape[1]
                
                # Weed detection
                detections, annotated_frame = self.weed_detector.detect_frame(frame)
                
                # Process detections
                self.process_detections(detections, frame_area)
                
                # Update irrigation system every 2 seconds
                if time.time() - last_irrigation_update > 2:
                    current_irrigation_decision = self.update_irrigation_system()
                    last_irrigation_update = time.time()
                
                # Draw system overlay
                final_frame = self.draw_system_overlay(annotated_frame, detections, current_irrigation_decision)
                
                # Update performance monitor
                frame_time = time.time() - frame_start
                self.performance_monitor.add_frame_time(frame_time)
                self.performance_monitor.add_detection_count(len(detections))
                
                # Display frame
                cv2.imshow('AI Agro Rover - Integrated System', final_frame)
                
                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                # Log status every 10 seconds
                if frame_count % 300 == 0:  # Assuming ~30 FPS
                    self._log_system_status()
        
        except KeyboardInterrupt:
            logger.info("System stopped by user")
        
        finally:
            self.running = False
            cap.release()
            cv2.destroyAllWindows()
            self._log_system_status()
    
    def _log_system_status(self):
        """Log current system status"""
        stats = self.performance_monitor.get_stats()
        irrigation_status = self.irrigation_controller.get_status()
        
        logger.info("=== System Status ===")
        logger.info(f"Performance: {stats['fps']:.1f} FPS, {stats['total_frames']} frames processed")
        logger.info(f"Irrigation: {irrigation_status['current_state']['current_level']}")
        logger.info(f"Weed Density: {self.current_weed_density:.2f}")
        logger.info(f"Total Irrigation Decisions: {irrigation_status['total_decisions']}")
    
    def get_system_report(self):
        """Get comprehensive system report"""
        stats = self.performance_monitor.get_stats()
        irrigation_status = self.irrigation_controller.get_status()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'performance': stats,
            'irrigation': irrigation_status,
            'current_weed_density': self.current_weed_density,
            'esp32_ip': self.esp32_ip,
            'system_running': self.running
        }
        
        return report
    
    def save_report(self, filepath="reports/system_report.json"):
        """Save system report to file"""
        report = self.get_system_report()
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"System report saved to {filepath}")

def main():
    """Main function for integrated system testing"""
    logger.info("AI Agro Rover Integrated System")
    logger.info("=" * 50)
    
    # Initialize integrated system
    rover = IntegratedAgroRover(
        model_path="runs/detect/train/weights/best.pt",
        esp32_ip="192.168.1.5",
        irrigation_model='decision_tree'
    )
    
    # Test with different sources
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Agro Rover Integrated System")
    parser.add_argument("--source", type=str, default="0",
                       help="Video source (0 for webcam, URL for ESP32)")
    parser.add_argument("--skip", type=int, default=2,
                       help="Skip frames for performance")
    parser.add_argument("--report", type=str, default="reports/system_report.json",
                       help="Report file path")
    
    args = parser.parse_args()
    
    try:
        # Run integrated system
        rover.run_integrated_system(source=args.source, skip_frames=args.skip)
        
        # Save final report
        rover.save_report(args.report)
        
    except Exception as e:
        logger.error(f"System error: {e}")
        raise

if __name__ == "__main__":
    main()
