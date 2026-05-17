/*
 * ESP32-CAM Live Feed Only - AI Agro Rover
 * Updated for Nolawi Hotspot
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// ==================== ESP32-CAM AI THINKER PIN CONFIGURATION ====================
#define CAMERA_MODEL_AI_THINKER

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5

#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ==================== GPIO PINS ====================
#define LED_PIN           4   // Built-in Flash LED

// ==================== WIFI CONFIGURATION ====================
// Updated to your Hotspot credentials
const char* ssid = "Nolawi";
const char* password = "12345678";

// ==================== WEB SERVER ====================
WebServer server(80);

// ==================== SYSTEM DATA ====================
struct SystemData {
  bool cameraActive;
  int detectionCount;
  unsigned long uptime;
  int wifiSignal;
  int freeHeap;
};

SystemData systemData = {0};

// ==================== CAMERA INITIALIZATION ====================
void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // SVGA provides the full Field of View (zoomed out) on OV2640
  config.frame_size = FRAMESIZE_SVGA; 
  // Higher value = lower quality, smaller file size -> much higher FPS
  config.jpeg_quality = 16;          
  config.fb_count = 2;               

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }

  sensor_t * s = esp_camera_sensor_get();
  s->set_brightness(s, 0);
  s->set_whitebal(s, 1);
  s->set_hmirror(s, 0);
  s->set_vflip(s, 0);
  // Enable downsize coordinate window (crucial for full zoomed out FOV on subsets)
  s->set_dcw(s, 1);

  systemData.cameraActive = true;
  Serial.println("Camera initialized successfully!");
}

// ==================== WEB SERVER HANDLERS ====================
void handleRoot() {
  String html = "<!DOCTYPE html><html><head>";
  html += "<title>ESP32-CAM Nolawi Feed</title>";
  html += "<meta name='viewport' content='width=device-width, initial-scale=1'>";
  html += "<style>";
  html += "body { font-family: Arial; background: #1a1a1a; color: white; text-align: center; }";
  html += ".container { max-width: 800px; margin: 0 auto; padding: 20px; }";
  html += ".stream { width: 100%; max-width: 640px; border: 3px solid #4CAF50; border-radius: 10px; }";
  html += ".status { background: #333; padding: 15px; border-radius: 8px; margin: 20px 0; display: flex; justify-content: space-around; }";
  html += ".btn { padding: 12px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }";
  html += ".info { background: #2196F3; padding: 10px; border-radius: 8px; font-size: 0.9em; }";
  html += "</style></head><body>";
  
  html += "<div class='container'>";
  html += "<h1>Rover Live Feed</h1>";
  
  html += "<div class='status'>";
  html += "<div>WiFi: <span id='wifiStatus'>--</span> dBm</div>";
  html += "<div>Uptime: <span id='uptime'>0</span>s</div>";
  html += "<div>Detections: <span id='detectionCount'>0</span></div>";
  html += "</div>";
  
  html += "<img src='/stream' class='stream' id='cameraStream'>";
  
  html += "<div style='margin: 20px 0;'>";
  html += "<button class='btn' onclick=\"fetch('/control?action=flash')\">Toggle Flash</button> ";
  html += "<button class='btn' style='background:#f44336' onclick=\"fetch('/control?action=reset')\">Reset Counter</button>";
  html += "</div>";

  html += "<div class='info'>";
  html += "<p>Connected to Hotspot: <strong>Nolawi</strong></p>";
  html += "<p>IP Address: " + WiFi.localIP().toString() + "</p>";
  html += "</div>";
  
  html += "</div>";
  
  html += "<script>";
  html += "setInterval(() => {";
  html += "  fetch('/status').then(r => r.json()).then(data => {";
  html += "    document.getElementById('wifiStatus').innerText = data.wifiSignal;";
  html += "    document.getElementById('uptime').innerText = data.uptime;";
  html += "    document.getElementById('detectionCount').innerText = data.detectionCount;";
  html += "  });";
  html += "}, 3000);";
  html += "</script></body></html>";
  
  server.send(200, "text/html", html);
}

void handleStream() {
  WiFiClient client = server.client();
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  server.sendContent(response);

  while (client.connected()) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) break;

    String frameHeader = "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + String(fb->len) + "\r\n\r\n";
    server.sendContent(frameHeader);
    client.write(fb->buf, fb->len);
    server.sendContent("\r\n");
    
    esp_camera_fb_return(fb);
    delay(1); 
  }
}

void handleStatus() {
  systemData.uptime = millis() / 1000;
  systemData.wifiSignal = WiFi.RSSI();
  systemData.freeHeap = ESP.getFreeHeap();
  
  String json = "{";
  json += "\"uptime\":" + String(systemData.uptime) + ",";
  json += "\"wifiSignal\":" + String(systemData.wifiSignal) + ",";
  json += "\"detectionCount\":" + String(systemData.detectionCount) + ",";
  json += "\"freeHeap\":" + String(systemData.freeHeap);
  json += "}";
  server.send(200, "application/json", json);
}

void handleControl() {
  String action = server.arg("action");
  if (action == "flash") {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  } else if (action == "reset") {
    systemData.detectionCount = 0;
  }
  server.send(200, "text/plain", "OK");
}

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  initCamera();
  
  Serial.print("Connecting to Hotspot: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    
    Serial.println("\n--- Access Points ---");
    Serial.print("Live Stream: http://");
    Serial.print(WiFi.localIP());
    Serial.println("/stream");
    
    Serial.print("Web Interface: http://");
    Serial.println(WiFi.localIP());
    Serial.println("---------------------\n");
  } else {
    Serial.println("\nConnection Failed. Check Hotspot/Credentials.");
  }
  
  server.on("/", handleRoot);
  server.on("/stream", handleStream);
  server.on("/status", handleStatus);
  server.on("/control", handleControl);
  
  server.begin();
}

void loop() {
  server.handleClient();
}
