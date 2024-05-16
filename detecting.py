import os
import mss
import mss.tools
from PIL import Image


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
        print("Saved as: cropped_screenshot.png")
        os.remove(self.screenshot_path)





#Ex
screen_capture = ScreenCapture()
screen_capture.crop_image()
