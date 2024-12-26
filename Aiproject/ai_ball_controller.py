import pyautogui
import math
import time

class BallController:
    def __init__(self):
        # Disable pyautogui's fail-safe
        pyautogui.FAILSAFE = False
        self.base_power = 100  # Base power for shots

    def execute_action(self, action):
        """
        Execute the shooting action based on the AI's decision
        action: tuple (angle, power)
        """
        try:
            angle, power = action
            
            # Calculate shot trajectory
            distance = power * self.base_power
            x_offset = distance * math.cos(math.radians(angle))
            y_offset = distance * math.sin(math.radians(angle))
            
            # Get current mouse position
            start_x, start_y = pyautogui.position()
            
            # Click and drag
            pyautogui.mouseDown()
            pyautogui.moveRel(x_offset, y_offset, duration=0.2)
            pyautogui.mouseUp()
            
            # Return to starting position
            time.sleep(0.1)
            pyautogui.moveTo(start_x, start_y)
            
        except Exception as e:
            print(f"Error executing ball control: {e}") 