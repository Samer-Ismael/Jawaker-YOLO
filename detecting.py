import logging
import os
import time
import gc  # For garbage collection
import traceback
import threading

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

_model = None
_file_lock = threading.Lock()

def load_model():
    """Load YOLO model with proper safe globals handling"""
    global _model
    if _model is not None:
        return _model
        
    try:
        safe_modules = [
            Module, ModuleList, Sequential,
            Conv2d, BatchNorm2d, MaxPool2d,
            SiLU, Upsample, 
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
        
        def custom_torch_load(file, **kwargs):
            return torch.load(file, map_location="cpu", weights_only=False), file

        import ultralytics.nn.tasks
        original_torch_safe_load = ultralytics.nn.tasks.torch_safe_load
        ultralytics.nn.tasks.torch_safe_load = custom_torch_load
        
        try:
            _model = YOLO("best.pt", task='detect')
            
            if not hasattr(_model, 'predict'):
                logging.error("Model loaded but predict method not found")
                return None
                
            logging.info("Model loaded successfully")
            return _model
        finally:
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
        self.current_files = set()  # Track current operation's files
        
        # Create necessary directories with absolute paths
        self.base_dir = os.path.abspath(os.getcwd())
        self.frontend_dir = os.path.join(self.base_dir, 'frontend')
        self.temp_dir = os.path.join(self.frontend_dir, 'temp')
        os.makedirs(self.frontend_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        # Initialize monitor settings
        with mss.mss() as sct:
            monitors = sct.monitors
            if self.display_index >= len(monitors):
                logging.warning(f"Display index {self.display_index} out of range. Using primary monitor.")
                self.display_index = 1
            self.monitor = monitors[self.display_index].copy()

    def _cleanup_temp_files(self):
        """Clean up temporary files but preserve current operation's files"""
        try:
            with _file_lock:
                if os.path.exists(self.temp_dir):
                    current_time = time.time()
                    for filename in os.listdir(self.temp_dir):
                        try:
                            file_path = os.path.join(self.temp_dir, filename)
                            # Don't delete files from current operation
                            if file_path in self.current_files:
                                continue
                            if os.path.isfile(file_path):
                                # Check file age (5 seconds)
                                if current_time - os.path.getctime(file_path) > 5:
                                    os.remove(file_path)
                        except Exception as e:
                            logging.warning(f"Failed to remove temp file {filename}: {e}")
        except Exception as e:
            logging.warning(f"Error during cleanup: {e}")

    def crop_image(self):
        temp_screenshot = None
        cropped_path = None
        self.current_files.clear()  # Clear previous operation's files
        
        try:
            # Clean up old files before starting
            self._cleanup_temp_files()

            # Generate unique filenames for this capture
            timestamp = int(time.time() * 1000)
            temp_screenshot = os.path.join(self.temp_dir, f'temp_screenshot_{timestamp}.png')
            cropped_path = os.path.join(self.temp_dir, f'cropped_{timestamp}.png')
            frontend_path = os.path.join(self.frontend_dir, 'live_view.png')

            # Track files for this operation
            self.current_files.update([temp_screenshot, cropped_path])

            # Capture screenshot
            with mss.mss() as sct:
                screenshot = sct.grab(self.monitor)
                png_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
                
                # Save screenshot with exclusive access
                with _file_lock:
                    # Save temp screenshot
                    with open(temp_screenshot, 'wb') as f:
                        f.write(png_bytes)
                    
                    if not os.path.exists(temp_screenshot):
                        raise FileNotFoundError("Failed to save temporary screenshot")
                    
                    # Process image
                    with Image.open(temp_screenshot) as img:
                        crop_region = (880, 140, 1080, 380)
                        cropped_img = img.crop(crop_region)
                        # Save cropped image for detection
                        cropped_img.save(cropped_path)
                        # Save to frontend
                        cropped_img.save(frontend_path)
                        cropped_img.close()

                    # Verify files exist
                    if not os.path.exists(cropped_path):
                        raise FileNotFoundError("Failed to save cropped image")
                    if not os.path.exists(frontend_path):
                        raise FileNotFoundError("Failed to save frontend image")

            return cropped_path

        except Exception as e:
            logging.error(f"Error in crop_image: {str(e)}")
            if temp_screenshot and os.path.exists(temp_screenshot):
                try:
                    os.remove(temp_screenshot)
                except:
                    pass
            if cropped_path and os.path.exists(cropped_path):
                try:
                    os.remove(cropped_path)
                except:
                    pass
            return None


def detect():
    screen_capture = ScreenCapture()
    max_retries = 3
    retry_delay = 0.1  # 100ms between retries
    
    for attempt in range(max_retries):
        try:
            cropped_path = screen_capture.crop_image()
            if not cropped_path:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                logging.error("Failed to capture screenshot after retries")
                return []
                
            if not os.path.exists(cropped_path):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                logging.error("Screenshot file not found after retries")
                return []

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
                model = load_model()
                if model is None:
                    return []

                with _file_lock:
                    if not os.path.exists(cropped_path):
                        logging.error("Screenshot file disappeared before prediction")
                        return []
                        
                    results = model.predict(cropped_path, conf=0.8)
                    result = results[0]

                class_ids = result.boxes.cls.tolist()
                detected_classes = [result.names[class_id] for class_id in class_ids]
                unique_detected_classes = list(set(detected_classes))
                
                if unique_detected_classes:
                    logging.info(f"Detected cards: {unique_detected_classes}")
                
                return unique_detected_classes

            finally:
                YOLO.predict = original_predict
                screen_capture._cleanup_temp_files()  # Clean up after prediction
                
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Detection attempt {attempt + 1} failed: {str(e)}")
                time.sleep(retry_delay)
                continue
            logging.error(f"Error during detection: {str(e)}")
            return []
        finally:
            gc.collect()
            
    return []  # If all retries failed


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
