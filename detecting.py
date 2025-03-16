import logging
import os
import time
import gc  # For garbage collection
import traceback

import mss
import mss.tools
from PIL import Image
from ultralytics import YOLO
import torch
import torch.serialization
from torch.nn import (
    Module, ModuleList, Sequential,
    Conv2d, BatchNorm2d, MaxPool2d,
    SiLU, Upsample
)
from ultralytics.nn.tasks import DetectionModel
from ultralytics.nn.modules.block import C2f, Bottleneck, SPPF
from ultralytics.nn.modules.conv import Conv
from ultralytics.nn.modules.head import Detect

logging.basicConfig(level=logging.INFO)

# Global model instance to avoid reloading
_model = None

def load_model():
    """Load YOLO model with proper safe globals handling"""
    global _model
    if _model is not None:
        return _model
        
    try:
        # Add all required modules to safe globals
        safe_modules = [
            # PyTorch base modules
            Module, ModuleList, Sequential,
            Conv2d, BatchNorm2d, MaxPool2d,
            SiLU, Upsample,  # Added Upsample
            # Ultralytics specific modules
            DetectionModel,
            Conv, C2f, Bottleneck, SPPF,
            Detect
        ]
        
        for module in safe_modules:
            try:
                torch.serialization.add_safe_globals([module])
                logging.info(f"Added {module.__name__} to safe globals")
            except Exception as e:
                logging.error(f"Failed to add {module.__name__}: {e}")
        
        # Override ultralytics' torch_safe_load to use weights_only=False
        def custom_torch_load(file, **kwargs):
            return torch.load(file, map_location="cpu", weights_only=False), file

        # Temporarily replace torch_safe_load
        import ultralytics.nn.tasks
        original_torch_safe_load = ultralytics.nn.tasks.torch_safe_load
        ultralytics.nn.tasks.torch_safe_load = custom_torch_load
        
        try:
            # Load model with explicit task
            _model = YOLO("best.pt", task='detect')
            
            # Verify model loaded correctly
            if not hasattr(_model, 'predict'):
                logging.error("Model loaded but predict method not found")
                return None
                
            logging.info("Model loaded successfully")
            return _model
        finally:
            # Restore original torch_safe_load
            ultralytics.nn.tasks.torch_safe_load = original_torch_safe_load
        
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        if hasattr(e, '__traceback__'):
            logging.error(f"Traceback: {traceback.format_exc()}")
        return None

class ScreenCapture:
    def __init__(self, display_index=1):
        self.display_index = display_index
        self.screenshot_path = None
        self.last_cleanup_time = time.time()
        
        # Ensure frontend directory exists
        os.makedirs('frontend', exist_ok=True)

    def crop_image(self):
        try:
            # Periodic cleanup of any stray temporary files (every 5 minutes)
            current_time = time.time()
            if current_time - self.last_cleanup_time > 300:
                self._cleanup_temp_files()
                self.last_cleanup_time = current_time

            with mss.mss() as sct:
                monitor = sct.monitors[self.display_index]
                screenshot = sct.grab(monitor)
                self.screenshot_path = 'temp_screenshot.png'
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.screenshot_path)

            img = Image.open(self.screenshot_path)
            try:
                crop_region = (880, 140, 1080, 380)
                cropped_img = img.crop(crop_region)
                
                # Save to frontend directory
                frontend_path = os.path.join('frontend', 'live_view.png')
                cropped_img.save(frontend_path)
                
                # Also save a copy for detection
                cropped_img.save('cropped_screenshot.png')
                cropped_img.close()
            finally:
                img.close()
        except Exception as e:
            logging.error(f"Error in crop_image: {e}")
            raise
        finally:
            self._cleanup_temp_files()

    def _cleanup_temp_files(self):
        """Clean up temporary files but preserve the frontend image"""
        temp_files = ['temp_screenshot.png']  # Don't delete live_view.png
        for file in temp_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                logging.warning(f"Failed to remove temporary file {file}: {e}")
        self.screenshot_path = None


def detect():
    screen_capture = ScreenCapture()
    try:
        screen_capture.crop_image()

        def custom_predict(self, *args, **kwargs):
            try:
                logging.disable(logging.ERROR)
                results = original_predict(self, *args, **kwargs)
                return results
            finally:
                logging.disable(logging.NOTSET)

        original_predict = YOLO.predict
        YOLO.predict = custom_predict

        try:
            # Get or create model instance
            model = load_model()
            if model is None:
                return []
            
            if not os.path.exists("cropped_screenshot.png"):
                logging.error("Screenshot file not found")
                return []

            results = model.predict("cropped_screenshot.png", conf=0.8)
            result = results[0]

            class_ids = result.boxes.cls.tolist()
            detected_classes = [result.names[class_id] for class_id in class_ids]
            unique_detected_classes = list(set(detected_classes))
            
            return unique_detected_classes

        finally:
            # Restore original predict method
            YOLO.predict = original_predict
            
    except Exception as e:
        logging.error(f"Error during detection: {e}")
        return []
    finally:
        # Clean up detection image but keep frontend image
        try:
            if os.path.exists("cropped_screenshot.png"):
                os.remove("cropped_screenshot.png")
        except Exception as e:
            logging.warning(f"Failed to cleanup detection image: {e}")
        gc.collect()


detected_cards = set()
last_gc_time = time.time()
last_error_time = 0
error_cooldown = 5  # seconds

def updating_list():
    global detected_cards, last_gc_time, last_error_time
    try:
        # Memory management: Run garbage collection periodically (every 60 seconds)
        current_time = time.time()
        if current_time - last_gc_time > 60:
            gc.collect()
            last_gc_time = current_time

        new_class_list = set(detect())
        new_cards = new_class_list - detected_cards
        if new_cards:
            detected_cards.update(new_cards)
        elif not new_class_list:
            detected_cards.clear()

        updated_list = list(detected_cards)
        print("Updated list of detected cards:", updated_list)
        return updated_list

    except Exception as e:
        # Error rate limiting
        current_time = time.time()
        if current_time - last_error_time > error_cooldown:
            logging.error(f"Error in updating_list: {e}")
            last_error_time = current_time
        return list(detected_cards)
