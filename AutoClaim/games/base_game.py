import pyautogui
import time
import keyboard
from pynput.mouse import Button, Controller
from config import COLORS

class BaseGame:
    name = "Base Game"
    description = "Base game class"
    assets_path = "assets/base/"

    def __init__(self, window):
        self.window = window
        self.mouse = Controller()
        self.running = True
        self.paused = False

    def get_window_region(self):
        return (
            self.window.left,
            self.window.top,
            self.window.width,
            self.window.height
        )

    def find_and_click_button(self, image_path, confidence=0.7):
        window_region = self.get_window_region()
        try:
            button = pyautogui.locateOnScreen(image_path, confidence=confidence, region=window_region)
            if button:
                x, y = pyautogui.center(button)
                self.click(x, y)
                return True
        except:
            pass
        return False

    def click(self, x, y):
        self.mouse.position = (x, y)
        self.mouse.press(Button.left)
        self.mouse.release(Button.left)
        time.sleep(0.1)

    def handle_hotkeys(self):
        if keyboard.is_pressed('K'):
            self.paused = not self.paused
            if self.paused:
                print(f"{COLORS['BLUE']}Bot paused... Press K to continue{COLORS['RESET']}")
            else:
                print(f"{COLORS['BLUE']}Bot continuing...{COLORS['RESET']}")
            time.sleep(0.2)

        if keyboard.is_pressed('S'):
            print(f"{COLORS['RED']}Stopping...{COLORS['RESET']}")
            self.running = False
            
        if keyboard.is_pressed('B'):
            print(f"{COLORS['YELLOW']}Returning to main menu...{COLORS['RESET']}")
            self.running = False
            return True
            
        return False

    def run(self):
        raise NotImplementedError("Each game must implement its own run method") 