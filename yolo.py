from ultralytics import YOLO
model = YOLO('yolo11n.pt') 
model.export(format='openvino')

# 3. Load the optimized version and run on your Intel GPU
# 'source=0' is your webcam. Press 'q' to stop.
ov_model = YOLO('yolo11n_openvino_model/')
ov_model.predict(source='0', device='intel:gpu', show=True)