# ESP32-CAM AI Thinker Setup Guide
## Complete Setup for Agricultural Monitoring

### 🎯 What You Need

#### Hardware
- **ESP32-CAM AI Thinker Board** (with OV2640 camera)
- **USB to TTL Serial Adapter** (CP2102 or CH340)
- **Jumper Wires** (female-to-female)
- **5V Power Supply** (2A minimum) or USB power bank
- **MicroSD Card** (optional, 4GB+ for image storage)

#### Software
- **Arduino IDE** (version 1.8.19 or newer)
- **ESP32 Board Manager** package
- **Required Libraries** (see below)

---

## 🔧 Step 1: Arduino IDE Setup

### Install ESP32 Board Support
1. Open Arduino IDE
2. Go to **File → Preferences**
3. In "Additional Boards Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Click **OK**
5. Go to **Tools → Board → Boards Manager**
6. Search for "**ESP32**" and install "**ESP32 by Espressif Systems**"

### Install Required Libraries
Go to **Tools → Manage Libraries** and install:
- **DHT sensor library** by Adafruit
- **ArduinoJson** by Benoit Blanchon

---

## 🔌 Step 2: Hardware Connections

### For Programming (USB to TTL Adapter)
```
USB-TTL    →    ESP32-CAM
VCC (5V)   →    5V
GND        →    GND
TXD        →    U0R (GPIO3)
RXD        →    U0T (GPIO1)
```

### For Power (Direct 5V)
```
5V Power Supply → ESP32-CAM
5V  →  5V
GND →  GND
```

### Optional Sensors (if using)
```
DHT22 Sensor:
VCC → 3.3V
GND → GND
DATA → GPIO13

Soil Moisture Sensor:
VCC → 3.3V
GND → GND
AOUT → GPIO12
```

---

## ⚙️ Step 3: Board Configuration

In Arduino IDE, set:
- **Tools → Board**: "ESP32 Arduino → AI Thinker ESP32-CAM"
- **Tools → Port**: Select your COM port
- **Tools → Flash Frequency**: "40MHz"
- **Tools → Flash Mode**: "QIO"
- **Tools → Partition Scheme**: "Huge APP (3MB No OTA/1MB SPIFFS)"
- **Tools → Core Debug Level**: "None"
- **Tools → Erase Flash**: "Only Sketch"

---

## 📥 Step 4: Upload Code

### Important: Upload Mode
1. **Disconnect all power** from ESP32-CAM
2. **Connect USB-TTL adapter** as shown above
3. **Connect GPIO0 to GND** (this puts it in upload mode)
4. **Connect USB-TTL to computer**
5. **Open the Serial Monitor** (115200 baud) - keep it open
6. **Upload the sketch** (`esp32cam_specific_setup.ino`)

### After Upload
1. **Disconnect GPIO0 from GND**
2. **Disconnect USB-TTL**
3. **Connect 5V power supply**
4. **Open Serial Monitor** (115200 baud) to see startup messages

---

## 🌐 Step 5: First Time Setup

### Configure WiFi
Edit these lines in the code:
```cpp
const char* ssid = "YOUR_WIFI_SSID";        // Your WiFi name
const char* password = "YOUR_WIFI_PASSWORD"; // Your WiFi password
```

### Set Flask Server IP
Update this line with your computer's IP:
```cpp
const char* flask_server = "192.168.1.100";  // Your PC's IP address
```

### Upload Again
After making changes, repeat the upload process.

---

## 🎯 Step 6: Test the Camera

### Check Serial Monitor
You should see:
```
🌱 ESP32-CAM Agro Rover Starting...
=====================================
✅ DHT22 sensor initialized
📹 Initializing camera...
✅ Camera initialized successfully!
📹 ESP32-CAM ready for agricultural monitoring
📡 Connecting to WiFi...
✅ WiFi connected!
📡 IP Address: 192.168.1.XXX
🌐 HTTP server started
```

### Access Web Interface
1. Open browser
2. Go to: `http://[ESP32_IP_ADDRESS]` (from Serial Monitor)
3. You should see the Agro Rover interface

### Test Camera Stream
1. Go to: `http://[ESP32_IP_ADDRESS]/stream`
2. You should see live video feed
3. Test controls on main page

---

## 🔧 Common Issues & Solutions

### ❌ "Camera init failed"
**Solutions:**
1. Check camera ribbon cable is properly connected
2. Ensure adequate power supply (5V 2A minimum)
3. Try resetting the board
4. Check if camera is damaged

### ❌ "WiFi connection failed"
**Solutions:**
1. Verify WiFi credentials are correct
2. Check signal strength (move closer to router)
3. Try 2.4GHz network (ESP32 doesn't support 5GHz)
4. Restart router and ESP32-CAM

### ❌ "Upload failed"
**Solutions:**
1. Make sure GPIO0 is connected to GND during upload
2. Check USB-TTL drivers are installed
3. Try different COM port
4. Hold reset button while starting upload

### ❌ "No video stream"
**Solutions:**
1. Check camera connections
2. Try different browser (Chrome/Firefox)
3. Reduce frame size in code (FRAMESIZE_VGA)
4. Check network connection

---

## 📱 Mobile Access

### On Same WiFi Network
1. Connect phone to same WiFi
2. Open browser
3. Go to ESP32 IP address
4. Full mobile interface available

### Remote Access (Advanced)
1. Set up port forwarding on router
2. Use dynamic DNS service
3. Consider VPN for security

---

## 🔍 Testing Features

### Test Sensors
1. Check sensor readings on web interface
2. Blow on DHT22 to see temperature/humidity change
3. Add water to soil moisture sensor to test

### Test Detection
1. Click "🔍 Trigger Detection" button
2. LED should flash
3. Detection counter should increment
4. Check Flask server logs

### Test Flash
1. Click "💡 Toggle Flash" button
2. Built-in LED should turn on/off

---

## 📊 Performance Optimization

### For Better Video Quality
```cpp
config.frame_size = FRAMESIZE_XGA;    // 1024x768
config.jpeg_quality = 10;            // Lower = better quality
```

### For Better Performance
```cpp
config.frame_size = FRAMESIZE_VGA;    // 640x480
config.jpeg_quality = 15;            // Higher = better performance
```

### For Low Light
```cpp
s->set_aec_value(s, 600);            // Increase exposure
s->set_gain_ctrl(s, 1);              // Enable gain control
```

---

## 🔄 Maintenance

### Regular Tasks
- Clean camera lens regularly
- Check WiFi signal strength
- Monitor battery levels
- Update firmware as needed

### Calibration
- Adjust soil moisture sensor readings
- Calibrate temperature sensor
- Test detection in various lighting

---

## 🚀 Integration with Flask

### Update Flask Integration
In `esp32_integration.py`, update ESP32 IP:
```python
esp32_manager = ESP32CameraManager(esp32_ip="YOUR_ESP32_IP")
```

### Test Integration
1. Run Flask application: `python app.py`
2. Go to: `http://localhost:5000/live`
3. Toggle between camera sources
4. Test ESP32 controls

---

## 📞 Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| No power | Check 5V power supply (minimum 2A) |
| No WiFi | Verify credentials, check signal strength |
| Camera fails | Check ribbon cable, ensure proper power |
| Can't upload | GPIO0 to GND, check COM port |
| No stream | Try different browser, check network |
| Sensors not working | Check wiring, verify pin assignments |

---

## 🎯 Success Indicators

✅ **Green LED** on ESP32-CAM indicates power  
✅ **Serial Monitor** shows successful initialization  
✅ **WiFi Connected** message appears  
✅ **IP Address** is displayed  
✅ **Web Interface** loads in browser  
✅ **Video Stream** shows live feed  
✅ **Sensor Data** updates every 3 seconds  
✅ **Detection Controls** work properly  

---

**🎉 Your ESP32-CAM Agro Rover is now ready for agricultural monitoring!**
