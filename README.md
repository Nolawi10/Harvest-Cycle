# Harvest Cycle

**Harvest Cycle** is an AI-powered precision agriculture platform that combines real-time weed detection, smart irrigation, and circular biomass utilization. A Flask web dashboard streams live camera feeds, runs YOLO-based vision on the edge, and classifies removed weeds for feed, slurry, or compost — reducing chemical use while closing the nutrient loop on the farm.

## Features

- **Live weed detection** — YOLOv11 with optional OpenVINO acceleration for faster inference
- **Biomass classification** — Maps detected weed types to feed, bio-slurry, or compost use
- **ESP32-CAM integration** — Field camera stream and sensor data over HTTP
- **Smart irrigation** — Rule-based and ML decision models (`ml/irrigation_model.py`)
- **Web dashboard** — Live feed, detection settings, saved snapshots, and system status
- **3D rover visualization** — Interactive GLB models in the browser
- **ML toolkit** — Training, dataset enhancement, and standalone detection scripts under `ml/`

## Project structure

```
Harvest-Cycle/
├── app.py                 # Main Flask application
├── esp32_integration.py   # ESP32 camera & sensor routes
├── esp32cam_livefeed_fixed.ino
├── requirements.txt
├── templates/             # Web UI (dashboard, live, team, etc.)
├── static/                # CSS, JS, models, detections
├── ml/                    # Training, detection, irrigation ML
├── dataset/               # YOLO dataset (images + labels)
├── yolo11n.pt             # Base detection weights
└── yolo11n_openvino_model/  # Exported OpenVINO model
```

## Prerequisites

- Python 3.10+
- Webcam (optional; ESP32-CAM can be used instead)
- [Git](https://git-scm.com/) and a [GitHub](https://github.com/) account

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/Harvest-Cycle.git
cd Harvest-Cycle
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

On first run, Ultralytics may download `yolo11n.pt` automatically if it is missing.

### 4. Run the web application

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/dashboard` | Control panel & analytics |
| `/live` | Live detection view |
| `/how-it-works` | System architecture |
| `/video_feed` | MJPEG camera stream |

### 5. ESP32-CAM (optional)

1. Flash `esp32cam_livefeed_fixed.ino` to your ESP32-CAM.
2. Set the device IP in `esp32_integration.py` (default `192.168.1.100`).
3. Use **ESP32 feed** routes from the dashboard or POST to `/esp32_configure`.

## Training & ML

See [`ml/README.md`](ml/README.md) for full ML documentation.

```bash
cd ml
python train_yolo.py          # Train weed/crop detector
python detect.py --source 0   # Webcam test
python irrigation_model.py    # Irrigation decision demo
```

Dataset layout (YOLO format):

```
dataset/
├── images/train|val|test/
├── labels/train|val/
└── data.yaml
```

Update paths in `dataset/data.yaml` to match your machine after cloning.

## OpenVINO export (optional, faster CPU inference)

The app attempts to export and load an OpenVINO model on startup. To export manually:

```python
from ultralytics import YOLO
YOLO("yolo11n.pt").export(format="openvino")
```

## Hardware

- **ESP32-CAM** — Field video stream (`esp32cam_livefeed_fixed.ino`)
- **USB webcam** — Local development (camera index `0` in `app.py`)
- **Robotic arm** — Referenced in system diagrams; integration via future GPIO/API hooks

## Large files not in Git

The following are excluded via `.gitignore` (GitHub 100MB limit or size):

- Demo videos (`*.MOV`, `*.mp4`)
- Dataset zip archives under `dataset/images/`
- Duplicate folders `version 1/` and `static/history/`

Add your own media locally or attach releases on GitHub as needed.

## Troubleshooting

| Issue | Suggestion |
|-------|------------|
| Camera not found | Try another index in `app.py` or use ESP32 stream |
| Model load fails | Ensure `yolo11n.pt` exists; run `pip install ultralytics` |
| ESP32 unreachable | Check Wi-Fi, IP, and firewall on port 80 |
| Low FPS | Enable OpenVINO export or reduce resolution in `app.py` |

## Team & research

- `/team` — Project team
- `/research` — Research notes
- `/impact` — Environmental impact

## License

This project is provided for educational and research use. Add a `LICENSE` file if you choose a specific open-source license.

## Acknowledgments

Built with [Ultralytics YOLO](https://github.com/ultralytics/ultralytics), [Flask](https://flask.palletsprojects.com/), [OpenCV](https://opencv.org/), and ESP32-CAM hardware.
