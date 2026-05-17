"""
ESP32 Camera Integration for AI Agro Rover
Handles communication between ESP32 camera and Flask web application
"""

import requests
import threading
import time
import json
from flask import Flask, request, jsonify
import cv2
import numpy as np

class ESP32CameraManager:
    def __init__(self, esp32_ip="192.168.1.100", esp32_port=80):
        self.esp32_ip = esp32_ip
        self.esp32_port = esp32_port
        self.base_url = f"http://{esp32_ip}:{esp32_port}"
        self.is_connected = False
        self.last_detection = None
        self.sensor_data = {}
        
    def test_connection(self):
        """Test connection to ESP32 camera"""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                self.is_connected = True
                self.sensor_data = response.json()
                return True
        except Exception as e:
            print(f"ESP32 connection failed: {e}")
            self.is_connected = False
        return False
    
    def get_camera_stream_url(self):
        """Get the camera stream URL"""
        return f"{self.base_url}/stream"
    
    def get_sensor_data(self):
        """Get current sensor data from ESP32"""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=3)
            if response.status_code == 200:
                self.sensor_data = response.json()
                return self.sensor_data
        except Exception as e:
            print(f"Failed to get sensor data: {e}")
        return {}
    
    def trigger_detection(self):
        """Trigger weed detection on ESP32"""
        try:
            response = requests.get(f"{self.base_url}/control?action=detect", timeout=3)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to trigger detection: {e}")
        return False
    
    def reset_detection_counter(self):
        """Reset detection counter on ESP32"""
        try:
            response = requests.get(f"{self.base_url}/control?action=reset", timeout=3)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to reset counter: {e}")
        return False

# Initialize ESP32 camera manager
esp32_manager = ESP32CameraManager(esp32_ip="192.168.1.3")

def generate_esp32_frames():
    """Generate frames from ESP32 camera stream"""
    stream_url = esp32_manager.get_camera_stream_url()
    
    while True:
        try:
            # Get frame from ESP32 stream
            response = requests.get(stream_url, stream=True, timeout=10)
            
            if response.status_code == 200:
                # Process MJPEG stream
                boundary = b'--frame'
                
                for chunk in response.iter_content(chunk_size=1024):
                    if boundary in chunk:
                        # Extract JPEG frame
                        start = chunk.find(b'\r\n\r\n') + 4
                        end = chunk.find(b'\r\n--frame', start)
                        
                        if start > 3 and end > start:
                            jpeg_data = chunk[start:end]
                            
                            # Add processing overlay
                            frame = cv2.imdecode(np.frombuffer(jpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                            
                            if frame is not None:
                                # Add AI processing overlay
                                frame = add_ai_overlay(frame)
                                
                                # Convert back to JPEG
                                _, buffer = cv2.imencode('.jpg', frame)
                                frame_bytes = buffer.tobytes()
                                
                                yield (b'--frame\r\n'
                                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Fallback to local camera if ESP32 fails
                yield generate_fallback_frame()
                
        except Exception as e:
            print(f"ESP32 stream error: {e}")
            yield generate_fallback_frame()
            
        time.sleep(0.033)  # ~30 FPS

def add_ai_overlay(frame):
    """Add AI detection overlay to frame"""
    height, width = frame.shape[:2]
    
    # Get sensor data
    sensor_data = esp32_manager.get_sensor_data()
    
    # Add system status overlay
    cv2.rectangle(frame, (10, 10), (300, 80), (0, 0, 0), -1)
    cv2.putText(frame, "AI AGRO ROVER - ESP32", (20, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Add sensor information
    if sensor_data:
        temp = sensor_data.get('temperature', 0)
        humidity = sensor_data.get('humidity', 0)
        soil_moisture = sensor_data.get('soilMoisture', 0)
        battery = sensor_data.get('batteryLevel', 0)
        detection_count = sensor_data.get('detectionCount', 0)
        
        cv2.putText(frame, f"Temp: {temp:.1f}C | Humidity: {humidity:.0f}%", 
                    (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(frame, f"Soil: {soil_moisture}% | Battery: {battery}%", 
                    (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(frame, f"Weeds Detected: {detection_count}", 
                    (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    # Add detection indicator
    if sensor_data.get('weedDetected', False):
        cv2.circle(frame, (width - 50, 50), 20, (0, 0, 255), -1)
        cv2.putText(frame, "WEED DETECTED", (width - 200, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # Add grid overlay for agricultural monitoring
    grid_color = (0, 255, 0)
    grid_thickness = 1
    
    # Vertical lines
    for x in range(0, width, 100):
        cv2.line(frame, (x, 0), (x, height), grid_color, grid_thickness)
    
    # Horizontal lines
    for y in range(0, height, 100):
        cv2.line(frame, (0, y), (width, y), grid_color, grid_thickness)
    
    # Add targeting reticle
    center_x, center_y = width // 2, height // 2
    cv2.circle(frame, (center_x, center_y), 50, (0, 255, 255), 2)
    cv2.line(frame, (center_x - 60, center_y), (center_x + 60, center_y), (0, 255, 255), 2)
    cv2.line(frame, (center_x, center_y - 60), (center_x, center_y + 60), (0, 255, 255), 2)
    
    return frame

def generate_fallback_frame():
    """Generate fallback frame when ESP32 is unavailable"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, "ESP32 CAMERA OFFLINE", (150, 240), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame, "Check Connection", (200, 280), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    _, buffer = cv2.imencode('.jpg', frame)
    frame_bytes = buffer.tobytes()
    
    return (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Flask routes for ESP32 integration
def setup_esp32_routes(app):
    
    @app.route('/esp32_stream')
    def esp32_stream():
        """Stream from ESP32 camera"""
        return Response(generate_esp32_frames(), 
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @app.route('/esp32_status')
    def esp32_status():
        """Get ESP32 camera status"""
        status = {
            'connected': esp32_manager.test_connection(),
            'sensor_data': esp32_manager.get_sensor_data(),
            'stream_url': esp32_manager.get_camera_stream_url()
        }
        return jsonify(status)
    
    @app.route('/esp32_control', methods=['POST'])
    def esp32_control():
        """Control ESP32 camera"""
        data = request.json
        action = data.get('action')
        
        if action == 'detect':
            success = esp32_manager.trigger_detection()
            return jsonify({'success': success, 'message': 'Detection triggered'})
        elif action == 'reset':
            success = esp32_manager.reset_detection_counter()
            return jsonify({'success': success, 'message': 'Counter reset'})
        else:
            return jsonify({'success': False, 'message': 'Unknown action'}), 400
    
    @app.route('/detection', methods=['POST'])
    def handle_detection():
        """Handle detection from ESP32"""
        data = request.json
        print(f"Detection received: {data}")
        
        # Process detection data
        device = data.get('device')
        weed_detected = data.get('weedDetected')
        timestamp = data.get('timestamp')
        
        # Store detection in database or trigger actions
        # This is where you could:
        # - Log detections to database
        # - Trigger robotic arm
        # - Send notifications
        # - Update dashboard
        
        return jsonify({'status': 'received', 'message': 'Detection processed'})

# Background thread to monitor ESP32 connection
def monitor_esp32_connection():
    """Background thread to monitor ESP32 connection"""
    while True:
        esp32_manager.test_connection()
        time.sleep(30)  # Check every 30 seconds

def start_esp32_monitoring():
    """Start ESP32 monitoring thread"""
    monitor_thread = threading.Thread(target=monitor_esp32_connection, daemon=True)
    monitor_thread.start()
