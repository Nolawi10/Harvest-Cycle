# 🌾 Harvest Cycle

> **An AI-powered precision agriculture system combining computer vision, IoT, smart irrigation, and circular biomass utilization.**

Harvest Cycle explores how affordable AI and connected hardware can support more efficient and sustainable farming.

The system combines **YOLO-based weed detection**, **ESP32-CAM field monitoring**, **irrigation decision models**, and a web dashboard into one experimental precision-agriculture platform.

---

## 🎥 Project Showcase

> **Multimedia goes here:** add a 30–90 second demo video or GIF showing the camera feed, weed detection, dashboard, and hardware working together.

| 🌱 AI Detection | 📡 Field Hardware | 💧 Smart Irrigation |
|---|---|---|
| YOLO-based weed/crop vision | ESP32-CAM + sensors | Rule-based / ML decisions |

**Recommended media to add:**
- `media/demo.gif` — short product demonstration
- `media/dashboard.png` — dashboard screenshot
- `media/weed-detection.png` — annotated detection result
- `media/esp32cam.jpg` — physical hardware
- `media/irrigation.jpg` — irrigation prototype

---

## 🌱 The Problem

Agricultural productivity can be limited by inefficient weed management, unnecessary chemical use, and poorly timed irrigation. At the same time, removed plant biomass is often treated as waste instead of a potential resource.

Harvest Cycle was designed as an exploration of a different approach: **use computer vision and low-cost connected hardware to observe the field, support decisions, and connect those decisions to practical farm actions.**

---

## 💡 The Idea

Harvest Cycle connects four stages:

```text
Field Camera / Sensors
        ↓
Computer Vision
        ↓
Decision & Classification
        ↓
Farm Action
        ↓
Monitoring & Feedback
```

The platform is intended to demonstrate how these components can work together rather than treating AI, IoT, and agriculture as separate systems.

---

## 🧠 How It Works

### 1. 📷 Capture

An **ESP32-CAM** or local USB camera provides field imagery. Sensor and device information can also be exchanged through HTTP endpoints.

### 2. 🔎 Detect

A **YOLOv11** model performs real-time computer-vision inference to identify relevant weeds/crops. The project also supports **OpenVINO** export for faster CPU-oriented inference.

### 3. 🌿 Classify Biomass

Detected weed types can be mapped to possible downstream uses such as:

- Animal feed
- Bio-slurry
- Compost

This creates the foundation for a circular biomass workflow rather than treating every removed plant as waste.

### 4. 💧 Support Irrigation Decisions

The `ml/irrigation_model.py` component provides rule-based and ML-oriented irrigation decision logic that can be connected to field measurements and future actuator control.

### 5. 📊 Monitor

A **Flask dashboard** provides live camera feeds, detection controls, saved snapshots, and system-status information.

---

## 🏗️ System Architecture

```text
┌───────────────────┐
│   FIELD INPUTS    │
│ ESP32-CAM / Camera│
│     + Sensors     │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│    AI VISION      │
│     YOLOv11       │
│    + OpenVINO     │
└─────────┬─────────┘
          │
          ▼
┌────────────────────────┐
│    DECISION LAYER       │
│ Weed Classification     │
│ Irrigation Decision     │
└──────────┬─────────────┘
           │
     ┌─────┴──────────┐
     ▼                ▼
┌────────────┐  ┌───────────────┐
│ Irrigation │  │ Biomass Use   │
│ / Actuation│  │ Feed/Slurry/  │
│            │  │ Compost       │
└────────────┘  └───────────────┘
           │
           ▼
┌──────────────────────┐
│   FLASK DASHBOARD    │
│ Live Feed • Analytics│
│ Status • Snapshots   │
└──────────────────────┘
```

---

## 🧰 Technology Stack

| Layer | Technologies |
|---|---|
| Computer Vision | YOLOv11, OpenCV |
| Edge Optimization | OpenVINO |
| Machine Learning | Python, Ultralytics, custom ML scripts |
| Backend | Flask |
| Hardware | ESP32-CAM, USB camera |
| Frontend | HTML, CSS, JavaScript |
| 3D Visualization | GLB / browser-based 3D assets |
| Data | YOLO-format image + label datasets |

---

## 📁 Project Structure

```text
Harvest-Cycle/
├── app.py                         # Flask application
├── esp32_integration.py           # ESP32 camera/sensor routes
├── esp32cam_livefeed_fixed.ino    # ESP32-CAM firmware
├── requirements.txt
├── templates/                     # Web interface
├── static/                        # Frontend assets and models
├── ml/                            # Training, detection, irrigation ML
├── dataset/                       # YOLO images, labels, configuration
├── yolo11n.pt                     # Base YOLO weights
└── yolo11n_openvino_model/        # OpenVINO model
```

---

## 🧪 Machine Learning

The `ml/` directory contains the experimental ML workflow.

```bash
cd ml
python train_yolo.py
python detect.py --source 0
python irrigation_model.py
```

The dataset follows the YOLO structure:

```text
dataset/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   └── val/
└── data.yaml
```

For reproducible research, model metrics such as **precision, recall, mAP, FPS, and inference latency** should be recorded here as experiments are finalized.

### 📊 Results

| Metric | Result |
|---|---:|
| Detection model | YOLOv11 |
| Classes | See dataset configuration |
| Precision | _Add measured result_ |
| Recall | _Add measured result_ |
| mAP | _Add measured result_ |
| CPU inference FPS | _Add measured result_ |
| Hardware cost | _Add measured result_ |

> **No performance numbers are claimed here until they are measured and documented.**

---

## 🔌 Hardware

### Current hardware path

- **ESP32-CAM** — field camera and HTTP stream
- **USB webcam** — local development/testing

### Experimental / future hardware

- Automated irrigation actuator control
- Robotic weed-removal integration
- Additional environmental sensors

The robotic-arm concept is represented in the system design, while direct GPIO/API actuator integration remains an area for further development.

---

## 🚀 Run Locally

### Requirements

- Python 3.10+
- Webcam, or ESP32-CAM
- Git

### Installation

```bash
git clone https://github.com/Nolawi10/Harvest-Cycle.git
cd Harvest-Cycle

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

### Main routes

| Route | Purpose |
|---|---|
| `/` | Project landing page |
| `/dashboard` | Monitoring and controls |
| `/live` | Live detection |
| `/how-it-works` | System explanation |
| `/video_feed` | MJPEG camera stream |

---

## 📸 Multimedia Checklist

To make this repository an admissions-ready project portfolio, the recommended media sequence is:

1. **Hero demo** — 30–90 second overview
2. **Hardware photo** — ESP32-CAM / physical prototype
3. **Detection screenshot** — bounding boxes and predictions
4. **Dashboard screenshot** — live monitoring interface
5. **System diagram** — end-to-end architecture
6. **Results chart** — model performance or latency
7. **Research poster** — if presented at a competition/conference
8. **Demo presentation** — optional slide deck

Keep large videos out of Git history; link to a hosted demo/video when available.

---

## 🌍 Why It Matters

Harvest Cycle is an engineering experiment around **accessible precision agriculture**.

The broader goal is to explore how AI can move beyond a prediction on a screen and become part of a connected physical system:

> **See → Understand → Decide → Act → Measure**

This approach can support future work in agricultural automation, resource efficiency, and sustainable farming systems.

---

## 🔬 Research Direction

Future development can investigate:

- Larger and more diverse field datasets
- Model benchmarking across devices
- Edge inference latency and energy consumption
- Sensor-driven irrigation prediction
- Automated actuator control
- Weed-removal robotics
- Quantitative water savings
- Biomass conversion efficiency
- Field trials under different crops and conditions

The project is intentionally structured so that future experiments can replace assumptions with measured evidence.

---

## 👨🏾‍💻 Project

**Harvest Cycle** is part of my broader work exploring the intersection of **AI, robotics, agriculture, climate, and real-world engineering**.

**Developer:** [Nolawi Hailu](https://github.com/Nolawi10)

---

## 🙏 Acknowledgments

Built with [Ultralytics YOLO](https://github.com/ultralytics/ultralytics), [Flask](https://flask.palletsprojects.com/), [OpenCV](https://opencv.org/), and ESP32-CAM hardware.

---

## 📄 License

This project is provided for educational and research use. Add an explicit open-source license if you intend to distribute the code under specific terms.
