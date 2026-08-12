# Harvest Cycle

<p align="center">
  <img src="https://img.shields.io/badge/AI-PRECISION%20AGRICULTURE-2F855A?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Computer%20Vision-YOLOv11-111827?style=for-the-badge" />
  <img src="https://img.shields.io/badge/IoT-ESP32--CAM-00979D?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask&logoColor=white" />
</p>

<p align="center"><strong>An experimental precision-agriculture system connecting computer vision, IoT, irrigation intelligence, and circular biomass ideas.</strong></p>

<p align="center">
  <a href="https://github.com/Nolawi10/Harvest-Cycle">Repository</a> ·
  <a href="https://github.com/Nolawi10">Author</a>
</p>

---

## The Idea

Agricultural decisions are often made with incomplete information. Harvest Cycle explores a different workflow: use affordable cameras and connected hardware to **observe the field, interpret what is happening, support decisions, and connect those decisions to practical actions**.

> **Observe → Understand → Decide → Act → Measure**

The project brings together AI, IoT, and agriculture instead of treating them as separate prototypes.

---

## What It Combines

| System | Role |
|---|---|
| **Computer Vision** | Detect relevant plants/weeds from camera imagery. |
| **ESP32-CAM** | Provide an affordable field-camera path. |
| **Irrigation Logic** | Support water-release decisions using available measurements. |
| **Biomass Classification** | Explore useful downstream pathways for removed plant material. |
| **Flask Dashboard** | Bring monitoring, detection, and controls into one interface. |
| **OpenVINO** | Explore optimized CPU-oriented inference. |

---

## System Flow

```text
                FIELD
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
     CAMERA              SENSORS
        │                   │
        └─────────┬─────────┘
                  ▼
             AI / VISION
                  │
         ┌────────┴────────┐
         ▼                 ▼
   WEED / CROP         IRRIGATION
    ANALYSIS            DECISION
         │                 │
         └────────┬────────┘
                  ▼
             FARM ACTION
                  │
                  ▼
              DASHBOARD
                  │
                  ▼
              FEEDBACK
```

---

## How It Works

### Capture

An **ESP32-CAM** or local USB camera supplies field imagery. Device and sensor information can be exchanged through the project's integration layer.

### Detect

A **YOLOv11** model performs object detection. OpenCV handles image and video processing, while OpenVINO support provides an optimized inference path for compatible hardware.

### Decide

Detection results and available field information can feed irrigation and agricultural decision logic.

### Monitor

A **Flask dashboard** provides the web interface for camera feeds, detection controls, snapshots, and system information.

### Explore Circular Use

The project also investigates whether removed plant material can be classified for potential uses such as **compost, bio-slurry, or feed**, subject to proper agricultural and safety validation.

---

## Architecture

```text
┌───────────────────────┐
│     FIELD INPUTS      │
│ ESP32-CAM / USB Camera│
│       + Sensors       │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│     AI VISION         │
│      YOLOv11          │
│      OpenCV           │
│      OpenVINO         │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│    DECISION LAYER     │
│ Weed Analysis         │
│ Irrigation Logic      │
│ Biomass Classification│
└───────────┬───────────┘
            │
      ┌─────┴─────┐
      ▼           ▼
 Irrigation    Biomass
  Actions       Pathways
      │           │
      └─────┬─────┘
            ▼
┌───────────────────────┐
│     FLASK DASHBOARD   │
│ Live Feed · Status    │
│ Controls · Snapshots  │
└───────────────────────┘
```

---

## Technology

<p align="center">
<img src="https://skillicons.dev/icons?i=python,flask,opencv,arduino,github,vscode" />
</p>

**AI:** YOLOv11 · Ultralytics · OpenCV  
**Inference:** OpenVINO  
**Backend:** Flask / Python  
**Hardware:** ESP32-CAM · USB camera  
**Frontend:** HTML · CSS · JavaScript  
**Data:** YOLO-format image/label datasets

---

## Project Structure

```text
Harvest-Cycle/
├── app.py
├── esp32_integration.py
├── esp32cam_livefeed_fixed.ino
├── requirements.txt
├── templates/
├── static/
├── ml/
├── dataset/
├── yolo11n.pt
└── yolo11n_openvino_model/
```

---

## Machine Learning

The `ml/` directory contains the experimental training, detection, and irrigation workflows.

```bash
cd ml
python train_yolo.py
python detect.py --source 0
python irrigation_model.py
```

Dataset organization:

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

### Reproducibility

The repository currently contains the model and dataset structure needed for further experiments. Performance should be reported from measured runs using a fixed model, dataset split, input resolution, and hardware configuration.

Recommended metrics:

**Precision · Recall · mAP50 · mAP50-95 · FPS · Latency · Model Size**

---

## Hardware

### Current Integration

- ESP32-CAM for camera connectivity
- USB webcam for local development/testing
- Computer running the Flask application and inference pipeline

### Future Hardware

- Automated irrigation actuator
- Environmental sensor network
- Robotic weed-removal mechanism
- Edge-compute deployment

---

## Run Locally

### Requirements

- Python 3.10+
- Git
- Webcam or ESP32-CAM

### Setup

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

### Main Routes

| Route | Purpose |
|---|---|
| `/` | Project landing page |
| `/dashboard` | Monitoring and controls |
| `/live` | Live detection interface |
| `/how-it-works` | System explanation |
| `/video_feed` | Camera stream |

---

## Multimedia

The strongest way to understand Harvest Cycle is to see the system running.

Recommended project showcase:

| Asset | What it should show |
|---|---|
| **Demo video** | Complete system flow from camera to dashboard. |
| **Hardware photo** | ESP32-CAM and physical prototype. |
| **Detection image** | YOLO bounding boxes and predictions. |
| **Dashboard screenshot** | Monitoring interface and controls. |
| **Architecture diagram** | AI + IoT + agriculture pipeline. |
| **Results chart** | Measured model or system performance. |
| **Research poster** | Competition/conference presentation where applicable. |

---

## Why It Matters

Harvest Cycle is an exploration of **accessible precision agriculture**: using affordable hardware and AI to build systems that can operate closer to the field.

The larger engineering question is:

> **How can a low-cost intelligent system move from seeing a problem to helping act on it?**

That question connects the project's computer vision, IoT, irrigation, and robotics directions.

---

## Research Directions

Future experiments can investigate:

- Larger and more diverse field datasets
- Local weed-species benchmarking
- Model accuracy and latency across devices
- Edge inference and energy consumption
- Sensor-driven irrigation prediction
- Automatic actuator control
- Quantified water savings
- Robotic weed removal
- Biomass conversion efficiency
- Field trials across crops and environments

---

## Development Status

**Working AI + IoT agriculture prototype**

The repository provides the foundation for continued experimentation in computer vision, connected agriculture, and agricultural robotics.

---

## License

See the repository license for usage terms.

---

<p align="center"><strong>AI × IoT × Agriculture × Robotics</strong><br>From field observations to intelligent action.</p>
