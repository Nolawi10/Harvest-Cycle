from flask import Flask, render_template, Response, request, jsonify
import time
import cv2
import numpy as np
import requests
import threading
import os
import base64
from datetime import datetime
from pathlib import Path
from esp32_integration import setup_esp32_routes, start_esp32_monitoring
from ultralytics import YOLO

# Ensure detections directory exists
os.makedirs('static/detections', exist_ok=True)

# ==================== WEED BIOMASS CLASSIFICATION ====================
# Maps detected weed classes to their agricultural biomass utility
WEED_BIOMASS_CLASSES = {
    # Grasses — good for livestock feed
    'grass':         {'use': 'Feed',    'color': '#22c55e', 'icon': '🐄', 'desc': 'High palatability for cattle and goats.'},
    'wild_grass':    {'use': 'Feed',    'color': '#22c55e', 'icon': '🐄', 'desc': 'Suitable for fresh livestock feed.'},
    'setaria':       {'use': 'Feed',    'color': '#22c55e', 'icon': '🐄', 'desc': 'Foxtail millet — preferred livestock fodder.'},
    'digitaria':     {'use': 'Feed',    'color': '#22c55e', 'icon': '🐄', 'desc': 'Crabgrass — quality forage grass.'},
    # Broad-leaf weeds — best for slurry/liquid fertilizer
    'broadleaf':     {'use': 'Slurry',  'color': '#3b82f6', 'icon': '💧', 'desc': 'Rich in nitrogen; ideal for bio-slurry.'},
    'amaranth':      {'use': 'Slurry',  'color': '#3b82f6', 'icon': '💧', 'desc': 'High nitrogen content; excellent bio-slurry base.'},
    'lambsquarter':  {'use': 'Slurry',  'color': '#3b82f6', 'icon': '💧', 'desc': 'Nitrogen-rich for fermentation and liquid feed.'},
    'spurge':        {'use': 'Slurry',  'color': '#3b82f6', 'icon': '💧', 'desc': 'Good for liquid manure production.'},
    # Leguminous / fibrous — best for compost
    'weed':          {'use': 'Compost', 'color': '#f59e0b', 'icon': '♻️', 'desc': 'General organic biomass for composting.'},
    'thistle':       {'use': 'Compost', 'color': '#f59e0b', 'icon': '♻️', 'desc': 'Fibrous matter; improves compost structure.'},
    'dock':          {'use': 'Compost', 'color': '#f59e0b', 'icon': '♻️', 'desc': 'Deep-rooted weed rich in minerals for compost.'},
    'clover':        {'use': 'Compost', 'color': '#f59e0b', 'icon': '♻️', 'desc': 'Nitrogen-fixing legume; premium compost input.'},
    'nettle':        {'use': 'Compost', 'color': '#f59e0b', 'icon': '♻️', 'desc': 'Activator plant — accelerates composting.'},
}

DEFAULT_WEED_CLASSIFICATION = {'use': 'Compost', 'color': '#f59e0b', 'icon': '♻️', 'desc': 'Unclassified weed — default to composting.'}

def classify_weed_biomass(class_name):
    """Returns the biomass utilization classification for a detected weed."""
    return WEED_BIOMASS_CLASSES.get(class_name.lower(), DEFAULT_WEED_CLASSIFICATION)

# ==================== FRAME CACHE (for save_detection) ====================
last_frame_lock = threading.Lock()
last_annotated_frame = None  # Stores the most recent annotated JPEG bytes

app = Flask(__name__)

# Setup ESP32 integration
setup_esp32_routes(app)
start_esp32_monitoring()

# Initialize camera with improved quality settings
camera = cv2.VideoCapture(0)

# Check if camera is available
if camera.isOpened():
    print("✅ Camera initialized successfully")
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Higher resolution
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    camera.set(cv2.CAP_PROP_FPS, 30)  # Target 30 FPS
    camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Enable autofocus
    camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Auto exposure
    camera.set(cv2.CAP_PROP_AUTO_WB, 1)  # Auto white balance
    
    # Test camera read
    success, test_frame = camera.read()
    if success:
        print("✅ Camera test successful - resolution:", test_frame.shape)
    else:
        print("❌ Camera test failed - no frame captured")
        print("🔄 Trying different camera indices...")
        
        # Try different camera indices
        for i in range(1, 5):
            test_cam = cv2.VideoCapture(i)
            if test_cam.isOpened():
                success, test_frame = test_cam.read()
                if success:
                    print(f"✅ Found working camera at index {i}")
                    camera.release()
                    camera = cv2.VideoCapture(i)
                    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    camera.set(cv2.CAP_PROP_FPS, 30)
                    break
                test_cam.release()
        else:
            print("❌ No working cameras found")
else:
    print("❌ Failed to initialize camera - no camera found or camera is in use")
    print("🔄 Creating virtual camera for demonstration...")
    
    # Create a virtual camera that generates test patterns
    camera = None

# Load YOLO model exactly like standalone script
general_model = None
ov_model = None

try:
    print("📦 Loading YOLOv11 model...")
    general_model = YOLO('yolo11n.pt') 
    print("✅ Loaded YOLOv11 model!")
    
    # Export to OpenVINO (same as standalone)
    print("🔧 Exporting to OpenVINO format...")
    general_model.export(format='openvino')
    print("✅ OpenVINO export successful!")
    
    # Load optimized version (same as standalone)
    print("🎯 Loading optimized OpenVINO model...")
    ov_model = YOLO('yolo11n_openvino_model/')
    general_model = ov_model  # Use OpenVINO model
    print("✅ Loaded optimized OpenVINO model!")
    
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    print("🔄 Trying to load regular model...")
    try:
        general_model = YOLO('yolo11n.pt')
        print("✅ Using regular YOLOv11 model")
    except Exception as e2:
        print(f"❌ Complete model loading failure: {e2}")
        general_model = None

# Color mapping for different object classes
CLASS_COLORS = {
    # People
    'person': (0, 255, 255),      # Cyan
    # Vehicles  
    'car': (255, 0, 0),           # Red
    'truck': (255, 0, 128),       # Maroon
    'bus': (255, 165, 0),         # Orange
    'motorcycle': (255, 255, 0),   # Yellow
    'bicycle': (0, 255, 0),       # Lime
    # Animals
    'cat': (255, 0, 255),         # Magenta
    'dog': (0, 165, 255),         # Deep Sky Blue
    'horse': (255, 192, 203),     # Light Pink
    'cow': (139, 69, 19),         # Brown
    'sheep': (245, 245, 220),     # Beige
    # Electronics
    'cell phone': (128, 0, 128),   # Purple
    'laptop': (0, 128, 128),       # Teal
    'tv': (64, 64, 64),            # Dark Gray
    'keyboard': (192, 192, 192),  # Silver
    'mouse': (255, 215, 0),        # Gold
    # Food & Kitchen
    'bottle': (0, 0, 255),         # Blue
    'cup': (255, 140, 0),          # Dark Orange
    'fork': (165, 42, 42),         # Brown
    'knife': (128, 128, 0),        # Olive
    'spoon': (255, 20, 147),       # Deep Pink
    'bowl': (70, 130, 180),        # Steel Blue
    'banana': (255, 255, 102),     # Light Yellow
    'apple': (255, 99, 71),        # Tomato
    'sandwich': (210, 105, 30),     # Chocolate
    'pizza': (255, 69, 0),         # Orange Red
    # Household
    'chair': (128, 0, 128),        # Purple
    'couch': (0, 100, 0),          # Dark Green
    'bed': (75, 0, 130),           # Indigo
    'table': (0, 139, 139),        # Dark Cyan
    # Nature
    'potted plant': (34, 139, 34),  # Forest Green
    'vase': (148, 0, 211),         # Dark Violet
    # Default color for other objects
    'default': (0, 255, 0)        # Green
}

# Detection variables
detection_lock = threading.Lock()
current_detections = []
detection_count = 0
current_model_type = "general"  # Use general model for basic detection
detection_settings = {
    "confidence": 0.5,
    "classes": [],  # Empty list means detect all classes
    "roi": {"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1}
}
saved_detections = []  # List of saved detection metadata

# ESP32 Camera Configuration
ESP32_IP = "192.168.1.3"
ESP32_STREAM_URL = f"http://{ESP32_IP}/stream"

def generate_esp32_stream():
    """Generate ESP32 camera stream with YOLO detection and rotation correction"""
    print(f"Attempting to connect to ESP32 at: {ESP32_STREAM_URL}")
    
    try:
        # Stream from ESP32
        response = requests.get(ESP32_STREAM_URL, stream=True, timeout=10)
        if response.status_code == 200:
            print("ESP32 connected successfully!")
            # Process MJPEG stream
            bytes_buffer = bytes()
            for chunk in response.iter_content(chunk_size=4096):
                bytes_buffer += chunk
                a = bytes_buffer.find(b'\xff\xd8') # JPEG start
                b = bytes_buffer.find(b'\xff\xd9') # JPEG end
                if a != -1 and b != -1:
                    jpg = bytes_buffer[a:b+2]
                    bytes_buffer = bytes_buffer[b+2:]
                    
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # Rotate frame 270 degrees for horizontal ESP32 mounting
                        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        
                        # Perform YOLO detection
                        frame, detections = detect_objects(frame)
                        
                        # Convert back to JPEG
                        _, buffer = cv2.imencode('.jpg', frame)
                        frame_bytes = buffer.tobytes()
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            print(f"ESP32 returned status code: {response.status_code}")
            # Fallback to local camera if ESP32 fails
            yield from generate_fallback_frame()
    except requests.exceptions.ConnectionError as e:
        print(f"ESP32 connection failed: {e}")
        yield from generate_fallback_frame()
    except Exception as e:
        print(f"ESP32 stream error: {e}")
        yield from generate_fallback_frame()

def detect_objects(frame):
    """Perform YOLO detection exactly like standalone script"""
    global current_detections, detection_count, current_model_type, detection_settings, ov_model
    
    # Use the OpenVINO model like standalone script
    model = ov_model if ov_model is not None else general_model
    
    if model is None:
        print("❌ No model available for detection!")
        return frame, []
    
    try:
        # Use predict() like standalone script - this handles everything automatically
        device = 'intel:gpu'  # Use Intel GPU like standalone script
        
        # Run prediction exactly like standalone script
        results = model.predict(frame, verbose=False, device=device)
        
        detections = []
        annotated_frame = frame.copy()
        
        # Process results (same as standalone script)
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    
                    # Get class and confidence
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    # COCO class names (same as standalone)
                    coco_classes = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
                    class_name = coco_classes[cls] if cls < len(coco_classes) else f"class_{cls}"
                    
                    # Create detection dictionary
                    detection = {
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'class': str(class_name),
                        'confidence': float(conf),
                        'class_id': int(cls)
                    }
                    detections.append(detection)
                    
                    # Get color for this class
                    color = CLASS_COLORS.get(class_name, CLASS_COLORS['default'])
                    label = f"{class_name}: {conf:.2f}"
                    
                    # Draw bounding box with thicker lines for better visibility
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
                    
                    # Draw label background for better readability
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), 
                                   (x1 + label_size[0], y1), color, -1)
                    
                    # Draw label text
                    cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Update global detection variables
        with detection_lock:
            current_detections = detections
            if any(d['class'] == 'weed' for d in detections):
                detection_count += 1

        # Cache annotated frame for save endpoint with higher quality
        ret2, buf = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if ret2:
            with last_frame_lock:
                global last_annotated_frame
                last_annotated_frame = buf.tobytes()

        return annotated_frame, detections
        
    except Exception as e:
        print(f"Detection error: {e}")
        return frame, []

def detect_combined(frame):
    """Run both weed and general models and combine results"""
    detections = []
    annotated_frame = frame.copy()
    
    # Run weed detection
    if weed_model is not None:
        try:
            weed_results = weed_model(frame, conf=detection_settings["confidence"], iou=0.45, verbose=False, device='cpu')
            for result in weed_results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        weed_classes = ['weed', 'crop']
                        class_name = weed_classes[cls] if cls < len(weed_classes) else f"plant_{cls}"
                        
                        detection = {
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'class': str(class_name),
                            'confidence': float(conf),
                            'class_id': int(cls)
                        }
                        detections.append(detection)
                        
                        # Draw bounding box
                        color = (0, 255, 0) if class_name == 'crop' else (0, 0, 255)
                        label = f"{class_name}: {conf:.2f}"
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(annotated_frame, label, (x1, y1-10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        except Exception as e:
            print(f"Weed detection error: {e}")
    
    # Run general detection
    if general_model is not None:
        try:
            device = 'intel:gpu'
            try:
                general_results = general_model(frame, conf=detection_settings["confidence"], iou=0.45, verbose=False, device=device)
            except:
                general_results = general_model(frame, conf=detection_settings["confidence"], iou=0.45, verbose=False, device='cpu')
                
            coco_classes = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
            
            for result in general_results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        
                        class_name = coco_classes[cls] if cls < len(coco_classes) else f"class_{cls}"
                        
                        # Skip if we already detected weed/crop in this area (avoid overlap)
                        overlap = False
                        for d in detections:
                            if d['class'] in ['weed', 'crop']:
                                bx1, by1, bx2, by2 = d['bbox']
                                # Simple overlap check
                                if not (x2 < bx1 or x1 > bx2 or y2 < by1 or y1 > by2):
                                    overlap = True
                                    break
                        
                        if not overlap:
                            detection = {
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'class': str(class_name),
                                'confidence': float(conf),
                                'class_id': int(cls)
                            }
                            detections.append(detection)
                            
                            # Draw bounding box
                            color = (255, 255, 0)  # Yellow for general objects
                            label = f"{class_name}: {conf:.2f}"
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(annotated_frame, label, (x1, y1-10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        except Exception as e:
            print(f"General detection error: {e}")
    
    return annotated_frame, detections

def generate_webcam_frame():
    """Generate frames from PC webcam with YOLO detection - optimized for smooth performance"""
    fps_counter = 0
    fps_start_time = time.time()
    camera_error_count = 0
    frame_count = 0
    
    print("📹 Starting webcam feed...")
    
    # Check if we have a real camera or need virtual camera
    if camera is None or not camera.isOpened():
        print("🎭 Using virtual camera for demonstration")
        return generate_virtual_frames()
    
    while True:
        success, frame = camera.read()
        frame_count += 1
        
        # Debug: Log every frame attempt
        if frame_count % 30 == 0:
            print(f"📸 Frame {frame_count}: Camera isOpened={camera.isOpened()}, Read success={success}")
        
        if not success:
            camera_error_count += 1
            print(f"❌ Camera read failed (attempt {camera_error_count})")
            
            # Create error frame with helpful information
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)  # Match camera resolution
            
            # Add error message
            cv2.putText(frame, "CAMERA ACCESS ERROR", (400, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            cv2.putText(frame, "Please check:", (450, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, "1. Camera is not connected", (380, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, "2. Another app is using the camera", (350, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, "3. Camera permissions denied", (400, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"Error count: {camera_error_count}", (500, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            
            # Try to reinitialize camera periodically
            if camera_error_count % 30 == 0:
                print("🔄 Attempting to reinitialize camera...")
                camera.release()
                time.sleep(1)
                camera.open(0)
                camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                camera.set(cv2.CAP_PROP_FPS, 30)
                print(f"📷 Camera reinitialized: {camera.isOpened()}")
        else:
            # Reset error count on successful read
            if camera_error_count > 0:
                print(f"✅ Camera recovered after {camera_error_count} errors")
                camera_error_count = 0
            
            # Debug: Log frame info
            if frame_count % 30 == 0:
                print(f"📷 Frame {frame_count}: Shape={frame.shape}, Type={type(frame)}")
            
            # Perform YOLO detection with optimized settings
            frame, detections = detect_objects(frame)
            
            # Add overlay info
            cv2.putText(frame, "PC WEBCAM - AI DETECTION", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Add detection count
            if detections:
                cv2.putText(frame, f"Objects: {len(detections)}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Calculate and display FPS
            fps_counter += 1
            if fps_counter % 10 == 0:  # Update FPS every 10 frames
                current_time = time.time()
                fps = 10 / (current_time - fps_start_time)
                fps_start_time = current_time
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Use higher quality JPEG for better compression
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not ret:
            print(f"❌ JPEG encoding failed for frame {frame_count}")
            continue
            
        frame_bytes = buffer.tobytes()
        
        # Debug: Log frame bytes size
        if frame_count % 30 == 0:
            print(f"📦 Frame {frame_count}: JPEG size={len(frame_bytes)} bytes")
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        # Dynamic frame rate adjustment
        time.sleep(0.025)  # ~40 FPS for smoother experience

def generate_virtual_frames():
    """Generate virtual camera frames with test patterns for demonstration"""
    frame_count = 0
    
    while True:
        frame_count += 1
        
        # Create a colorful test pattern
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        # Create animated background
        time_val = time.time()
        
        # Animated gradient background
        for i in range(0, 1280, 10):
            color_val = int((np.sin(i/100 + time_val) + 1) * 127)
            frame[:, i:i+10] = [color_val//2, color_val, color_val//3]
        
        # Add moving shapes to simulate detection
        # Simulate a "person" moving
        person_x = int(400 + np.sin(time_val) * 200)
        person_y = int(200 + np.cos(time_val * 0.7) * 50)
        cv2.rectangle(frame, (person_x, person_y), (person_x + 100, person_y + 200), (0, 255, 255), 3)
        cv2.putText(frame, "person: 0.95", (person_x, person_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Simulate a "car" moving
        car_x = int(800 + np.sin(time_val * 1.2) * 150)
        car_y = int(400 + np.cos(time_val * 0.8) * 30)
        cv2.rectangle(frame, (car_x, car_y), (car_x + 150, car_y + 80), (255, 0, 0), 3)
        cv2.putText(frame, "car: 0.87", (car_x, car_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Simulate a "phone" moving
        phone_x = int(600 + np.sin(time_val * 2) * 100)
        phone_y = int(300 + np.cos(time_val * 1.5) * 100)
        cv2.rectangle(frame, (phone_x, phone_y), (phone_x + 40, phone_y + 80), (128, 0, 128), 3)
        cv2.putText(frame, "cell phone: 0.92", (phone_x, phone_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add overlay info
        cv2.putText(frame, "VIRTUAL CAMERA - DEMO MODE", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Frame: {frame_count}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Objects: 3", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")
        cv2.putText(frame, f"Time: {timestamp}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add instructions
        cv2.putText(frame, "This is a virtual camera for demonstration", (10, 680), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, "Connect a real camera to see live feed", (10, 700), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Encode and yield frame
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if ret:
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.033)  # ~30 FPS

def generate_fallback_frame():
    """Generate fallback frame when ESP32 is unavailable"""
    while True:
        success, frame = camera.read()
        if success:
            # Perform YOLO detection
            frame, detections = detect_objects(frame)
            
            # Minimal overlay for performance
            cv2.putText(frame, "AI DETECTION", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Use higher quality JPEG for better compression
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # Use virtual camera as fallback
            for frame_bytes in generate_virtual_frames():
                yield frame_bytes
                break
        
        time.sleep(0.033)  # ~30 FPS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/live')
def live():
    return render_template('live.html')

@app.route('/dashboard')
def dashboard():
    # Comprehensive mock sensor data for all dashboard sections
    sensor_data = {
        # 1. AI & DETECTION DATA (CORE)
        'ai': {
            'weeds_detected': 127,
            'weeds_removed': 89,
            'detection_accuracy': 94,
            'detection_speed': 45,
            'current_detection': 'Weed',
            'confidence_score': 87
        },
        
        # 2. ROBOT STATUS
        'robot': {
            'system_status': 'Online',
            'movement_state': 'Moving',
            'arm_status': 'Idle',
            'claw_status': 'Open',
            'connection_status': 'Connected'
        },
        
        # 3. POWER & BATTERY
        'power': {
            'battery_level': 78,
            'voltage': 24.5,
            'power_consumption': 125,
            'estimated_runtime': 4.5
        },
        
        # 4. SENSOR DATA (VERY IMPORTANT)
        'sensor': {
            'temperature': 28.4,
            'soil_moisture': 65,
            'humidity': 72,
            'light_intensity': 8500,
            'soil_condition': 'Optimal'
        },
        
        # 5. IRRIGATION SYSTEM (YOUR UNIQUE ADDITION 🔥)
        'irrigation': {
            'water_usage': 45.2,
            'status': 'ON',
            'water_efficiency': 82,
            'water_saved': 35,
            'recommended_level': 68
        },
        
        # 6. COLLECTION SYSTEM
        'collection': {
            'basket_fill_level': 62,
            'weeds_collected': 89,
            'basket_status': 'Half'
        },
        
        # 7. NAVIGATION (OPTIONAL BUT 🔥)
        'navigation': {
            'position_x': 125.4,
            'position_y': 87.2,
            'direction': 45,
            'area_covered': 68,
            'obstacle_detected': False
        },
        
        # 8. PERFORMANCE METRICS
        'performance': {
            'runtime': '2h 34m',
            'efficiency_score': 91,
            'crop_protection_rate': 96,
            'chemical_reduction': 78
        },
        
        # 9. LOGS / ACTIVITY FEED (VERY IMPRESSIVE)
        'logs': [
            {'time': '14:32:15', 'message': 'Weed detected at (125.4, 87.2)'},
            {'time': '14:32:18', 'message': 'Claw activated'},
            {'time': '14:32:21', 'message': 'Weed removed successfully'},
            {'time': '14:32:24', 'message': 'Basket updated - 89 weeds collected'},
            {'time': '14:32:30', 'message': 'Moving to next waypoint'},
            {'time': '14:32:35', 'message': 'Detection scan initiated'},
            {'time': '14:32:38', 'message': 'Soil moisture optimal - no irrigation needed'},
            {'time': '14:32:42', 'message': 'Battery level: 78%'},
            {'time': '14:32:45', 'message': 'System performance check completed'},
            {'time': '14:32:48', 'message': 'Area coverage: 68%'}
        ],
        
        # GPS Data for map
        'gps': {
            'latitude': 9.1450,
            'longitude': 40.4897,
            'altitude': 2450,
            'speed': 2.5
        }
    }
    
    return render_template('dashboard.html', data=sensor_data)

@app.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')

@app.route('/impact')
def impact():
    return render_template('impact.html')

@app.route('/research')
def research():
    return render_template('research.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_webcam_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webcam_feed')
def webcam_feed():
    """Dedicated webcam feed route"""
    return Response(generate_webcam_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera_test')
def camera_test():
    """Simple camera test without detection"""
    def generate_test_frames():
        try:
            # Test camera directly
            test_cam = cv2.VideoCapture(0)
            test_cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            test_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            print("🔍 Testing camera directly...")
            
            if test_cam.isOpened():
                print("✅ Test camera opened")
                
                for i in range(10):  # Test 10 frames
                    success, frame = test_cam.read()
                    if success:
                        print(f"✅ Frame {i+1} captured: {frame.shape}")
                        
                        # Add timestamp
                        timestamp = time.strftime("%H:%M:%S")
                        cv2.putText(frame, f"Camera Test - {timestamp}", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.putText(frame, f"Frame: {i+1}/10", (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        ret, buffer = cv2.imencode('.jpg', frame)
                        if ret:
                            frame_bytes = buffer.tobytes()
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    else:
                        print(f"❌ Frame {i+1} failed")
                        break
                    
                    time.sleep(0.1)
                test_cam.release()
            else:
                print("❌ Test camera failed to open")
                
                # Create error frame
                error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(error_frame, "CAMERA TEST FAILED", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                ret, buffer = cv2.imencode('.jpg', error_frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    
        except Exception as e:
            print(f"❌ Camera test error: {e}")
            
            # Create error frame
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(error_frame, f"ERROR: {str(e)}", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', error_frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    return Response(generate_test_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/esp32_feed')
def esp32_feed():
    """ESP32 camera feed with YOLO detection"""
    return Response(generate_esp32_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detection_status')
def detection_status():
    """Get current detection status"""
    with detection_lock:
        return jsonify({
            'detections': current_detections,
            'detection_count': detection_count,
            'model_loaded': general_model is not None or ov_model is not None,
            'current_model': current_model_type,
            'settings': detection_settings
        })

@app.route('/update_detection_settings', methods=['POST'])
def update_detection_settings():
    """Update detection settings"""
    global current_model_type, detection_settings
    
    try:
        data = request.json
        current_model_type = data.get('model', 'agricultural')
        detection_settings['confidence'] = data.get('confidence', 0.5)
        detection_settings['classes'] = data.get('classes', [])
        detection_settings['roi'] = data.get('roi', {"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1})
        
        return jsonify({'success': True, 'message': 'Settings updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/esp32_configure', methods=['POST'])
def esp32_configure():
    """Configure ESP32 camera settings"""
    try:
        data = request.json
        ip = data.get('ip')
        port = data.get('port')
        resolution = data.get('resolution')
        quality = data.get('quality')
        
        # Update ESP32 configuration (implementation depends on ESP32 firmware)
        # For now, just store the settings
        global ESP32_IP, ESP32_STREAM_URL
        ESP32_IP = ip
        ESP32_STREAM_URL = f"http://{ip}:{port}/stream"
        
        return jsonify({'success': True, 'message': f'ESP32 configured: {resolution}, {quality}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/process_image', methods=['POST'])
def process_image():
    """Process uploaded image for object detection"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No image selected'})
        
        # Read image
        image_bytes = file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'success': False, 'error': 'Invalid image format'})
        
        # Run detection
        annotated_frame, detections = detect_objects(frame)
        
        return jsonify({
            'success': True,
            'detections': detections,
            'count': len(detections)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_detection', methods=['POST'])
def save_detection():
    """Save the current annotated frame to disk when a weed is detected."""
    global last_annotated_frame, saved_detections
    try:
        data = request.json or {}
        detections = data.get('detections', [])

        with last_frame_lock:
            frame_bytes = last_annotated_frame

        if not frame_bytes:
            return jsonify({'success': False, 'error': 'No frame available yet'})

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]
        filename = f'detection_{timestamp}.jpg'
        filepath = f'static/detections/{filename}'

        with open(filepath, 'wb') as f:
            f.write(frame_bytes)

        # Build record
        record = {
            'filename': filename,
            'url': f'/static/detections/{filename}',
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'detections': detections
        }
        saved_detections.insert(0, record)  # newest first
        saved_detections = saved_detections[:50]  # keep last 50

        return jsonify({'success': True, 'url': record['url'], 'filename': filename})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/saved_detections')
def get_saved_detections():
    """Return list of saved detection snapshots."""
    return jsonify(saved_detections)


@app.route('/weed_classes')
def weed_classes():
    """Return the full weed biomass classification table."""
    return jsonify(WEED_BIOMASS_CLASSES)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
