# AI Agro Rover ML Systems

Complete machine learning systems for AI-powered agricultural rover with real-time weed detection and smart irrigation decisions.

## System Overview

This package contains two integrated ML systems:

1. **Weed Detection** - Real-time YOLO-based weed and crop detection
2. **Smart Irrigation** - Multi-parameter irrigation decision engine

## File Structure

```
ml/
|--- utils.py                 # Common utilities and helper functions
|--- train_yolo.py           # YOLO training script for weed detection
|--- detect.py               # Real-time weed detection (webcam/ESP32)
|--- irrigation_model.py     # Smart irrigation decision system
|--- integrated_system.py    # Complete integrated rover system
|--- README.md               # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install ultralytics opencv-python numpy scikit-learn pandas requests
```

### 2. Train Weed Detection Model

```bash
cd ml
python train_yolo.py
```

This will:
- Load dataset from `dataset/` directory
- Train YOLOv8n model (15 epochs, 416px images)
- Save model to `runs/detect/train/weights/best.pt`

### 3. Test Weed Detection

```bash
# Test with webcam
python detect.py --source 0

# Test with ESP32-CAM
python detect.py --source http://192.168.1.5/stream

# Test on images
python detect.py --source test_images/
```

### 4. Test Smart Irrigation

```bash
python irrigation_model.py
```

### 5. Run Complete Integrated System

```bash
# With webcam
python integrated_system.py --source 0

# With ESP32-CAM
python integrated_system.py --source http://192.168.1.5/stream
```

## Detailed Usage

### Weed Detection System

#### Training
```python
from ml.train_yolo import YOLOTrainer

trainer = YOLOTrainer(dataset_path="dataset", model_size="n")
trainer.load_model(pretrained=True)
results = trainer.train(epochs=15, imgsz=416, batch=8)
```

#### Real-time Detection
```python
from ml.detect import WeedDetector

detector = WeedDetector(model_path="runs/detect/train/weights/best.pt")
detections, annotated_frame = detector.detect_frame(frame)
```

#### ESP32-CAM Integration
```python
from ml.detect import ESP32StreamDetector

esp32_detector = ESP32StreamDetector(esp32_ip="192.168.1.5")
esp32_detector.start_detection()
```

### Smart Irrigation System

#### Rule-based Decisions
```python
from ml.irrigation_model import IrrigationDecisionEngine

engine = IrrigationDecisionEngine('rule_based')
decision = engine.predict_irrigation(soil_moisture=25, temperature=30, humidity=40)
```

#### ML-based Decisions
```python
engine = IrrigationDecisionEngine('decision_tree')
engine.train_ml_model(dataset_size=1000)
decision = engine.predict_irrigation(soil_moisture=25, temperature=30, humidity=40)
```

#### Complete Controller
```python
from ml.irrigation_model import SmartIrrigationController

controller = SmartIrrigationController('random_forest')
decision = controller.update_sensors(soil_moisture, temperature, humidity)
```

### Integrated System

```python
from ml.integrated_system import IntegratedAgroRover

rover = IntegratedAgroRover(
    model_path="runs/detect/train/weights/best.pt",
    esp32_ip="192.168.1.5",
    irrigation_model='decision_tree'
)
rover.run_integrated_system(source="0", skip_frames=2)
```

## Dataset Format

### YOLO Dataset Structure
```
dataset/
|--- images/
|   |--- train/
|   |--- val/
|--- labels/
|   |--- train/
|   |--- val/
|--- data.yaml
```

### data.yaml Example
```yaml
train: dataset/images/train
val: dataset/images/val
nc: 2
names: ['weed', 'crop']
```

### Label Format
Each `.txt` file should contain:
```
<class_id> <x_center> <y_center> <width> <height>
```

## Performance Optimization

### For Real-time Performance
- Use YOLOv8n (nano) model
- Reduce image size to 416x416
- Skip frames (skip_frames=2)
- Use GPU if available

### Memory Optimization
- Limit queue sizes
- Clear old frames regularly
- Use efficient data structures

### Accuracy vs Speed Trade-offs
```python
# High accuracy (slower)
detector = WeedDetector(confidence=0.7, iou_threshold=0.3)

# High speed (less accurate)
detector = WeedDetector(confidence=0.3, iou_threshold=0.5)
```

## Irrigation Decision Logic

### Rule-based System
- **LOW**: Normal conditions
- **MEDIUM**: Low moisture + low humidity
- **HIGH**: Very low moisture + high temperature

### ML Models
- **Decision Tree**: Fast, interpretable
- **Random Forest**: More accurate, ensemble method

### Input Parameters
- `soil_moisture`: 0-100%
- `temperature`: -50 to 60°C
- `humidity`: 0-100%
- `time_of_day`: morning/afternoon/night
- `weed_density`: weeds per unit area

## Integration with Flask

The ML systems are designed to integrate seamlessly with Flask:

```python
from ml.integrated_system import IntegratedAgroRover

# Initialize in Flask app
rover = IntegratedAgroRover()

@app.route('/api/detect')
def api_detect():
    # Get frame from ESP32
    frame = get_frame_from_esp32()
    detections, _ = rover.weed_detector.detect_frame(frame)
    return jsonify(detections)

@app.route('/api/irrigation')
def api_irrigation():
    decision = rover.irrigation_controller.update_sensors(moisture, temp, humidity)
    return jsonify(decision)
```

## Troubleshooting

### Common Issues

1. **Model not found**: Ensure `runs/detect/train/weights/best.pt` exists
2. **ESP32 connection failed**: Check ESP32 IP and network connection
3. **Low FPS**: Reduce image size or increase skip_frames
4. **Memory issues**: Reduce queue sizes or batch sizes

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Monitoring
```python
stats = rover.performance_monitor.get_stats()
print(f"FPS: {stats['fps']:.1f}")
print(f"Average frame time: {stats['avg_frame_time']*1000:.1f}ms")
```

## Model Files

After training, you'll find:
- `runs/detect/train/weights/best.pt` - Best YOLO model
- `models/irrigation_*.pkl` - Trained irrigation models
- `reports/system_report.json` - System performance reports

## Future Enhancements

- **Multi-class detection**: Add more crop/weed types
- **Advanced irrigation**: Weather forecast integration
- **Edge optimization**: TensorFlow Lite models
- **Sensor fusion**: Combine multiple sensor inputs
- **Active learning**: Improve models with new data

## License

This code is part of the AI Agro Rover project. Use according to project guidelines.
