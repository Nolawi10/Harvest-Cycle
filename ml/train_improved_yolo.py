"""
Improved YOLO Training for Weed Detection
Advanced techniques for higher accuracy
"""

import cv2
import numpy as np
import yaml
from pathlib import Path
from ultralytics import YOLO
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedYOLOTrainer:
    """Enhanced YOLO trainer with accuracy improvements"""
    
    def __init__(self, dataset_path="d:/agri car/dataset", 
                 model_size="s", pretrained=True):
        """
        Initialize improved YOLO trainer
        
        Args:
            dataset_path: Path to dataset
            model_size: Model size (n/s/m/l/x) - using 's' for better accuracy
            pretrained: Use pretrained weights
        """
        self.dataset_path = Path(dataset_path)
        self.model_size = model_size
        self.model = None
        self.results = None
        
        # Check if dataset exists
        if not self.dataset_path.exists():
            logger.error(f"Dataset not found at {dataset_path}")
            self.model = None
            return
        
        self._setup_dataset()
        self._load_model(pretrained)
    
    def _setup_dataset(self):
        """Setup and validate dataset"""
        # Create data.yaml for YOLO
        data_config = {
            'train': str(self.dataset_path / "images" / "train"),
            'val': str(self.dataset_path / "images" / "val"),
            'test': str(self.dataset_path / "images" / "test"),
            'nc': 2,  # Number of classes
            'names': ['crop', 'weed']  # Class names
        }
        
        data_yaml_path = self.dataset_path / "data.yaml"
        with open(data_yaml_path, 'w') as f:
            yaml.dump(data_config, f, default_flow_style=False)
        
        logger.info(f"Dataset configuration created: {data_yaml_path}")
        logger.info(f"Classes: {data_config['names']}")
        
        # Count dataset items
        train_count = len(list((self.dataset_path / "images" / "train").glob("*.jpg")))
        val_count = len(list((self.dataset_path / "images" / "val").glob("*.jpg")))
        test_count = len(list((self.dataset_path / "images" / "test").glob("*.jpg")))
        
        logger.info(f"Dataset split - Train: {train_count}, Val: {val_count}, Test: {test_count}")
    
    def _load_model(self, pretrained=True):
        """Load YOLO model with improved configuration"""
        model_name = f"yolov8{self.model_size}.pt"
        
        if pretrained:
            self.model = YOLO(model_name)
            logger.info(f"Loaded pretrained {model_name}")
        else:
            self.model = YOLO(model_name.replace('.pt', '-cls.yaml'))
            logger.info(f"Loaded {model_name} without pretrained weights")
    
    def analyze_dataset(self):
        """Analyze dataset characteristics for better training"""
        logger.info("Analyzing dataset...")
        
        # Sample some images to get statistics
        train_images = list((self.dataset_path / "images" / "train").glob("*.jpg"))
        sample_images = train_images[:min(100, len(train_images))]
        
        sizes = []
        aspect_ratios = []
        
        for img_path in sample_images:
            img = cv2.imread(str(img_path))
            if img is not None:
                h, w = img.shape[:2]
                sizes.append((w, h))
                aspect_ratios.append(w/h)
        
        if sizes:
            avg_width = np.mean([s[0] for s in sizes])
            avg_height = np.mean([s[1] for s in sizes])
            avg_aspect = np.mean(aspect_ratios)
            
            logger.info(f"Average image size: {avg_width:.0f}x{avg_height:.0f}")
            logger.info(f"Average aspect ratio: {avg_aspect:.2f}")
            
            # Recommend image size based on dataset
            if avg_width > 800 or avg_height > 800:
                recommended_size = 640
            elif avg_width > 600 or avg_height > 600:
                recommended_size = 512
            else:
                recommended_size = 416
            
            logger.info(f"Recommended training image size: {recommended_size}")
            return recommended_size
        
        return 640  # Default
    
    def train(self, epochs=50, imgsz=None, batch=16, patience=20):
        """
        Train model with enhanced techniques
        
        Args:
            epochs: Number of training epochs
            imgsz: Image size (auto-determined if None)
            batch: Batch size
            patience: Early stopping patience
        """
        if not self.model:
            logger.error("Model not loaded")
            return None
        
        # Auto-determine image size if not specified
        if imgsz is None:
            imgsz = self.analyze_dataset()
        
        logger.info(f"Starting improved training with {epochs} epochs, imgsz={imgsz}, batch={batch}")
        
        # Enhanced training configuration
        results = self.model.train(
            data=str(self.dataset_path / "data.yaml"),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device='cpu',  # Force CPU
            name='improved_train',
            project='runs/detect',
            exist_ok=True,
            pretrained=True,
            
            # Enhanced hyperparameters for better accuracy
            optimizer='AdamW',  # Better than Adam
            lr0=0.001,  # Lower learning rate for stability
            lrf=0.01,  # Final learning rate
            momentum=0.937,
            weight_decay=0.0005,
            warmup_epochs=5,  # Longer warmup
            warmup_momentum=0.8,
            warmup_bias_lr=0.1,
            
            # Loss function weights
            box=7.5,
            cls=1.0,
            dfl=1.5,
            pose=12.0,
            kobj=1.0,
            
            # Data augmentation
            hsv_h=0.015,  # Hue augmentation
            hsv_s=0.7,    # Saturation augmentation
            hsv_v=0.4,    # Value augmentation
            degrees=0.0,  # Rotation
            translate=0.1,  # Translation
            scale=0.5,    # Scale
            shear=0.0,    # Shear
            perspective=0.0,  # Perspective
            flipud=0.0,   # Vertical flip
            fliplr=0.5,   # Horizontal flip
            mosaic=1.0,   # Mosaic augmentation
            mixup=0.0,    # Mixup augmentation
            
            # Training control
            patience=patience,  # Early stopping
            save_period=10,    # Save every 10 epochs
            cache=False,       # Disable caching for CPU
            
            # Performance
            workers=4,
            amp=False,  # Disable AMP for CPU
            fraction=1.0,  # Use all data
            
            # Validation
            val=True,
            plots=True,
            save_json=True,  # Save COCO results
        )
        
        logger.info("Improved training completed!")
        logger.info(f"Best model saved at: runs/detect/improved_train/weights/best.pt")
        
        self.results = results
        return results
    
    def validate_model(self, conf=0.25, iou=0.45):
        """Validate trained model with detailed metrics"""
        if not self.model:
            logger.error("Model not loaded")
            return None
        
        logger.info("Validating improved model...")
        
        # Load best model
        best_model_path = "runs/detect/improved_train/weights/best.pt"
        if Path(best_model_path).exists():
            self.model = YOLO(best_model_path)
        
        results = self.model.val(
            data=str(self.dataset_path / "data.yaml"),
            imgsz=640,
            batch=16,
            conf=conf,
            iou=iou,
            device='cpu',
            split='val',  # Validate on validation set
            plots=True,
            save_json=True,
        )
        
        logger.info(f"Validation completed. mAP50: {results.box.map50:.3f}")
        logger.info(f"mAP50-95: {results.box.map:.3f}")
        logger.info(f"Precision: {results.box.mp:.3f}")
        logger.info(f"Recall: {results.box.mr:.3f}")
        
        return results
    
    def test_model(self):
        """Test model on test set"""
        if not self.model:
            logger.error("Model not loaded")
            return None
        
        logger.info("Testing model on test set...")
        
        results = self.model.val(
            data=str(self.dataset_path / "data.yaml"),
            imgsz=640,
            batch=16,
            device='cpu',
            split='test',  # Test on test set
            plots=True,
        )
        
        logger.info(f"Test completed. mAP50: {results.box.map50:.3f}")
        return results
    
    def export_model(self, format='onnx'):
        """Export model to different formats"""
        if not self.model:
            logger.error("Model not loaded")
            return False
        
        logger.info(f"Exporting model to {format}...")
        
        # Load best model
        best_model_path = "runs/detect/improved_train/weights/best.pt"
        if Path(best_model_path).exists():
            self.model = YOLO(best_model_path)
        
        try:
            results = self.model.export(format=format, imgsz=640, device='cpu')
            logger.info(f"Model exported successfully to {format}")
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def analyze_performance(self):
        """Analyze and visualize training performance"""
        if not self.results:
            logger.error("No training results available")
            return
        
        logger.info("Performance Analysis:")
        logger.info(f"Training epochs: {len(self.results)}")
        logger.info(f"Best mAP50: {max([r['metrics/mAP50'] for r in self.results]):.3f}")
        logger.info(f"Best mAP50-95: {max([r['metrics/mAP50-95'] for r in self.results]):.3f}")
        
        # Class-wise performance
        if 'results_dict' in dir(self.results):
            results_dict = self.results.results_dict
            logger.info("Class-wise performance:")
            for class_name in ['crop', 'weed']:
                if class_name in results_dict:
                    class_metrics = results_dict[class_name]
                    logger.info(f"{class_name}: AP50={class_metrics.get('AP50', 0):.3f}")

def main():
    """Main function for improved YOLO training"""
    logger.info("Improved YOLO Weed Detection Training")
    logger.info("=" * 50)
    
    # Initialize improved trainer
    trainer = ImprovedYOLOTrainer(
        dataset_path="d:/agri car/dataset",
        model_size="s",  # Use small model for better accuracy
        pretrained=True
    )
    
    if not trainer.model:
        logger.error("Failed to initialize trainer")
        return
    
    # Analyze dataset
    img_size = trainer.analyze_dataset()
    
    # Train with enhanced configuration
    results = trainer.train(
        epochs=50,  # More epochs for better convergence
        imgsz=img_size,
        batch=16,   # Adjust based on your memory
        patience=20  # Early stopping
    )
    
    if results:
        # Validate model
        val_results = trainer.validate_model(conf=0.25, iou=0.45)
        
        # Test model
        test_results = trainer.test_model()
        
        # Export model
        trainer.export_model(format='onnx')
        
        # Analyze performance
        trainer.analyze_performance()
        
        logger.info("Improved training pipeline completed successfully!")
    else:
        logger.error("Training failed")

if __name__ == "__main__":
    main()
