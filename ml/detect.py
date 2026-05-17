"""
Real-time Weed Detection using YOLO
Performs inference on webcam or ESP32-CAM stream
"""

import cv2
import numpy as np
import time
import requests
import threading
from pathlib import Path
from ultralytics import YOLO
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ml.utils import (
    logger, Colors, draw_bbox, calculate_fps, 
    resize_frame, preprocess_frame, PerformanceMonitor
)

class WeedDetector:
    """Real-time weed detection using YOLO"""
    
    def __init__(self, model_path="runs/detect/train/weights/best.pt", 
                 confidence=0.5, iou_threshold=0.45):
        """
        Initialize weed detector
        
        Args:
            model_path: Path to trained YOLO model
            confidence: Detection confidence threshold
            iou_threshold: IoU threshold for NMS
        """
        self.model_path = model_path
        self.confidence = confidence
        self.iou_threshold = iou_threshold
        self.model = None
        self.class_names = {0: 'weed', 1: 'crop'}
        self.performance_monitor = PerformanceMonitor()
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLO model"""
        try:
            if Path(self.model_path).exists():
                self.model = YOLO(self.model_path)
                logger.info(f"Loaded model: {self.model_path}")
            else:
                logger.warning(f"Model not found: {self.model_path}")
                logger.info("Using pretrained YOLOv8n for demo")
                self.model = YOLO('yolov8n.pt')
                # Update class names for demo
                self.model.names = {0: 'weed', 1: 'crop'}
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
        
        return True
    
    def detect_frame(self, frame):
        """
        Detect objects in a single frame
        
        Args:
            frame: Input frame (BGR)
        
        Returns:
            detections: List of detection dictionaries
            annotated_frame: Frame with bounding boxes
        """
        if self.model is None:
            return [], frame
        
        start_time = time.time()
        
        # Run inference
        results = self.model(
            frame,
            conf=self.confidence,
            iou=self.iou_threshold,
            verbose=False
        )
        
        detections = []
        annotated_frame = frame.copy()
        
        # Process results
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # Get class and confidence
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # Get class name
                    class_name = self.class_names.get(cls, f"class_{cls}")
                    
                    # Create detection dictionary
                    detection = {
                        'bbox': [x1, y1, x2, y2],
                        'class': class_name,
                        'confidence': conf,
                        'class_id': cls
                    }
                    detections.append(detection)
                    
                    # Draw on frame
                    draw_bbox(annotated_frame, [x1, y1, x2, y2], 
                             class_name, conf)
        
        # Update performance monitor
        frame_time = time.time() - start_time
        self.performance_monitor.add_frame_time(frame_time)
        self.performance_monitor.add_detection_count(len(detections))
        
        return detections, annotated_frame
    
    def detect_from_stream(self, stream_url, skip_frames=2):
        """
        Detect from video stream (webcam or ESP32-CAM)
        
        Args:
            stream_url: Stream source (0 for webcam, URL for ESP32)
            skip_frames: Number of frames to skip for performance
        """
        logger.info(f"Starting detection from: {stream_url}")
        
        # Initialize video capture
        if isinstance(stream_url, str) and stream_url.startswith('http'):
            # ESP32-CAM stream
            cap = cv2.VideoCapture(stream_url)
            if not cap.isOpened():
                logger.error(f"Failed to open stream: {stream_url}")
                return
        else:
            # Webcam
            cap = cv2.VideoCapture(stream_url)
            if not cap.isOpened():
                logger.error("Failed to open webcam")
                return
        
        # Set capture properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        frame_count = 0
        start_time = time.time()
        last_stats_time = start_time
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame")
                    break
                
                frame_count += 1
                
                # Skip frames for performance
                if frame_count % (skip_frames + 1) != 0:
                    continue
                
                # Resize frame for performance
                small_frame = resize_frame(frame, (640, 480))
                
                # Detect objects
                detections, annotated_frame = self.detect_frame(small_frame)
                
                # Calculate FPS
                current_fps = calculate_fps(start_time, frame_count)
                
                # Draw FPS and stats
                cv2.putText(annotated_frame, f"FPS: {current_fps:.1f}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, Colors.GREEN, 2)
                
                cv2.putText(annotated_frame, f"Detections: {len(detections)}", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, Colors.GREEN, 2)
                
                # Show performance stats every 5 seconds
                if time.time() - last_stats_time > 5:
                    stats = self.performance_monitor.get_stats()
                    logger.info(f"Performance: {stats['fps']:.1f} FPS, "
                              f"Avg frame time: {stats['avg_frame_time']*1000:.1f}ms")
                    last_stats_time = time.time()
                
                # Display frame
                cv2.imshow('AI Agro Rover - Weed Detection', annotated_frame)
                
                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            logger.info("Detection stopped by user")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            
            # Final stats
            final_stats = self.performance_monitor.get_stats()
            logger.info("Final Performance Stats:")
            for key, value in final_stats.items():
                logger.info(f"  {key}: {value}")

class ESP32StreamDetector:
    """Specialized detector for ESP32-CAM streams"""
    
    def __init__(self, esp32_ip="192.168.1.5", model_path="runs/detect/train/weights/best.pt"):
        """
        Initialize ESP32 stream detector
        
        Args:
            esp32_ip: IP address of ESP32-CAM
            model_path: Path to YOLO model
        """
        self.esp32_ip = esp32_ip
        self.stream_url = f"http://{esp32_ip}/stream"
        self.detector = WeedDetector(model_path)
        self.status_url = f"http://{esp32_ip}/status"
        
    def check_esp32_status(self):
        """Check ESP32-CAM status"""
        try:
            response = requests.get(self.status_url, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to check ESP32 status: {e}")
        return None
    
    def start_detection(self, skip_frames=2):
        """Start detection from ESP32-CAM stream"""
        logger.info(f"Connecting to ESP32-CAM at {self.esp32_ip}")
        
        # Check ESP32 status
        status = self.check_esp32_status()
        if status:
            logger.info(f"ESP32-CAM Status: {status}")
        else:
            logger.warning("ESP32-CAM not responding, using stream anyway")
        
        # Start detection
        self.detector.detect_from_stream(self.stream_url, skip_frames)

def test_on_images(test_dir="test_images"):
    """Test model on static images"""
    test_path = Path(test_dir)
    if not test_path.exists():
        logger.error(f"Test directory not found: {test_dir}")
        return
    
    detector = WeedDetector()
    image_files = list(test_path.glob("*.jpg")) + list(test_path.glob("*.png"))
    
    for image_file in image_files:
        logger.info(f"Processing: {image_file}")
        
        # Read image
        frame = cv2.imread(str(image_file))
        if frame is None:
            logger.error(f"Failed to read image: {image_file}")
            continue
        
        # Detect objects
        detections, annotated_frame = detector.detect_frame(frame)
        
        # Print results
        logger.info(f"Found {len(detections)} objects:")
        for det in detections:
            logger.info(f"  {det['class']}: {det['confidence']:.2f}")
        
        # Display result
        cv2.imshow('Detection Result', annotated_frame)
        cv2.waitKey(0)
    
    cv2.destroyAllWindows()

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Agro Rover Weed Detection")
    parser.add_argument("--source", type=str, default="0",
                       help="Source (0 for webcam, URL for ESP32, path for images)")
    parser.add_argument("--model", type=str, 
                       default="runs/detect/train/weights/best.pt",
                       help="Path to trained model")
    parser.add_argument("--conf", type=float, default=0.5,
                       help="Confidence threshold")
    parser.add_argument("--skip", type=int, default=2,
                       help="Skip frames for performance")
    
    args = parser.parse_args()
    
    # Initialize detector
    detector = WeedDetector(args.model, args.conf)
    
    # Start detection
    if args.source == "0" or args.source.isdigit():
        # Webcam
        detector.detect_from_stream(int(args.source), args.skip)
    elif args.source.startswith("http"):
        # ESP32-CAM
        esp32_detector = ESP32StreamDetector()
        esp32_detector.detector = detector
        detector.detect_from_stream(args.source, args.skip)
    else:
        # Images
        test_on_images(args.source)

if __name__ == "__main__":
    main()
