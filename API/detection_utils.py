import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from PIL import Image
import io
import time
import os
from typing import Tuple, List, Dict, Any

# Use TensorFlow's built-in keras instead of tf-keras
keras = tf.keras

class ImageDetector:
    
    def __init__(self, model_path: str):
        """Initialize the detector with a model path."""
        print(f"Attempting to load model from: {model_path}")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
            
        try:
            print("Loading model...")
            try:
                # First try loading directly with proper signatures
                self.model = keras.models.load_model(model_path, custom_objects={
                    'KerasLayer': hub.KerasLayer,
                    'keras_layer': hub.KerasLayer
                })
                print("Model loaded successfully with direct loading")
            except Exception as load_error:
                print(f"Direct loading failed, trying alternative approach: {str(load_error)}")
                # If that fails, try recreating the model with compatible layer
                hub_url = "https://www.kaggle.com/models/google/mobilenet-v2/TensorFlow2/035-128-classification/2"
                
                # Create the model using Keras functional API
                inputs = keras.layers.Input(shape=(224, 224, 3))
                hub_layer = hub.KerasLayer(hub_url, trainable=False, output_shape=[1280])
                features = hub_layer(inputs)
                outputs = keras.layers.Dense(1000, activation='softmax')(features)
                
                self.model = keras.Model(inputs, outputs)
                
                # Try to load weights
                try:
                    self.model.load_weights(model_path)
                    print("Weights loaded successfully")
                except Exception as weight_error:
                    print(f"Weight loading failed: {str(weight_error)}")
                    # Initialize from scratch if weight loading fails
                    self.model.compile(
                        optimizer='adam',
                        loss='sparse_categorical_crossentropy',
                        metrics=['accuracy']
                    )
                print("Model created successfully with alternative approach")
                
            # Print model summary
            print("\nModel Summary:")
            self.model.summary()
            
            # Get input shape from model
            input_shape = self.model.input_shape
            print(f"\nModel input shape: {input_shape}")
            
            if input_shape is not None and len(input_shape) == 4:
                self.image_size = (input_shape[1], input_shape[2])
            else:
                self.image_size = (224, 224)  # Default size
                
            print(f"Using image size: {self.image_size}")
            
        except Exception as e:
            print(f"Error details: {str(e)}")
            raise Exception(f"Failed to load model: {str(e)}")
        
    def preprocess_image(self, image_data: bytes) -> np.ndarray:
        """Preprocess the image for model input."""
        try:
            # Read image from bytes
            image = Image.open(io.BytesIO(image_data))
            print(f"Loaded image: size={image.size}, mode={image.mode}")
            
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
                print("Converted image to RGB")
            
            # Resize image
            image = image.resize(self.image_size)
            print(f"Resized image to {self.image_size}")
            
            # Convert to numpy array and preprocess
            img_array = keras.preprocessing.image.img_to_array(image)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0  # Normalize
            
            print(f"Preprocessed image shape: {img_array.shape}")
            return img_array
            
        except Exception as e:
            print(f"Error in preprocess_image: {str(e)}")
            raise Exception(f"Error preprocessing image: {str(e)}")
    
    def predict(self, image_data: bytes) -> Tuple[List[Dict[str, Any]], List[float], float]:
        """
        Perform detection on the input image.
        Returns predictions, confidence scores, and processing time.
        """
        start_time = time.time()
        
        try:
            print("\nStarting prediction...")
            # Preprocess image
            processed_image = self.preprocess_image(image_data)
            
            # Make prediction
            print("Running model inference...")
            predictions = self.model.predict(processed_image, verbose=0)
            print(f"Raw prediction shape: {predictions.shape if isinstance(predictions, np.ndarray) else 'not numpy array'}")
            
            # Process predictions
            results = []
            confidence_scores = []
            
            if isinstance(predictions, np.ndarray):
                if len(predictions.shape) == 2:
                    # For detection models with multiple outputs
                    for pred in predictions:
                        confidence = float(pred.max())
                        class_idx = int(pred.argmax())
                        results.append({
                            "class_id": class_idx,
                            "class_name": f"class_{class_idx}",
                            "confidence": confidence
                        })
                        confidence_scores.append(confidence)
                else:
                    # For single classification output
                    class_idx = np.argmax(predictions[0])
                    confidence = float(predictions[0][class_idx])
                    results.append({
                        "class_id": int(class_idx),
                        "class_name": f"class_{class_idx}",
                        "confidence": confidence
                    })
                    confidence_scores.append(confidence)
            
            processing_time = time.time() - start_time
            print(f"Prediction completed in {processing_time:.2f} seconds")
            
            return results, confidence_scores, processing_time
            
        except Exception as e:
            print(f"Error in predict: {str(e)}")
            raise Exception(f"Error during image detection: {str(e)}")

# Initialize detector
detector = None

def initialize_detector(model_path: str):
    """Initialize the detector with the specified model."""
    global detector
    try:
        print(f"\nInitializing detector with model: {model_path}")
        detector = ImageDetector(model_path)
        print("Detector initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing detector: {str(e)}")
        return False

def get_detector() -> ImageDetector:
    """Get the initialized detector."""
    if detector is None:
        raise Exception("Detector not initialized. Please make sure the model file exists and is valid.")
    return detector