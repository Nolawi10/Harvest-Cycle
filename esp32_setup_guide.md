# ESP32 Camera Setup Guide for AI Agro Rover

## 📋 Hardware Requirements

### ESP32-CAM (Recommended)
- ESP32-CAM board with OV2640 camera
- MicroUSB cable for programming
- 5V power supply (minimum 2A)

### Alternative: ESP32 + Camera Module
- ESP32 Development Board
- OV2640 Camera Module
- Jumper wires
- Breadboard

### Optional Sensors
- DHT22 Temperature & Humidity Sensor
- Soil Moisture Sensor (Capacitive)
- LiPo Battery with charging module
- Servo motors (SG90) for robotic arm

## 🔧 Software Requirements

### Arduino IDE Setup
1. Install Arduino IDE 1.8.19 or newer
2. Add ESP32 Board Manager:
   - File → Preferences → Additional Boards Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. Install ESP32 boards:
   - Tools → Board → Boards Manager
   - Search "ESP32" and install "ESP32 by Espressif Systems"

### Required Libraries
Install these libraries via Arduino IDE Library Manager:
- `WiFi` (built-in)
- `WebServer` (built-in)
- `HTTPClient` (built-in)
- `ArduinoJson` by Benoit Blanchon
- `esp_camera` (built-in with ESP32)

## ⚙️ Configuration

### 1. WiFi Settings
Edit the `esp32_camera_server.ino` file:
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
```

### 2. Flask Server IP
Update the Flask server IP address:
```cpp
const char* flask_server = "192.168.1.100"; // Your PC's IP
const int flask_port = 5000;
```

### 3. Camera Pin Configuration
For ESP32-CAM, the default pins should work. For custom setups, update `camera_pins.h`:
```cpp
#define Y2_GPIO_NUM 5
#define Y3_GPIO_NUM 4
#define Y4_GPIO_NUM 0
#define Y5_GPIO_NUM 2
// ... etc
```

## 🚀 Installation Steps

### 1. Hardware Setup
1. Connect ESP32-CAM to your computer via USB
2. For ESP32 + separate camera:
   - Connect camera to ESP32 following pin diagram
   - Ensure proper power connections

### 2. Upload Code
1. Open Arduino IDE
2. Select board: Tools → Board → ESP32 Arduino → AI Thinker ESP32-CAM
3. Select correct COM port
4. Open `esp32_camera_server.ino`
5. Upload the sketch

### 3. First Time Setup
1. After upload, open Serial Monitor (115200 baud)
2. Note the ESP32's IP address
3. Test camera by visiting `http://[ESP32_IP]` in browser

### 4. Flask Integration
1. Update `esp32_integration.py` with correct ESP32 IP:
   ```python
   esp32_manager = ESP32CameraManager(esp32_ip="YOUR_ESP32_IP")
   ```
2. Install Python dependencies:
   ```bash
   pip install requests opencv-python numpy
   ```
3. Run Flask application:
   ```bash
   python app.py
   ```

## 🌐 Web Interface

### ESP32 Web Interface
- **Main Page**: `http://[ESP32_IP]`
- **Camera Stream**: `http://[ESP32_IP]/stream`
- **Status API**: `http://[ESP32_IP]/status`
- **Control API**: `http://[ESP32_IP]/control?action=detect`

### Flask Web Interface
- **Live Feed**: `http://[PC_IP]:5000/live`
- **ESP32 Stream**: `http://[PC_IP]:5000/esp32_stream`
- **ESP32 Status**: `http://[PC_IP]:5000/esp32_status`

## 🔧 Troubleshooting

### Camera Not Working
1. Check camera connections
2. Ensure proper power supply (5V 2A minimum)
3. Try different frame sizes in code
4. Check Serial Monitor for error messages

### WiFi Connection Issues
1. Verify SSID and password are correct
2. Check if ESP32 is within WiFi range
3. Try moving closer to router
4. Restart ESP32 and router

### Flask Integration Issues
1. Ensure ESP32 and PC are on same network
2. Check firewall settings on PC
3. Verify Flask server is running
4. Test ESP32 API endpoints directly

### Performance Issues
1. Reduce JPEG quality in camera config
2. Lower frame size (FRAMESIZE_VGA instead of SVGA)
3. Check WiFi signal strength
4. Ensure sufficient power supply

## 📱 Mobile Access

### For Mobile Viewing
1. Connect mobile device to same WiFi network
2. Access Flask web interface: `http://[PC_IP]:5000/live`
3. Toggle between ESP32 and local camera feeds
4. Use detection controls remotely

### Port Forwarding (Optional)
For remote access outside your network:
1. Forward ports 5000 (Flask) and 80 (ESP32) on your router
2. Use dynamic DNS for static domain
3. Ensure security measures are in place

## 🔒 Security Considerations

1. Change default WiFi credentials
2. Use WPA2/WPA3 encryption
3. Consider adding authentication to ESP32 web interface
4. Use HTTPS for Flask in production
5. Regularly update ESP32 and library versions

## 📊 Performance Monitoring

Monitor these metrics:
- WiFi signal strength (RSSI)
- Frame rate (FPS)
- Memory usage (Free Heap)
- Battery level (if using battery)
- Detection accuracy

Access status via:
- ESP32: `http://[ESP32_IP]/status`
- Flask: `http://[PC_IP]:5000/esp32_status`

## 🔄 Maintenance

### Regular Tasks
1. Clean camera lens regularly
2. Check WiFi signal strength
3. Monitor battery levels
4. Update firmware as needed
5. Backup configuration settings

### Calibration
1. Adjust camera focus for your field of view
2. Calibrate sensors for accurate readings
3. Test detection in various lighting conditions
4. Validate communication with Flask server

## 📞 Support

For issues:
1. Check Serial Monitor output
2. Test individual components
3. Verify network connectivity
4. Review this troubleshooting guide
5. Check GitHub issues for similar problems

---

**Note**: This setup is designed for agricultural monitoring and weed detection. Adjust camera settings and detection parameters based on your specific crop types and field conditions.
