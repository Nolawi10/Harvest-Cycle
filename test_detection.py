from ultralytics import YOLO
import cv2
import time

print("🚀 Starting YOLO Detection Test...")

# 1. Load and export YOLO model
print("📦 Loading YOLOv11 model...")
model = YOLO('yolo11n.pt') 
print("✅ Model loaded successfully!")

# 2. Export to OpenVINO for Intel GPU acceleration
print("🔧 Exporting to OpenVINO format...")
try:
    model.export(format='openvino')
    print("✅ OpenVINO export successful!")
except Exception as e:
    print(f"❌ OpenVINO export failed: {e}")
    print("🔄 Using regular model instead...")

# 3. Load the optimized version
print("🎯 Loading optimized model...")
try:
    ov_model = YOLO('yolo11n_openvino_model/')
    print("✅ OpenVINO model loaded!")
    use_model = ov_model
    device = 'intel:gpu'
except:
    print("⚠️ OpenVINO model not found, using regular model")
    use_model = model
    device = 'cpu'

# 4. Test with webcam
print("📹 Starting webcam detection...")
print("🎮 Controls: Press 'q' to quit, 'c' to capture frame")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Could not open webcam!")
    exit()

print("🟢 Webcam opened successfully!")
print("🔍 Starting detection loop...")

frame_count = 0
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Could not read frame!")
        break
    
    # Run detection every frame for real-time performance
    results = use_model(frame, verbose=False, device=device)
    
    # Process results and draw boxes
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                # Get bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                
                # Get class and confidence
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                # COCO class names
                coco_classes = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
                
                class_name = coco_classes[cls] if cls < len(coco_classes) else f"class_{cls}"
                
                # Draw bounding box
                color = (0, 255, 0)  # Green for all objects
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{class_name}: {conf:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
                cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    # Calculate FPS
    frame_count += 1
    if frame_count % 30 == 0:
        fps = 30 / (time.time() - start_time)
        start_time = time.time()
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        print(f"📊 FPS: {fps:.1f}")
    
    # Show the frame
    cv2.imshow('🎯 YOLO Detection Test', frame)
    
    # Handle key presses
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("🛑 Quitting...")
        break
    elif key == ord('c'):
        # Capture and save frame
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"detection_test_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        print(f"📸 Frame saved as {filename}")

# Cleanup
cap.release()
cv2.destroyAllWindows()
print("✅ Test completed!")
