import logging
import os
import mss
import mss.tools
from PIL import Image
from ultralytics import YOLO


class ScreenCapture:
    def __init__(self, display_index=-1):
        self.display_index = display_index
        self.screenshot_path = None

    def crop_image(self):
        with mss.mss() as sct:
            monitor = sct.monitors[self.display_index]
            screenshot = sct.grab(monitor)
            self.screenshot_path = 'secondary_display_screenshot_that_will_be_deleted.png'
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=self.screenshot_path)

        img = Image.open(self.screenshot_path)
        crop_region = (880, 100, 1080, 380)
        cropped_img = img.crop(crop_region)
        cropped_img.save('cropped_screenshot.png')
        os.remove(self.screenshot_path)


# This will return a list of the classes that are being detected in the picture
def detect():
    screen_capture = ScreenCapture()
    screen_capture.crop_image()

    # This will remove the annoying logging text that will be printed out everytime.
    def custom_predict(self, *args, **kwargs):
        logging.disable(logging.ERROR)
        results = original_predict(self, *args, **kwargs)
        logging.disable(logging.NOTSET)
        return results

    original_predict = YOLO.predict
    YOLO.predict = custom_predict

    model = YOLO("best.pt")
    results = model.predict("cropped_screenshot.png", conf=0.8)
    result = results[0]

    class_ids = result.boxes.cls.tolist()
    detected_classes = [result.names[class_id] for class_id in class_ids]
    unique_detected_classes = list(set(detected_classes))
    return unique_detected_classes


detected_cards = set()


def updating_list():
    global detected_cards
    new_class_list = set(detect())
    new_cards = new_class_list - detected_cards
    detected_cards.update(new_cards)
    updated_list = list(detected_cards)

    return updated_list


if __name__ == '__main__':
    while True:
        # Get updated list of detected cards
        updated_list = updating_list()
        print(updated_list)

        # Check if the updated list is empty (game restarted)
        if not detect():
            # Clear the global set of detected cards
            detected_cards = set()
