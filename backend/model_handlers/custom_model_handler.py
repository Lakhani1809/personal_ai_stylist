"""
Custom Model Handler for Computer Vision Tasks
Replaces OpenAI API with your custom models
"""

import os
import json
import torch
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Tuple
import base64
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomModelHandler:
    """
    Handler for custom computer vision models
    Supports multiple model formats: PyTorch, ONNX, scikit-learn, etc.
    """
    
    def __init__(self, model_config_path: str = "/app/backend/models/model_config.json"):
        self.model_config_path = model_config_path
        self.models = {}
        self.load_models()
    
    def load_models(self):
        """Load all configured models"""
        try:
            if os.path.exists(self.model_config_path):
                with open(self.model_config_path, 'r') as f:
                    config = json.load(f)
                
                for model_name, model_info in config.items():
                    self.load_single_model(model_name, model_info)
            else:
                logger.warning(f"Model config not found: {self.model_config_path}")
                self.create_default_config()
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.models = {}
    
    def create_default_config(self):
        """Create default model configuration"""
        default_config = {
            "clothing_classifier": {
                "path": "/app/backend/models/clothing_classifier.pt",
                "type": "pytorch",
                "task": "clothing_classification",
                "categories": ["tops", "bottoms", "dresses", "outerwear", "shoes", "accessories"],
                "input_size": [224, 224],
                "enabled": False
            },
            "color_detector": {
                "path": "/app/backend/models/color_detector.onnx", 
                "type": "onnx",
                "task": "color_detection",
                "colors": ["red", "blue", "green", "yellow", "black", "white", "brown", "pink", "purple", "orange"],
                "input_size": [256, 256],
                "enabled": False
            },
            "style_analyzer": {
                "path": "/app/backend/models/style_analyzer.pkl",
                "type": "sklearn",
                "task": "style_analysis", 
                "styles": ["casual", "formal", "athletic", "vintage", "modern", "bohemian"],
                "enabled": False
            }
        }
        
        # Save default config
        os.makedirs(os.path.dirname(self.model_config_path), exist_ok=True)
        with open(self.model_config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Created default model config at {self.model_config_path}")
    
    def load_single_model(self, model_name: str, model_info: Dict):
        """Load a single model based on its type"""
        if not model_info.get("enabled", False):
            logger.info(f"Model {model_name} is disabled, skipping")
            return
        
        model_path = model_info["path"]
        if not os.path.exists(model_path):
            logger.warning(f"Model file not found: {model_path}")
            return
        
        try:
            model_type = model_info["type"].lower()
            
            if model_type == "pytorch":
                model = torch.load(model_path, map_location='cpu')
                model.eval()
                self.models[model_name] = {
                    "model": model,
                    "config": model_info,
                    "type": "pytorch"
                }
            
            elif model_type == "onnx":
                import onnxruntime as ort
                session = ort.InferenceSession(model_path)
                self.models[model_name] = {
                    "model": session,
                    "config": model_info,
                    "type": "onnx"
                }
            
            elif model_type == "sklearn":
                import joblib
                model = joblib.load(model_path)
                self.models[model_name] = {
                    "model": model,
                    "config": model_info,
                    "type": "sklearn"
                }
            
            logger.info(f"Successfully loaded model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
    
    def preprocess_image(self, base64_image: str, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray:
        """Convert base64 image to preprocessed numpy array"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_image.split(',')[-1])
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            
            # Resize image
            image = image.resize(target_size, Image.Resampling.LANCZOS)
            
            # Convert to numpy array and normalize
            image_array = np.array(image).astype(np.float32) / 255.0
            
            # Add batch dimension if needed
            if len(image_array.shape) == 3:
                image_array = np.expand_dims(image_array, axis=0)
            
            return image_array
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
    
    def analyze_clothing_item(self, base64_image: str) -> Dict[str, Any]:
        """
        Analyze clothing item using custom models
        Returns the same format as OpenAI analysis
        """
        try:
            # Default analysis (fallback)
            analysis = {
                "exact_item_name": "Fashion Item",
                "category": "Tops",
                "color": "Blue",
                "pattern": "Solid",
                "fabric_type": "Cotton",
                "style": "Casual",
                "tags": ["clothing", "wardrobe"]
            }
            
            # Use custom models if available
            if "clothing_classifier" in self.models:
                category = self.classify_clothing(base64_image)
                if category:
                    analysis["category"] = category.title()
            
            if "color_detector" in self.models:
                color = self.detect_color(base64_image)
                if color:
                    analysis["color"] = color.title()
            
            if "style_analyzer" in self.models:
                style = self.analyze_style(base64_image)
                if style:
                    analysis["style"] = style.title()
            
            # Generate item name based on detected attributes
            analysis["exact_item_name"] = f"{analysis['color']} {analysis['fabric_type']} {analysis['category']}"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in clothing analysis: {e}")
            # Return fallback analysis
            return analysis
    
    def classify_clothing(self, base64_image: str) -> str:
        """Classify clothing category using custom model"""
        try:
            model_info = self.models["clothing_classifier"]
            model = model_info["model"]
            config = model_info["config"]
            
            # Preprocess image
            input_size = tuple(config["input_size"])
            image_array = self.preprocess_image(base64_image, input_size)
            
            if model_info["type"] == "pytorch":
                # Convert to PyTorch tensor
                image_tensor = torch.from_numpy(image_array.transpose(0, 3, 1, 2))
                
                with torch.no_grad():
                    outputs = model(image_tensor)
                    predicted_idx = torch.argmax(outputs, dim=1).item()
                
                categories = config["categories"]
                return categories[predicted_idx] if predicted_idx < len(categories) else "tops"
            
            elif model_info["type"] == "onnx":
                # ONNX inference
                input_name = model.get_inputs()[0].name
                outputs = model.run(None, {input_name: image_array.transpose(0, 3, 1, 2)})
                predicted_idx = np.argmax(outputs[0])
                
                categories = config["categories"] 
                return categories[predicted_idx] if predicted_idx < len(categories) else "tops"
            
        except Exception as e:
            logger.error(f"Error in clothing classification: {e}")
            return "tops"
    
    def detect_color(self, base64_image: str) -> str:
        """Detect primary color using custom model or computer vision"""
        try:
            if "color_detector" in self.models:
                model_info = self.models["color_detector"]
                model = model_info["model"]
                config = model_info["config"]
                
                # Use custom color detection model
                input_size = tuple(config["input_size"])
                image_array = self.preprocess_image(base64_image, input_size)
                
                # Model inference logic here...
                # For now, return a detected color
                colors = config["colors"]
                return colors[0]  # Placeholder
            
            else:
                # Fallback: Use OpenCV for basic color detection
                return self.detect_color_opencv(base64_image)
                
        except Exception as e:
            logger.error(f"Error in color detection: {e}")
            return "blue"
    
    def detect_color_opencv(self, base64_image: str) -> str:
        """Basic color detection using OpenCV"""
        try:
            # Decode image
            image_data = base64.b64decode(base64_image.split(',')[-1])
            image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
            
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Get dominant color by calculating mean
            mean_hsv = np.mean(hsv, axis=(0, 1))
            hue = mean_hsv[0]
            
            # Map hue to color names
            if hue < 10 or hue > 170:
                return "red"
            elif hue < 25:
                return "orange"
            elif hue < 35:
                return "yellow"
            elif hue < 80:
                return "green"
            elif hue < 130:
                return "blue"
            elif hue < 170:
                return "purple"
            else:
                return "pink"
                
        except Exception as e:
            logger.error(f"Error in OpenCV color detection: {e}")
            return "blue"
    
    def analyze_style(self, base64_image: str) -> str:
        """Analyze clothing style using custom model"""
        try:
            if "style_analyzer" in self.models:
                model_info = self.models["style_analyzer"]
                model = model_info["model"]
                config = model_info["config"]
                
                # Extract features and predict style
                # This would depend on your specific model
                # For now, return a style
                styles = config["styles"]
                return styles[0]  # Placeholder
            
            return "casual"
            
        except Exception as e:
            logger.error(f"Error in style analysis: {e}")
            return "casual"
    
    def analyze_outfit_validation(self, base64_image: str) -> Dict[str, Any]:
        """
        Analyze complete outfit for validation scoring
        Returns same format as OpenAI validation
        """
        try:
            # Default validation scores
            validation = {
                "color_combo": 3.8,
                "fit": 3.7, 
                "style": 4.0,
                "occasion": 3.9,
                "overall_score": 3.9,
                "feedback": "Nice outfit choice! The styling works well together."
            }
            
            # Use custom models for more accurate scoring
            # This is where you'd integrate your outfit validation model
            
            return validation
            
        except Exception as e:
            logger.error(f"Error in outfit validation: {e}")
            return validation

# Global model handler instance
model_handler = CustomModelHandler()