import numpy as np
import pyautogui
from PIL import Image

class ScreenCapture:
    def __init__(self):
        self.game_region = None

    def capture_window(self, window_info):
        """Capture screenshot of the Telegram window"""
        try:
            # Capture the window area
            screenshot = pyautogui.screenshot(
                region=(
                    window_info['left'],
                    window_info['top'],
                    window_info['width'],
                    window_info['height']
                )
            )
            return np.array(screenshot)
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None

    def set_game_region(self, x1, y1, x2, y2):
        """Set specific region where the game is located"""
        self.game_region = (x1, y1, x2, y2)

    def get_game_screen(self, window_info):
        """Capture only the game area"""
        full_screen = self.capture_window(window_info)
        if full_screen is not None and self.game_region:
            x1, y1, x2, y2 = self.game_region
            return full_screen[y1:y2, x1:x2]
        return full_screen 