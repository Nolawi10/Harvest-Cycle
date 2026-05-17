"""
Create sample dataset for YOLO training
Generates synthetic weed and crop images for testing
"""

import cv2
import numpy as np
from pathlib import Path
import random

def create_sample_image(width=416, height=416):
    """Create a sample image with synthetic weeds and crops"""
    # Create green background (soil/plant)
    image = np.random.randint(50, 100, (height, width, 3), dtype=np.uint8)
    image[:, :, 1] = np.minimum(image[:, :, 1] + 50, 255)  # Add green tint
    
    # Add some texture
    noise = np.random.normal(0, 10, (height, width, 3))
    image = np.clip(image + noise, 0, 255).astype(np.uint8)
    
    return image

def draw_weed(image, x, y, w, h):
    """Draw a synthetic weed"""
    # Weed is typically small, irregular, dark green
    weed_color = (20, 80, 20)  # Dark green
    
    # Draw simple irregular shape using circles
    center_x, center_y = x + w//2, y + h//2
    radius = min(w, h) // 3
    
    # Draw multiple circles to create irregular shape
    for i in range(5):
        offset_x = random.randint(-radius//2, radius//2)
        offset_y = random.randint(-radius//2, radius//2)
        cv2.circle(image, (center_x + offset_x, center_y + offset_y), 
                   radius, weed_color, -1)
    
    # Add some texture
    texture = np.random.normal(0, 3, (h, w, 3))
    roi = image[y:y+h, x:x+w]
    roi = np.clip(roi + texture, 0, 255).astype(np.uint8)
    image[y:y+h, x:x+w] = roi

def draw_crop(image, x, y, w, h):
    """Draw a synthetic crop"""
    # Crop is typically larger, regular, bright green
    crop_color = (50, 200, 50)  # Bright green
    
    # Draw regular crop shape (rectangle with rounded corners)
    cv2.rectangle(image, (x, y), (x+w, y+h), crop_color, -1)
    
    # Add some texture/pattern
    for i in range(0, w, 20):
        cv2.line(image, (x+i, y), (x+i, y+h), (30, 150, 30), 1)
    
    # Add leaves
    leaf_size = 10
    for _ in range(3):
        lx = random.randint(x+5, x+w-5)
        ly = random.randint(y+5, y+h-5)
        cv2.circle(image, (lx, ly), leaf_size, (40, 180, 40), -1)

def create_yolo_label(x, y, w, h, image_width, image_height, class_id):
    """Create YOLO format label"""
    # Convert to YOLO format (normalized coordinates)
    x_center = (x + w/2) / image_width
    y_center = (y + h/2) / image_height
    width = w / image_width
    height = h / image_height
    
    return f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"

def create_dataset(num_images=20, train_ratio=0.8):
    """Create complete dataset"""
    dataset_path = Path("dataset")
    images_train = dataset_path / "images" / "train"
    images_val = dataset_path / "images" / "val"
    labels_train = dataset_path / "labels" / "train"
    labels_val = dataset_path / "labels" / "val"
    
    # Ensure directories exist
    images_train.mkdir(parents=True, exist_ok=True)
    images_val.mkdir(parents=True, exist_ok=True)
    labels_train.mkdir(parents=True, exist_ok=True)
    labels_val.mkdir(parents=True, exist_ok=True)
    
    num_train = int(num_images * train_ratio)
    num_val = num_images - num_train
    
    print(f"Creating {num_train} training images and {num_val} validation images...")
    
    # Create training images
    for i in range(num_train):
        image = create_sample_image()
        
        # Add random objects
        labels = []
        num_objects = random.randint(1, 4)
        
        for _ in range(num_objects):
            # Random position and size
            obj_w = random.randint(30, 80)
            obj_h = random.randint(30, 80)
            obj_x = random.randint(10, 416 - obj_w - 10)
            obj_y = random.randint(10, 416 - obj_h - 10)
            
            # Random class (0=weed, 1=crop)
            class_id = random.choice([0, 1])
            
            if class_id == 0:  # Weed
                draw_weed(image, obj_x, obj_y, obj_w, obj_h)
            else:  # Crop
                draw_crop(image, obj_x, obj_y, obj_w, obj_h)
            
            # Create YOLO label
            label = create_yolo_label(obj_x, obj_y, obj_w, obj_h, 416, 416, class_id)
            labels.append(label)
        
        # Save image
        image_path = images_train / f"image_{i:04d}.jpg"
        cv2.imwrite(str(image_path), image)
        
        # Save labels
        label_path = labels_train / f"image_{i:04d}.txt"
        with open(label_path, 'w') as f:
            f.write('\n'.join(labels))
        
        if (i + 1) % 5 == 0:
            print(f"Created {i + 1}/{num_train} training images...")
    
    # Create validation images
    for i in range(num_val):
        image = create_sample_image()
        
        # Add random objects
        labels = []
        num_objects = random.randint(1, 3)
        
        for _ in range(num_objects):
            obj_w = random.randint(30, 80)
            obj_h = random.randint(30, 80)
            obj_x = random.randint(10, 416 - obj_w - 10)
            obj_y = random.randint(10, 416 - obj_h - 10)
            class_id = random.choice([0, 1])
            
            if class_id == 0:  # Weed
                draw_weed(image, obj_x, obj_y, obj_w, obj_h)
            else:  # Crop
                draw_crop(image, obj_x, obj_y, obj_w, obj_h)
            
            label = create_yolo_label(obj_x, obj_y, obj_w, obj_h, 416, 416, class_id)
            labels.append(label)
        
        # Save image
        image_path = images_val / f"val_{i:04d}.jpg"
        cv2.imwrite(str(image_path), image)
        
        # Save labels
        label_path = labels_val / f"val_{i:04d}.txt"
        with open(label_path, 'w') as f:
            f.write('\n'.join(labels))
        
        if (i + 1) % 5 == 0:
            print(f"Created {i + 1}/{num_val} validation images...")
    
    print("Dataset creation completed!")
    print(f"Training images: {num_train}")
    print(f"Validation images: {num_val}")
    print(f"Dataset saved to: {dataset_path}")

if __name__ == "__main__":
    create_dataset(num_images=20, train_ratio=0.8)
