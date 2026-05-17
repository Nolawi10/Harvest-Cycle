"""
YOLO Training Script for Weed Detection
Trains lightweight YOLO model for agricultural weed detection
"""

import os
import sys
from pathlib import Path
import yaml
from ultralytics import YOLO
import torch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ml.utils import logger, Colors

class YOLOTrainer:
    """YOLO model trainer for weed detection"""
    
    def __init__(self, dataset_path="dataset", model_size="n"):
        """
        Initialize YOLO trainer
        
        Args:
            dataset_path: Path to YOLO dataset
            model_size: Model size (n=s, s=m, l=l, x=x)
        """
        self.dataset_path = Path(dataset_path)
        self.model_size = model_size
        self.model = None
        self.data_yaml = None
        
        # Check if dataset exists
        if not self.dataset_path.exists():
            logger.error(f"Dataset not found at {dataset_path}")
            logger.info("Please create dataset with structure:")
            logger.info("dataset/")
            logger.info("├── images/")
            logger.info("│   ├── train/")
            logger.info("│   └── val/")
            logger.info("├── labels/")
            logger.info("│   ├── train/")
            logger.info("│   └── val/")
            logger.info("└── data.yaml")
            self.model = None
            return
        
        self._setup_dataset()
    
    def _setup_dataset(self):
        """Setup dataset and validate structure"""
        # Check data.yaml
        data_yaml_path = self.dataset_path / "data.yaml"
        if not data_yaml_path.exists():
            self._create_data_yaml()
        
        # Load data configuration
        with open(data_yaml_path, 'r') as f:
            self.data_yaml = yaml.safe_load(f)
        
        logger.info(f"Dataset loaded: {self.data_yaml}")
        return True
    
    def _create_data_yaml(self):
        """Create data.yaml configuration file"""
        data_config = {
            'train': str(self.dataset_path / 'images' / 'train'),
            'val': str(self.dataset_path / 'images' / 'val'),
            'nc': 2,  # Number of classes
            'names': ['weed', 'crop']  # Class names
        }
        
        with open(self.dataset_path / "data.yaml", 'w') as f:
            yaml.dump(data_config, f, default_flow_style=False)
        
        logger.info("Created data.yaml configuration")
    
    def load_model(self, pretrained=True):
        """Load YOLO model"""
        if pretrained:
            self.model = YOLO(f'yolov8{self.model_size}.pt')
            logger.info(f"Loaded pretrained YOLOv8{self.model_size} model")
        else:
            self.model = YOLO(f'yolov8{self.model_size}.yaml')
            logger.info(f"Created new YOLOv8{self.model_size} model")
        
        return self.model
    
    def train(self, epochs=15, imgsz=416, batch=8, device='auto'):
        """
        Train YOLO model
        
        Args:
            epochs: Number of training epochs
            imgsz: Image size for training
            batch: Batch size
            device: Training device (auto, cpu, 0, 1, etc.)
        """
        if not self.model:
            logger.error("Model not loaded. Call load_model() first.")
            return None
        
        logger.info(f"Starting training with {epochs} epochs, imgsz={imgsz}, batch={batch}")
        
        # Training configuration optimized for speed
        results = self.model.train(
            data=str(self.dataset_path / "data.yaml"),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device='cpu',  # Force CPU since CUDA not available
            name='train',
            project='runs/detect',
            exist_ok=True,
            pretrained=True,
            optimizer='Adam',
            lr0=0.01,
            weight_decay=0.0005,
            warmup_epochs=3,
            warmup_momentum=0.8,
            box=7.5,
            cls=0.5,
            dfl=1.5,
            patience=50,
            save_period=5,
            # Speed optimizations
            workers=2,  # Reduce workers for CPU
            amp=False,  # Disable Automatic Mixed Precision for CPU
        )
        
        logger.info("Training completed!")
        logger.info(f"Best model saved at: runs/detect/train/weights/best.pt")
        
        return results
    
    def validate_model(self):
        """Validate trained model"""
        if not self.model:
            logger.error("Model not loaded")
            return None
        
        logger.info("Validating model...")
        results = self.model.val(
            data=str(self.dataset_path / "data.yaml"),
            imgsz=416,
            batch=8,  # Smaller batch for CPU
            device='cpu'  # Force CPU
        )
        
        logger.info(f"Validation completed. mAP50: {results.box.map50:.3f}")
        return results
    
    def export_model(self, format='onnx'):
        """Export model to different formats"""
        if not self.model:
            logger.error("Model not loaded")
            return False
        
        model_path = 'runs/detect/train/weights/best.pt'
        if not Path(model_path).exists():
            logger.error("Trained model not found")
            return False
        
        # Load best model and export
        best_model = YOLO(model_path)
        exported_path = best_model.export(format=format)
        
        logger.info(f"Model exported to {exported_path}")
        return True

def create_sample_dataset():
    """Create a sample dataset structure for testing"""
    dataset_path = Path("dataset")
    
    # Create directories
    (dataset_path / "images" / "train").mkdir(parents=True, exist_ok=True)
    (dataset_path / "images" / "val").mkdir(parents=True, exist_ok=True)
    (dataset_path / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (dataset_path / "labels" / "val").mkdir(parents=True, exist_ok=True)
    
    logger.info("Created sample dataset structure")
    logger.info("Please add your images and label files to:")
    logger.info(f"{dataset_path}/images/train/")
    logger.info(f"{dataset_path}/images/val/")
    logger.info(f"{dataset_path}/labels/train/")
    logger.info(f"{dataset_path}/labels/val/")

def main():
    """Main training function"""
    logger.info("YOLO Weed Detection Training")
    logger.info("=" * 40)
    
    # Initialize trainer
    trainer = YOLOTrainer(dataset_path="dataset", model_size="n")
    
    if not trainer.dataset_path.exists():
        create_sample_dataset()
        return
    
    # Load model
    trainer.load_model(pretrained=True)
    
    # Train model
    results = trainer.train(
        epochs=15,
        imgsz=416,
        batch=8,
        device='auto'  # Use GPU if available
    )
    
    if results:
        # Validate model
        trainer.validate_model()
        
        # Export model
        trainer.export_model(format='onnx')
        
        logger.info("Training pipeline completed successfully!")
    else:
        logger.error("Training failed!")

if __name__ == "__main__":
    main()
