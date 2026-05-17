"""
Dataset Enhancement for YOLO Training
Advanced data augmentation techniques to improve model accuracy
"""

import cv2
import numpy as np
import random
import albumentations as A
from pathlib import Path
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatasetEnhancer:
    """Advanced dataset augmentation for YOLO training"""
    
    def __init__(self, dataset_path="d:/agri car/dataset"):
        """
        Initialize dataset enhancer
        
        Args:
            dataset_path: Path to dataset
        """
        self.dataset_path = Path(dataset_path)
        self.images_path = self.dataset_path / "images" / "train"
        self.labels_path = self.dataset_path / "labels" / "train"
        
        # Enhanced augmentation pipeline
        self.transform = A.Compose([
            # Geometric augmentations
            A.RandomRotate90(p=0.5),
            A.Flip(p=0.5),
            A.Transpose(p=0.3),
            A.ShiftScaleRotate(
                shift_limit=0.1,
                scale_limit=0.2,
                rotate_limit=15,
                p=0.7
            ),
            
            # Color augmentations
            A.RandomBrightnessContrast(
                brightness_limit=0.3,
                contrast_limit=0.3,
                p=0.8
            ),
            A.HueSaturationValue(
                hue_shift_limit=20,
                sat_shift_limit=30,
                val_shift_limit=20,
                p=0.8
            ),
            A.CLAHE(p=0.3),
            
            # Noise and blur
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
            A.GaussianBlur(blur_limit=3, p=0.2),
            
            # Weather effects
            A.RandomRain(p=0.1),
            A.RandomFog(p=0.1),
            A.RandomSunFlare(p=0.05),
            
            # Crop and resize
            A.RandomResizedCrop(
                height=416,
                width=416,
                scale=(0.8, 1.0),
                ratio=(0.9, 1.1),
                p=0.5
            ),
        ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
    
    def load_yolo_labels(self, label_path):
        """Load YOLO format labels"""
        if not label_path.exists():
            return []
        
        with open(label_path, 'r') as f:
            lines = f.readlines()
        
        bboxes = []
        class_labels = []
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                
                bboxes.append([x_center, y_center, width, height])
                class_labels.append(class_id)
        
        return bboxes, class_labels
    
    def save_yolo_labels(self, label_path, bboxes, class_labels):
        """Save YOLO format labels"""
        with open(label_path, 'w') as f:
            for bbox, class_id in zip(bboxes, class_labels):
                x_center, y_center, width, height = bbox
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
    
    def augment_image(self, image_path, label_path, augmentations_per_image=3):
        """Augment a single image with multiple variations"""
        try:
            # Load image and labels
            image = cv2.imread(str(image_path))
            if image is None:
                return []
            
            bboxes, class_labels = self.load_yolo_labels(label_path)
            if not bboxes:
                return []
            
            augmented_images = []
            
            # Create multiple augmentations
            for i in range(augmentations_per_image):
                # Apply augmentation
                transformed = self.transform(
                    image=image,
                    bboxes=bboxes,
                    class_labels=class_labels
                )
                
                aug_image = transformed['image']
                aug_bboxes = transformed['bboxes']
                aug_labels = transformed['class_labels']
                
                # Save augmented image
                aug_filename = f"{image_path.stem}_aug_{i}{image_path.suffix}"
                aug_image_path = image_path.parent / aug_filename
                cv2.imwrite(str(aug_image_path), aug_image)
                
                # Save augmented labels
                aug_label_path = label_path.parent / f"{aug_filename[:-4]}.txt"
                self.save_yolo_labels(aug_label_path, aug_bboxes, aug_labels)
                
                augmented_images.append({
                    'image_path': aug_image_path,
                    'label_path': aug_label_path
                })
            
            return augmented_images
        
        except Exception as e:
            logger.error(f"Error augmenting {image_path}: {e}")
            return []
    
    def enhance_dataset(self, augmentations_per_image=2, max_workers=4):
        """Enhance the entire dataset"""
        logger.info("Starting dataset enhancement...")
        
        # Get all training images
        image_files = list(self.images_path.glob("*.jpg"))
        logger.info(f"Found {len(image_files)} training images")
        
        # Process images in parallel
        all_augmented = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            for image_path in image_files:
                label_path = self.labels_path / f"{image_path.stem}.txt"
                
                if label_path.exists():
                    future = executor.submit(
                        self.augment_image,
                        image_path,
                        label_path,
                        augmentations_per_image
                    )
                    futures.append(future)
            
            # Collect results
            for i, future in enumerate(futures):
                try:
                    augmented = future.result()
                    all_augmented.extend(augmented)
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"Processed {i + 1}/{len(futures)} images...")
                
                except Exception as e:
                    logger.error(f"Error processing image: {e}")
        
        logger.info(f"Dataset enhancement completed!")
        logger.info(f"Created {len(all_augmented)} augmented images")
        logger.info(f"Total training images: {len(image_files) + len(all_augmented)}")
        
        return all_augmented
    
    def create_balanced_dataset(self):
        """Create a balanced dataset with equal weed and crop samples"""
        logger.info("Creating balanced dataset...")
        
        # Analyze class distribution
        weed_count = 0
        crop_count = 0
        
        for label_path in self.labels_path.glob("*.txt"):
            bboxes, class_labels = self.load_yolo_labels(label_path)
            weed_count += class_labels.count(1)  # weed class
            crop_count += class_labels.count(0)  # crop class
        
        logger.info(f"Current distribution - Weed: {weed_count}, Crop: {crop_count}")
        
        # Create synthetic samples if needed
        if abs(weed_count - crop_count) > min(weed_count, crop_count) * 0.2:
            logger.info("Dataset is imbalanced, creating balanced samples...")
            
            # This would involve creating synthetic samples for the minority class
            # For now, just report the imbalance
            imbalance_ratio = max(weed_count, crop_count) / min(weed_count, crop_count)
            logger.info(f"Imbalance ratio: {imbalance_ratio:.2f}")
    
    def validate_augmented_dataset(self):
        """Validate the augmented dataset"""
        logger.info("Validating augmented dataset...")
        
        # Check image-label correspondence
        image_files = set([f.stem for f in self.images_path.glob("*.jpg")])
        label_files = set([f.stem for f in self.labels_path.glob("*.txt")])
        
        missing_labels = image_files - label_files
        missing_images = label_files - image_files
        
        if missing_labels:
            logger.warning(f"Missing labels for {len(missing_labels)} images")
        
        if missing_images:
            logger.warning(f"Missing images for {len(missing_images)} labels")
        
        # Check label format
        invalid_labels = 0
        for label_path in self.labels_path.glob("*.txt"):
            try:
                bboxes, class_labels = self.load_yolo_labels(label_path)
                for bbox in bboxes:
                    if not all(0 <= coord <= 1 for coord in bbox):
                        invalid_labels += 1
                        break
            except:
                invalid_labels += 1
        
        if invalid_labels > 0:
            logger.warning(f"Found {invalid_labels} invalid label files")
        
        logger.info("Dataset validation completed")

def main():
    """Main function for dataset enhancement"""
    logger.info("Dataset Enhancement for YOLO Training")
    logger.info("=" * 40)
    
    # Initialize enhancer
    enhancer = DatasetEnhancer(
        dataset_path="d:/agri car/dataset"
    )
    
    # Create balanced dataset analysis
    enhancer.create_balanced_dataset()
    
    # Enhance dataset with augmentations
    augmented = enhancer.enhance_dataset(
        augmentations_per_image=2,  # Create 2 augmented versions per image
        max_workers=4  # Parallel processing
    )
    
    # Validate enhanced dataset
    enhancer.validate_augmented_dataset()
    
    logger.info("Dataset enhancement pipeline completed!")

if __name__ == "__main__":
    main()
